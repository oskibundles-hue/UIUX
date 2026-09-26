# Instagram one-post publisher

Posts **one** Reel ("The floor goes down") through Meta's official Instagram Graph API.
Instagram downloads the video straight from a Dropbox link, so the full-quality
299 MB file goes up unchanged. There is no 100 MB cap on this path.

## What stops it from going wrong

- **Dry run by default.** Nothing posts without `--publish`.
- **Right account only.** It refuses if the token belongs to any account other than
  `account_username` in `post.json`. That field ships blank, so nothing can post until
  someone fills it in.
- **No double posts.** It refuses if a post containing "The floor goes down" is already on
  the account. It checks before uploading and again right before publishing, in case
  another agent posts it in between. It never retries the publish call.
- **No secrets in this repo.** The token (`IG_ACCESS_TOKEN`) and the video link
  (`IG_VIDEO_URL`) come from environment variables. This repo is public.

## One-time setup

1. The Instagram account must be a **professional account** (Business or Creator).
   In the Instagram app: Settings → Account type and tools → Switch to professional account.
2. At [developers.facebook.com](https://developers.facebook.com/apps), create an app with the
   Instagram use case (API setup with **Instagram login**). Add the Instagram account and
   generate an access token. It needs `instagram_business_basic` and
   `instagram_business_content_publish`.
3. Store the token as the environment variable `IG_ACCESS_TOKEN`. In Claude Code on the
   web, open the environment's settings and edit its environment variables. Never paste it
   into a chat or commit it. Store the video's direct Dropbox link (ending `raw=1`) as
   `IG_VIDEO_URL`.
4. Put the account name in `post.json` → `account_username` (for example `nq.young`).

## Run

```bash
cd tools/instagram-one-post
python3 post_reel.py              # dry run: checks account, duplicates, quota, video link
python3 post_reel.py --publish    # posts it, then prints the link
```

If Instagram can't fetch the link, download the file and upload it directly instead:
`python3 post_reel.py --publish --video-file reel.mp4`.

| Exit code | Meaning |
|---|---|
| 0 | Posted (or the dry run passed) |
| 1 | A safety check refused. Nothing posted. |
| 2 | Setup problem (token, config, video link). Nothing posted. |
| 3 | Instagram error. If it says the **publish** call failed, check the account before trying again. |

Tests (fake Instagram API, no network): `python3 -m unittest -v test_post_reel.py`

After the post is up, delete `IG_ACCESS_TOKEN` from the environment and remove the app's
access in Instagram (Settings → Website permissions → Apps and websites).
