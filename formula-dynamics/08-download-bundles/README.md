# Download Bundles

Zipped packs you can download and unzip straight into a CapCut media folder or
a phone album — no need to pull the whole repository.

| Bundle | Contents |
|---|---|
| **`FD-00-VERTICAL-STARTER-PACK.zip`** | **Start here.** Everything for 9:16 — TikTok, Reels, Shorts — and nothing else. |
| `FD-01-logo-bugs.zip` | Logo pre-positioned on a full transparent frame, all canvases |
| `FD-02-lower-thirds.zip` | Service, partner and CTA name plates |
| `FD-03-title-cards.zip` | Two-line openers |
| `FD-04-end-cards.zip` | Full-frame closing cards |
| `FD-05-service-badges.zip` | Feature-callout chips |
| `FD-06-accent-bars.zip` | Racing stripe and red bars |
| `FD-07-ALL-OVERLAYS.zip` | Every overlay, every format, plus safe-zone guides |
| `FD-08-logos.zip` | Every logo lockup — SVG vector plus PNG at three sizes |

Each zip contains a **`HOW-TO-USE.txt`** with the sizing rules and a full file
listing, so a bundle still makes sense on its own once it leaves this folder.

## Downloading one file from GitHub

GitHub won't let you download a single file from the repo view directly. Open
the file, then use the **Download raw file** button (the ⤓ icon, top right of
the file view). For a whole bundle, open the `.zip` and click **View raw** —
that downloads it.

## Regenerating

```bash
cd 99-toolkit && python3 build_bundles.py
```

Archives are written with fixed timestamps and sorted entries, so rebuilding
without changing an asset produces a byte-identical file — the repository never
accumulates a second copy of an unchanged bundle.
