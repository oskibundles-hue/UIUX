#!/usr/bin/env python3
"""The posting queue: nothing goes to Instagram until Omarie approves that exact post.

    add        queue a Reel, photo or carousel with its caption, cover and time
    page       build the approval page (the post mockup look) from what's waiting
    approvals  read the decisions saved from that page
    publish    post what's approved and due; a dry run unless --live
    list       what's in the queue and where each post stands

The gate: every post has a digest, a SHA-256 over its account, kind, caption,
every media file's bytes, its cover and its options. An approval names the
digest it was given for. publish recomputes it from the files on disk and
refuses when they differ, so an edited caption or a re-exported video needs a
fresh yes. A posted post never posts again.

usage:
    python3 post_queue.py add --brand fd --kind reel --media reel.mp4 --cover covers/reel/cover-02-text.jpg \\
        --caption-file caption.txt --at "2026-10-28 18:00"
    python3 post_queue.py add --brand fd --kind carousel --media 01.jpg 02.jpg 03.mp4 \\
        --url https://.../01.jpg https://.../02.jpg - --caption "..."
    python3 post_queue.py page --out approve/          # then publish approve/index.html as an Artifact
    python3 post_queue.py approvals ~/Downloads/approvals.json
    python3 post_queue.py publish                       # shows what would post
    python3 post_queue.py publish --live                # posts it
"""
import argparse, datetime as dt, glob, hashlib, json, os, re, secrets, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
QUEUE = os.environ.get("POST_QUEUE", os.path.join(KIT, "posting", "queue"))
TEMPLATE = os.path.join(KIT, "posting", "approve-template.html")
BRANDS = {"fd": {"name": "Formula Dynamics", "accent": "#FE0F13", "ground": "#0A0A0B",
                 "display": "'Bebas Neue','Oswald','Arial Narrow',Impact,sans-serif", "font": "Bebas+Neue"},
          "se": {"name": "Supercar Experience", "accent": "#FF4F16", "ground": "#0F1014",
                 "display": "'Space Grotesk','Helvetica Neue',Arial,sans-serif", "font": "Space+Grotesk:wght@500;700"},
          "vlog": {"name": "Personal", "accent": "#FBD101", "ground": "#0A0A0B",
                   "display": "'Bebas Neue','Oswald','Arial Narrow',Impact,sans-serif", "font": "Bebas+Neue"}}
VIDEO = (".mp4", ".mov", ".m4v")
CAPTION_MAX, HASHTAG_MAX = 2200, 30


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def digest(post):
    """What the approval binds to, recomputed from the files on disk."""
    body = {"account": post["account"], "kind": post["kind"], "caption": post["caption"],
            "media": [[sha(m["path"]), m.get("url")] for m in post["media"]],
            "cover": sha(post["cover"]) if post.get("cover") else None, "cover_url": post.get("cover_url"),
            "thumb_offset_ms": post.get("thumb_offset_ms"), "share_to_feed": post.get("share_to_feed", True)}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def path_of(pid):
    return os.path.join(QUEUE, pid, "post.json")


def load(pid):
    return json.load(open(path_of(pid)))


def save(post):
    os.makedirs(os.path.dirname(path_of(post["id"])), exist_ok=True)
    json.dump(post, open(path_of(post["id"]), "w"), indent=1)


def all_posts():
    return sorted((json.load(open(p)) for p in glob.glob(os.path.join(QUEUE, "*", "post.json"))), key=lambda p: p["created"])


def caption_problems(cap):
    out = []
    if len(cap) > CAPTION_MAX:
        out.append(f"caption is {len(cap)} characters; Instagram stops at {CAPTION_MAX}")
    if len(re.findall(r"#\w+", cap)) > HASHTAG_MAX:
        out.append(f"more than {HASHTAG_MAX} hashtags; Instagram rejects the post")
    if "[CHECK" in cap:
        out.append("caption still has a [CHECK: ...] to source")
    return out


def cover_time(cover):
    """thumbnail.py covers carry their frame time in covers.json next to them."""
    m = re.search(r"cover-(\d+)-", os.path.basename(cover))
    cj = os.path.join(os.path.dirname(cover), "covers.json")
    if m and os.path.exists(cj):
        for c in json.load(open(cj)).get("covers", []):
            if c.get("n") == int(m.group(1)):
                return c.get("time")
    return None


def cmd_add(a):
    if a.brand not in BRANDS:
        sys.exit(f"--brand is one of {', '.join(BRANDS)}")
    media = [os.path.abspath(m) for m in a.media]
    for m in media + ([os.path.abspath(a.cover)] if a.cover else []):
        if not os.path.isfile(m):
            sys.exit(f"no such file: {m}")
    urls = (a.url or []) + ["-"] * (len(media) - len(a.url or []))
    if len(urls) != len(media):
        sys.exit("--url takes one entry per --media file, - for none")
    items = [{"path": m, "video": m.lower().endswith(VIDEO), "url": None if u == "-" else u} for m, u in zip(media, urls)]
    n = len(items)
    if a.kind == "reel" and not (n == 1 and items[0]["video"]):
        sys.exit("a reel is one video file")
    if a.kind == "image" and not (n == 1 and not items[0]["video"]):
        sys.exit("an image post is one photo")
    if a.kind == "carousel" and not 2 <= n <= 10:
        sys.exit("a carousel has 2-10 items")
    cap = open(a.caption_file).read().strip() if a.caption_file else (a.caption or "").strip()
    if not cap:
        sys.exit("a post needs a caption (--caption or --caption-file)")
    when = dt.datetime.fromisoformat(a.at).isoformat(timespec="minutes") if a.at else None
    t = a.cover_time if a.cover_time is not None else (cover_time(a.cover) if a.cover else None)
    post = {"id": dt.datetime.now().strftime("%Y%m%d") + "-" + a.brand + "-" + secrets.token_hex(3),
            "brand": a.brand, "account": a.account or a.brand, "handle": a.handle or "", "kind": a.kind,
            "title": a.title or os.path.splitext(os.path.basename(media[0]))[0], "media": items, "caption": cap,
            "cover": os.path.abspath(a.cover) if a.cover else None, "cover_url": a.cover_url,
            "thumb_offset_ms": int(round(t * 1000)) if t is not None and a.kind == "reel" else None,
            "share_to_feed": not a.reel_only, "post_at": when, "notes": a.note or [],
            "created": dt.datetime.now().isoformat(timespec="seconds"), "status": "pending", "history": []}
    post["digest"] = digest(post)
    save(post)
    print(f"queued {post['id']}  {a.kind}, {n} file(s), digest {post['digest'][:12]}")
    for p in caption_problems(cap):
        print("  warning:", p)
    missing = [os.path.basename(i["path"]) for i in items if not i["video"] and not i["url"]]
    if missing:
        print("  warning: photos need a public URL before they can post:", ", ".join(missing))


def preview(src, dst, at=None):
    """A light JPEG for the page: the photo itself, or a frame of the video."""
    from PIL import Image
    if src.lower().endswith(VIDEO):
        tmp = dst + ".png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at or 0), "-i", src, "-frames:v", "1", tmp], check=True)
        src = tmp
    im = Image.open(src).convert("RGB")
    im.thumbnail((1080, 1920))
    im.save(dst, quality=85)
    if src.endswith(".png") and src.startswith(dst):
        os.remove(src)


def page_data(posts, out):
    data = []
    for p in posts:
        d = os.path.join(out, p["id"])
        os.makedirs(d, exist_ok=True)
        items = []
        if p["kind"] == "reel":
            if p.get("cover"):
                preview(p["cover"], os.path.join(d, "01.jpg"))
            else:
                preview(p["media"][0]["path"], os.path.join(d, "01.jpg"), (p.get("thumb_offset_ms") or 0) / 1000)
            items.append({"f": "01.jpg", "label": "Reel cover", "name": os.path.basename(p["media"][0]["path"]), "v": True})
        else:
            for i, m in enumerate(p["media"], 1):
                preview(m["path"], os.path.join(d, f"{i:02d}.jpg"))
                items.append({"f": f"{i:02d}.jpg", "label": f"{'Video' if m['video'] else 'Photo'} {i}",
                              "name": os.path.basename(m["path"]), "v": m["video"]})
        problems = caption_problems(p["caption"]) + [f"{os.path.basename(m['path'])} has no public URL" for m in p["media"]
                                                    if not m["video"] and not m["url"]]
        data.append({"id": p["id"], "label": p["title"], "brand": p["brand"], "account": p["account"], "handle": p["handle"] or p["account"],
                     "kind": p["kind"], "aspect": "9/16" if p["kind"] == "reel" else "4/5", "caption": p["caption"],
                     "items": items, "digest": p["digest"], "post_at": p["post_at"], "status": p["status"],
                     "notes": p.get("notes", []), "problems": problems})
    return data


def cmd_page(a):
    posts = [p for p in all_posts() if p["status"] in ("pending", "changes")
             and (not a.id or p["id"] in a.id) and (not a.brand or p["brand"] == a.brand)]
    if not posts:
        sys.exit("nothing waiting for approval")
    brands = {p["brand"] for p in posts}
    if len(brands) > 1:
        sys.exit(f"posts from {', '.join(sorted(brands))} are waiting; two brands never share a page, use --brand")
    for p in posts:  # the page shows the digest of the files as they are now
        p["digest"] = digest(p)
        save(p)
    os.makedirs(a.out, exist_ok=True)
    b = BRANDS[posts[0]["brand"]]
    html = open(TEMPLATE).read()
    html = (html.replace("/*BRAND_TOKENS*/", f"--ground:{b['ground']};--accent:{b['accent']};--display:{b['display']};")
                .replace("FONT_FAMILY", b["font"])
                .replace("/*POSTS*/[]", json.dumps(page_data(posts, a.out), indent=1).replace("</", "<\\/"))
                .replace("PAGE_TITLE", "Posts to approve"))
    open(os.path.join(a.out, "index.html"), "w").write(html)
    print(f"{len(posts)} post(s) -> {a.out}/index.html (publish with capabilities db, user, downloads)")


def cmd_approvals(a):
    rec = json.load(open(a.file))
    decisions = rec.get("decisions", rec if isinstance(rec, list) else [])
    for d in decisions:
        if not os.path.exists(path_of(d.get("id", ""))):
            print(f"skip {d.get('id')}: not in this queue")
            continue
        p = load(d["id"])
        if p["status"] == "posted":
            print(f"skip {p['id']}: already posted")
            continue
        if d.get("decision") not in ("approve", "changes", "reject"):
            print(f"skip {p['id']}: unknown decision {d.get('decision')!r}")
            continue
        now = digest(p)
        stale = d.get("digest") != now
        p["history"].append({"decision": d["decision"], "digest": d.get("digest"), "note": d.get("note", ""),
                             "at": d.get("at"), "by": d.get("by"), "read": dt.datetime.now().isoformat(timespec="seconds")})
        if stale:
            p["status"], p["approval"] = "pending", None
            print(f"{p['id']}: that {d['decision']} was for different content (digest {str(d.get('digest'))[:12]}, files now {now[:12]}); needs a fresh look")
        else:
            p["status"] = {"approve": "approved", "changes": "changes", "reject": "rejected"}[d["decision"]]
            p["approval"] = p["history"][-1] if d["decision"] == "approve" else None
            print(f"{p['id']}: {p['status']}" + (f"  note: {d['note']}" if d.get("note") else ""))
        save(p)


def due(p, now):
    return not p.get("post_at") or dt.datetime.fromisoformat(p["post_at"]) <= now


def cmd_publish(a):
    import ig_graph
    now = dt.datetime.now()
    todo = [p for p in all_posts() if p["status"] == "approved" and (not a.id or p["id"] in a.id)]
    if not todo:
        print("nothing approved to post")
        return
    bad = 0
    for p in todo:
        cur = digest(p)
        appr = p.get("approval") or {}
        if appr.get("digest") != cur:
            p["status"], p["approval"] = "pending", None
            save(p)
            print(f"REFUSED {p['id']}: files or caption changed since the yes (approved {str(appr.get('digest'))[:12]}, now {cur[:12]}); back to pending")
            bad += 1
            continue
        if not due(p, now):
            print(f"later   {p['id']}: due {p['post_at']}")
            continue
        probs = caption_problems(p["caption"])
        if probs:
            print(f"HELD    {p['id']}: " + "; ".join(probs))
            bad += 1
            continue
        if not a.live:
            print(f"would post {p['id']}  {p['kind']} to '{p['account']}', {len(p['media'])} file(s), digest {cur[:12]}")
            continue
        try:
            g = ig_graph.Graph(*ig_graph.credentials(p["account"]), base=a.graph_base, upload_base=a.upload_base, poll=a.poll)
            p["status"] = "posting"  # a crash mid-call leaves it here, never back in approved
            save(p)
            r = g.publish(p)
            p.update(status="posted", posted_at=dt.datetime.now().isoformat(timespec="seconds"), **r)
            print(f"POSTED  {p['id']}  {r.get('permalink') or r['media_id']}")
        except ig_graph.GraphError as e:
            p.update(status="failed", error=str(e))
            print(f"FAILED  {p['id']}: {e}")
            bad += 1
        save(p)
    if not a.live:
        print("dry run: add --live to post")
    sys.exit(1 if bad else 0)


def cmd_list(a):
    for p in all_posts():
        flag = "" if p["status"] in ("posted", "posting", "failed") or digest(p) == p["digest"] else "  (files changed since queued)"
        print(f"{p['id']}  {p['status']:<9} {p['kind']:<8} {p['account']:<5} {p['post_at'] or 'when approved':<17} {p['title']}{flag}")


def cmd_retry(a):
    p = load(a.id)
    if p["status"] not in ("failed", "posting"):
        sys.exit(f"{a.id} is {p['status']}; only failed or stuck posts go back")
    p["status"] = "approved"
    save(p)
    print(f"{a.id} back to approved. Check Instagram first: a post stuck in 'posting' may already be up.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add")
    s.add_argument("--brand", required=True)
    s.add_argument("--kind", required=True, choices=["reel", "image", "carousel"])
    s.add_argument("--media", nargs="+", required=True)
    s.add_argument("--url", nargs="+", help="public URL per media file in the same order, - for none")
    s.add_argument("--caption")
    s.add_argument("--caption-file")
    s.add_argument("--cover", help="cover image (a thumbnail.py cover reads its frame time itself)")
    s.add_argument("--cover-time", type=float, help="reel cover frame, seconds into the video")
    s.add_argument("--cover-url", help="public URL of a custom reel cover image")
    s.add_argument("--reel-only", action="store_true", help="don't also show the reel on the grid")
    s.add_argument("--at", help="post no earlier than this local time, e.g. '2026-10-28 18:00'")
    s.add_argument("--account", help="credentials key (default: the brand)")
    s.add_argument("--handle", help="handle shown on the approval page")
    s.add_argument("--title")
    s.add_argument("--note", action="append", help="a line for the page's notes (repeatable)")
    s = sub.add_parser("page")
    s.add_argument("--out", default=os.path.join(KIT, "posting", "approve"))
    s.add_argument("--id", nargs="+")
    s.add_argument("--brand", help="only this brand's posts")
    s = sub.add_parser("approvals")
    s.add_argument("file")
    s = sub.add_parser("publish")
    s.add_argument("--live", action="store_true")
    s.add_argument("--id", nargs="+")
    s.add_argument("--graph-base", help=argparse.SUPPRESS)
    s.add_argument("--upload-base", help=argparse.SUPPRESS)
    s.add_argument("--poll", type=float, default=5, help=argparse.SUPPRESS)
    sub.add_parser("list")
    s = sub.add_parser("retry")
    s.add_argument("id")
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    {"add": cmd_add, "page": cmd_page, "approvals": cmd_approvals, "publish": cmd_publish, "list": cmd_list,
     "retry": cmd_retry}[a.cmd](a)


if __name__ == "__main__":
    main()
