# Claude Code Agent Tooling

This directory configures the Claude Code plugins and MCP servers used with
this repository. Everything here is committed so it loads automatically in
both local and Claude Code on the web sessions.

> Plugins and MCP servers are installed at **session start**. After changing
> these files, start a new session (or run `/reload-plugins`) to pick them up.

## Plugins (`.claude/settings.json`)

Declared via `extraKnownMarketplaces` + `enabledPlugins`. Claude Code installs
them from their marketplaces at session start (requires network access).

| Plugin | Marketplace | Source | Skill namespace |
| :----- | :---------- | :----- | :-------------- |
| `superpowers` | `superpowers-marketplace` | `obra/superpowers-marketplace` | `/superpowers:*` |
| `ecc` | `ecc` | `affaan-m/ECC` | `/ecc:*` |
| `claude-mem` | `thedotmack` | `thedotmack/claude-mem` | `/claude-mem:*` |

Notes:
- **ecc** is large (advertises 67 agents / 271 skills / hooks) and adds
  meaningful per-turn context cost.
- **claude-mem** ships an MCP server and hooks for persistent cross-session
  memory; it may start its own server and write memory state.
- To disable a plugin without removing it, set its `enabledPlugins` value to
  `false`. The marketplace stays registered.

## MCP servers (`.mcp.json`)

| Server | Package | Purpose |
| :----- | :------ | :------ |
| `nano-banana` | [`nano-banana-mcp`](https://github.com/ConechoAI/Nano-Banana-MCP) (ConechoAI) | Image generation/editing via Google Gemini 2.5 Flash Image ("Nano Banana") |

### Required: `GEMINI_API_KEY`

The `nano-banana` server needs a Google Gemini API key. It is referenced in
`.mcp.json` as `${GEMINI_API_KEY}` so **no secret is committed** — you provide
the value through the environment.

1. Get a key from <https://aistudio.google.com/apikey>.
2. Provide it to the session:
   - **Claude Code on the web:** add `GEMINI_API_KEY` as an environment
     variable in your environment configuration (Environment → Environment
     variables). Note: env vars are visible to anyone who can edit that
     environment.
   - **Local terminal:** export it before launching, e.g.
     `export GEMINI_API_KEY=...` (add to your shell profile or a local
     `.env` that is **not** committed).
3. Start a new session. The first time the server runs you'll be prompted to
   approve it, since MCP servers execute code.

Without the key set, the `nano-banana` server loads but its tools fail when
called.
