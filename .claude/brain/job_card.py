#!/usr/bin/env python3
"""Job cards: a compact record of one job, saved when nq-check returns, so a failed job can be lined up
against a good one of the same kind (job_diff.py, "gap 2" of the reel-harness comparison).

usage: python3 .claude/brain/job_card.py capture < hook-event.json     the hook's entry (job_diff_hook.py calls it)
       python3 .claude/brain/job_card.py list [--format reel]          saved cards, newest first
       python3 .claude/brain/job_card.py show <card id | path>

A card holds what the transcripts know about the job, because transcripts vanish with the cloud container:
  job, workstream, format, style, playbook   detected from the briefs and nq-check's report
  brief        the key fields of each brief (who, style, playbook, the first 600 characters)
  steps        the ordered working steps of the lead and the builders: tool, program, normalised flags
               (looking around - ls, cat, grep, Read - is left out; paths become file names)
  outputs      the files nq-check examined: ffprobe duration, size and fps, plus loudness from the report
  verdict      PASS or FAIL, and each check's verdict from nq-check's table
The job is everything since the previous nq-check in the same session.

Cards quote briefs and evidence, which can carry client copy, so they live only in the private brain
(nq-agent-channel/brain/jobcards/) when it is attached, else in the git-ignored .claude/brain/work/jobcards/.
NQOS_JOBCARDS overrides the folder (tests). Stdlib only, no model call; ffprobe is used when it is installed.
"""
import datetime, glob, json, os, re, shlex, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nqos_config import HAVE_NOTES, HOME, WORK
from post_mortem import FORMATS, parse_fails   # gap 1's format order and FAIL-bullet reader, shared

CARDS = os.environ.get("NQOS_JOBCARDS") or (os.path.join(HOME, "jobcards") if HAVE_NOTES
                                            else os.path.join(WORK, "jobcards"))
CHECK_AGENT = "nq-check"
BUILD_AGENTS = ("nq-build", "nq-fix", "nq-run", "nq-label")
WORKSTREAMS = (("Anti Stock", r"anti[ -]?stock|antistock"),
               ("Formula Dynamics", r"formula dynamics|(?<![a-z])fd(?![a-z])"),
               ("Supercar Experience", r"supercar experience|(?<![a-z])se(?![a-z])|(?<![a-z])se-vlog"))
STYLES = ("Locked-On", "Quick-Promo", "Fast Cut", "Reel Cut", "Now Boarding", "Paste-Up", "iPhone index",
          "post mockup", "studio carousel", "rally v2")
PLAYBOOK_RE = re.compile(r"playbooks/([\w-]+)\.md|\b(formula-dynamics|supercar-experience|anti-stock|research|"
                         r"vlog-lifestyle|sound-layer|review)\b(?: playbook)?", re.I)
# Commands that only look around: they never change the output, so they aren't steps.
LOOK = {"ls", "cat", "head", "tail", "grep", "rg", "find", "echo", "printf", "wc", "which", "pwd", "cd", "stat",
        "file", "du", "df", "tree", "less", "true", "sleep", "test", "[", "diff", "sort", "uniq", "jq", "awk",
        "date", "sha256sum", "md5sum", "basename", "dirname", "realpath", "readlink", "export", "set", "source"}
LOOK_GIT = {"status", "log", "diff", "show", "fetch", "branch", "rev-parse", "ls-files", "remote", "worktree"}
WORK_TOOLS = {"Bash", "Write", "Edit", "NotebookEdit", "Skill", "Agent", "Task"}
MEDIA = r"[\w./~+-]+\.(?:mp4|mov|m4v|webm|mkv|mp3|wav|m4a|png|jpe?g|webp|gif)"
LUFS_RE = re.compile(r"(-\d+(?:\.\d+)?)\s*LUFS", re.I)
VERDICT_RE = re.compile(r"^[^\w]*\**\s*(PASS|FAIL|N/?A)\b", re.I)
# Noise that always differs between two runs: replaced before anything is compared.
NOISE = ((re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "<id>"),
         (re.compile(r"\bsession_[A-Za-z0-9]+|\bcse_[A-Za-z0-9]+|\btoolu_[A-Za-z0-9]+"), "<id>"),
         (re.compile(r"\b20\d\d-?\d\d-?\d\d[T_ ]?\d\d:?\d\d(?::?\d\d)?(?:\.\d+)?Z?\b"), "<time>"),
         (re.compile(r"/tmp/claude-\d+/[^\s'\"]*/"), "/tmp/"))


def denoise(text):
    for pat, rep in NOISE:
        text = pat.sub(rep, text)
    return text


def short_path(tok):
    """A path keeps only its file name, so the same step in two worktrees compares equal."""
    if "/" in tok and not tok.startswith(("http:", "https:")):
        head, _, tail = tok.rpartition("=")          # loudnorm=I=-14:print_format=json keeps its options
        if "/" in tail and "/" not in head:
            return f"{head}={os.path.basename(tail.rstrip('/'))}" if head else os.path.basename(tail.rstrip("/"))
        return os.path.basename(tok.rstrip("/")) or tok
    return tok


# ---- detection -------------------------------------------------------------------------------------------

def detect(text, which):
    text = text or ""
    if which == "format":
        hits = [f for f in FORMATS if re.search(rf"(?<![a-z]){f}s?(?![a-z])", text, re.I)]
        return hits[0] if hits else ""
    if which == "workstream":
        for name, pat in WORKSTREAMS:
            if re.search(pat, text, re.I):
                return name
        return ""
    if which == "style":
        hits = [s for s in STYLES if re.search(re.escape(s).replace(r"\-", "[- ]?").replace(r"\ ", "[- ]?"), text, re.I)]
        return hits[0] if hits else ""
    if which == "playbook":
        m = PLAYBOOK_RE.search(text)
        return (m.group(1) or m.group(2)).lower() if m else ""
    raise ValueError(which)


# ---- commands into steps -------------------------------------------------------------------------------

def split_commands(cmd):
    """One shell command line into simple commands (&&, ||, ;, | and newlines), heredoc bodies dropped."""
    cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\s*(?:\n|$)", "\n", cmd, flags=re.S)
    cmd = cmd.replace("\\\n", " ")
    parts = re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", cmd)
    return [p.strip() for p in parts if p.strip() and not p.strip().startswith("#")]


def parse_flags(args):
    """-x value / --x=value / --x value pairs, in order; a bare word after a flag is its value."""
    flags, i = [], 0
    while i < len(args):
        a = args[i]
        if a.startswith("-") and len(a) > 1 and not re.match(r"^-\d", a):
            if "=" in a and a.startswith("--"):
                k, v = a.split("=", 1)
                flags.append([k, short_path(v)])
            elif i + 1 < len(args) and not (args[i + 1].startswith("-") and not re.match(r"^-\d", args[i + 1])):
                flags.append([a, short_path(args[i + 1])])
                i += 1
            else:
                flags.append([a, ""])
        i += 1
    return flags


def bash_steps(cmd, who):
    steps = []
    for simple in split_commands(denoise(cmd)):
        try:
            toks = shlex.split(simple)
        except ValueError:
            toks = simple.split()
        while toks and (re.match(r"^\w+=", toks[0]) or toks[0] in ("env", "sudo", "nice", "time", "exec")):
            toks.pop(0)
        if toks and toks[0] in ("timeout", "gtimeout"):
            toks = toks[1:]
            while toks and (toks[0].startswith("-") or re.match(r"^\d+[smh]?$", toks[0])):
                toks.pop(0)
        if not toks:
            continue
        prog = os.path.basename(toks[0])
        args = toks[1:]
        if prog in LOOK or (prog == "sed" and "-i" not in args) or (prog == "git" and args[:1] and args[0] in LOOK_GIT):
            continue
        if prog.startswith("python") or prog in ("node", "bash", "sh"):
            script = next((a for a in args if not a.startswith("-")), "")
            if script:
                prog = f"{prog.rstrip('0123456789.')} {short_path(script)}"
                args = args[args.index(script) + 1:]
            elif "-c" in args:
                prog, args = f"{prog.rstrip('0123456789.')} -c", []
        elif prog == "git" and args:
            prog, args = f"git {args[0]}", args[1:]
        steps.append({"who": who, "tool": "Bash", "prog": prog, "flags": parse_flags(args),
                      "cmd": " ".join(short_path(t) for t in [toks[0]] + toks[1:])[:240]})
    return steps


def tool_steps(name, inp, who):
    if name == "Bash":
        return bash_steps(inp.get("command", ""), who)
    if name in ("Write", "Edit", "NotebookEdit"):
        f = os.path.basename(inp.get("file_path") or inp.get("notebook_path") or "")
        return [{"who": who, "tool": name, "prog": f"{name.lower()} {f}", "flags": [], "cmd": f"{name} {f}"}]
    if name == "Skill":
        return [{"who": who, "tool": name, "prog": f"skill {inp.get('skill', '')}", "flags": [], "cmd": inp.get("skill", "")}]
    if name in ("Agent", "Task"):
        t = inp.get("subagent_type", "") or "agent"
        return [{"who": who, "tool": "Agent", "prog": f"brief {t}", "flags": [], "cmd": inp.get("description", "")[:120]}]
    return []


# ---- transcripts ---------------------------------------------------------------------------------------

def records(path):
    if not path or not os.path.isfile(path):
        return []
    out = []
    for raw in open(path, errors="replace"):
        try:
            out.append(json.loads(raw))
        except ValueError:
            pass
    return out


def tool_uses(recs):
    """(tool_use id, name, input) in transcript order, each id once (a transcript may repeat a record)."""
    seen, out = set(), []
    for r in recs:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") not in seen:
                seen.add(b.get("id"))
                out.append((b.get("id"), b.get("name", ""), b.get("input") or {}))
    return out


def agent_transcripts(lead_path):
    """{tool_use id of the Agent call: the agent's transcript path}, from <session>/subagents/*.meta.json."""
    base = os.path.splitext(lead_path or "")[0]
    out = {}
    for meta in glob.glob(os.path.join(base, "subagents", "*.meta.json")):
        try:
            tid = json.load(open(meta)).get("toolUseId")
        except (ValueError, OSError):
            continue
        if tid:
            out[tid] = meta[:-len(".meta.json")] + ".jsonl"
    return out


def job_scope(uses, check_tool_id=None):
    """The lead's tool calls since the nq-check before this one, up to and including this nq-check call."""
    checks = [i for i, (tid, name, inp) in enumerate(uses)
              if name in ("Agent", "Task") and inp.get("subagent_type") == CHECK_AGENT]
    if not checks:
        return uses
    end = next((i for i in checks if uses[i][0] == check_tool_id), checks[-1])
    start = max([i for i in checks if i < end], default=-1) + 1
    return uses[start:end + 1]


# ---- nq-check's report ---------------------------------------------------------------------------------

def parse_report(text):
    """Each table row with a PASS/FAIL/N/A cell: {check: verdict}; plus the overall verdict."""
    checks = {}
    for line in (text or "").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for i, c in enumerate(cells[1:], 1):
            m = VERDICT_RE.match(c)
            if m:
                name = re.sub(r"[*`_]", "", cells[0]).strip()
                if name:
                    checks[name] = m.group(1).upper().replace("NA", "N/A")
                break
    if not checks:   # no table: "- Audio level: FAIL - too loud" bullets, read the way gap 1's log reads them
        checks = {check: "FAIL" for check, _ in parse_fails(text)}
    if any(v == "FAIL" for v in checks.values()):
        verdict = "FAIL"
    elif checks:
        verdict = "PASS"
    else:
        tail = (text or "")[-400:].lower()
        verdict = "FAIL" if re.search(r"\bfail|must change|do not ship|don't ship", tail) else (
            "PASS" if re.search(r"\bship\b|\bpass", tail) else "")
    return verdict, checks


def probe(path):
    if not shutil.which("ffprobe") or not os.path.isfile(path):
        return {}
    try:
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", path],
                           capture_output=True, text=True, timeout=5)
        d = json.loads(p.stdout or "{}")
    except (subprocess.SubprocessError, ValueError, OSError):
        return {}
    out = {}
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if v:
        out["size"] = f"{v.get('width')}x{v.get('height')}"
        num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
        if float(den or 1) and float(num) and not path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            out["fps"] = round(float(num) / float(den or 1), 3)
    dur = (d.get("format") or {}).get("duration")
    if dur and not path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        out["duration"] = round(float(dur), 2)
    return out


def outputs(report, roots=()):
    out, seen = [], set()
    for m in re.finditer(MEDIA, report or "", re.I):
        p = m.group(0)
        name = os.path.basename(p)
        if name in seen or "contact" in name.lower() or "/gate/" in p:
            continue
        seen.add(name)
        full = next((c for c in [p] + [os.path.join(r, p) for r in roots] if os.path.isfile(c)), p)
        out.append({"file": name, **probe(full)})
    lufs = LUFS_RE.findall(report or "")
    if lufs:
        if out:
            out[0]["lufs"] = float(lufs[0])
        else:
            out.append({"file": "", "lufs": float(lufs[0])})
    return out[:6]


# ---- the card ------------------------------------------------------------------------------------------

def brief_fields(who, text):
    return {"who": who, "style": detect(text, "style"), "playbook": detect(text, "playbook"),
            "text": denoise(text or "")[:600]}


def build_card(lead_path, report, check_tool_id=None, session="", agent_id="", cwd=""):
    uses = job_scope(tool_uses(records(lead_path)), check_tool_id)
    subs = agent_transcripts(lead_path)
    steps, briefs, check_brief = [], [], ""
    for tid, name, inp in uses:
        if name in ("Agent", "Task"):
            kind = inp.get("subagent_type", "")
            if kind == CHECK_AGENT:
                check_brief = inp.get("prompt", "")
                continue
            briefs.append(brief_fields(kind or "agent", inp.get("prompt", "")))
            steps += tool_steps(name, inp, "lead")
            if kind in BUILD_AGENTS or kind not in ("claude-code-guide", "Explore", "Plan"):
                for _, n2, i2 in tool_uses(records(subs.get(tid))):
                    if n2 in WORK_TOOLS:
                        steps += tool_steps(n2, i2, kind or "agent")
        elif name in WORK_TOOLS:
            steps += tool_steps(name, inp, "lead")
    all_text = "\n".join([b["text"] for b in briefs] + [check_brief, report or ""])
    brief_text = "\n".join(b["text"] for b in briefs) or check_brief
    verdict, checks = parse_report(report)
    at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    first = re.sub(r"\s+", " ", (briefs[0]["text"] if briefs else check_brief))[:80]
    return {
        "id": f"{at[:10].replace('-', '')}-{(session or 'nosession')[:8]}-{(agent_id or check_tool_id or 'x')[-6:]}",
        "at": at, "session": session, "job": first,
        "workstream": detect(brief_text, "workstream") or detect(all_text, "workstream"),
        "format": detect(brief_text, "format") or detect(report, "format"),
        "style": detect(brief_text, "style") or detect(check_brief, "style"),
        "playbook": detect(brief_text, "playbook"),
        "brief": briefs or [brief_fields(CHECK_AGENT, check_brief)],
        "steps": steps,
        "outputs": outputs(report, [r for r in (cwd,) if r]),
        "verdict": verdict, "checks": checks,
    }


def save(card):
    os.makedirs(CARDS, exist_ok=True)
    path = os.path.join(CARDS, card["id"] + ".json")
    with open(path, "w") as fh:
        json.dump(card, fh, indent=1)
    return path


def load_all():
    cards = []
    for p in glob.glob(os.path.join(CARDS, "*.json")):
        if os.path.basename(p) == "refs.json":
            continue
        try:
            c = json.load(open(p))
        except (ValueError, OSError):
            continue
        c["_path"] = p
        cards.append(c)
    return sorted(cards, key=lambda c: (c.get("at", ""), os.path.getmtime(c["_path"])), reverse=True)   # same second: file time


def load(ref):
    if os.path.isfile(ref):
        return json.load(open(ref))
    for c in load_all():
        if c["id"] == ref or c["id"].startswith(ref):
            return c
    return None


def from_event(ev):
    """A SubagentStop or PostToolUse hook event for an nq-check run into a card (None for anything else)."""
    kind = ev.get("agent_type") or (ev.get("tool_input") or {}).get("subagent_type")
    if kind != CHECK_AGENT:
        return None
    report = ev.get("last_assistant_message") or ""
    if not report:
        resp = ev.get("tool_response")
        if isinstance(resp, dict):
            if resp.get("status") == "async_launched":
                return None                            # a background launch: SubagentStop captures it later
            resp = resp.get("content", resp.get("result", ""))
        if isinstance(resp, list):
            resp = "\n".join(b.get("text", "") for b in resp if isinstance(b, dict))
        report = resp if isinstance(resp, str) else ""
    if not report and ev.get("agent_transcript_path"):
        msgs = [b.get("text", "") for r in records(ev["agent_transcript_path"]) if r.get("type") == "assistant"
                for b in (r.get("message") or {}).get("content") or [] if isinstance(b, dict) and b.get("type") == "text"]
        report = msgs[-1] if msgs else ""
    if not report or "launched successfully" in report[:200]:
        return None                                    # a background launch, not the finished check
    check_tool_id = ev.get("tool_use_id")
    if not check_tool_id and ev.get("agent_transcript_path"):
        try:
            check_tool_id = json.load(open(ev["agent_transcript_path"][:-len(".jsonl")] + ".meta.json")).get("toolUseId")
        except (ValueError, OSError):
            pass
    agent_id = ev.get("agent_id") or ((ev.get("tool_response") or {}).get("agentId", "")
                                      if isinstance(ev.get("tool_response"), dict) else "")
    return build_card(ev.get("transcript_path"), report, check_tool_id, ev.get("session_id", ""),
                      agent_id, ev.get("cwd", ""))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["capture"]:
        card = from_event(json.load(sys.stdin))
        print(save(card) if card else "not an nq-check result: no card")
    elif a[:1] == ["list"]:
        fmt = a[a.index("--format") + 1] if "--format" in a else None
        for c in load_all():
            if not fmt or c.get("format") == fmt:
                print(f"{c['id']}  {c.get('verdict', '?'):4}  {c.get('format', '') or '-':9} {c.get('workstream', '')[:20]:20} {c.get('job', '')[:50]}")
    elif a[:1] == ["show"] and len(a) > 1:
        print(json.dumps(load(a[1]), indent=1))
    else:
        sys.exit(__doc__)
