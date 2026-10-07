# NQ OS in every session (cloud)

Omarie, 2026-10-06: "it should work in every session thats the point." The repo's own settings only load when a
session opens inside this repo, on a current checkout. On 6 Oct a research session opened one folder up, on a
stale checkout, and ran without the cost guard, the 300k auto-compact, the note lookup, the regret gate and the
NQ agents.

`install.py` puts the latest system at the user level, which every session loads. It fetches the default
branch, copies its `.claude/` and `CLAUDE.md` to `/home/user/.nqos-system`, then merges the env, deny rules and
hooks into `~/.claude/settings.json`. It also copies the agents to `~/.claude/agents/` and imports the rules
into `~/.claude/CLAUDE.md`. `run_hook.py` skips a hook the project's own settings already run, so a session
inside the repo doesn't fire it twice.

## Turn it on (once)

In the claude.ai cloud environment: open the environment menu in a session's title bar, click **Edit**, and
add this to **Setup script**:

```bash
git clone -q --depth 1 -b claude/new-session-mucc2q https://github.com/oskibundles-hue/uiux /tmp/nqos-src \
  && python3 /tmp/nqos-src/.claude/cloud/install.py
```

Every new session then starts with the system loaded, whatever repo or folder it opens. The private notes still
need `oskibundles-hue/nq-agent-channel` attached to the session (clone it to `/home/user/nq-agent-channel`).

- **In a session that started without it:** run `python3 <repo>/.claude/cloud/install.py`. Hooks and env load
  when a session starts, so start a fresh session afterwards.
- **To check it's on:** `python3 .claude/cloud/test_install.py` runs the installer against a scratch home
  folder.
- **To undo:** delete `/home/user/.nqos-system` and the `nqos-system` block in `~/.claude/CLAUDE.md`, and
  remove the hooks that run `run_hook.py` from `~/.claude/settings.json`.

The Mac has its own install (`~/.claude/settings.json` there, see the notes' handoff), so this is for cloud
sessions.
