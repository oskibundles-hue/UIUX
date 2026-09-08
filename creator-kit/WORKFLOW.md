# The system

You film. You drop it in Dropbox. I edit. You post.

## Dropbox

```
/Anti Stock Media/
  01 Raw D-Log/YYYY-MM-DD/   camera originals — you drop here
  02 Published Edits/        posts that already went out
  03 Grade Reference/        what grades get matched against (one file; older ones in _previous/)
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

## If you grade it yourself

Drop the graded clips (Rec.709, not D-Log M) into `01 Raw D-Log/<date>/`
the same way and say they are graded. I run the same edit with the grade
step turned off (`cut_clip.sh --graded`): window selection, silence cut at
your rhythm, 4K export at CRF 16 with no bitrate cap. Nothing touches the colour.

Two things to keep in mind when grading for this pipeline:

- Export from your grading app at the camera's resolution and frame rate
  (4K, 60 or 30 fps) and at a high bitrate. Every generation after yours is
  one more encode; a 20 Mbps hand-off lands at Instagram noticeably softer
  than a 100 Mbps one.
- Keep the grade consistent across a session. The cut order is the shooting
  order, so a warm clip next to a cool one shows.

## Trial Reels (combined cuts)

`docs/05-trial-reels.md`. Several exports joined in shooting order into one
30-60s Reel with captions, hook, logo bug and end card, checked with
`reel_check.py` before it goes out. Footage takes one encode from the
assembled master to the delivery file.

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

4K, 29.97fps, quality-first (CRF 16, no bitrate cap), then **upload through Instagram's Edits app**
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

## Looks and caption styles

Two grades and two caption styles ship in the kit. Both come off the same
reference frames in `hm/`; the difference is how hard they lean on them.

| flag | what it does |
|---|---|
| `cut_clip.sh ... --look match` (default) | copies the reference grade exactly: full tone match, greys at the reference's +5.7 R-B |
| `cut_clip.sh ... --look vlog` | natural cinematic: 85% tone match, greys aimed at +2.0 R-B (less red), blacks lifted 0.03, highlight knee 0.08, saturation 92%, no sharpening. Pair with `compose_reel.sh ... --sharpen 0` |
| props `"captionStyle": "classic"` (default) | measured reference style: white line, spoken word turns gold |
| props `"captionStyle": "pop"` | line pops in with an overshoot, spoken word gets a gold pill with dark type and a small lift |

Under the hood `match_grade.py` grew `--grey-target`, `--lift` and `--knee`,
and `autocut.py` grew `--post` for an extra filter after the grade.

## Working notes (2026-09-08)

- **Disk on the remote box is ~8 GB usable.** Rebuilding a series means pulling Dropbox raws in waves (single-use links, 15-minute expiry), cutting, deleting each raw at once, and dropping a local final only after the hosted copy answers HTTP 200 with a matching Content-Length. `cut_clip.sh` is deterministic from the audio, so re-cuts land on the original timeline and the existing transcripts stay valid (checked within 0.2 s on all 18 clips).
- **To do:** install the `/watch` video plugin (`claude plugin marketplace add bradautomates/claude-video`, then `claude plugin install watch@claude-video`). It costs ~40 tokens a turn in the listing, ~3k when invoked, and ~1.5k per extracted frame. Local-file transcripts need `GROQ_API_KEY` or `OPENAI_API_KEY` in `~/.config/watch/.env`.
- **Motion graphics preferences (Omarie, 2026-09-08):** keep the chapter bar (start-to-end progress with named chapters), the SF90 spec callouts, the kinetic intro and the card outro. Drop the "send this to your friend" CTA. Captions stay one size: no oversized key word. Grade every new cut in the vlog look.
- **To do:** replace the grade reference in Dropbox `03 Grade Reference` and rebuild `hm/ref_*.ppm` from it (reminder set for 2026-09-08 20:00 UTC).

## Whose voice is it

`scripts/who_speaks.py` tags every transcript segment as Omarie or someone else using a
speaker embedding (Resemblyzer) compared to `voice/omarie_profile.json`. The profile was
built on 2026-09-08 from 14 confirmed segments of his voice; his lines score 0.72–0.89,
the one other speaker in the session scored 0.64. Threshold 0.70.

```
python3 scripts/who_speaks.py tag <audio> <transcript.json> --profile voice/omarie_profile.json -o drop.json
python3 scripts/who_speaks.py build <audio> <transcript.json> --not 8.8-13.3 --profile voice/omarie_profile.json -o voice/omarie_profile.json   # keep teaching it
```

`drop.json` feeds `rewords.py` so captions only follow his voice. Re-run `build` with
`--not` ranges whenever he confirms a mis-tag; the profile blends the new segments in.
Setup on a fresh box: `pip install torch --index-url https://download.pytorch.org/whl/cpu librosa scipy`,
`pip install --no-deps resemblyzer`, and a stub `webrtcvad.py` (see notes) because the real one needs a compiler.
- **Motion graphics palette (2026-09-08):** accent red is Formula Dynamics red `#DE1A22` (bars, underlines, wipes, title rule), not the theme orange; gold `#FBD101` for highlights. Uniform captions sit at 70.5% of frame height at 2.35% of height (Archivo 800); he found the earlier 62% / 3.1% too high and too big.
- **Deliverables PDF:** `motion/index.html` is built from DELIVERY.md and printed with headless Chromium; one file to drop into Dropbox. Regenerate after each delivery round.

## Fast Cut series (2026-09-08, evening)

- Build driver for the MR series lives in `/home/user/footage/motion2/` (driver.sh for waves and cuts, reels2.sh + build_mr.sh per reel, make_page.py for the page, rows.py for DELIVERY rows and the Dropbox note). Presigned upload slots die after roughly two hours, so request each reel's slot when its build starts, not up front.
- `plan_reel.py` now slides a window back when the only speech sits late in a take, and `--drop-dir` keeps other-voice lines from attracting the window. Before this, MR4 opened on 20 s of silence.
- Any loop that runs ffmpeg or curl inside `while read` must read from fd 3 (`read -u 3 … done 3< list`) and give the tools `</dev/null`; twice today a tool swallowed the rest of the list.
- Scores: MR1 96, MR2 97, MR3 91, MR4 85 (low-speech part), MR5 94, MR6 93, MR7 94, MR8 93.

## Delivery format (standing, from 2026-09-08 evening)

- Deliver files through the Downloads page (`motion2/make_hub.py` builds it from DELIVERY.md; artifact https://claude.ai/code/artifact/fb14668e-2db5-4cf4-9e6c-ae9df97b0d82): one row per file, real filename, a Download button beside it, grouped by the Dropbox folder it belongs in. Re-run the generator and republish the same file whenever DELIVERY.md gains rows.
- Dropbox cannot take binary uploads from the connector; the Downloads page plus the "ALL LINKS" note in 04 Exports is the hand-off. Kit assets ship as one zip (`2026-09-08 CREATOR KIT … .zip`).
