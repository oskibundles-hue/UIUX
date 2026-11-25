#!/usr/bin/env python3
"""QR lead callback server for Omarie's Formula Dynamics referrals.

A person scans the QR, fills in index.html, and this server:
  1. validates the form and the consent tick, and refuses anything without consent;
  2. writes the lead and its consent record to leads.csv (plus the full record, with the exact
     consent wording, user agent and page URL, to consent_log.jsonl);
  3. asks the voice provider (Vapi by default, Retell as the second) to call them back,
     inside the legal calling window only;
  4. takes the provider's end-of-call report on /webhook/<provider>, writes the outcome to
     leads.csv, puts opt-outs on dnc.txt, and emails or texts Omarie a summary.

Python 3.10+, standard library only. Keys come from environment variables only (see SETUP.md).

    uv run --no-project --python 3.12 python callback_server.py --dry-run
    uv run --no-project --python 3.12 python callback_server.py --dry-run --port 8787 --data-dir /tmp/x

--dry-run logs the exact API request it would send (key redacted) to dry_run_requests.jsonl and
places no call, sends no text and no email.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import html
import io
import json
import logging
import os
import re
import secrets
import smtplib
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from datetime import datetime, timedelta
from email.message import EmailMessage
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

if sys.version_info < (3, 10):
    sys.exit("callback_server.py needs Python 3.10 or newer (try: uv run --python 3.12 ...)")

HERE = Path(__file__).resolve().parent
FD_ROOT = HERE.parent.parent  # formula-dynamics/

# leads.csv columns. Must match the tracker's LEADS tab exactly; do not reorder.
COLUMNS = ["received_at", "first_name", "phone", "car", "need", "best_time", "consent",
           "consent_text_version", "consent_ip", "source", "call_status", "call_outcome",
           "booked_time", "notes"]

NEEDS = {"Service", "Parts", "A problem", "A mod"}
BEST_TIMES = {"Morning", "Afternoon", "Evening", "Any time"}
OUTCOMES = {"booked", "transferred", "callback_requested", "not_interested", "voicemail",
            "no_answer", "opt_out", "wrong_number", "failed"}
DNC_OUTCOMES = {"opt_out", "wrong_number"}
PENDING = {"queued", "queued_window", "dialing", "dry_run"}   # a call is still on its way
REF_DEFAULT = "OMARIE"
FONT_FILES = {"BebasNeue-Regular.ttf", "BarlowCondensed-Medium.ttf", "BarlowCondensed-Bold.ttf"}
FONT_DIRS = [HERE / "fonts", FD_ROOT / "07-fonts", FD_ROOT / "11-service-reels/fonts"]

MAX_BODY = 16 * 1024
RATE_LIMIT_PER_IP = 5            # form posts per IP per hour
DEDUPE_MINUTES = 15              # one call per number per 15 minutes
MAX_CALL_SECONDS = 180           # hard cap; the prompt aims for 90 s

log = logging.getLogger("callback")


# ------------------------------------------------------------------------- settings ---------
def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


class Settings:
    def __init__(self, args: argparse.Namespace):
        self.dry_run: bool = args.dry_run
        self.data_dir = Path(args.data_dir).resolve()
        self.trust_proxy: bool = args.trust_proxy
        self.provider = env("CALLBACK_PROVIDER", "vapi").lower()
        self.tz = ZoneInfo(env("CALLBACK_TZ", "America/Los_Angeles"))
        # TCPA allows calls 8 AM to 9 PM the called person's local time; some states are
        # tighter. Default is narrower on purpose. Change only with a reason.
        self.window = parse_window(env("CALL_WINDOW", "09:00-20:00"))
        self.delay = int(env("CALL_DELAY_SECONDS", "20"))
        self.public_url = env("PUBLIC_BASE_URL", f"http://{args.host}:{args.port}").rstrip("/")
        self.webhook_token = env("WEBHOOK_TOKEN")
        self.shop_number = env("FD_SHOP_NUMBER")          # E.164, e.g. +1702...; empty = no transfer
        self.shop_hours = parse_shop_hours(env("FD_SHOP_HOURS", ""))  # empty = transfer never offered
        self.ref = env("CALLBACK_REF", REF_DEFAULT)
        self.ignore_window: bool = args.ignore_window
        if self.ignore_window and not self.dry_run:
            sys.exit("--ignore-window is for --dry-run tests only. Live calls always respect CALL_WINDOW.")

        if self.provider not in ADAPTERS:
            sys.exit(f"CALLBACK_PROVIDER must be one of {sorted(ADAPTERS)}, got {self.provider!r}")
        if not self.dry_run:
            missing = [k for k in ADAPTERS[self.provider].required_env if not env(k)]
            if not self.webhook_token:
                missing.append("WEBHOOK_TOKEN")
            if self.public_url.startswith("http://127.") or "localhost" in self.public_url:
                missing.append("PUBLIC_BASE_URL (must be the public https address)")
            if missing:
                sys.exit("Live mode needs these environment variables: " + ", ".join(missing)
                         + "\nRun with --dry-run to test without them.")


def parse_window(spec: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", spec)
    if not m:
        sys.exit(f"CALL_WINDOW must look like 09:00-20:00, got {spec!r}")
    a, b = int(m[1]) * 60 + int(m[2]), int(m[3]) * 60 + int(m[4])
    if not (8 * 60 <= a < b <= 21 * 60):
        sys.exit("CALL_WINDOW must sit inside 08:00-21:00 (the federal calling hours).")
    return a, b


DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_shop_hours(spec: str) -> dict[int, tuple[int, int]]:
    """'mon-fri 09:00-17:00; sat 10:00-14:00' -> {weekday: (start_min, end_min)}."""
    hours: dict[int, tuple[int, int]] = {}
    for part in filter(None, (p.strip().lower() for p in spec.split(";"))):
        m = re.fullmatch(r"([a-z]{3})(?:-([a-z]{3}))?\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", part)
        if not m or m[1] not in DAYS or (m[2] and m[2] not in DAYS):
            sys.exit(f"FD_SHOP_HOURS part not understood: {part!r} (want e.g. 'mon-fri 09:00-17:00')")
        d0, d1 = DAYS.index(m[1]), DAYS.index(m[2] or m[1])
        for d in range(d0, d1 + 1):
            hours[d] = (int(m[3]) * 60 + int(m[4]), int(m[5]) * 60 + int(m[6]))
    return hours


# ------------------------------------------------------------------------- prompt -----------
def prompt_block(text: str, name: str) -> str:
    m = re.search(rf"<!-- {name} -->\s*(.*?)\s*<!-- /{name} -->", text, re.S)
    if not m:
        sys.exit(f"agent_prompt.md is missing the {name} block")
    return m.group(1).strip()


def load_prompt() -> dict[str, str]:
    text = (HERE / "agent_prompt.md").read_text(encoding="utf-8")
    return {k: prompt_block(text, k.upper()) for k in ("first_message", "system_prompt", "voicemail")}


def fill(template: str, values: dict[str, str]) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m[1], m[0]), template)


# ------------------------------------------------------------------------- consent ----------
class Consent:
    """The consent wording lives in index.html. Its hash is pinned per version in
    consent_texts.json, so a lead's version always points at the exact words they ticked."""

    def __init__(self):
        page = (HERE / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<p id="consent-text" data-version="([^"]+)">(.*?)</p>', page, re.S)
        hidden = re.search(r'name="consent_text_version" value="([^"]+)"', page)
        if not m or not hidden:
            sys.exit("index.html: consent text or consent_text_version field not found")
        self.version = m[1]
        if hidden[1] != self.version:
            sys.exit(f"index.html: hidden consent_text_version {hidden[1]!r} does not match "
                     f"data-version {self.version!r}")
        self.text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", m[2])).split())
        self.sha256 = hashlib.sha256(self.text.encode()).hexdigest()

        reg_path = HERE / "consent_texts.json"
        reg = json.loads(reg_path.read_text()) if reg_path.exists() else {}
        known = reg.get(self.version)
        if known and known["sha256"] != self.sha256:
            sys.exit(f"Consent text in index.html changed but its version {self.version!r} did not. "
                     "Give the new wording a new version (both places in index.html).")
        if not known:
            reg[self.version] = {"sha256": self.sha256, "text": self.text,
                                 "first_seen": datetime.now().astimezone().isoformat(timespec="seconds")}
            reg_path.write_text(json.dumps(reg, indent=2) + "\n")
            log.info("consent text %s registered (sha256 %s)", self.version, self.sha256[:12])


# ------------------------------------------------------------------------- storage ----------
def csv_safe(v: str) -> str:
    """Stop spreadsheet formula injection from form text."""
    v = v.replace("\r", " ").replace("\n", " ").strip()
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t") else v


class Store:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.leads = data_dir / "leads.csv"
        self.consent_log = data_dir / "consent_log.jsonl"
        self.dry_log = data_dir / "dry_run_requests.jsonl"
        self.notify_log = data_dir / "notifications.log"
        self.dnc = data_dir / "dnc.txt"
        self.calls = data_dir / "calls.json"           # provider call id -> lead id
        self.lock = threading.RLock()
        with self.lock:
            if not self.leads.exists() or self.leads.stat().st_size == 0:
                self.leads.write_text(",".join(COLUMNS) + "\n")
            else:
                header = self.leads.read_text().splitlines()[0]
                if header != ",".join(COLUMNS):
                    sys.exit(f"{self.leads} header does not match the required columns")

    def rows(self) -> list[dict]:
        with self.lock, self.leads.open(newline="") as f:
            return list(csv.DictReader(f))

    def append(self, row: dict):
        with self.lock, self.leads.open("a", newline="") as f:
            csv.DictWriter(f, COLUMNS).writerow({k: row.get(k, "") for k in COLUMNS})

    def update(self, lead_id: str, **changes) -> dict | None:
        with self.lock:
            rows, hit = self.rows(), None
            for r in rows:
                if lead_id_of(r) == lead_id:
                    r.update({k: v for k, v in changes.items() if v is not None})
                    hit = r
            if hit is None:
                return None
            buf = io.StringIO()
            w = csv.DictWriter(buf, COLUMNS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
            tmp = self.leads.with_suffix(".csv.tmp")
            tmp.write_text(buf.getvalue())
            os.replace(tmp, self.leads)
            return hit

    def jsonl(self, path: Path, obj: dict):
        with self.lock, path.open("a") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def dnc_has(self, e164: str) -> bool:
        with self.lock:
            return self.dnc.exists() and e164 in self.dnc.read_text().split()

    def dnc_add(self, e164: str, why: str):
        with self.lock:
            if not self.dnc_has(e164):
                with self.dnc.open("a") as f:
                    f.write(f"{e164}\t{now_iso()}\t{why}\n")

    def map_call(self, call_id: str, lead_id: str):
        with self.lock:
            m = json.loads(self.calls.read_text()) if self.calls.exists() else {}
            m[call_id] = lead_id
            self.calls.write_text(json.dumps(m, indent=1))

    def lead_for_call(self, call_id: str) -> str | None:
        with self.lock:
            return (json.loads(self.calls.read_text()) if self.calls.exists() else {}).get(call_id)


def lead_id_of(row: dict) -> str:
    m = re.match(r"lead=([a-f0-9]{10})", row.get("notes", ""))
    return m[1] if m else ""


def now_iso(tz: ZoneInfo | None = None) -> str:
    return datetime.now(tz).astimezone(tz).isoformat(timespec="seconds")


# ------------------------------------------------------------------------- validation -------
def normalise_phone(raw: str) -> str | None:
    """US numbers only. Returns E.164 (+1XXXXXXXXXX) or None."""
    d = re.sub(r"\D", "", raw or "")
    if len(d) == 11 and d[0] == "1":
        d = d[1:]
    if len(d) != 10 or d[0] in "01" or d[3] in "01":
        return None
    return "+1" + d


def display_phone(e164: str) -> str:
    d = e164[2:]
    return f"{d[:3]}-{d[3:6]}-{d[6:]}"


def clean_text(v: str, n: int) -> str:
    v = " ".join((v or "").split())
    v = re.sub(r"[{}<>`\\]", "", v)        # no template or markup characters reach the prompt
    return v[:n]


def validate(form: dict[str, str], consent: Consent) -> tuple[dict | None, str | None]:
    if form.get("consent", "").lower() not in ("yes", "on", "true", "1"):
        return None, "Consent is required. Tick the box to agree to the call."
    if form.get("consent_text_version", "") != consent.version:
        return None, "This form is out of date. Reload the page and try again."
    first = clean_text(form.get("first_name", ""), 40)
    if not re.fullmatch(r"[A-Za-zÀ-ÿ' .-]{1,40}", first or "-") or not first:
        return None, "Add your first name."
    phone = normalise_phone(form.get("phone", ""))
    if not phone:
        return None, "Add a 10-digit US mobile number."
    car = clean_text(form.get("car", ""), 80)
    if len(car) < 2:
        return None, "Add your car."
    need = form.get("need", "")
    if need not in NEEDS:
        return None, "Pick what the car needs."
    best = form.get("best_time", "")
    if best not in BEST_TIMES:
        return None, "Pick the best time for the shop to call."
    detail = clean_text(form.get("need_detail", ""), 240)
    ref = re.sub(r"[^A-Z0-9]", "", form.get("ref", "").upper())[:20]
    page = form.get("page_url", "")[:300]
    if not page.startswith(("http://", "https://")):
        page = ""
    return {"first_name": first, "e164": phone, "car": car, "need": need,
            "need_full": f"{need}: {detail}" if detail else need,
            "best_time": best, "ref": ref, "page_url": page}, None


# ------------------------------------------------------------------------- providers --------
class Adapter:
    name = ""
    required_env: list[str] = []

    def build(self, lead: dict, ctx: dict) -> dict:
        """Return {'method', 'url', 'headers', 'json'} for the outbound call."""
        raise NotImplementedError

    def call_id(self, response: dict) -> str:
        raise NotImplementedError


class VapiAdapter(Adapter):
    """Vapi: POST https://api.vapi.ai/call with an inline assistant (or VAPI_ASSISTANT_ID)."""
    name = "vapi"
    required_env = ["VAPI_API_KEY", "VAPI_PHONE_NUMBER_ID"]

    def build(self, lead, ctx):
        p, values = ctx["prompt"], ctx["values"]
        body: dict = {
            "phoneNumberId": env("VAPI_PHONE_NUMBER_ID") or "<VAPI_PHONE_NUMBER_ID>",
            "customer": {"number": lead["e164"], "name": lead["first_name"]},
        }
        if env("VAPI_ASSISTANT_ID"):
            # Assistant built in the Vapi dashboard from agent_prompt.md; just pass the values.
            body["assistantId"] = env("VAPI_ASSISTANT_ID")
            body["assistantOverrides"] = {"variableValues": values,
                                          "metadata": {"lead_id": lead["lead_id"]}}
        else:
            tools: list[dict] = [{"type": "endCall"}]
            if values["transfer_available"] == "yes":
                tools.append({
                    "type": "transferCall",
                    "destinations": [{
                        "type": "number",
                        "number": ctx["shop_number"],
                        "message": "Putting you through to Formula Dynamics now.",
                        "transferPlan": {
                            "mode": "warm-transfer-say-message",
                            "message": (f"Hi, this is Omarie's AI assistant with a referral. "
                                        f"{lead['first_name']}, {lead['car']}, needs "
                                        f"{lead['need_full']}. Putting them through now."),
                        },
                    }],
                })
            body["assistant"] = {
                "name": "FD callback for Omarie",
                "firstMessage": fill(p["first_message"], values),
                "firstMessageMode": "assistant-speaks-first",
                "model": {
                    "provider": env("VAPI_MODEL_PROVIDER", "openai"),
                    "model": env("VAPI_MODEL", "gpt-4o"),
                    "temperature": 0.3,
                    "messages": [{"role": "system", "content": fill(p["system_prompt"], values)}],
                    "tools": tools,
                },
                "voicemailMessage": fill(p["voicemail"], values),
                "endCallFunctionEnabled": True,
                "maxDurationSeconds": MAX_CALL_SECONDS,
                "serverMessages": ["end-of-call-report"],
                "server": {"url": ctx["webhook_url"]},
                "analysisPlan": {
                    "summaryPlan": {"enabled": True},
                    "structuredDataPlan": {"enabled": True, "schema": OUTCOME_SCHEMA},
                },
                "metadata": {"lead_id": lead["lead_id"], "ref": lead["ref"]},
            }
            if env("VAPI_VOICE_PROVIDER") and env("VAPI_VOICE_ID"):
                body["assistant"]["voice"] = {"provider": env("VAPI_VOICE_PROVIDER"),
                                              "voiceId": env("VAPI_VOICE_ID")}
        return {"method": "POST", "url": "https://api.vapi.ai/call",
                "headers": {"Authorization": f"Bearer {env('VAPI_API_KEY')}",
                            "Content-Type": "application/json"},
                "json": body}

    def call_id(self, response):
        return str(response.get("id", ""))


class RetellAdapter(Adapter):
    """Retell: POST https://api.retellai.com/v2/create-phone-call. The agent (prompt, voice,
    transfer, post-call fields, webhook URL) is set up in Retell's dashboard; this sends the
    per-call values."""
    name = "retell"
    required_env = ["RETELL_API_KEY", "RETELL_FROM_NUMBER"]

    def build(self, lead, ctx):
        body = {
            "from_number": env("RETELL_FROM_NUMBER") or "<RETELL_FROM_NUMBER>",
            "to_number": lead["e164"],
            "retell_llm_dynamic_variables": ctx["values"],
            "metadata": {"lead_id": lead["lead_id"], "ref": lead["ref"]},
        }
        if env("RETELL_AGENT_ID"):
            body["override_agent_id"] = env("RETELL_AGENT_ID")
        return {"method": "POST", "url": "https://api.retellai.com/v2/create-phone-call",
                "headers": {"Authorization": f"Bearer {env('RETELL_API_KEY')}",
                            "Content-Type": "application/json"},
                "json": body}

    def call_id(self, response):
        return str(response.get("call_id", ""))


ADAPTERS: dict[str, Adapter] = {"vapi": VapiAdapter(), "retell": RetellAdapter()}

OUTCOME_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": sorted(OUTCOMES)},
        "booked_time": {"type": "string",
                        "description": "Day and time the shop should call, caller's words plus the day. Empty if none."},
        "notes": {"type": "string",
                  "description": "One or two sentences for the shop: car as confirmed, need in the caller's words, urgency, any 'text instead' or 'not drivable'."},
    },
    "required": ["outcome"],
}


def redact(req: dict) -> dict:
    out = json.loads(json.dumps(req))
    for k in list(out["headers"]):
        if k.lower() == "authorization":
            v = out["headers"][k]
            out["headers"][k] = "Bearer <redacted>" if len(v) > len("Bearer ") else "Bearer <MISSING KEY>"
    return out


def http_json(req: dict, timeout: int = 20) -> dict:
    data = json.dumps(req["json"]).encode()
    r = urllib.request.Request(req["url"], data=data, method=req["method"], headers=req["headers"])
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read() or b"{}")


# ------------------------------------------------------------------------- notify -----------
def notify(app: "App", subject: str, body: str):
    """Email (SMTP) and/or text (Twilio) Omarie. Dry-run and unset config only log it."""
    app.store.jsonl(app.store.notify_log, {"at": now_iso(app.s.tz), "subject": subject, "body": body,
                                           "sent": not app.s.dry_run})
    if app.s.dry_run:
        log.info("notify (dry-run, not sent): %s", subject)
        return
    sent = False
    if env("NOTIFY_EMAIL") and env("SMTP_HOST"):
        try:
            msg = EmailMessage()
            msg["Subject"], msg["To"] = subject, env("NOTIFY_EMAIL")
            msg["From"] = env("SMTP_FROM") or env("SMTP_USER") or env("NOTIFY_EMAIL")
            msg.set_content(body)
            with smtplib.SMTP(env("SMTP_HOST"), int(env("SMTP_PORT", "587")), timeout=20) as s:
                s.starttls()
                if env("SMTP_USER"):
                    s.login(env("SMTP_USER"), env("SMTP_PASS"))
                s.send_message(msg)
            sent = True
        except Exception as e:  # never let a mail error lose the lead
            log.error("email notify failed: %s", e)
    if env("NOTIFY_SMS_TO") and env("TWILIO_ACCOUNT_SID") and env("TWILIO_AUTH_TOKEN") and env("TWILIO_FROM"):
        try:
            sid = env("TWILIO_ACCOUNT_SID")
            auth = b64encode(f"{sid}:{env('TWILIO_AUTH_TOKEN')}".encode()).decode()
            data = urllib.parse.urlencode({"To": env("NOTIFY_SMS_TO"), "From": env("TWILIO_FROM"),
                                           "Body": f"{subject}\n{body}"[:1500]}).encode()
            urllib.request.urlopen(urllib.request.Request(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data=data,
                headers={"Authorization": f"Basic {auth}"}), timeout=20).read()
            sent = True
        except Exception as e:
            log.error("sms notify failed: %s", e)
    if not sent:
        log.warning("notify: no email or SMS settings, summary only in notifications.log")


# ------------------------------------------------------------------------- app --------------
class App:
    def __init__(self, s: Settings):
        self.s = s
        self.store = Store(s.data_dir)
        self.consent = Consent()
        self.prompt = load_prompt()
        self.adapter = ADAPTERS[s.provider]
        self.hits: dict[str, list[float]] = {}
        self.hits_lock = threading.Lock()

    # -- timing
    def local_now(self) -> datetime:
        return datetime.now(self.s.tz)

    def in_window(self, t: datetime) -> bool:
        if self.s.ignore_window:
            return True
        m = t.hour * 60 + t.minute
        return self.s.window[0] <= m < self.s.window[1] - 3   # leave room for a 3-minute call

    def next_window_open(self, t: datetime) -> datetime:
        start = t.replace(hour=self.s.window[0] // 60, minute=self.s.window[0] % 60, second=0, microsecond=0)
        return start if t < start else start + timedelta(days=1)

    def transfer_available(self, t: datetime) -> bool:
        if not self.s.shop_number or t.weekday() not in self.s.shop_hours:
            return False
        a, b = self.s.shop_hours[t.weekday()]
        return a <= t.hour * 60 + t.minute < b - 5

    def rate_ok(self, ip: str) -> bool:
        now = time.time()
        with self.hits_lock:
            recent = [h for h in self.hits.get(ip, []) if now - h < 3600]
            ok = len(recent) < RATE_LIMIT_PER_IP
            if ok:
                recent.append(now)
            self.hits[ip] = recent
            return ok

    def recent_call_for(self, display: str) -> bool:
        cutoff = self.local_now() - timedelta(minutes=DEDUPE_MINUTES)
        for r in self.store.rows():
            if r["phone"] == display and r["call_status"] in PENDING:
                try:
                    if datetime.fromisoformat(r["received_at"]) >= cutoff:
                        return True
                except ValueError:
                    pass
        return False

    # -- intake
    def take_lead(self, form: dict, ip: str, ua: str, referer: str) -> tuple[int, dict]:
        if form.get("website"):                       # honeypot: bots fill it, people never see it
            log.info("honeypot hit from %s, dropped", ip)
            return 200, {"ok": True, "message": "Thanks."}
        if not self.rate_ok(ip):
            return 429, {"ok": False, "error": "Too many tries. Wait a little and try again."}
        lead, err = validate(form, self.consent)
        if err:
            log.info("REJECTED from %s: %s", ip, err)
            return 400, {"ok": False, "error": err}

        lead["lead_id"] = secrets.token_hex(5)
        lead["ref"] = lead["ref"] or self.s.ref
        lead["page_url"] = lead["page_url"] or referer[:300]
        received = now_iso(self.s.tz)
        display = display_phone(lead["e164"])

        on_dnc = self.store.dnc_has(lead["e164"])
        if not on_dnc and self.recent_call_for(display):
            return 200, {"ok": True, "message": "We already have your request. The call is on its way."}

        t = self.local_now()
        if on_dnc:
            status, msg = "skipped_dnc", ("Thanks. This number asked us not to call before, so we won't. "
                                           "Omarie will pass your details to the shop instead.")
        elif self.in_window(t):
            status, msg = "queued", ("An AI assistant calling for Omarie about Formula Dynamics will ring "
                                     "you in about two minutes.")
        else:
            opens = self.next_window_open(t)
            status = "queued_window"
            msg = (f"Thanks. It's outside calling hours, so the AI assistant will call you after "
                   f"{opens.strftime('%-I %p').lower()} {('today' if opens.date() == t.date() else 'tomorrow')}.")

        row = {
            "received_at": received,
            "first_name": csv_safe(lead["first_name"]),
            "phone": display,
            "car": csv_safe(lead["car"]),
            "need": csv_safe(lead["need_full"]),
            "best_time": lead["best_time"],
            "consent": "yes",
            "consent_text_version": self.consent.version,
            "consent_ip": ip,
            "source": csv_safe(f"qr ref={lead['ref']} page={lead['page_url'] or 'unknown'}"),
            "call_status": status,
            "call_outcome": "",
            "booked_time": "",
            "notes": f"lead={lead['lead_id']};",
        }
        self.store.append(row)
        self.store.jsonl(self.store.consent_log, {
            "lead_id": lead["lead_id"], "received_at": received, "phone_e164": lead["e164"],
            "consent": True, "consent_text_version": self.consent.version,
            "consent_text_sha256": self.consent.sha256, "consent_text": self.consent.text,
            "ip": ip, "user_agent": ua[:300], "page_url": lead["page_url"], "ref": lead["ref"],
        })
        log.info("LEAD %s stored: %s, %s, %s, status=%s", lead["lead_id"], lead["first_name"],
                 display, lead["car"], status)

        if status == "queued":
            threading.Timer(self.s.delay, self.place_call, args=(lead,)).start()
        elif status == "skipped_dnc":
            notify(self, f"FD lead (number on do-not-call): {lead['first_name']}, {lead['car']}",
                   self.summary(row, "Not called: the number is on dnc.txt. Decide by hand."))
        return 200, {"ok": True, "message": msg, "lead_id": lead["lead_id"]}

    # -- outbound call
    def call_values(self, lead: dict, t: datetime) -> dict[str, str]:
        shop = self.s.shop_number
        return {
            "first_name": lead["first_name"], "car": lead["car"], "need": lead["need_full"],
            "best_time": lead["best_time"].lower() if lead["best_time"] != "Any time" else "any time",
            "shop_phone_spoken": spoken_phone(shop) if shop else "the number on formuladynamicsperformance.com",
            "transfer_available": "yes" if self.transfer_available(t) else "no",
            "lead_id": lead["lead_id"],
        }

    def place_call(self, lead: dict):
        t = self.local_now()
        if self.store.dnc_has(lead["e164"]):
            self.store.update(lead["lead_id"], call_status="skipped_dnc")
            return
        if not self.in_window(t):
            self.store.update(lead["lead_id"], call_status="queued_window")
            return
        ctx = {"prompt": self.prompt, "values": self.call_values(lead, t),
               "shop_number": self.s.shop_number,
               "webhook_url": f"{self.s.public_url}/webhook/{self.adapter.name}?token="
                              f"{self.s.webhook_token or '<WEBHOOK_TOKEN>'}"}
        req = self.adapter.build(lead, ctx)
        if self.s.dry_run:
            entry = {"at": now_iso(self.s.tz), "lead_id": lead["lead_id"], "provider": self.adapter.name,
                     "request": redact(req)}
            self.store.jsonl(self.store.dry_log, entry)
            log.info("DRY-RUN would %s %s for lead %s (no call placed); body keys: %s",
                     req["method"], req["url"], lead["lead_id"], ", ".join(req["json"]))
            self.store.update(lead["lead_id"], call_status="dry_run")
            return
        try:
            resp = http_json(req)
            cid = self.adapter.call_id(resp)
            if cid:
                self.store.map_call(cid, lead["lead_id"])
            self.store.update(lead["lead_id"], call_status="dialing",
                              notes=f"lead={lead['lead_id']}; call={cid};")
            log.info("CALL started for lead %s: %s", lead["lead_id"], cid)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            detail = e.read().decode(errors="replace")[:300] if isinstance(e, urllib.error.HTTPError) else str(e)
            self.store.update(lead["lead_id"], call_status="error",
                              notes=f"lead={lead['lead_id']}; provider error: {detail}")
            log.error("CALL failed for lead %s: %s", lead["lead_id"], detail)
            notify(self, f"FD lead call FAILED: {lead['first_name']}",
                   f"The provider refused the call for lead {lead['lead_id']}: {detail}\n"
                   "Nobody was called. Call back by hand or fix the settings.")

    def sweep_queued(self):
        """Dial leads that came in outside calling hours, once the window opens."""
        while True:
            time.sleep(60)
            if not self.in_window(self.local_now()):
                continue
            for r in self.store.rows():
                if r["call_status"] != "queued_window":
                    continue
                lid = lead_id_of(r)
                rec = self.consent_record(lid)
                if not rec:
                    continue
                need = r["need"].lstrip("'")
                lead = {"lead_id": lid, "first_name": r["first_name"].lstrip("'"), "e164": rec["phone_e164"],
                        "car": r["car"].lstrip("'"), "need": need.split(":")[0], "need_full": need,
                        "best_time": r["best_time"], "ref": rec.get("ref", self.s.ref)}
                self.store.update(lid, call_status="queued")
                self.place_call(lead)
                time.sleep(5)

    def consent_record(self, lead_id: str) -> dict | None:
        if not self.store.consent_log.exists():
            return None
        for line in self.store.consent_log.read_text().splitlines():
            rec = json.loads(line)
            if rec.get("lead_id") == lead_id:
                return rec
        return None

    # -- end-of-call report
    def take_report(self, provider: str, body: dict) -> tuple[int, dict]:
        if provider == "vapi":
            msg = body.get("message", body)
            if msg.get("type") != "end-of-call-report":
                return 200, {"ok": True, "ignored": msg.get("type")}
            call = msg.get("call") or {}
            call_id = call.get("id", "")
            meta = {**(call.get("assistant") or {}).get("metadata", {}), **(call.get("metadata") or {}),
                    **((call.get("assistantOverrides") or {}).get("metadata") or {})}
            analysis = msg.get("analysis") or {}
            data = analysis.get("structuredData") or {}
            summary = analysis.get("summary") or msg.get("summary") or ""
            ended = msg.get("endedReason", "")
        elif provider == "retell":
            event = body.get("event", "")
            if event not in ("call_ended", "call_analyzed"):
                return 200, {"ok": True, "ignored": event}
            call = body.get("call") or {}
            call_id = call.get("call_id", "")
            meta = call.get("metadata") or {}
            ca = call.get("call_analysis") or {}
            data = ca.get("custom_analysis_data") or {}
            if ca.get("in_voicemail") and not data.get("outcome"):
                data["outcome"] = "voicemail"
            summary = ca.get("call_summary", "")
            ended = call.get("disconnection_reason", "")
            if event == "call_ended" and not ca:
                lid = self.store.lead_for_call(call_id) or meta.get("lead_id", "")
                if lid:
                    self.store.update(lid, call_status="ended")
                return 200, {"ok": True, "waiting_for": "call_analyzed"}
        else:
            return 404, {"ok": False}

        lead_id = self.store.lead_for_call(call_id) or str(meta.get("lead_id", ""))
        if not re.fullmatch(r"[a-f0-9]{10}", lead_id):
            log.warning("end-of-call report for unknown call %s", call_id)
            return 200, {"ok": True, "matched": False}

        outcome = str(data.get("outcome", "")).strip().lower()
        if outcome not in OUTCOMES:
            outcome = guess_outcome(ended)
        booked = clean_text(str(data.get("booked_time", "")), 80)
        note = clean_text(str(data.get("notes", "") or summary), 400)
        row = self.store.update(lead_id, call_status="ended", call_outcome=outcome,
                                booked_time=csv_safe(booked),
                                notes=csv_safe(f"lead={lead_id}; call={call_id}; ended={ended or '?'}; {note}"))
        if row is None:
            return 200, {"ok": True, "matched": False}
        if outcome in DNC_OUTCOMES:
            rec = self.consent_record(lead_id)
            if rec:
                self.store.dnc_add(rec["phone_e164"], f"{outcome} lead={lead_id}")
                log.info("DNC: %s added (%s)", display_phone(rec["phone_e164"]), outcome)
        log.info("REPORT lead %s: outcome=%s booked=%r", lead_id, outcome, booked)
        notify(self, f"FD lead: {row['first_name']} · {outcome}" + (f" · {booked}" if booked else ""),
               self.summary(row, summary))
        return 200, {"ok": True, "lead_id": lead_id, "outcome": outcome}

    @staticmethod
    def summary(row: dict, extra: str) -> str:
        return "\n".join([
            f"Name: {row['first_name'].lstrip(chr(39))}", f"Phone: {row['phone']}",
            f"Car: {row['car'].lstrip(chr(39))}", f"Need: {row['need'].lstrip(chr(39))}",
            f"Best time: {row['best_time']}", f"Outcome: {row['call_outcome'] or row['call_status']}",
            f"Shop to call: {row['booked_time'] or '-'}", f"Notes: {extra or '-'}",
            "Code: OMARIE. Pass it to Formula Dynamics with the code so the referral is logged.",
        ])


def guess_outcome(ended: str) -> str:
    e = ended.lower()
    if "voicemail" in e:
        return "voicemail"
    if any(k in e for k in ("did-not-answer", "no-answer", "no_answer", "busy", "dial_no_answer", "dial_busy")):
        return "no_answer"
    if "transfer" in e or "forward" in e:
        return "transferred"
    return "failed"


def spoken_phone(e164: str) -> str:
    d = re.sub(r"\D", "", e164)[-10:]
    return f"{' '.join(d[:3])}, {' '.join(d[3:6])}, {' '.join(d[6:])}"


# ------------------------------------------------------------------------- http -------------
def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = "fd-callback/1"

        def log_message(self, fmt, *args):
            log.debug("%s %s", self.client_ip(), fmt % args)

        def client_ip(self) -> str:
            if app.s.trust_proxy and self.headers.get("X-Forwarded-For"):
                return self.headers["X-Forwarded-For"].split(",")[0].strip()[:64]
            return self.client_address[0]

        def send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, code: int, obj: dict):
            self.send(code, json.dumps(obj).encode(), "application/json")

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path in ("/", "/index.html"):
                self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8",
                          {"Cache-Control": "no-store"})
            elif path.startswith("/fonts/") and path[7:] in FONT_FILES:
                for d in FONT_DIRS:
                    f = d / path[7:]
                    if f.exists():
                        return self.send(200, f.read_bytes(), "font/ttf", {"Cache-Control": "max-age=604800"})
                self.send(404, b"not found", "text/plain")
            elif path == "/healthz":
                self.send_json(200, {"ok": True, "provider": app.adapter.name, "dry_run": app.s.dry_run})
            else:
                self.send(404, b"not found", "text/plain")

        def read_body(self) -> bytes | None:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return None
            return self.rfile.read(n) if n else b""

        def do_POST(self):
            url = urllib.parse.urlparse(self.path)
            raw = self.read_body()
            if raw is None:
                return self.send_json(413, {"ok": False, "error": "Too large."})
            if url.path == "/lead":
                ctype = self.headers.get("Content-Type", "")
                try:
                    if "json" in ctype:
                        form = {k: str(v) for k, v in json.loads(raw or b"{}").items()}
                    else:
                        form = {k: v[-1] for k, v in urllib.parse.parse_qs(raw.decode(), keep_blank_values=True).items()}
                except (ValueError, UnicodeDecodeError):
                    return self.send_json(400, {"ok": False, "error": "Bad form data."})
                code, out = app.take_lead(form, self.client_ip(), self.headers.get("User-Agent", ""),
                                          self.headers.get("Referer", ""))
                if "json" in self.headers.get("Accept", ""):
                    return self.send_json(code, out)
                text = html.escape(out.get("message") or out.get("error", ""))
                page = (f'<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">'
                        f'<body style="background:#08080a;color:#fff;font:18px system-ui;padding:32px">'
                        f'<p>{text}</p><p><a style="color:#fff" href="/">Back</a></p>')
                return self.send(code, page.encode(), "text/html; charset=utf-8")
            m = re.fullmatch(r"/webhook/(vapi|retell)", url.path)
            if m:
                token = urllib.parse.parse_qs(url.query).get("token", [""])[0] or self.headers.get("x-vapi-secret", "")
                if app.s.webhook_token and not hmac.compare_digest(token, app.s.webhook_token):
                    log.warning("webhook with bad token from %s", self.client_ip())
                    return self.send_json(403, {"ok": False})
                try:
                    body = json.loads(raw or b"{}")
                except ValueError:
                    return self.send_json(400, {"ok": False})
                code, out = app.take_report(m[1], body)
                return self.send_json(code, out)
            self.send(404, b"not found", "text/plain")

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="log the API request it would send; no calls, texts or emails")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--data-dir", default=str(HERE), help="where leads.csv and the logs live (default: this folder)")
    ap.add_argument("--trust-proxy", action="store_true", help="take the client IP from X-Forwarded-For (behind a tunnel or host)")
    ap.add_argument("--ignore-window", action="store_true", help="dry-run tests only: build the call even outside calling hours")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    app = App(Settings(args))
    threading.Thread(target=app.sweep_queued, daemon=True).start()
    srv = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    log.info("listening on http://%s:%d  provider=%s  dry_run=%s  data=%s  window=%02d:%02d-%02d:%02d %s",
             args.host, args.port, app.adapter.name, app.s.dry_run, app.s.data_dir,
             app.s.window[0] // 60, app.s.window[0] % 60, app.s.window[1] // 60, app.s.window[1] % 60,
             app.s.tz.key)
    if not app.s.webhook_token:
        log.warning("WEBHOOK_TOKEN not set: webhooks accept any caller (dry-run only)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
