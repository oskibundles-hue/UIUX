#!/usr/bin/env python3
"""Dry-run test for callback_server.py. Places no call; uses fake data only (555-01xx numbers).

    uv run --no-project --python 3.12 python test_callback.py [--keep DIR]

Starts the server in --dry-run on a spare port with its own data folder, then:
  1. GET /           the form is served and carries the consent text, ref and version
  2. POST a lead WITH consent     -> 200, row in leads.csv, consent record, would-be API payload
  3. POST a lead WITHOUT consent  -> 400, nothing written
  4. POST a lead with a wrong-version consent -> 400
  5. POST a Vapi end-of-call report (opt-out) -> outcome written, number on dnc.txt
  6. POST the same number again   -> stored but not called (skipped_dnc)
  7. POST a webhook with a bad token -> 403
  8. Retell adapter builds the right request (no server needed)
"""
import argparse
import csv
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN = "test-token-not-secret"
FAILS = []


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


def post(base, path, data, headers=None, as_json=False):
    body = json.dumps(data).encode() if as_json else urllib.parse.urlencode(data).encode()
    h = {"Accept": "application/json",
         "Content-Type": "application/json" if as_json else "application/x-www-form-urlencoded",
         "User-Agent": "test-callback/1 (iPhone fake)", "Referer": base + "/?ref=omarie"}
    h.update(headers or {})
    req = urllib.request.Request(base + path, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def wait_for(fn, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if fn():
            return True
        time.sleep(0.2)
    return False


def rows(d):
    with (d / "leads.csv").open(newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", help="use this folder for the data and keep it")
    a = ap.parse_args()
    data = Path(a.keep or tempfile.mkdtemp(prefix="fd-callback-test-"))
    data.mkdir(parents=True, exist_ok=True)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    base = f"http://127.0.0.1:{port}"
    envv = {k: v for k, v in os.environ.items()
            if not k.startswith(("VAPI_", "RETELL_", "TWILIO_", "SMTP_", "NOTIFY_"))}
    envv.update({"CALL_DELAY_SECONDS": "1", "WEBHOOK_TOKEN": TOKEN,
                 "FD_SHOP_NUMBER": "+17025550199", "FD_SHOP_HOURS": "mon-sun 00:00-23:59"})
    log = (data / "server.log").open("w")
    srv = subprocess.Popen([sys.executable, str(HERE / "callback_server.py"), "--dry-run", "--ignore-window",
                            "--port", str(port), "--data-dir", str(data)], env=envv, stdout=log, stderr=log)
    try:
        up = wait_for(lambda: _ok(base + "/healthz"))
        check(up, f"server up in dry-run on {base}, data in {data}")
        if not up:
            return

        page = urllib.request.urlopen(base + "/").read().decode()
        check('name="ref" value="OMARIE"' in page and "not a condition of any purchase" in page
              and 'type="checkbox" name="consent" value="yes" id="consent">' in page,
              "form served: ref=OMARIE, consent text present, box not pre-ticked")

        lead = {"first_name": "Testy", "phone": "(702) 555-0100", "car": "2019 Test Car GT",
                "need": "A problem", "need_detail": "fake test lead, rattle at idle",
                "best_time": "Afternoon", "consent": "yes", "consent_text_version": "2026-11-24.v1",
                "ref": "OMARIE", "page_url": base + "/?ref=omarie", "website": ""}
        code, out = post(base, "/lead", lead)
        print(f"     POST /lead with consent -> {code} {out}")
        check(code == 200 and out.get("ok"), "lead with consent accepted")
        lid = out.get("lead_id", "")

        check(wait_for(lambda: (data / "dry_run_requests.jsonl").exists()), "would-be API request written")
        r = rows(data)[-1]
        print("     leads.csv row: " + json.dumps(r))
        check(r["consent"] == "yes" and r["consent_text_version"] == "2026-11-24.v1"
              and r["consent_ip"] == "127.0.0.1" and "page=http" in r["source"], "consent record in leads.csv")
        check(r["phone"] == "702-555-0100" and r["call_status"] == "dry_run", "phone stored, call_status=dry_run")
        rec = json.loads((data / "consent_log.jsonl").read_text().splitlines()[-1])
        print(f"     consent_log: version={rec['consent_text_version']} sha256={rec['consent_text_sha256'][:16]}... "
              f"ip={rec['ip']} page={rec['page_url']} ua={rec['user_agent']!r}")
        check(rec["consent_text"].startswith("By ticking this box") and rec["lead_id"] == lid,
              "full consent text kept in consent_log.jsonl")
        dr = json.loads((data / "dry_run_requests.jsonl").read_text().splitlines()[-1])
        req = dr["request"]
        print(f"     would send: {req['method']} {req['url']}  Authorization: {req['headers']['Authorization']}")
        body = req["json"]
        asst = body["assistant"]
        print(f"     customer={body['customer']}  maxDurationSeconds={asst['maxDurationSeconds']}  "
              f"tools={[t['type'] for t in asst['model']['tools']]}")
        print(f"     firstMessage: {asst['firstMessage']}")
        check(asst["firstMessage"].split(".")[0].count("AI assistant") == 1, "AI disclosed in first sentence")
        check(body["customer"]["number"] == "+17025550100" and "{{" not in json.dumps(body),
              "payload filled, no unfilled variables")
        check("test-token" not in json.dumps(req["headers"]), "no key in logged headers")

        before = len(rows(data))
        no = dict(lead, phone="702-555-0101"); no.pop("consent")
        code, out = post(base, "/lead", no)
        print(f"     POST /lead without consent -> {code} {out}")
        check(code == 400 and len(rows(data)) == before, "lead without consent rejected, nothing stored")

        code, out = post(base, "/lead", dict(lead, phone="702-555-0102", consent_text_version="old"))
        check(code == 400 and len(rows(data)) == before, f"wrong consent version rejected ({code})")

        report = {"message": {"type": "end-of-call-report", "endedReason": "customer-ended-call",
                              "call": {"id": "fake-call-1", "assistant": {"metadata": {"lead_id": lid}}},
                              "analysis": {"summary": "Caller asked to stop calls.",
                                           "structuredData": {"outcome": "opt_out", "notes": "Asked not to be called."}}}}
        code, out = post(base, f"/webhook/vapi?token={TOKEN}", report, as_json=True)
        print(f"     POST /webhook/vapi (opt-out) -> {code} {out}")
        r = [x for x in rows(data) if x["notes"].startswith(f"lead={lid}")][0]
        check(r["call_outcome"] == "opt_out" and r["call_status"] == "ended", "outcome written to leads.csv")
        check("+17025550100" in (data / "dnc.txt").read_text(), "opted-out number on dnc.txt")

        code, out = post(base, "/lead", dict(lead, first_name="Testy Again"))
        print(f"     POST same number after opt-out -> {code} {out.get('message')}")
        time.sleep(1.5)
        check(rows(data)[-1]["call_status"] == "skipped_dnc"
              and len((data / "dry_run_requests.jsonl").read_text().splitlines()) == 1,
              "number on DNC is not called again")

        code, _ = post(base, "/webhook/vapi?token=wrong", report, as_json=True)
        check(code == 403, "webhook with bad token refused (403)")
    finally:
        srv.terminate(); srv.wait(5); log.close()

    sys.path.insert(0, str(HERE))
    import callback_server as cs
    req = cs.RetellAdapter().build({"e164": "+17025550100", "lead_id": "abc", "ref": "OMARIE"},
                                   {"values": {"first_name": "Testy"}})
    check(req["url"].endswith("/v2/create-phone-call") and req["json"]["to_number"] == "+17025550100",
          "Retell adapter builds create-phone-call request")
    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAILED'}  (data folder: {data})")
    sys.exit(1 if FAILS else 0)


def _ok(url):
    try:
        return urllib.request.urlopen(url, timeout=1).status == 200
    except Exception:
        return False


if __name__ == "__main__":
    main()
