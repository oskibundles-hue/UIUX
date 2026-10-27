#!/usr/bin/env python3
"""Instagram Graph API publishing, stdlib only. post_queue.py is the only caller.

Nothing here decides whether something may post; post_queue.py checks the
approval first and only then calls publish().

Credentials stay on the Mac, never in the repo:
    ~/.config/creator-kit/instagram.json
    {"accounts": {"fd": {"ig_user_id": "1784...", "token": "EAAG..."},
                  "se": {...}, "vlog": {...}},
     "host": "graph.facebook.com"}            # graph.instagram.com for Instagram-login tokens
or, for one account, IG_USER_ID and IG_ACCESS_TOKEN in the environment.

How each kind goes up:
    reel      local video via resumable upload (no public URL needed); cover frame by thumb_offset
              or a public cover_url
    image     needs a public image_url (Instagram fetches it; it can't take an image upload)
    carousel  2-10 children: photos by public URL, videos by resumable upload
Then it waits for every container to say FINISHED and calls media_publish.
"""
import json, os, time, urllib.error, urllib.parse, urllib.request

VERSION = os.environ.get("IG_GRAPH_VERSION", "v23.0")
CONFIG = os.path.expanduser(os.environ.get("IG_CONFIG", "~/.config/creator-kit/instagram.json"))


class GraphError(Exception):
    pass


def credentials(account):
    if os.path.exists(CONFIG):
        cfg = json.load(open(CONFIG))
        acc = cfg.get("accounts", {}).get(account)
        if acc:
            return acc["ig_user_id"], acc["token"], cfg.get("host", "graph.facebook.com")
    if os.environ.get("IG_USER_ID") and os.environ.get("IG_ACCESS_TOKEN"):
        return os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"], os.environ.get("IG_GRAPH_HOST", "graph.facebook.com")
    raise GraphError(f"no Instagram credentials for account '{account}' (set {CONFIG} or IG_USER_ID/IG_ACCESS_TOKEN)")


class Graph:
    def __init__(self, ig_user_id, token, host="graph.facebook.com", base=None, upload_base=None, poll=5, timeout=900):
        self.ig, self.token = ig_user_id, token
        self.base = base or f"https://{host}/{VERSION}"
        self.upload_base = upload_base or f"https://rupload.facebook.com/ig-api-upload/{VERSION}"
        self.poll, self.timeout = poll, timeout

    def _req(self, url, data=None, headers=None, method=None):
        h = {"Authorization": f"OAuth {self.token}"}  # header, so the token never lands in a logged URL
        h.update(headers or {})
        body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
        req = urllib.request.Request(url, data=body, headers=h, method=method or ("POST" if body is not None else "GET"))
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read()).get("error", {})
                msg = f"{err.get('message', '')} (code {err.get('code')}, subcode {err.get('error_subcode')})"
            except Exception:
                msg = str(e)
            raise GraphError(f"{req.get_method()} {url.split('?')[0]} -> HTTP {e.code}: {msg}") from None

    def container(self, **fields):
        fields = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in fields.items() if v is not None}
        r = self._req(f"{self.base}/{self.ig}/media", fields)
        if "id" not in r:
            raise GraphError(f"no container id in {r}")
        return r

    def upload(self, container_id, path):
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            r = self._req(f"{self.upload_base}/{container_id}", f.read(),
                          {"offset": "0", "file_size": str(size), "Content-Type": "application/octet-stream"})
        if not r.get("success", True):
            raise GraphError(f"upload of {os.path.basename(path)} failed: {r}")

    def wait(self, container_id):
        end = time.time() + self.timeout
        while True:
            r = self._req(f"{self.base}/{container_id}?fields=status_code,status")
            code = r.get("status_code")
            if code in ("FINISHED", "PUBLISHED"):
                return
            if code in ("ERROR", "EXPIRED"):
                raise GraphError(f"container {container_id} {code}: {r.get('status', '')}")
            if time.time() > end:
                raise GraphError(f"container {container_id} still {code} after {self.timeout}s")
            time.sleep(self.poll)

    def video_child(self, media, carousel=False, **extra):
        c = self.container(media_type="VIDEO" if carousel else "REELS", is_carousel_item=True if carousel else None,
                           upload_type="resumable", **extra)
        self.upload(c["id"], media["path"])
        return c["id"]

    def publish(self, post):
        """post: the post.json dict from post_queue.py. Returns {"media_id", "permalink"}."""
        kind, media, cap = post["kind"], post["media"], post["caption"]
        if kind == "reel":
            cid = self.video_child(media[0], caption=cap, share_to_feed=post.get("share_to_feed", True),
                                   cover_url=post.get("cover_url"),
                                   thumb_offset=None if post.get("cover_url") else post.get("thumb_offset_ms"))
        elif kind == "image":
            cid = self.container(image_url=need_url(media[0]), caption=cap)["id"]
        elif kind == "carousel":
            kids = []
            for m in media:
                if m.get("video"):
                    kids.append(self.video_child(m, carousel=True))
                else:
                    kids.append(self.container(image_url=need_url(m), is_carousel_item=True)["id"])
            for k in kids:
                self.wait(k)
            cid = self.container(media_type="CAROUSEL", children=",".join(kids), caption=cap)["id"]
        else:
            raise GraphError(f"unknown kind {kind}")
        self.wait(cid)
        mid = self._req(f"{self.base}/{self.ig}/media_publish", {"creation_id": cid}).get("id")
        if not mid:
            raise GraphError(f"media_publish returned no id for container {cid}")
        try:
            link = self._req(f"{self.base}/{mid}?fields=permalink").get("permalink")
        except GraphError:
            link = None  # posted; the link is a nicety
        return {"media_id": mid, "permalink": link}


def need_url(m):
    if not m.get("url"):
        raise GraphError(f"{os.path.basename(m['path'])}: Instagram needs a public URL for photos; add it with --url")
    return m["url"]
