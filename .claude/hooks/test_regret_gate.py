#!/usr/bin/env python3
"""Check regret_gate.py against commands with known answers (no model, under 2 s).

usage: python3 .claude/hooks/test_regret_gate.py
Builds two throwaway git repos in the temp folder (one on a protected branch, one on a work branch)
so a bare `git push` can be judged by the branch it would really update.
"""
import json, os, subprocess, sys, tempfile, time

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regret_gate.py")
TMP = tempfile.mkdtemp(prefix="regret-gate-test-", dir="/tmp")   # macOS temp is /var/folders, which the gate does not count as /tmp
ON_DEFAULT = os.path.join(TMP, "on-default")
ON_WORK = os.path.join(TMP, "on-work")
for path, branch in ((ON_DEFAULT, "claude/new-session-mucc2q"), (ON_WORK, "feat/x")):
    subprocess.run(["git", "init", "-q", "-b", branch, path], check=True)
GO_DIR = os.path.join(TMP, "go")
os.makedirs(GO_DIR)
os.environ["GENJUTSU_GO_DIR"] = GO_DIR   # the gate inherits it, so tests never touch the real ticket folder
HF = "e17b92d9-8ef6-414a-9d7c-cbcd27995067"
HOME_REPO = "/home/user/UIUX"   # a path outside the temp folder, for the delete checks


def run(tool, inp, cwd=ON_WORK):
    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True,
                       input=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": cwd}))
    if p.returncode:
        return f"crash: {p.stderr.strip().splitlines()[-1]}"
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "allow"


B = lambda c, cwd=ON_WORK: ("Bash", {"command": c}, cwd)
M = lambda s, n, **a: (f"mcp__{s}__{n}", a, ON_WORK)
CASES = [
    # pushes to a branch that only changes through a PR
    (B("git push origin main"), "deny"),
    (B("git push -u origin main"), "deny"),
    (B("git push origin HEAD:main"), "deny"),
    (B("git push origin feat:refs/heads/main"), "deny"),
    (B("git push origin +main"), "deny"),
    (B("cd x && git push origin master"), "deny"),
    (B("GIT_TRACE=1 git push origin main"), "deny"),
    (B("git -C /home/user/UIUX push origin main"), "deny"),
    (B("git push --repo=origin main"), "deny"),
    (B("git push origin claude/new-session-mucc2q"), "deny"),
    (B("git push origin HEAD:claude/new-session-mucc2q"), "deny"),
    (B("git push origin --delete claude/new-session-mucc2q"), "deny"),
    (B("git push", ON_DEFAULT), "deny"),
    (B("git push origin", ON_DEFAULT), "deny"),
    (B("git push -u origin HEAD", ON_DEFAULT), "deny"),
    (B(f"git -C {ON_DEFAULT} push"), "deny"),
    (B(f"cd {ON_DEFAULT} && git push"), "deny"),
    (B("sudo git push origin main"), "deny"),
    (B("env -i git push origin main"), "deny"),
    (B("sudo -u root git push origin main"), "deny"),
    (B("bash -c 'git push origin main'"), "deny"),
    (B("(cd /tmp && git push origin main)"), "deny"),
    (M("github", "push_files", branch="claude/new-session-mucc2q"), "deny"),
    (M("github", "create_or_update_file", branch="main"), "deny"),
    (M("github", "delete_file", branch="refs/heads/main"), "deny"),
    (M("github", "push_files"), "deny"),
    # asks
    (B("git push --force origin feat/x"), "ask"),
    (B("git push -f origin feat/x"), "ask"),
    (B("git push --force-with-lease origin feat/x"), "ask"),
    (B("git push origin +feat/x"), "ask"),
    (B("git push --all origin"), "ask"),
    (B("git reset --hard HEAD~1"), "ask"),
    (B("git -C /home/user/UIUX reset --hard"), "ask"),
    (B("git clean -fd"), "ask"),
    (B("git checkout ."), "ask"),
    (B(f"rm -rf {HOME_REPO}/src"), "ask"),
    (B("rm -r build", HOME_REPO), "ask"),
    (B("rm --recursive build", HOME_REPO), "ask"),
    (B("sudo rm -rf /home/user/UIUX"), "ask"),
    (B("rm -rf /tmp/../home/user/UIUX"), "ask"),
    (B("rm -rf /tmp"), "ask"),
    (B("ls | xargs rm -rf"), "ask"),
    (B("sudo -E rm -rf /home/user/UIUX"), "ask"),
    (B("ls | xargs -I {} rm -rf {}"), "ask"),
    (B("find . -name '*.tmp' -delete", HOME_REPO), "ask"),
    (B("find /home/user/UIUX -type d -exec rm -rf {} +"), "ask"),
    (B("echo $(rm -rf /home/user/UIUX)"), "ask"),
    (M("Higgsfield", "generate_video"), "ask"),
    (M("Higgsfield", "upscale_image"), "ask"),
    (M("Higgsfield", "publish_website"), "ask"),
    (M("Higgsfield", "tiktok_prepare_publish"), "ask"),
    (M("Dropbox", "delete"), "ask"),
    (M("Dropbox", "move"), "ask"),
    (M("Windsor_ai", "execute_action"), "ask"),
    (M("vidIQ", "vidiq_update_video_thumbnail"), "ask"),
    (M("Vertiso_Memory", "remember"), "ask"),
    (M("Vertiso_Memory", "approve_constraint"), "ask"),
    (M("github", "merge_pull_request"), "ask"),
    (M("github", "enable_pr_auto_merge"), "ask"),
    # allowed
    (B("git push -u origin claude/feature-x"), "allow"),
    (B("git push", ON_WORK), "allow"),
    (B("git push -u origin HEAD", ON_WORK), "allow"),
    (B("git push -u origin maintenance"), "allow"),
    (B("git push --tags origin", ON_DEFAULT), "allow"),
    (B("git status"), "allow"),
    (B("git -C /home/user/UIUX log --oneline -3"), "allow"),
    (B("rm -rf /tmp/foo"), "allow"),
    (B("cd /tmp/work && rm -rf build", HOME_REPO), "allow"),
    (B("rm -r build"), "allow"),   # run from the temp repo, so inside /tmp,
    (B("rm -rf \"$TMPDIR/x\""), "allow"),
    (B("rm file.txt"), "allow"),
    (B("find /tmp/x -delete"), "allow"),
    (B("find . -name '*.py'"), "allow"),
    (B("cat <<'EOF'\ngit push origin main\nEOF"), "allow"),
    (B("git commit -m 'fix (the thing)'"), "allow"),
    (M("github", "push_files", branch="feat/x"), "allow"),
    (M("github", "create_pull_request"), "allow"),
    (M("Higgsfield", "show_generations"), "allow"),
    (M("Dropbox", "list_folder"), "allow"),
    (M("Dropbox", "copy"), "allow"),
    (M("Vertiso_Memory", "recall"), "allow"),
    # connectors named by their claude.ai id are gated like the named ones
    (M(HF, "generate_video", params={"model": "hf_mult_replace_object"}), "ask"),
    (M(HF, "execute_preset", preset_id="genjutsu-style:abc"), "ask"),
    (M(HF, "upscale_video"), "ask"),
    (M(HF, "publish_website"), "ask"),
    (M("a8f752c9-094c-401f-bfd1-5765c16a1cac", "delete"), "ask"),
    (M(HF, "show_generations"), "allow"),
    # a price check submits nothing
    (M(HF, "generate_video", params={"model": "hf_mult_motion_control", "get_cost": True}), "allow"),
    (M("Higgsfield", "generate_video", params={"model": "x", "get_cost": True}), "allow"),
    (M(HF, "generate_video", params={"model": "hf_mult_motion_control", "get_cost": "true"}), "ask"),
]


def ticket(doc="gen-1", **over):
    t = {"doc_id": doc, "tool": "generate_video", "key": "hf_mult_replace_object",
         "cost": 30, "quote": 24, "use_unlim": False, "expires": time.time() + 600, **over}
    with open(os.path.join(GO_DIR, f"{over.pop('file', doc)}.json"), "w") as f:
        json.dump(t, f)


def clear():
    for f in os.listdir(GO_DIR):
        os.remove(os.path.join(GO_DIR, f))


GV = lambda **p: M(HF, "generate_video", params={"model": "hf_mult_replace_object", "use_unlim": False, **p})
PT = lambda pid="genjutsu-style:abc", **a: M(HF, "execute_preset", source="genjutsu", preset_id=pid, inputs={}, **a)
# Go tickets: (setup, call, want). Each runs on an empty ticket folder.
GO_CASES = [
    ("Go ticket lets the matching call through", lambda: ticket(), GV(), "allow"),
    ("no ticket still asks", lambda: None, GV(), "ask"),
    ("expired ticket asks", lambda: ticket(expires=time.time() - 1), GV(), "ask"),
    ("re-price above the tapped cost asks", lambda: ticket(quote=31), GV(), "ask"),
    ("ticket for another model asks", lambda: ticket(key="hf_mult_motion_control"), GV(), "ask"),
    ("count above 1 asks", lambda: ticket(), GV(count=2), "ask"),
    ("non-Genjutsu model asks", lambda: ticket(key="kling"), M(HF, "generate_video", params={"model": "kling"}), "ask"),
    ("ticket file not named for its doc asks", lambda: ticket(file="other"), GV(), "ask"),
    ("ticket missing a cost asks", lambda: ticket(cost=None), GV(), "ask"),
    ("broken ticket asks", lambda: open(os.path.join(GO_DIR, "gen-1.json"), "w").write("{"), GV(), "ask"),
    ("preset Go lets execute_preset through",
     lambda: ticket(tool="execute_preset", key="genjutsu-style:abc"), PT(), "allow"),
    ("trending preset Go lets execute_preset through",
     lambda: ticket(tool="execute_preset", key="genjutsu:trending:abc"), PT("genjutsu:trending:abc"), "allow"),
    ("preset ticket for another preset asks",
     lambda: ticket(tool="execute_preset", key="genjutsu-style:abc"), PT("genjutsu-style:xyz"), "ask"),
    ("non-Genjutsu preset asks",
     lambda: ticket(tool="execute_preset", key="viral:abc"), PT("viral:abc"), "ask"),
    ("other genjutsu: preset family asks",
     lambda: ticket(tool="execute_preset", key="genjutsu:other:abc"), PT("genjutsu:other:abc"), "ask"),
    ("preset from another source asks",
     lambda: ticket(tool="execute_preset", key="genjutsu-style:abc"),
     M(HF, "execute_preset", source="viral", preset_id="genjutsu-style:abc", inputs={}), "ask"),
    ("preset with count 5 asks",
     lambda: ticket(tool="execute_preset", key="genjutsu-style:abc"),
     M(HF, "execute_preset", source="genjutsu", preset_id="genjutsu-style:abc", inputs={"count": 5}), "ask"),
    ("count that isn't a number asks", lambda: ticket(), GV(count="three"), "ask"),
    ("count null asks", lambda: ticket(), GV(count=None), "ask"),
    ("count 1 is fine", lambda: ticket(), GV(count=1), "allow"),
    ("ticket living past 15 minutes asks", lambda: ticket(expires=time.time() + 99999), GV(), "ask"),
    ("ticket not for a gen- doc asks", lambda: ticket(doc="ad-7"), GV(), "ask"),
    ("unlimited ticket lets the unlimited call through",
     lambda: ticket(quote=0, cost=0, use_unlim=True), GV(use_unlim=True), "allow"),
    ("free quote never covers a credit charge",
     lambda: ticket(quote=0, cost=10, use_unlim=True), GV(use_unlim=False), "ask"),
    ("free quote ticket marked credits asks",
     lambda: ticket(quote=0, cost=10, use_unlim=False), GV(use_unlim=False), "ask"),
    ("payer left out asks", lambda: ticket(), M(HF, "generate_video", params={"model": "hf_mult_replace_object"}), "ask"),
    ("ticket with no payer asks", lambda: ticket(use_unlim=None), GV(), "ask"),
    ("Go ticket does not open other paid tools", lambda: ticket(), M(HF, "upscale_video"), "ask"),
    ("named server takes the ticket too", lambda: ticket(),
     M("Higgsfield", "generate_video", params={"model": "hf_mult_replace_object", "use_unlim": False}), "allow"),
]

bad = 0
for (tool, inp, cwd), want in CASES:
    got = run(tool, inp, cwd)
    label = (inp.get("command") or f"{tool} {inp}").replace("\n", "\\n").replace(TMP, "$T")
    ok = got == want
    bad += not ok
    print(f"{'PASS' if ok else 'MISS'}  want {want:5} got {got:5}  {label}")
for label, setup, (tool, inp, cwd), want in GO_CASES:
    clear()
    setup()
    got = run(tool, inp, cwd)
    ok = got == want
    bad += not ok
    print(f"{'PASS' if ok else 'MISS'}  want {want:5} got {got:5}  Go: {label}")
clear()
ticket()
first, second = run(*GV()), run(*GV())
ok = (first, second) == ("allow", "ask") and os.path.exists(os.path.join(GO_DIR, "gen-1.used"))
bad += not ok
print(f"{'PASS' if ok else 'MISS'}  want allow,ask got {first},{second}  Go: a ticket works once")
# the hook only runs when settings.json routes the call to it, so every gated server must match
import re  # noqa: E402
SETTINGS = os.path.join(os.path.dirname(GATE), "..", "settings.json")
with open(SETTINGS) as f:
    hooks = json.load(f)["hooks"]["PreToolUse"]
gate_matcher = next(h["matcher"] for h in hooks if any("regret_gate" in c.get("command", "") for c in h["hooks"]))
sys.path.insert(0, os.path.dirname(GATE))
import regret_gate  # noqa: E402
servers = ["Higgsfield", "Dropbox", "Windsor_ai", "vidIQ", "Vertiso_Memory", "github", *regret_gate.SERVER_IDS]
for srv in servers:
    ok = re.fullmatch(gate_matcher, f"mcp__{srv}__x") is not None
    bad += not ok
    print(f"{'PASS' if ok else 'MISS'}  settings.json routes mcp__{srv}__ to the gate")
total_extra = len(servers)
p = subprocess.run([sys.executable, GATE], input="not json", capture_output=True, text=True)
malformed = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout else "none"
ok = malformed == "ask"
bad += not ok
print(f"{'PASS' if ok else 'MISS'}  want ask   got {malformed:5}  (payload that isn't JSON)")
total = len(CASES) + len(GO_CASES) + 2 + total_extra
print(f"\n{total - bad}/{total} right")
sys.exit(1 if bad else 0)
