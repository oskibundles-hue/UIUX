# agentmesh in cloud sessions (cloud v1.3)

Omarie's NQ OS team is the main team in every session (Omarie, 2026-09-30: "I want my nq os team to be
the main team that also runs with my second brain"). Each job goes to a **class**, and the class
decides the model and effort, so nobody picks a model per agent by feel. The classes come from the
Mac's `~/.nqos/os/agentmesh/` (`MESH.md`, `router_block.js`, v1.2 since 2026-09-27). The cloud cells
moved to v1.3 on 2026-09-30 at Omarie's request (below); the Mac stays on v1.2 until it takes the same
change. Keep the two in step: when one changes, note it in the other.

## The table

| class | agent | model/effort | floor | what it is | examples |
|---|---|---|:--:|---|---|
| `run` | `nq-run` | sonnet/low | | run a script, read a file, report lines word for word | run a checker and return its result lines; confirm a file exists and parses |
| `label` | `nq-label` | sonnet/low | | tags, captions, sorting, contact-sheet calls — never a verdict | tag 40 files by topic; accept/reject thumbnails from one contact sheet |
| `build` | `nq-build` | opus/medium | | write or patch a step and run it | build an ad from a cue; write a converter and run it; a sourced research report |
| `fix` | `nq-fix` | sonnet/medium | | debug a failing chain | a script exits 1; an output is the wrong length; an off-by-one |
| `check` | `nq-check` | opus/medium | | is this good enough to show the owner | the quality and copy pass on a finished piece; which variant is strongest |
| `story` | `nq-story` | opus/high | | the big creative call | the angle, the hook, the concept, one piece or two |
| `plate` | — | opus/high | **yes** | visual truth check on the delivered file | switched off; no cloud agent until plate work comes back |
| `facts` | `nq-facts` | opus/high | **yes** | numbers, specs, names, "we did X" | a spec with no source becomes BLOCKED, not guessed |
| `second` | `nq-second` | sonnet/high | **yes** | independent voter | its own look at the same delivered file; may only **add** a block |

Cloud v1.3 (2026-09-30; Omarie: "assign each of my agents a sonnet to opus model you can choose the
respective effort level for max efficiency"). Sonnet takes the lanes that follow a plan or report what
they see (`run`, `label`, `build`), where speed counts and Sonnet uses less of the weekly limit. Opus
keeps the lanes where a wrong call costs a client piece or a rebuild: `fix` (diagnosis), `check` (the
quality gate, now a different model from the Sonnet builder it checks), `story` (the creative call) and
the `facts` floor. `second` stays on Sonnet so it is a different model from `facts`. `facts` drops from
xhigh to high: on the 2026-09-26 bench, high, xhigh and max gave the same answers on both fact tests.
For a job that needs more, the lead says so in the brief.

Evidence behind it (2026-09-30 facts-panel test on a fixture with known answers): `nq-facts` at
opus/xhigh took 117 s and 39k tokens; `nq-second` at sonnet/high took 35 s and 22k tokens and caught the
same three problems. v1.2 (2026-09-26) had Opus everywhere but `second`, so one run paid one cold cache
start; a chain now pays two (Sonnet and Opus), which the cheaper Sonnet lanes more than cover.

**Head-to-head bench, 2026-09-30** (`bench-2026-09-30.md`): build, check, fix and story each did the
same real job on Sonnet and on Opus, and the rule was to keep Sonnet unless Opus got something right
that Sonnet missed. Two cells moved. `build` goes to **opus/medium**: asked for a token counter that
keeps the last usage record per message id, only Opus found that every transcript record is written
mid-stream, so "last record" still undercounts output about 10x, and it took the final usage from the
Agent result instead; Sonnet's build ran but its output column was wrong. `fix` goes to
**sonnet/medium**: both found and reverted the planted bug and restored eval to 33/33, Sonnet in 24 s
against 51 s. `check` stays on Opus (it caught a defect Sonnet's check passed), `story` stays on Opus
(Omarie called the blind pair even; Sonnet's set carried a wrong claim about the brief), and `label`
stays on Sonnet (58/58). Trade-off: `check` and `build` are now the same model, so the quality gate is
no longer a different model from the builder; the facts panel still is.

`build` applies a planned change; `fix` diagnoses a failure. The workstream knowledge (branches,
pipelines, brand rules) lives in `.claude/playbooks/`, and the brief names the playbook, so the same
`nq-build` builds a Formula Dynamics ad, a Supercar Experience vlog or an Anti Stock reel.

## The two rules that matter

**1. A floor is a procedure with an evidence contract, not a model.**
A gate once passed a file twice because it checked a record *about* the file, never the file itself.
A better model on the same input passes the same way. So `facts` and `second`:

- never receive a detector, gate or other agent's verdict in their brief;
- must name the exact file they examined and return per-claim evidence (the claim, where it appears,
  its source);
- a result without those fields is **BLOCKED regardless of which model produced it**;
- run as a panel of two on different models: **either voter may block, only both together may clear**;
- an empty or missing result is a block, never a smaller panel.

**2. Mechanical failures never escalate.**
`run`, `build` and `fix` retry **once on the same class**, then report. A broken flag or a recurring
off-by-one is a source patch, not a reasoning problem; a bigger model fails at it identically and burns
the top lane doing so.

## The usual chain

One agent at a time (`.claude/settings.json` caps it). The lead briefs each one with the class, the
playbook and, for creative work, the style Omarie picked.

    nq-story (only if the direction isn't settled) → Omarie picks
    nq-build → nq-check → [nq-facts → nq-second, when the piece carries figures or claims] → lead delivers

A failure in `nq-build` goes to `nq-fix`, then back to `nq-build` or on to `nq-check`.

## Where the tokens go (measured on the original NQ OS)

A 20-agent probe cost ~1.1M tokens for twenty three-question agents: **about 55k per agent, nearly
the same on Haiku and Opus**, because almost all of it is fixed context loaded at agent start.

**So the lever is fewer agents, not cheaper agents.** Three cheap agents cost more than one strong
agent doing all three jobs. The worst week on record came from two long-*resumed* agents (400–565k
context per call), about 90% of a week's usage. Hence: one call, one job, fresh context; merge small
jobs before handing them out; a floor agent is always fresh. Small jobs the lead can do in a few
commands stay with the lead.

## Workflows

The Mac runs multi-agent jobs through `router_block.js` (`go()`, `goLabel()`, `panel()`, `done()`),
stamped into each Workflow script by `mesh_new.py`. Those files aren't in this repo yet. Cloud sessions
run the classes as the agents above, one at a time, and use a Workflow only when a job can't be done
well without one (CLAUDE.md, "No ultracode unless necessary").
