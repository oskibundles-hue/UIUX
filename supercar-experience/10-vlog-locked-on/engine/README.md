# Vlog engine: ingest and planning (everything before the render)

One CLI, `vlog.py`, takes a shoot day from Dropbox to an editor-ready index, and later from an `edl.json`
to full-quality mezzanines. It replaces the Sep 15 scratch scripts (`proc.py`, `transcribe.py`, `day.py`,
`sheet.py`, `mp4index.py`, `fetchplan.py`, `fetch.py`). The render lives elsewhere
(`../2026-09-15-rally-v2/`, `../vlog-kit/`), and this engine does not touch it.

| stage (Sep 15: 44 clips, 158 GB, 2 h 54 min of footage) | before | now |
|---|---|---|
| survey: download, audio, thumbnails, idx | 80 min, serial, babysat | one unattended run, 5 clips in flight, no original on disk |
| transcripts | ran alongside | same model and settings, runs inside the survey on the cores it frees |
| finding moments + exclusions | 30-40 min by hand | `index`: 80 s (11 s re-run) → moments.md, flags.json, day.md |
| fetch + full-quality clips | 40 min | fetched only as needed, cuts start as spans arrive, 1 ffmpeg per core, x264 superfast |

The measured numbers and the projection are under "Timings". Python 3 with numpy, Pillow, PyAV and faster-whisper,
all already installed. It uses `curl` and the ffmpeg from `imageio_ffmpeg` (or `$VLOG_FFMPEG`). The speaker model
(26 MB ONNX) downloads from the Hugging Face hub on first use.

## Local mode (footage already on this machine)

Use it for footage on the Mac's Dropbox folder, a camera card or an offload drive. `links DAY --local FOLDER`
registers the videos in a folder. `ingest --local` and `fetch --local` then serve those files on 127.0.0.1 through
the same single-use-link code path as Dropbox (`lib/localsrc.py`, `lib/rangeserver.py`), so nothing has to be
requested and nothing expires. NEED.json is answered automatically.

Clips registered with Dropbox paths (`--clips`) are looked up under `--local-root DIR`, or under the Dropbox desktop
folder by default, matching upper/lower case like Dropbox does. `ingest --edl edl.json` surveys only the clips a cut
uses.

Online-only Dropbox files are downloaded in full by the Dropbox app when read. Local mode totals them first and stops
if they would not fit on the disk. `VLOG_HWACCEL=videotoolbox` makes fetch decode the HEVC sources on the Mac's media
engine. `doctor.py` turns it on only after checking that the frames match the CPU decode. Mac setup:
`../MAC-SETUP.md`.

## Runbook

`DAY` is a working directory for one shoot day, for example `$S/days/2026-10-02`. Keep it outside the repo, because it
holds audio, thumbnails and transcripts. `E=supercar-experience/10-vlog-locked-on/engine`.

### 1. Clip list → link request

```bash
python3 $E/vlog.py links DAY --clips clips.txt
```
`clips.txt` holds one Dropbox path per line, with an optional `TAB size`. The raw JSON from Dropbox `list_folder` also works.
Only `.MP4`, `.MOV` and `.M4V` files are kept. The command registers the clips in `DAY/clips.json` and assigns ids: DJI
`DJI_20260915161022_0001_D.MP4` becomes `0001`, and a phone clip becomes `P<hhmm>` from its upload name, with `a`/`b`/`c`
added when several share a minute (the Sep 15 ids). It then writes `DAY/links/request.json`, which lists batches of at
most 24 entries, 12 clips per call, each path twice. The batches are in the order the clips will stream.

### 2. Links → `DAY/links/*.json` (this step is yours: only you can call the Dropbox tool)

For each batch in `request.json`, call `download_link(entries=<that batch's entries>, expiration_in_sec=900)`
and save the tool's answer unchanged as `DAY/links/batch_01.json`, `batch_02.json` and so on. Any file name
ending in `.json` works, except `request.json` and `NEED.json`.

**What a links file must contain:** the raw tool answer, which is `{"entries": [{"download_url": ..., "expiration_in_sec": ...,
"path_display": ..., "path": ..., "name": ..., "size": ..., ...}, ...]}`. Each entry needs a `download_url` and a
`path_display` (or `path`) equal to the clip's Dropbox path. The path can differ in case but not otherwise. Ingest also
uses `size` and `expiration_in_sec`. A clip needs two entries, one for the tail read and one for the stream, and their
order does not matter. Several answers can go in one file, pasted one after another or wrapped in a list. An MCP wrapper
whose text content is that JSON also works. A link's clock starts at the file's mtime, so save each answer as soon as the
tool returns it. Ingest stops using a link 90 s before its stated expiry.

When to call: on Sep 15 sizes, streaming uses call 1 within seconds, call 2 within about 1 min, call 3 by 2.5 to 3.6 min
and call 4 by 5 to 7 min (at 420 to 280 MB/s). Making **all calls back to back at the start** keeps every link inside its
15 min, even at 200 MB/s. If links still run short, because a batch was not requested, links expired or a clip failed,
ingest writes **`DAY/links/NEED.json`** with the exact `entries` of the next call. Call the tool with them, save the
answer as a new `DAY/links/*.json`, and ingest continues on its own. To wait for it:
`until [ -f DAY/links/NEED.json ]; do sleep 5; done` (Monitor tool).

### 3. Ingest (unattended)

```bash
python3 $E/vlog.py ingest DAY          # run in the background; log: DAY/logs/ingest.log
python3 $E/vlog.py status DAY          # any time: one line per clip
```
The run exits when every clip is surveyed and transcribed. It also exits when clips still need links and none arrive
for `--wait-links` seconds (default 900). Its report goes to `DAY/logs/ingest_report.json`, with per-clip timings, errors
and anything not done. **Re-running is safe and is how failures are fixed.** A failed clip keeps what it already has (its
moov stays cached, so it needs only one new link), ingest asks for fresh links through NEED.json, and every link is
logged to `links/used.log` before its first request, so no link is ever reused. A lock file (`DAY/.ingest.lock`, `flock`,
no `pgrep`) stops a second copy from starting. Useful flags: `--streams 5`, `--kf-step 2` (seconds between kept
keyframes), `--kf-workers 2`, `--asr-workers 4`, `--no-asr` (then run `vlog.py transcribe DAY`), `--big-first 2`.

### 4. Index

```bash
python3 $E/vlog.py index DAY                                    # uses the saved host voiceprint
python3 $E/vlog.py index DAY --host-ref 0001:0-48 --host-ref 0001:83-105   # or name clear host narration
```
It reads `DAY` and writes to `--out`, which defaults to `DAY`. The files are listed under "What index writes".

### 5. The cut → mezzanines

```bash
python3 $E/vlog.py plan DAY --edl edl.json            # -> DAY/fetch/fetchplan.json + DAY/fetch/request.json
#   call download_link for each batch of DAY/fetch/request.json (one link per span), save answers in DAY/fetch/links/
python3 $E/vlog.py fetch DAY --out $S/mezz            # all spans in parallel, 4 cuts at a time
```
`edl.json` uses the Sep 15 schema: `shots` (a `speed` of `"keyframes"` means a keyframe timelapse), `dialog` and
`audio_extra`. The mezzanines match the ones the v2 render reads: `<src>_<t0>-<t1>.mov`, display-rotated, long side
1920, native frame rate (VFR phone clips become 29.97 CFR), iPhone HLG tone-mapped to BT.709, x264 High 10 CRF 13,
PCM 24-bit. There is also `<src>_timelapse.mov`. Options: `--handles 0.8` (seconds around every range), `--preset superfast`,
`--crf 13`, `--workers 4`, `--streams 6`. **`plan --audio-only-vo`** turns VO and nat ranges that no shot shows on
screen into `<src>_<t0>-<t1>.wav`. That cuts 20% of the 4K decode on Sep 15, but only use it once the render reads
dialog from those `.wav` files, because the v2 render reads it from the `.mov` files.

## How ingest works

Each clip uses two single-use links:

1. **Tail**: one Range request for the last `max(16 MB, size/1000)` bytes. `find_moov_in_tail` finds the `moov` whose
   size chains exactly to EOF and whose first child is `mvhd`, and saves it as `idx/<id>.moov`. On Sep 15 the largest
   moov is 4.2 MB. If the tail holds no moov (a faststart `.MOV` with `moov` at the front), the stream picks it up.
2. **Stream**: one plain GET of the whole file, fed through `StreamFilter`. The filter walks the top-level atoms as
   they arrive and writes into a sparse file of the original size. It writes every non-`mdat` atom (the head and the
   moov) plus, inside `mdat`, only the bytes of every audio sample of the first sound track and of the video sync
   samples nearest a 2 s grid. That is about 1.3% of a 4K DJI file (31 MB of 2.4 GB). With neither a tail moov nor a
   front moov, a file under 2 GB is kept whole ("spill"), and a larger one fails with a clear error. The original is
   never on disk.
3. **Post**: `idx/<id>.head`, `.moov` and `.json` (atoms, probe, clock, rotation, HLG). Audio is stream-copied from
   the sparse file to `aud/.<id>.m4a.part` and renamed to `aud/<id>.m4a` only when complete (the Sep 15 crash was a
   transcriber reading a half-written file). Thumbnails are decoded **straight from the sample tables**: one PyAV
   decoder built from the track's `hvcC`/`avcC` is fed only the kept sync samples, each read at its own offset. They
   are display-rotated, 270 px wide, saved as `kf/<id>/<ms>.jpg`, with picture statistics in `kf/<id>/stats.json`. Then
   the sparse file is deleted.
4. **Whisper** is faster-whisper `small.en` with the Sep 15 settings (int8, VAD, beam 1, word timestamps). It runs in
   1-thread worker processes, which were the most efficient here: 150 s of dense speech took 23.4 s on 1 thread,
   16.5 s on 2 and 18.2 s on 4. The pool grows as cores free up (4 cores − 1 while streams run − busy thumbnail
   workers). Clips queue longest audio first, a clip is queued only after its audio file is renamed, and each clip gets
   3 attempts. Batched inference was 1.7× faster but dropped 17% of the words, so it is not used.

**Why this order.** The network (280-420 MB/s) is not the limit; the 4 cores are. Whisper, thumbnails and stream
handling add up to about 45 core-minutes for Sep 15. Streaming the largest files first leaves the cores idle for the
first 3-4 minutes, because nothing finishes until then. The scheduler therefore starts the 2 largest clips at once, so
their long downloads overlap everything, and then takes the rest **smallest first**, so audio and keyframes reach the
CPU work within seconds. `tests/sim_order.py` simulates this on the real Sep 15 sizes and speech amounts. It puts
this order at 11.2-13.3 min, against 12.6-14.4 min for largest-first, when a single stream can reach 70-97 MB/s. At
about 50 MB/s per stream both orders come out at about 15 min.

## What index writes

- **day.md**: a table of clips (clock, length, picture note), then per clip every transcript line on the camera clock
  (`16:10:24  0:02.1-0:08.6 HOST  0.95  What's going on guys? ...`). A line is a whisper segment split at pauses of
  0.5 s or more, so a question and its answer get separate lines. Flagged lines are marked `[NO: speed]` or `[bleep: profanity]`.
  Each clip also shows its contact sheet (`sheets/<id>.jpg`) and its never-use spans.
- **speakers.json**: HOST or OTHER per line, with confidence, the voice score and the reason ("reply to a host
  question"). The voice embeddings come from WeSpeaker ResNet34-LM (VoxCeleb) as ONNX on onnxruntime, with 80-bin Kaldi
  fbank computed in numpy. The host centroid is built from `--host-ref` or the saved voiceprint, then re-estimated from
  the day's clearly-host lines. A line is HOST when `w(len)·(cos − τ)/0.07 + priors > 0`, where
  τ = self-similarity of the reference − 0.20 (0.42 on Sep 15). The priors are +0.3 for camera (DJI) clips and −1.2 for
  short replies within about 3 s after a HOST question. Short lines carry little voice evidence, so their weight shrinks.
  Confidence below 0.65 means treat the label as a guess. The voiceprint is saved to `voiceprints/host.npy`, which is
  git-ignored because it is biometric data.
- **flags.json**: never-use spans (`block`) and bleep spans (`caution`), timed from word timestamps. The categories are
  password or code, request to cut ("take that out", "don't post that", which reaches back 20 s or over the
  "17 second segment" it names, but only to the start of the flagged talk it refers to), speed numbers and speed talk,
  weapons, unsafe driving, fleet faults, police, and profanity or slurs (bleep, not block).
- **moments.json / moments.md**: the 15 best candidates per category: intro, offer/CTA, lineup/car naming, guest
  arrival, briefing/route, leading/convoy, food/dinner/team, guest reactions and closing. Each candidate has clip,
  in/out, clock, speaker, text, why (the phrases that matched) and a keyframe strip (`sheets/moments/<cat>_<rank>.jpg`).
  Candidates that overlap a block flag are listed separately as blocked. Candidates are runs of 1-6 lines, scored on
  phrase evidence, speaker fit, time of day, whisper confidence and length, minus filler.
- **quality.json**: per-clip picture notes from the thumbnails: very dark, black frame, lens covered or blurred, camera
  sideways, camera upside down, each with time ranges.

## Tests (all local; none touch Dropbox)

`tests/rangeserver.py` is a stand-in for Dropbox temporary links. Each token works for exactly one request of any kind,
after which it returns 410. A single `Range` gets a 206 and multi-range gets a 200 with the whole file. It serves with `sendfile`.

| test | result |
|---|---|
| `test_stream.py` on `raw/keep/DJI_0027.MP4`, `DJI_0029.MP4` (moov at end) and a faststart `.MOV` made from 0027 (moov at front) | moov from tail = moov streamed = original; **audio stream copy byte-identical** to one from the full file (182 / 673 packets); **every kept keyframe pixel-identical** to ffmpeg's decode of the full file (framemd5 of the 10-bit planes, 3/3, 8/8, 3/3); 1 Range (206) + 1 GET (200) per clip |
| `test_ingest.py functional` | 3 clips, 1 clip per call so NEED.json runs, one link burnt beforehand (410): the failure is reported, a fresh link is requested and used, and all 3 clips are surveyed and transcribed, with sparse/ empty afterwards |
| `test_ingest.py throughput` | 5 × 2.4 GB, whisper off: 12 GB in 44 s wall. Streaming ran about 365 MB/s per stream, which is local and CPU-bound (Dropbox caps it lower). 109 thumbnails per clip in about 12 s |
| `test_fetch.py` | plan + fetch of 4 range cuts + 1 keyframe timelapse from local links: 60 s wall; **frames cut from the sparse file are identical** to the same cut from the full original |
| `validate_sep15.py raw OUT --edl raw/edl.json` | speakers 5/5, flags 13/13, approved dialog 31/31 in the top 10 of its category (24 in the top 3, 28 in the top 5), and no block flag overlaps the approved cut |

## Timings

Measured here, with another agent's render benchmark sharing the 4 cores, so these are pessimistic:

- Stream filter: 0.54 CPU-s/GB in Python plus 1.11 in curl writing to the pipe. One stream reaches 890 MB/s on
  localhost, far above Dropbox. TLS to the local proxy is extra and cannot be measured without Dropbox.
- Thumbnails: 0.11 s per keyframe for 3840×2160 and about 0.14 s for 3840×3840, covering decode, scale, JPEG and
  statistics on one core. Sep 15 at 1 per 2 s is about 5,200 keyframes, or about 11 core-minutes.
- Whisper: 150 s of dense speech took 23.4 s on 1 thread. Sep 15 has 4,209 s of speech, about 26 core-minutes.
- Index: 79 s for Sep 15 (59 s of that is voice embeddings); a re-run takes 11 s.
- Cuts, per core, decode + lanczos + x264 10-bit CRF 13:

  | source | decode + scale, no encode | faster (Sep 15) | **superfast** | ultrafast |
  |---|---|---|---|---|
  | 3840×2160 | 6.7 fps | 3.2 fps, Y-PSNR 49.9 dB | **4.7 fps, 50.8 dB** | 5.8 fps, 49.8 dB |
  | 3840×3840 | 4.3 fps (decode alone 4.8) | – | **3.0 fps** | 3.7 fps |

  The Y-PSNR is measured against the lanczos-scaled source, 10-bit, over 120 frames.

  `superfast` is the default because it scores higher than the approved mezzanines and runs about 1.5× faster per core.
  `ultrafast` matches the Sep 15 quality (−0.1 dB) and runs 1.8× faster, but it has no AQ and no deblocking.

**Projection for a day like Sep 15 (44 clips, 158 GB):** streaming takes 8-10.5 min at 280-420 MB/s. The CPU work is
2,600-2,900 core-seconds, about 11-12 min on 4 free cores. The whole-pipeline simulation gives **11-13 min** when a
stream can reach 70-97 MB/s and about 15 min when a single stream tops out near 50 MB/s. Both are inside the 20 min
target, provided the 4 cores are not shared with a render benchmark. `plan` for the Sep 15 EDL gives 48 cuts, 47 links
in 2 calls, 10.6 GB and about 19,700 source frames, 33 of the cuts from square 3840×3840 clips. At the rates measured
under load that is about 26 min of cutting with superfast, 21 with ultrafast, and about 20% less with `--audio-only-vo`.
The last run took 40 min. This stage is bound by HEVC decode, and the remaining levers are fewer frames (handles,
audio-only VO) or free cores.

### Real run on Dropbox (2026-09-27, Sep 15 day)

46 clips (33 DJI, 13 iPhone), 169.3 GB, 92 links in 4 back-to-back calls. The render agent's SSIM/PSNR comparisons
shared the 4 cores for the whole run.

| step | before (Sep 15) | real run |
|---|---|---|
| survey: stream, audio, thumbnails, idx | 80 min, babysat | **12.1 min** streaming (+727 s), 0 failures, exactly 92 links used (NEED.json appeared twice while batches 2-4 were still being saved; no extra call) |
| transcripts | ran alongside | done at **19.3 min** (+1155 s); whisper sat at 1 worker while thumbnails held the cores, then cleared 26 queued clips in 7 min |
| index | 30-40 min by hand | **103 s** (voice embeddings 96 s) → 2,324 lines, 88 flags (13 block), 112 moments |
| disk | 17 GB peak, originals on disk | 534 MB for the whole day, no original on disk |

Streaming ran at 233-277 MB/s aggregate while 5 clips were live. Single streams ran at 21-95 MB/s; the slowest, 0015 at
21 MB/s, took 343 s and was the tail. `tests/validate_sep15.py` on the real index: speakers 5/5, flags 13/13, no block
flag on approved dialog. Moments: 22/31 of the approved dialog pieces in the top 3, 30/31 in the top 10. The 31st, the
host's "you'll get the R8" (transcribed "RA"), is #13 in lineup, at score 3.7 against a nine-way tie at 3.8. It is
still listed in moments.md and day.md.

Next lever for this stage: give whisper priority over thumbnails, because thumbnails aren't needed until `index`, and a
free core for ASR during streaming would take off most of the 7 min tail.

## Files

```
vlog.py            CLI
lib/common.py      ffmpeg, logging, clip ids and camera clocks, the DAY layout
lib/mp4.py         atoms, moov sample tables (numpy), moov-in-tail, keep ranges, byte spans, Annex-B
lib/links.py       Dropbox link JSON parsing, the single-use pool (used.log), request batches
lib/stream.py      curl Range / stream, SparseFile, StreamFilter
lib/thumbs.py      keyframes straight from sample tables -> thumbnails + stats; old kf/ layout reader
lib/asr.py         whisper worker processes and the pool
lib/ingest.py      the scheduler (tails, streams, post, thumbnails, whisper, NEED.json, report)
lib/speaker.py     fbank, WeSpeaker ONNX embeddings, host centroid, HOST/OTHER labels
lib/flags.py       exclusion rules
lib/moments.py     moment categories and scoring
lib/quality.py     picture notes
lib/sheets.py      contact sheets and moment strips
lib/dayindex.py    index: day.md, speakers.json, moments.*, flags.json, quality.json
lib/fetch.py       plan + fetch + cut (range, keyframe timelapse, audio-only)
tests/             rangeserver.py, test_stream.py, test_ingest.py, test_fetch.py, validate_sep15.py
```

## Known limits

- Speaker labels on very short replies (under 1 s) rely on the reply-after-a-question prior more than on the voice.
  On Sep 15, "Wonderful time." comes out OTHER at only 0.58 confidence, and the host's own "Glad to hear it" right
  after the check-in reads as OTHER. The guide's briefing (P2236) and the Roma answer are clear-cut.
- Picture notes are brightness and texture heuristics. They catch the Sep 15 cases (finger on the lens at 0015 5:40,
  0011 on its side, 0008 upside down, night interiors) but can miss a partial occlusion such as the ring at 0015 5:47.
- The moment phrase lists were written and checked on one day. Expect to add car names, places and CTA phrasing as
  new days show them. They are plain regexes at the top of `lib/moments.py` and `lib/flags.py`.
- The real-Dropbox timing (TLS through the proxy, per-stream speed) has not been measured with this code yet.
