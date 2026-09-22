# Fast Cut / Singles recovery

**Status as of 2026-09-22: 26 files, 8.60 GB, no copy in Dropbox. All 26 still
reachable on the CDN. Not yet recovered.**

## What happened — these were never uploaded, not deleted

**Corrected 2026-09-22 after checking the Dropbox file requests.** Nothing was
deleted. These files were never uploaded in the first place.

The evidence is unambiguous — every relevant file request reports
`file_count: 0`, meaning it has never received a single file:

| File request | Destination | Created | Files received | Open? |
| --- | --- | --- | --- | --- |
| Fast Cut Series — MR1 to MR8 | `/Portfolio/03 Personal Vlogs/Fast Cut Series` | 2026-09-09 05:00 | **0** | **closed** |
| Singles and Intros — 18 clips | `/Portfolio/03 Personal Vlogs/Singles` | 2026-09-09 05:01 | **0** | open |
| Personal Vlogs — Anti Stock build series | `/Portfolio/03 Personal Vlogs` | 2026-09-09 04:41 | **0** | open |

Both `Singles/README.md` and `INDEX.md` carry "Upload here" instructions and
active file-request links. They are destination placeholders describing what
*should* arrive, written 2026-09-09, complete with the CloudFront links someone
would fetch the files from in order to upload them. `Singles/` exists with only
its README because the folder was created for the upload that never came;
`Fast Cut Series/` was never created at all.

`Reel Cut Series/` in the same parent folder *did* get its uploads (RC01–RC12,
17 GB), which is why it looks complete next to two that do not.

So the practical situation is unchanged — these 26 files have no durable copy and
the re-render cannot run without them — but the cause is an unfinished upload
from 2026-09-09, not a loss. Nothing needs recovering *from* anything; the files
need uploading for the first time.

Note the Fast Cut Series file request is **closed**, so that upload path is shut.
Reopen it, or drag straight into the Dropbox app at that path.

### What the check found

Checked directly against the Dropbox API on 2026-09-22:

| Expected | Actual |
| --- | --- |
| `/Portfolio/03 Personal Vlogs/Fast Cut Series/` | **Does not exist.** Not the 8 masters, not the `README.md` holding the recipe. |
| `/Portfolio/03 Personal Vlogs/Singles/` | Contains only `README.md`. All 18 graded clips absent. |

That is **26 files / 8.60 GB** whose only copies are the CloudFront URLs
published on the artifacts page and in the two READMEs. A CDN is a cache, not
storage — those URLs can stop resolving without notice, and they have been the
only copies since 2026-09-09.

All 26 were range-requested on 2026-09-22 and returned HTTP 206 with the byte
sizes recorded in `fast-cut-manifest.tsv`. `x-cache: Miss from cloudfront` on
the samples means they came from origin rather than an edge cache, so the origin
still held them at that point. That is the good case, and it is not permanent.

## Why it blocks work

Every Fast Cut is assembled from the Singles. The re-render scheduled 2026-09-22
— correct the red (`#DE1A22` → `#FE0F13`), apply the Telemetry overlay with the
FD icon, rebuild the captions on MR3/MR4/MR6, all in one pass — **cannot run**
until the sources are back.

## How to recover

Run on a machine where Dropbox syncs:

```bash
# 1. Confirm the CDN copies are still there (downloads nothing)
DRY_RUN=1 ./restore-fast-cut.sh

# 2. Pull them into Dropbox
./restore-fast-cut.sh

# If your Dropbox is not at ~/Dropbox:
DEST="/your/path/Dropbox/Portfolio/03 Personal Vlogs" ./restore-fast-cut.sh
```

Safe to re-run — files already present at the right byte size are skipped, and
partial downloads resume. It exits non-zero and names anything still missing, so
`echo $?` tells you whether you are clear. Do not start the re-render until it
reports 26.

The script only ever writes into `Fast Cut Series/` and `Singles/`. It creates
those two folders and nothing else, and it never deletes.

## Still outstanding after this script runs

Two finished files that this cannot recover, because they were never hosted and
exist only as chat attachments:

- **Lamborghini Aventador S — 6 s preroll** (~2.9 MB) → save to `/Portfolio/01 Business Ads/Lamborghini Aventador S/`
- **Lamborghini Aventador S — detail walk** (~5.3 MB) → same folder

Verified 2026-09-22: that folder holds only the 14 s main cut and three layout
tests. Save both out of the chat by hand.

Also note: `INDEX.md` points at `Fast Cut Series/README.md` for "download links
and the full recipe", but that file **was never created** — the folder never
existed, so nothing was lost with it. Earlier notes in this repo described it as
"gone with the folder"; that was wrong and is corrected here. The recipe itself
survives in the render-job note at
`/Portfolio/03 Personal Vlogs/00 RENDER JOB - Fast Cut re-render (2026-09-22).md`
and in section 10 ("What works") of the artifacts page. Write it into the folder
when the folder is created.

## Files here

- `fast-cut-manifest.tsv` — status, folder, filename, exact byte size, source URL
  for all 26. Tab-separated, one file per line.
- `restore-fast-cut.sh` — the recovery script described above.

## The rule this cost us

**Nothing counts as delivered until it is in Dropbox.** Chat attachments and CDN
links are not storage. This is exactly how 28 finished files ended up with no
durable copy.

The sharper version, given what actually happened here: **a folder with a README
and an open file request is not a delivery — it is an intention.** Three folders
were set up on 2026-09-09 with upload links and contents lists, and two of them
never received a byte. Anything that checks whether work is filed has to count
files, not folders.
