# Creator Kit — Osmo Action 6 → Instagram

A colour and delivery pipeline for vlog / lifestyle / automotive content shot
on a DJI Osmo Action 6 in D-Log M, plus the packaging and growth playbook that goes
with it.

```
creator-kit/
├── luts/                  6 look LUTs + 1 measured D-Log M rescue (.cube, 33³)
├── scripts/
│   ├── build_luts.py      regenerates the look pack (pure stdlib)
│   ├── autocut.py         silence-cut + grade + 4K export, one command
│   ├── idea_scraper.py    outlier videos/posts from your watchlist -> idea list
│   ├── thumbnail.py       best cover frames -> branded IG covers + grid check
│   ├── voice_build.py     his transcripts/captions -> voice/style.json + STYLE.md
│   ├── script_write.py    idea -> script brief (and drafts with --api) in his voice
│   ├── voice_check.py     flags AI tells, long lines, stiff wording, read time
│   ├── match_grade.py     copy a grade from a reference by histogram matching
│   ├── bake_lut.py        bakes any ffmpeg colour chain into a .cube
│   └── ig_export.sh       Osmo clip → Instagram-ready 1080×1920 master
└── docs/
    ├── 01-capture-settings.md    what to set on the camera
    ├── 02-mobile-workflow.md     DJI Mimo + CapCut → upload
    ├── 03-hooks-and-captions.md  hooks, captions, covers
    └── 04-growth-system.md       pillars, cadence, 30-day plan
```

## autocut — the one command

```bash
python3 scripts/autocut.py source.MOV -l luts/AK_NQ_Signature.cube -o reel.mp4
```

Finds the silences, cuts them out, applies the grade, and exports 4K at
29.97fps aiming at a 75 MB file — then you upload through Instagram's Edits
app rather than the Reels composer.

`--dry-run` prints the cut plan without encoding. Tune the cut with
`--noise` (dB threshold) and `--min-silence`. On this footage `--noise -26
--min-silence 0.35` removed 20% and left 29 segments at 3.2s average, which
matches the reference edit's rhythm; the default `-30` only found 6%.

Performance matters on 4K60: raw decode runs at 0.84x realtime and the LUT
drops it to 0.23x. So it defaults to a single ABR pass. Add `--two-pass` for
exact size targeting at double the time, and `--fast` to run the LUT after
the downscale when you are not exporting at native resolution.

## idea_scraper — what to film next

```bash
brew install yt-dlp                     # once, on the Mac
python3 scripts/idea_scraper.py         # writes ideas/out/ideas-<date>.md
```

Reads the latest uploads of every YouTube channel and this week's top posts of
every subreddit in `ideas/watchlist.json`, and lists what is beating its own
source's normal: views over the channel's median, upvotes over the
subreddit's median. A 3x video on a small channel counts the same as one on a
big channel, because the shape is what you copy. Each idea comes with its
title pattern (`I spent $N on N wheels`) and the brand topics it hits.

Re-runs only show new ideas (`--all` shows everything again). `--brand`,
`--top`, `--min-outlier` and `--per-channel` tune it, and `--offline` scores a
saved fetch with no network. Add the channels you actually study to the
watchlist first; the YouTube lists start nearly empty on purpose. Free: no API
keys, no logins, nothing posted. Test: `python3 ideas/test_idea_scraper.py`.

## thumbnail — pick and brand the cover

```bash
python3 scripts/thumbnail.py reel.mp4 --brand fd --text "FORGED|FITMENT DAY"
python3 scripts/thumbnail.py reel.mp4 --brand se --text "KEYS|HANDED OVER" --kicker "THE PICKUP"
```

Never let Instagram pick the cover. This scores 80 frames of the Reel on
sharpness, exposure and colour, keeps the best few (spread out, never a soft or
black frame) and renders each as a 1080x1920 cover twice: clean, and with your
headline. The words after `|` take the accent colour. Each brand keeps its own
look, in the Locked-On style: FD is Bebas Neue with FD red, SE is Space Grotesk
with gold corner brackets and a `[ KICKER ]`, and `vlog` uses the caption gold.

Every cover also gets a grid check: the 3:4 profile-grid crop is drawn on it,
and the script flags a headline that falls outside the crop, in the bottom
third, in the top-left UI corner, or with too little contrast against the
frame. Pick from `covers/<clip>/sheet.png`. `--at 12.5` uses your own frame,
`--lut luts/X.cube` grades it to match the Reel, and `--picks` sets how many.
It never writes copy; the headline is yours. Test: `python3 scripts/test_thumbnail.py`.

## script in my voice — idea to a script Omarie would actually say

```bash
python3 scripts/transcribe.py talking-reels/*.mp4 -o transcripts/       # his own words, on the Mac
python3 scripts/voice_build.py transcripts/ old-captions.txt               # -> voice/style.json, voice/STYLE.md
python3 scripts/script_write.py --idea "why we torque wheels by hand" --brand fd --seconds 30
python3 scripts/script_write.py --from ideas/out/2026-10-27.json --brand se --pick 2 --api
python3 scripts/voice_check.py my-edit.txt --seconds 30
```

- `voice_build.py` measures how he talks: sentence length, pace, questions,
  contractions, fillers, openers, the phrases he repeats and a bank of his own
  lines. Under 1,500 words it says the profile is thin. Feed it talking reels,
  not music-only ones.
- `script_write.py` always writes `scripts-out/<idea>/brief.md` (paste into
  Claude Code). `--api` calls Claude (`claude-opus-5-5`, server-side refusal
  fallbacks on) for 3 drafts with hook, body, CTA, on-screen text and a shot
  list, each run through `voice_check.py`. Edit `drafts.json` by hand, then
  `--check` it again.
- Facts it doesn't have come back as `[CHECK: ...]`, and `voice_check.py` lists
  every figure as a claim to source; those go through nq-facts. Nothing posts.

Test: `python3 scripts/test_voice.py` (no network, the Claude call is faked).

## post_queue — nothing posts without Omarie's yes

```bash
python3 scripts/post_queue.py add --brand fd --kind reel --media reel.mp4 \
    --cover covers/reel/cover-02-text.jpg --caption-file caption.txt --at "2026-10-28 18:00"
python3 scripts/post_queue.py add --brand fd --kind carousel --media 01.jpg 02.jpg 03.mp4 \
    --url https://.../01.jpg https://.../02.jpg - --caption "..."
python3 scripts/post_queue.py page --brand fd       # -> posting/approve/index.html, the post mockup look
python3 scripts/post_queue.py approvals ~/Downloads/approvals.json
python3 scripts/post_queue.py publish               # dry run: what would post
python3 scripts/post_queue.py publish --live        # posts what's approved and due
python3 scripts/post_queue.py list
```

- **The gate.** Every post has a digest: a SHA-256 over the account, type,
  caption, every media file's bytes, the cover and the options. The approval
  page saves the digest each yes was given for. `publish` works the digest out
  again from the files on disk and refuses if anything changed. An edited
  caption or a re-exported video goes back to pending and needs a fresh yes. A
  posted post never posts again. A post is marked `posting` before the API
  call, so a crash can't leave it approved and post it twice; `retry <id>`
  puts a failed post back once you've checked Instagram.
- **Held, not posted:** a caption over 2,200 characters or over 30 hashtags,
  an unsourced `[CHECK: ...]`, a photo with no public URL, or a post whose
  `--at` time hasn't come yet.
- **The approval page** is the post mockup (IG phone frame plus kit) in the
  brand's own look, one brand per page. Each post has Approve, Needs changes
  (a note is required) and Reject. Publish `posting/approve/index.html` as an
  Artifact with `capabilities: {db: {rules: [{path: "approvals", read: "view",
  write: "owner"}]}, user: {}, downloads: true}`, so only Omarie can decide.
  Decisions save to the page's `approvals` collection. The **Save approval
  file** button downloads `approvals.json` for the `approvals` step. Or the
  lead reads the collection with ArtifactData and writes that file.
- **Types.** Reels go up straight from the file (resumable upload), and the
  cover frame comes from `thumbnail.py`'s `covers.json`, `--cover-time` or a
  public `--cover-url`. Instagram only takes photos by public URL (`--url`, `-`
  for none), so photos in a feed post or carousel need hosting first. Videos in
  a carousel upload from the file.

**One-time setup on the Mac** (the token never goes in this repo):

1. The Instagram account must be a Business or Creator account linked to a
   Facebook Page.
2. In a Meta developer app, add Instagram Graph API with
   `instagram_basic` and `instagram_content_publish` (plus `pages_show_list`
   and `pages_read_engagement`). Make a long-lived user token and find the
   Instagram user id (`/me/accounts` → the page → `instagram_business_account`).
3. Save `~/.config/creator-kit/instagram.json` with `chmod 600`:
   `{"accounts": {"fd": {"ig_user_id": "1784...", "token": "EAAG..."}}}`. Add
   one entry per account (`se`, `vlog`). Use `"host": "graph.instagram.com"` for
   an Instagram-login token. Long-lived tokens last about 60 days, so refresh
   before then.

Test: `python3 scripts/test_posting.py` (a fake Graph API on localhost, no
token, nothing reaches Instagram).

## match_grade — copy a look you have no recipe for

```bash
# sample frames from both, then match
ffmpeg -ss 20 -i reference.mp4 -frames:v 1 -vf scale=216:384 -pix_fmt rgb24 hm/ref_20.ppm
ffmpeg -ss 20 -i source.MOV    -frames:v 1 -vf scale=216:384 -pix_fmt rgb24 hm/src_20.ppm
python3 scripts/match_grade.py --ref "hm/ref_*.ppm" --src "hm/src_*.ppm" --out look.cube
```

Measures where the reference puts its shadows, mids and highlights per channel
and builds the curves that move your source onto it. Both sets need to come
from similar content — same room and lighting — or you transfer the scene's
colour distribution rather than its grade.

## Start here

1. **Camera** — `docs/01-capture-settings.md`. Shoot 4K 4:3, 60fps, D-Log M
   10-bit, manual white balance, 1/120 shutter.
2. **Convert** — download DJI's official D-Log M → Rec.709 LUT from
   <https://www.dji.com/lut>. This kit deliberately does not ship one; see below.
3. **Grade** — apply a look from `luts/` on top of that conversion.
4. **Deliver** — `docs/02-mobile-workflow.md` for CapCut, or `ig_export.sh` on
   a laptop.

## Why there is no conversion LUT in this kit

DJI does not publish the D-Log M transfer function. A conversion LUT generated
without it is guesswork, and a wrong conversion is worse than none — it bakes
in a colour error that every later adjustment amplifies.

So the look pack ships **look** LUTs only. They expect footage already in
Rec.709 and are applied after DJI's official conversion:

```
D-Log M clip → DJI official conversion → look LUT from this kit
```

## AK_DLogM_Rescue — read this before using it

`luts/AK_DLogM_Rescue.cube` is a **measured** D-Log M → Rec.709 stretch, derived
empirically from real Osmo Action 6 D-Log M footage (black point, white point
and saturation loss measured off the actual signal), not from DJI's undisclosed
transfer function. It is deliberately skin-safe: it does **not** push deep skin
tones orange, which most warm "cinematic" conversions do.

Use it when you cannot get DJI's official LUT into your app. When you can,
DJI's official conversion is still the more correct starting point. Either way,
**denoise before it** — stretching a flat log band multiplies whatever
compression noise is already in the file.

## AK_Garage_Dark — for the build footage

`luts/AK_Garage_Dark.cube` is a second measured rescue, built from real Anti
Stock garage footage: black walls, dark floor, hard point lights. It stretches
the shadows harder than `AK_DLogM_Rescue` and cools them, so concrete and steel
separate from the warm work lights instead of everything sitting in one muddy
band. Denoise before it, same as the other one.

Use `AK_DLogM_Rescue` for normally-lit scenes and `AK_Garage_Dark` for the shop.

## The looks

| LUT | For |
|---|---|
| `AK_Neutral_Punch` | Daily driver. Clean contrast and colour, nothing stylistic. |
| `AK_Golden_Vlog` | Golden hour, cafés, interiors. Warm midtones, cool shadows. |
| `AK_Garage_Chrome` | Garages, workshops, showrooms, car builds. Cool steel, warm protected skin. |
| `AK_Nordic_Steel` | Overcast, combat, winter. Cold, high contrast, desaturated. |
| `AK_Film_Halation` | Montage and B-roll. Lifted matte blacks, faded film feel. |
| `AK_Night_City` | Low light, firelight, streets. Opens shadows without noise bloom. |

Every look carries mild compensation for Instagram's encoder baked in: a small
black floor lift so shadows band less after transcode, a guard on extreme reds
(the first thing 4:2:0 chroma subsampling smears), and a highlight rolloff so
skies compress instead of clipping.

Regenerate or tweak them:

```bash
python3 scripts/build_luts.py            # writes luts/*.cube
python3 scripts/build_luts.py --size 65  # finer, larger files
```

The generator validates every look before writing: output stays inside the
legal 0–1 cube, the neutral ramp stays monotonic (no posterising on grey
gradients), and black and white points land in range. A look that fails
validation is not written.

## The export script

```bash
./scripts/ig_export.sh clip.mp4 \
  -c ~/Downloads/DJI_DLogM_to_Rec709.cube \
  -l luts/AK_Garage_Chrome.cube \
  -m fill -f 30 -o reel.mp4
```

Produces 1080×1920, square pixels, H.264 High, yuv420p, tagged bt709, faststart,
audio normalised to −14 LUFS. Reframe modes are `fill` (centre crop), `fit`
(letterbox) and `blur` (blurred background fill).

Requires ffmpeg with `libx264`, `lut3d`, `unsharp` and `loudnorm`. Run
`--help` for all options.

**Why it targets 1080×1920 rather than 4K:** Instagram re-encodes everything and
downscales anything above 1080 on the long edge. Delivering a clean 1080×1920
master means you control the resampling and sharpening instead of their
encoder. 4K uploads typically come back softer, not sharper.
