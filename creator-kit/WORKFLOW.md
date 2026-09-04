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
| **Edit** | **`cut_clip.sh`** | **The whole edit off one download: window, grade, cut, export.** |
| Captions | `remotion/` | Matched to your style: `#FDFDFD` base, `#FBD101` active word, 72.6% down frame. |
| Overlays | `overlay.sh` | Timed logo bugs, lower thirds, CTAs, title cards burned onto the master. |

`cut_clip.sh` replaces the old `prep_clip.sh` → `autocut.py` two-step, which
needed the clip downloaded twice. It makes three decisions from measurement:

**Which 60 seconds.** A nine-minute take silence-cut end to end is a
seven-minute file. That is not a Reel and you would never upload it.
`speech_window.py` slides a window over the clip and keeps the one holding the
most speech, with the edges snapped to phrase boundaries so it does not open
mid-word. In a build vlog the strongest stretch is where you are talking, not
where the room is quiet and the camera is drifting.

**Which grade.** Matched per clip against `03 Grade Reference`, because this
session ran YAVG 90–122 and one fixed curve leaves the bright clips bright.

**Which silence threshold.** Swept −26 to −18 dB, and the plan whose average
shot length lands closest to your ~4s rhythm wins. −26 dB removes almost
nothing from a clip recorded next to running tools; −18 dB shreds a quiet
walkthrough. Sweeping per clip is what holds the pacing steady across a
session.

Downloading and deleting deliberately stay *outside* the script. Temporary
Dropbox links last 900 seconds, and a script holding one while it encodes for
half an hour will fail — which is exactly how an earlier run lost a clip.

## Which brand?

Two companies, and it decides the overlays and the language. See `BRANDS.md`.
Short version: **Formula Dynamics** is the shop (installs, bay work,
detailing); **Supercar Experience** is the rental side (pickups, dropoffs,
handovers). The Anti Stock shirt is Supercar Experience merch and is *not* a
brand marker — he wears it in the FD shop. Judge by what is happening.

## Overlays

Two packs, one for each company:

- **Formula Dynamics** — 86 PNGs, supplied. Shop content.
- **Supercar Experience** — 34 PNGs in `overlays-se/`, built from
  supercarexp.vip's own tokens. Rental content: pickups, dropoffs, the fleet.

They are geometry-matched, so a video can cut between shop and rental footage
without the graphics appearing to change size. Bug 331×88 against FD's 315×101;
lower thirds both 211px tall ending at y=1486; CTA bars both ~110px at y~1362;
titles both ~400–430px from y~635. `build_se_overlays.py --verify` prints every
bounding box so this stays checkable rather than trusted.

Both packs are full-frame 1080x1920 PNGs with alpha. `overlay.sh` burns them on with timing:

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

## What the encode actually costs

Measured on this machine, 4 cores, no GPU:

| | rate |
|---|---|
| 4K60 HEVC decode, no filter | 0.84× realtime |
| 4K60 decode + LUT + x264 | **0.17–0.21× realtime** |
| Dropbox download | ~42 MB/s |

The x264 preset barely moves that number — `medium`, `fast` and `faster` come
in at 0.17, 0.19 and 0.21. **The source decode is the bottleneck, not the
encode**, so there is nothing to buy by dropping quality.

This is why windowing matters. Cutting whole takes would have been about five
hours for one session. Editing a 60s window means ffmpeg decodes a minute
instead of nine.

One more that was costing more than everything else combined: `silencedetect`
without `-vn` decodes the video stream to read a waveform. On a 4K60 source
that is 183 seconds per pass, and the threshold sweep runs five passes per clip.
Audio-only takes it under one second. Same numbers, 200× faster.

## Parked

- Animations in-video (Remotion, or generative via the art skills)
- Stream-style handle overlays for nq.young / youngomarie / youngomarie
