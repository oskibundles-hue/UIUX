#!/usr/bin/env python3
"""Check regret_gate.py against commands with known answers (no model, under 2 s).

usage: python3 .claude/hooks/test_regret_gate.py
Builds two throwaway git repos in the temp folder (one on a protected branch, one on a work branch)
so a bare `git push` can be judged by the branch it would really update.
"""
import json, os, subprocess, sys, tempfile

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regret_gate.py")
TMP = tempfile.mkdtemp(prefix="regret-gate-test-")
ON_DEFAULT = os.path.join(TMP, "on-default")
ON_WORK = os.path.join(TMP, "on-work")
for path, branch in ((ON_DEFAULT, "claude/new-session-mucc2q"), (ON_WORK, "feat/x")):
    subprocess.run(["git", "init", "-q", "-b", branch, path], check=True)
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
]

bad = 0
for (tool, inp, cwd), want in CASES:
    got = run(tool, inp, cwd)
    label = (inp.get("command") or f"{tool} {inp}").replace("\n", "\\n").replace(TMP, "$T")
    ok = got == want
    bad += not ok
    print(f"{'PASS' if ok else 'MISS'}  want {want:5} got {got:5}  {label}")
p = subprocess.run([sys.executable, GATE], input="not json", capture_output=True, text=True)
malformed = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout else "none"
ok = malformed == "ask"
bad += not ok
print(f"{'PASS' if ok else 'MISS'}  want ask   got {malformed:5}  (payload that isn't JSON)")
print(f"\n{len(CASES) + 1 - bad}/{len(CASES) + 1} right")
sys.exit(1 if bad else 0)
