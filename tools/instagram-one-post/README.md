# Instagram one-post publisher

Posts **one** Reel ("The floor goes down") to @nq.young through Meta's official Instagram
Graph API. It posts the **corrected** version of the reel, rendered from the 4K master by
`fix/fix_reel.py`, and uploads that file directly. `post.json` refuses the old Dropbox
link, which still has the errors.

## The corrected reel

`fix/fix_reel.py` rebuilds the Instagram file (1080x1920, x264 CRF 18, like the approved
export) from the 4K master with three fixes. Everything else is untouched, and the audio is
copied from the master.

| When | Was | Now |
|---|---|---|
| 1:48–1:51 | Lower third "FORMULA DYNAMICS · TWO-POST LIFTS" | "… · SCISSOR LIFTS" (the lifts on screen are scissor lifts), same typewriter timing |
| 2:18–2:19 | Callout "3500 KG" only | Adds "= 7,716 LB" under it once the count lands, answering "what is that in poundage?" |
| 2:11–2:13 | Caption "3 ,500 KILOGRAMS." | "3,500 KILOGRAMS." |

## What stops it from going wrong

- **Dry run by default.** Nothing posts without `--publish`.
- **Right account only.** It refuses if the token belongs to any account other than
  `account_username` in `post.json` (`nq.young`).
- **Right file only.** `require_video_file` makes it refuse the Dropbox link (the unfixed
  version); only a local file passed with `--video-file` can go up.
- **No double posts.** It refuses if a post containing "The floor goes down" is already on
  the account. It checks before uploading and again right before publishing, in case
  another agent posts it in between. It never retries the publish call.
- **No secrets in this repo.** The token (`IG_ACCESS_TOKEN`) comes from an environment
  variable. This repo is public.

## One-time setup

1. The Instagram account must be a **professional account** (Business or Creator).
   In the Instagram app: Settings → Account type and tools → Switch to professional account.
2. At [developers.facebook.com](https://developers.facebook.com/apps), create an app with the
   Instagram use case (API setup with **Instagram login**). Add the Instagram account and
   generate an access token. It needs `instagram_business_basic` and
   `instagram_business_content_publish`.
3. Store the token as the environment variable `IG_ACCESS_TOKEN`. In Claude Code on the
   web, open the environment's settings and edit its environment variables. Never paste it
   into a chat or commit it.

## Run

```bash
cd tools/instagram-one-post
pip install numpy pillow opencv-python-headless imageio-ffmpeg   # ffmpeg with libx264

# 1. Download the 4K master from Dropbox (about 2.2 GB):
#    NQ Studio/04 Exports/2026-09-12 Reel Cut/01 2026-09-01 the floor goes down (reel cut) v3 FD.mp4
# 2. Render the corrected Instagram file (about 5 minutes on 4 cores):
python3 fix/fix_reel.py master.mp4 fixed.mp4
# 3. Dry run, then post:
python3 post_reel.py --video-file fixed.mp4
python3 post_reel.py --video-file fixed.mp4 --publish
```

| Exit code | Meaning |
|---|---|
| 0 | Posted (or the dry run passed) |
| 1 | A safety check refused. Nothing posted. |
| 2 | Setup problem (token, config, video). Nothing posted. |
| 3 | Instagram error. If it says the **publish** call failed, check the account before trying again. |

Tests (fake Instagram API, no network): `python3 -m unittest -v test_post_reel.py`

After the post is up, delete `IG_ACCESS_TOKEN` from the environment and remove the app's
access in Instagram (Settings → Website permissions → Apps and websites).

`fix/fonts/BebasNeue-Regular.ttf` is Bebas Neue by Dharma Type, under the SIL Open Font
License (`fix/fonts/OFL.txt`).
