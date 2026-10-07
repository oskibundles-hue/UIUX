# Why these five agents are archived

On 2026-09-30 Omarie made his NQ OS team the main team in every session ("I want my nq os team to be
the main team that also runs with my second brain"), and picked replacing these five over keeping both
teams.

They were superseded by the agentmesh v1.2 classes in `.claude/agents/nq-*.md` (policy in
`.claude/agentmesh/MESH.md`). Nothing they knew was dropped:

| archived agent | its job now | its workstream knowledge now |
|---|---|---|
| `fd-ads` | `nq-build` (and `nq-fix`) | `.claude/playbooks/formula-dynamics.md` |
| `se-ads` | `nq-build` (and `nq-fix`) | `.claude/playbooks/supercar-experience.md` |
| `anti-stock-editor` | `nq-build` (and `nq-fix`, `nq-label`) | `.claude/playbooks/anti-stock.md` |
| `researcher` | `nq-build` | `.claude/playbooks/research.md` |
| `reviewer` | `nq-check`, with figures going on to `nq-facts` and `nq-second` | `.claude/playbooks/review.md` |

They're kept here, outside `.claude/agents/`, so they no longer load as agents but can be read or
restored.
