#!/usr/bin/env python3
"""Publish ONE Instagram Reel through Meta's official Instagram Graph API.

Built for a single post ("The floor goes down"). Safe by default:
  - dry run unless --publish is passed;
  - refuses if the token belongs to a different account than post.json names;
  - refuses if a post containing `duplicate_marker` is already on the account
    (checked before creating the upload and again right before publishing);
  - refuses if this machine already posted it (state file);
  - never retries the publish call itself, so it cannot double-post.

The access token is read from the IG_ACCESS_TOKEN environment variable only.
The video link comes from --video-url or IG_VIDEO_URL, never from this public
repo, so the unposted video can't be downloaded from GitHub.
Standard library only (Python 3.8+).

Exit codes: 0 posted (or dry run passed), 1 refused by a safety check,
2 setup problem (token/config), 3 Instagram API or upload failure.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REELS_MAX_BYTES = 300 * 1000 * 1000  # Meta's Reels limit: 300 MB
HERE = os.path.dirname(os.path.abspath(__file__))


class Refused(Exception):
    """A safety check stopped the run. Nothing was published."""


class SetupError(Exception):
    pass


class ApiError(Exception):
    pass


def log(msg=""):
    print(msg, flush=True)


class Graph:
    def __init__(self, base, version, token, timeout=60):
        self.base = base.rstrip("/")
        self.version = version
        self.token = token
        self.timeout = timeout

    def _redact(self, text):
        return text.replace(self.token, "***") if self.token else text

    def _url(self, path):
        return f"{self.base}/{self.version}/{path.lstrip('/')}"

    def _send(self, req, what):
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            try:
                err = json.loads(body).get("error", {})
                detail = (f"{err.get('message')} (code {err.get('code')}, "
                          f"subcode {err.get('error_subcode')}, trace {err.get('fbtrace_id')})")
            except ValueError:
                detail = body[:300]
            raise ApiError(self._redact(f"{what} failed: HTTP {e.code}: {detail}")) from None
        except urllib.error.URLError as e:
            raise ApiError(self._redact(f"{what} failed: {e.reason}")) from None
        return json.loads(body) if body else {}

    def get(self, path, **params):
        params["access_token"] = self.token
        req = urllib.request.Request(self._url(path) + "?" + urllib.parse.urlencode(params))
        return self._send(req, f"GET {path}")

    def post(self, path, **params):
        params["access_token"] = self.token
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(self._url(path), data=data, method="POST")
        return self._send(req, f"POST {path}")

    def upload(self, uri, file_path):
        """Resumable upload of a local file to the container's rupload URI."""
        size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            req = urllib.request.Request(uri, data=f, method="POST", headers={
                "Authorization": f"OAuth {self.token}",
                "offset": "0",
                "file_size": str(size),
                "Content-Length": str(size),
                "Content-Type": "application/octet-stream",
            })
            saved, self.timeout = self.timeout, max(self.timeout, 1800)
            try:
                return self._send(req, "video upload")
            finally:
                self.timeout = saved


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("title", "account_username", "caption", "duplicate_marker"):
        if not str(cfg.get(key) or "").strip():
            raise SetupError(f"{os.path.basename(path)}: '{key}' is empty. Fill it in first.")
    cfg["account_username"] = cfg["account_username"].strip().lstrip("@").lower()
    if len(cfg["caption"]) > 2200:
        raise SetupError("caption is longer than Instagram's 2,200-character limit")
    if cfg["caption"].count("#") > 30:
        raise SetupError("caption has more than 30 hashtags")
    return cfg


def state_path(state_dir, title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return os.path.join(state_dir, f"posted-{slug}.json")


def resolve_account(api, cfg):
    """Return (ig_user_id, username) for the account the token publishes to."""
    if cfg.get("ig_user_id"):  # Facebook-Login token: /me is the Facebook user, not Instagram
        info = api.get(str(cfg["ig_user_id"]), fields="username")
        return str(cfg["ig_user_id"]), info.get("username", "")
    info = api.get("me", fields="user_id,username,account_type")
    return str(info.get("user_id") or info["id"]), info.get("username", "")


def find_existing(api, ig_id, marker):
    """Return the recent post whose caption contains the marker, if any."""
    res = api.get(f"{ig_id}/media", fields="id,caption,timestamp,permalink,media_product_type", limit=25)
    for m in res.get("data", []):
        if marker.lower() in (m.get("caption") or "").lower():
            return m
    return None


def check_quota(api, ig_id):
    try:
        res = api.get(f"{ig_id}/content_publishing_limit", fields="quota_usage,config")
    except ApiError as e:  # informational only
        log(f"  (could not read publishing quota: {e})")
        return
    row = (res.get("data") or [{}])[0]
    used, total = row.get("quota_usage"), (row.get("config") or {}).get("quota_total")
    log(f"  publishing quota: {used} of {total} used in the last 24 h")
    if used is not None and total is not None and used >= total:
        raise Refused("the account has used its 24-hour publishing quota")


def check_video_url(url, expected_size):
    req = urllib.request.Request(url, headers={"Range": "bytes=0-15"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            ctype = resp.headers.get("Content-Type", "")
            crange = resp.headers.get("Content-Range", "")
            resp.read()
    except urllib.error.URLError as e:
        raise SetupError(f"the video link is not reachable: {e}") from None
    total = int(crange.rsplit("/", 1)[1]) if "/" in crange else None
    log(f"  video link: {ctype}, {total if total is not None else '?'} bytes")
    if not ctype.startswith("video/"):
        raise SetupError(f"the video link serves '{ctype}', not a video. Use a direct link (Dropbox: raw=1).")
    if total is not None and total > REELS_MAX_BYTES:
        raise SetupError(f"video is {total} bytes; Reels allow at most {REELS_MAX_BYTES}")
    if expected_size and total is not None and total != expected_size:
        raise SetupError(f"the video link serves {total} bytes but post.json expects {expected_size}: wrong file?")


def wait_for_container(api, container_id, poll_seconds, timeout_minutes):
    deadline = time.time() + timeout_minutes * 60
    while True:
        res = api.get(container_id, fields="status_code,status")
        code = res.get("status_code")
        log(f"  processing: {code}")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise ApiError(f"Instagram could not process the video: {code}: {res.get('status')}")
        if time.time() >= deadline:
            raise ApiError(f"video still processing after {timeout_minutes} min; not publishing. "
                           f"Container {container_id} expires unpublished in 24 h.")
        time.sleep(poll_seconds)


def run(args):
    cfg = load_config(args.config)
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        raise SetupError("IG_ACCESS_TOKEN is not set. Add it to the environment's variables.")
    api = Graph(args.graph_base or cfg.get("graph_host", "https://graph.instagram.com"),
                cfg.get("api_version", "v23.0"), token)
    state_file = state_path(args.state_dir, cfg["title"])

    log(f"Reel: {cfg['title']}")
    log("Checks:")
    if os.path.exists(state_file):
        with open(state_file, encoding="utf-8") as f:
            done = json.load(f)
        raise Refused(f"already posted from here on {done.get('timestamp')}: {done.get('permalink')}")

    ig_id, username = resolve_account(api, cfg)
    log(f"  token account: @{username} (id {ig_id})")
    if username.lower() != cfg["account_username"]:
        raise Refused(f"token is for @{username}, but post.json says @{cfg['account_username']}")

    existing = find_existing(api, ig_id, cfg["duplicate_marker"])
    if existing:
        raise Refused(f"@{username} already has this post ({existing.get('timestamp')}): {existing.get('permalink')}")
    log(f"  not on @{username} yet (checked the latest 25 posts)")
    check_quota(api, ig_id)

    if args.video_file:
        size = os.path.getsize(args.video_file)
        log(f"  video file: {args.video_file} ({size} bytes)")
        if size > REELS_MAX_BYTES:
            raise SetupError(f"video file is {size} bytes; Reels allow at most {REELS_MAX_BYTES}")
    else:
        video_url = args.video_url or os.environ.get("IG_VIDEO_URL", "").strip()
        if not video_url:
            raise SetupError("no video: pass --video-url, set IG_VIDEO_URL, or use --video-file")
        check_video_url(video_url, cfg.get("expected_size_bytes"))

    params = {"media_type": "REELS", "caption": cfg["caption"],
              "share_to_feed": "true" if cfg.get("share_to_feed", True) else "false"}
    if cfg.get("thumb_offset_ms") is not None:
        params["thumb_offset"] = str(int(cfg["thumb_offset_ms"]))

    log("Caption:")
    log("  " + cfg["caption"].replace("\n", "\n  "))
    if not args.publish:
        log(f"\nDRY RUN passed. Nothing was posted. Re-run with --publish to post to @{username}.")
        return 0

    log(f"\nPublishing to @{username}...")
    if args.video_file:
        created = api.post(f"{ig_id}/media", upload_type="resumable", **params)
        uri = created.get("uri") or f"{args.rupload_base}/ig-api-upload/{api.version}/{created['id']}"
        log("  uploading video...")
        api.upload(uri, args.video_file)
    else:
        created = api.post(f"{ig_id}/media", video_url=video_url, **params)
    container_id = created["id"]
    log(f"  upload container: {container_id}")
    wait_for_container(api, container_id, args.poll_seconds, args.timeout_minutes)

    # Another agent may have posted while the video processed.
    existing = find_existing(api, ig_id, cfg["duplicate_marker"])
    if existing:
        raise Refused(f"it went up elsewhere while this one processed: {existing.get('permalink')}. "
                      f"Not publishing; container {container_id} expires unpublished.")

    try:
        media_id = api.post(f"{ig_id}/media_publish", creation_id=container_id)["id"]
    except ApiError as e:
        raise ApiError(f"{e}\nThe publish call failed. Check @{username} before trying again: "
                       f"it may have gone live anyway. Do not re-run blindly.") from None
    media = api.get(media_id, fields="permalink,timestamp")

    os.makedirs(args.state_dir, exist_ok=True)
    record = {"title": cfg["title"], "account": username, "media_id": media_id,
              "permalink": media.get("permalink"), "timestamp": media.get("timestamp")}
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    log(f"\nPOSTED to @{username}: {media.get('permalink')} ({media.get('timestamp')})")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--config", default=os.path.join(HERE, "post.json"))
    p.add_argument("--publish", action="store_true", help="actually post (default is a dry run)")
    p.add_argument("--video-url", help="direct link to the MP4 (or set IG_VIDEO_URL)")
    p.add_argument("--video-file", help="upload this local file instead of a link")
    p.add_argument("--state-dir", default=os.path.join(HERE, ".state"))
    p.add_argument("--graph-base", help="override the Graph API host (tests)")
    p.add_argument("--rupload-base", default="https://rupload.facebook.com")
    p.add_argument("--poll-seconds", type=float, default=15)
    p.add_argument("--timeout-minutes", type=float, default=20)
    args = p.parse_args(argv)
    try:
        return run(args)
    except Refused as e:
        log(f"\nREFUSED, nothing posted: {e}")
        return 1
    except SetupError as e:
        log(f"\nSETUP PROBLEM, nothing posted: {e}")
        return 2
    except ApiError as e:
        log(f"\nFAILED: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
