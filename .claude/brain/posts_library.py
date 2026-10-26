#!/usr/bin/env python3
"""Add a handed-over post to the NQ Posts Library, the page that keeps each post's video, caption and stills together.

usage: python3 .claude/brain/posts_library.py add VIDEO --brand fd|se|as --id <post-id> --title "<title>"
           [--num 12] [--car "<car>"] [--caption-file FILE --caption-source "<who approved it, when>"]
           [--hook "<line>"] [--note "<line>"] [--post-on "Wed 28 Oct"] [--dropbox-path "<folder/file>"]
           [--drop-card <Video Drop card id>] [--still FILE]... [--ai] [--in-dropbox] [--no-parts | --preview-only]
           [--work DIR]
       python3 .claude/brain/posts_library.py record <post-id> name=<asset id>... [--part <asset id>:<bytes>]... [--work DIR] [--update]
       python3 .claude/brain/posts_library.py dropbox <post-id>         tick In Dropbox once the copy is confirmed
       python3 .claude/brain/posts_library.py read                      the call that reads every post back
       python3 .claude/brain/posts_library.py supersede <post-id> "<why>"   mark an older cut as replaced

Omarie, 2026-10-13: "i cant keep track of all this through dropbox and dropbox aint gonna keep my captions."
Run it at hand-over, right after the Video Drop card step (playbooks/lead.md), so nobody re-types a post.

`add` cuts a poster, a small preview and three frames from VIDEO with ffmpeg, splits the master into 19 MiB
parts and copies any --still files next to them, all in a work folder outside the repo. Give --work your
session's scratchpad folder (and the same --work to `record`): files anywhere else each need their own upload
call and approval (seen 13 Oct, six files refused in one call). It prints one JSON
object per Artifact upload call (url, asset, file_paths: at most 25 files each). Make those calls, then run
`record` with name=<asset id> for every uploaded file (the names are the work folder's file names: poster.jpg,
preview.mp4, frame1.jpg, part-001.mp4, still1.jpg ...). `record` writes the post's document and prints the
ArtifactData call (a `set` with file_path; a new post needs no if_version).

--no-parts skips the split when the master is already on the Video Drop page: copy those parts across on the
server (Artifact publish with asset, from_url and asset_ids) and give `record` the new ids in order with
--part <id>:<bytes>. The copy keeps the bytes off this machine's upload.

--preview-only is for a long vlog (Omarie, 26 Oct: "Preview + Dropbox path"): no parts at all, so the page
shows the poster, preview, frames, caption and Dropbox path, and the full file is posted from Dropbox.

The caption is read from --caption-file byte for byte and never edited here: it has to be the approved one,
and --caption-source says who approved it and when. The file must hold the caption and nothing else: a file
with a Markdown heading or a code fence is refused, because all of it would land in Copy caption.
`record` prints a `set`, which is right for a new post only. For a post already on the page give --update:
it prints an `update` that leaves his Posted tick, the hand-over date and the order alone (add if_version). With no caption file the page shows the hook and
"caption not on record". --ai labels every still "AI still" (a commercial that is all generated footage).
Posted is Omarie's tick on the page; `read` prints the call that reads it back (steps.posted, posted_at).
Post records live in the page's database, never in this repo. No model call; `add` takes a few seconds.
"""
import json, os, shutil, subprocess, sys, time

URL = "https://claude.ai/artifact/Y3shBejn5Lat1TZY7hVWYk"   # the NQ Posts Library
PART = 19 * 1024 * 1024                                       # same part size as the Video Drop page
WORK = os.path.join(os.environ.get("TMPDIR") or "/tmp", "posts-library-handover")   # --work overrides it
BRANDS = ("fd", "se", "as")                                   # two brands never share a post
FLAGS = {"--ai", "--in-dropbox", "--no-parts", "--preview-only", "--update"}    # options that take no value
KNOWN = FLAGS | {"--brand", "--id", "--title", "--num", "--car", "--caption-file", "--caption-source", "--hook", "--note",
                 "--post-on", "--dropbox-path", "--drop-card", "--still", "--part", "--work"}
MANY = {"--still", "--part"}                                  # options that can repeat
FRAMES = (0.15, 0.5, 0.85)                                    # where the three frames are cut, as a share of the length


def tool(name):
    return shutil.which(name) or os.path.expanduser("~/.local/bin/" + name)


def parse(argv):
    pos, opt = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--") and a not in KNOWN:
            sys.exit(f"unknown option {a}")
        if a in FLAGS:
            opt[a] = True
        elif a.startswith("--"):
            if i + 1 >= len(argv):
                sys.exit(f"{a} needs a value")
            i += 1
            if a in MANY:
                opt.setdefault(a, []).append(argv[i])
            else:
                opt[a] = argv[i]
        else:
            pos.append(a)
        i += 1
    return pos, opt


def safe_id(s):
    ok = s and all(c.isalnum() or c in "-_." for c in s) and not s.startswith(".")
    if not ok:
        sys.exit(f"post id {s!r}: use letters, digits, - _ . only")
    return s


def length(video):
    out = subprocess.run([tool("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        sys.exit(f"ffprobe couldn't read {video}: {out.stderr.strip()[:200]}")


def ff(args):
    r = subprocess.run([tool("ffmpeg"), "-v", "error", "-y"] + args, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr.strip()[:300])


def split(video, folder):
    parts, n = [], 0
    with open(video, "rb") as f:
        while True:
            chunk = f.read(PART)
            if not chunk:
                break
            n += 1
            name = f"part-{n:03d}.mp4"
            with open(os.path.join(folder, name), "wb") as o:
                o.write(chunk)
            parts.append({"name": name, "size": len(chunk)})
    return parts


def add(pos, opt):
    if len(pos) != 1:
        sys.exit(__doc__)
    video = pos[0]
    if not os.path.isfile(video):
        sys.exit(f"no such video: {video}")
    brand = opt.get("--brand")
    if brand not in BRANDS:
        sys.exit("--brand must be one of: " + ", ".join(BRANDS))
    pid = safe_id(opt.get("--id", ""))
    if not opt.get("--title"):
        sys.exit("--title is needed")
    if opt.get("--preview-only") and not opt.get("--dropbox-path"):
        sys.exit("--preview-only needs --dropbox-path: it is the only way to the full file")
    caption = ""
    if opt.get("--caption-file"):
        if not opt.get("--caption-source"):
            sys.exit("--caption-source is needed with a caption: say who approved it and when")
        with open(opt["--caption-file"], encoding="utf-8") as f:
            caption = f.read().strip("\n")
        if "```" in caption or any(l.startswith("# ") or l.startswith("## ") for l in caption.split("\n")):
            sys.exit("the caption file has a heading or a code fence: give a file with only the caption text")
    folder = os.path.join(opt.get("--work", WORK), pid)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    dur = length(video)
    name = os.path.basename(video)
    base = name.rsplit(".", 1)[0].replace(" - INSTAGRAM 1080x1920", "")
    ff(["-ss", str(dur * 0.35), "-i", video, "-frames:v", "1", "-vf", "scale=540:-2", "-q:v", "4", os.path.join(folder, "poster.jpg")])
    # the bitrate cap keeps a 3-minute vlog's preview under the 20 MB asset limit
    ff(["-i", video, "-vf", "scale=540:-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "29", "-maxrate", "650k",
        "-bufsize", "1300k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
        os.path.join(folder, "preview.mp4")])
    kind = "ai" if opt.get("--ai") else "video"
    stills = []
    for i, src in enumerate(opt.get("--still", []), 1):
        if not os.path.isfile(src):
            sys.exit(f"no such still: {src}")
        ext = os.path.splitext(src)[1].lower() or ".jpg"
        local = f"still{i}{ext}"
        shutil.copyfile(src, os.path.join(folder, local))
        stills.append({"name": local, "kind": "ai" if opt.get("--ai") else "cover", "filename": os.path.basename(src)})
    for i, at in enumerate(FRAMES, 1):
        local = f"frame{i}.jpg"
        ff(["-ss", str(dur * at), "-i", video, "-frames:v", "1", "-q:v", "2", os.path.join(folder, local)])
        stills.append({"name": local, "kind": kind, "filename": f"{base} - frame {i}.jpg"})
    for s in stills:
        s["size"] = os.path.getsize(os.path.join(folder, s["name"]))
    parts = [] if opt.get("--no-parts") or opt.get("--preview-only") else split(video, folder)
    doc = {
        "brand": brand, "num": opt.get("--num", ""), "title": opt["--title"], "car": opt.get("--car", ""),
        "length": f"{dur:.1f} s", "handed": time.strftime("%Y-%m-%d"), "post_on": opt.get("--post-on", ""),
        "hook": opt.get("--hook", ""), "caption": caption, "caption_source": opt.get("--caption-source", "") if caption else "",
        "note": opt.get("--note", ""), "superseded": False, "order": int(time.time()),
        "dropbox_path": opt.get("--dropbox-path", "").lstrip("/"), "drop_card": opt.get("--drop-card", ""),
        "steps": {"built": True, "checked": True, "dropbox": bool(opt.get("--in-dropbox")), "posted": False}, "posted_at": "",
    }
    manifest = {"id": pid, "doc": doc, "video": {"filename": name, "total": os.path.getsize(video)}, "parts": parts, "stills": stills,
                "preview_only": bool(opt.get("--preview-only"))}
    with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    files = ["poster.jpg", "preview.mp4"] + [s["name"] for s in stills] + [p["name"] for p in parts]
    paths = [os.path.join(folder, n) for n in files]
    for i in range(0, len(paths), 25):
        print(json.dumps({"tool": "Artifact", "url": URL, "asset": True, "file_paths": paths[i:i + 25]}, ensure_ascii=False))
    print(f"{len(files)} files in {folder}. Upload them, then: posts_library.py record {pid} "
          + " ".join(n + "=<asset id>" for n in files)
          + (" --part <asset id>:<bytes> for each part copied from Video Drop" if opt.get("--no-parts") else ""), file=sys.stderr)


def record(pos, opt):
    if not pos:
        sys.exit(__doc__)
    pid = safe_id(pos[0])
    folder = os.path.join(opt.get("--work", WORK), pid)
    try:
        with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as f:
            m = json.load(f)
    except OSError:
        sys.exit(f"no manifest for {pid} in {folder}: run `add` first")
    ids = {}
    for pair in pos[1:]:
        name, sep, aid = pair.partition("=")
        if not sep or len(aid) != 32 or any(c not in "0123456789abcdef" for c in aid):
            sys.exit(f"{pair!r}: write name=<asset id> (32 hex characters)")
        ids[name] = aid
    need = ["poster.jpg", "preview.mp4"] + [s["name"] for s in m["stills"]] + [p["name"] for p in m["parts"]]
    missing = [n for n in need if n not in ids]
    if missing:
        sys.exit("no asset id given for: " + ", ".join(missing))
    parts = [{"id": ids[p["name"]], "size": p["size"]} for p in m["parts"]]
    for spec in opt.get("--part", []):
        aid, _, size = spec.partition(":")
        if not size.isdigit():
            sys.exit(f"--part {spec!r}: write <asset id>:<bytes>")
        parts.append({"id": aid, "size": int(size)})
    if not parts and not m.get("preview_only"):
        sys.exit("no video parts: give --part <asset id>:<bytes> for each part copied from Video Drop")
    total = sum(p["size"] for p in parts) if parts else m["video"]["total"]
    if parts and total != m["video"]["total"]:
        sys.exit(f"the parts add up to {total:,} bytes but the master is {m['video']['total']:,}: check the ids and their order")
    doc = dict(m["doc"])
    doc["poster"], doc["preview"] = ids["poster.jpg"], ids["preview.mp4"]
    doc["video"] = {"filename": m["video"]["filename"], "total": total, "parts": parts}
    doc["stills"] = [{"id": ids[s["name"]], "kind": s["kind"], "filename": s["filename"], "size": s["size"]} for s in m["stills"]]
    path = os.path.join(folder, "doc.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    if opt.get("--update"):
        for k in ("steps", "posted_at", "handed", "order"):
            doc.pop(k, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    call = {"tool": "ArtifactData", "url": URL, "action": "update" if opt.get("--update") else "set", "collection": "posts",
            "doc_id": pid, "file_path": path}
    if opt.get("--update"):
        call["if_version"] = "<the version `read` showed>"
    print(json.dumps(call, ensure_ascii=False))


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    cmd, (pos, opt) = argv[0], parse(argv[1:])
    if cmd == "add":
        add(pos, opt)
    elif cmd == "record":
        record(pos, opt)
    elif cmd == "read":
        print(json.dumps({"tool": "ArtifactData", "url": URL, "action": "list", "collection": "posts"}))
    elif cmd == "dropbox" and len(pos) == 1:
        print(json.dumps({"tool": "ArtifactData", "url": URL, "action": "update", "collection": "posts", "doc_id": safe_id(pos[0]),
                          "data": {"steps": {"dropbox": True}}, "if_version": "<the version `read` showed>"}))
    elif cmd == "supersede" and len(pos) == 2:
        print(json.dumps({"tool": "ArtifactData", "url": URL, "action": "update", "collection": "posts", "doc_id": safe_id(pos[0]),
                          "data": {"superseded": True, "note": pos[1]}, "if_version": "<the version `read` showed>"}, ensure_ascii=False))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
