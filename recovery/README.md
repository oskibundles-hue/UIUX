# Fast Cut / Singles recovery

**Status as of 2026-09-22: 26 files, 8.60 GB, no copy in Dropbox. All 26 still
reachable on the CDN. Not yet recovered.**

## What happened

A review of the artifacts page ("Download Everything") on 2026-09-22 flagged that
the Anti Stock source files were missing from Dropbox. Checked directly against
the Dropbox API the same day, and confirmed:

| Expected | Actual |
| --- | --- |
| `/Portfolio/03 Personal Vlogs/Fast Cut Series/` | **Does not exist.** Not the 8 masters, not the `README.md` holding the recipe. |
| `/Portfolio/03 Personal Vlogs/Singles/` | Contains only `README.md`. All 18 graded clips absent. |

That is **26 files / 8.60 GB** whose only surviving copies are the CloudFront
URLs published on the artifacts page. A CDN is a cache, not storage — those URLs
can stop resolving without notice.

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

Also note `README.md` for the Fast Cut Series folder held the build recipe and is
gone with the rest. The recipe survives in the render-job note at
`/Portfolio/03 Personal Vlogs/00 RENDER JOB - Fast Cut re-render (2026-09-22).md`
and in section 10 ("What works") of the artifacts page — rewrite it from there
once the folder is back.

## Files here

- `fast-cut-manifest.tsv` — status, folder, filename, exact byte size, source URL
  for all 26. Tab-separated, one file per line.
- `restore-fast-cut.sh` — the recovery script described above.

## The rule this cost us

**Nothing counts as delivered until it is in Dropbox.** Chat attachments and CDN
links are not storage. This is exactly how 28 finished files ended up with no
durable copy.
