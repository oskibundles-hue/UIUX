# The system

You film. You drop it in Dropbox. I edit. You post.

## Dropbox

```
/Anti Stock Media/
  01 Raw D-Log/YYYY-MM-DD/   camera originals — you drop here
  02 Published Edits/        posts that already went out
  03 Grade Reference/        what grades get matched against
  04 Exports/YYYY-MM-DD/     finished Reels — post from here, top to bottom
  05 Overlays/               logos, handle bugs, lower thirds
```

**Raw clips** are named `YYYY-MM-DD HH-MM-SS what-you-were-doing.mov`. The
timestamp keeps them in shooting order; the description means you can find a
shot without opening anything.

**Exports** are named `NN YYYY-MM-DD description.mp4` — the `NN` prefix is
post order, so you work down the folder and upload in sequence.

## What you do

1. Film.
2. Drop the clips into `01 Raw D-Log/<today>/`. Don't rename them.
3. Tell me they're there.
4. I index, cut, grade, and hand back finished Reels.
5. You drop them into `04 Exports/<today>/` and post in order.

Step 5 is manual because the Dropbox connector here can read files but cannot
write binaries. I deliver finished Reels through chat; you file them.

## What I do per clip

| Step | Tool | Notes |
|---|---|---|
| Index | `index_clip.sh` | Length, exposure, thumbnails. Deletes the clip after — peak disk stays at one file. |
| Plan | `prep_clip.sh` | Cut plans at four silence thresholds + a grade LUT matched to that clip. |
| Cut & grade | `autocut.py` | Removes silences, applies the LUT, exports 4K 29.97fps. |
| Captions | `remotion/` | Matched to your style: `#FDFDFD` base, `#FBD101` active word, 72.6% down frame. |
| Overlays | `overlay.sh` | Timed logo bugs, lower thirds, CTAs, title cards burned onto the master. |

## Overlays

The Formula Dynamics vertical pack is 86 full-frame 1080x1920 PNGs with alpha,
plus badges and bars. `overlay.sh` burns them on with timing:

```bash
./overlay.sh reel.mp4 out.mp4 \
  "pack/corner-logo-bugs/bug_9x16_top-left_logo-white.png:0" \
  "pack/lower-thirds/lt_9x16_service_detailing.png:1.5:6" \
  "pack/cta-captions/cta_9x16_soft_follow-for-more_bar.png:24:30"
```

Each spec is `PATH:START[:END]` in seconds. Omit END and it runs to the end of
the video — that is how the logo bug stays up throughout.

**Overlays are 1080x1920 and our masters are 4K**, so each is scaled 2x.
Tested against a native-1080 composite: on these clean vector-derived PNGs
lanczos holds up, with only slight softening on letterform edges. Keeping the
4K master is the better trade than dropping the whole video to 1080 for the
sake of the graphics.

Use `white` / `logo-white` variants on dark footage, `black` / `light` on
bright footage. `safe-zone-guide/safe-zones_9x16.png` shows what Instagram's
UI covers — worth checking any new placement against it.

## Export target

4K, 29.97fps, 10–35 Mbps, ~75 MB, then **upload through Instagram's Edits app**
rather than the Reels composer.

75 MB and the 10 Mbps floor only both hold up to about 60 seconds. Past that,
either the file grows or the picture starves — autocut keeps the bitrate and
tells you.

## Two things that are not automatic

**Silence thresholds are per-clip.** −26 dB suited the walkthrough; the
detailing clip needed −22; the trim-install clip needed −18. Always
`--dry-run` first.

**Exposure varies clip to clip.** This session ranged YAVG 90–122. One shared
LUT leaves bright clips bright, so posts won't match on the grid. `prep_clip.sh`
builds a per-clip LUT to fix that.

## Posting

I cannot post to Instagram — no tool for it exists here. TikTok is possible
through Higgsfield if the `youngomarie` account gets connected.

## Parked

- Animations in-video (Remotion, or generative via the art skills)
- Stream-style handle overlays for nq.young / youngomarie
