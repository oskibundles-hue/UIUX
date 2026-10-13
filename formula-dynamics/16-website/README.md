# Formula Dynamics · The Job Board (website)

A static, vlog-first site for Formula Dynamics Performance, Las Vegas. The 12 shop episodes play in full as
work-order tickets on a job board, with the store's parts, before-and-afters and a work-order form beside them.

- Layout: **The Job Board**, approved by Omarie on 30 Sept 2026, built to the Locked-On motion standard in FD's brand.
- Host: Render static site, `render.yaml` at the repo root (`rootDir: formula-dynamics/16-website`). Render serves
  byte ranges, which the player needs for seeking.
- Local preview: `npx http-server formula-dynamics/16-website -p 8765` (supports byte ranges). Opening the file
  directly works for everything except seeking.

Files: `index.html` (the whole site, no build), `ep/<k>/` (share pages), `media/` (everything else).
Tools: `../16-website-tools/` (`build_media.py`, `make_episode_pages.py`, `share-card.html`).
How to add an episode or a product, the rules and the open items: `HANDOFF.md`.
