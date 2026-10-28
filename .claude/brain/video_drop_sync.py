#!/usr/bin/env python3
"""Save Video Drop cards straight into Omarie's Dropbox, each into the folder written on its card.

Omarie, 18 Oct 2026: "save all videos in video drop automatically and organize where it should go in dropbox".
The Dropbox connector can't upload a video, so this talks to the Dropbox API with a key kept in the cloud
environment's settings (never in chat or in this repo):
    DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY (+ DROPBOX_APP_SECRET)   lasts; preferred
    DROPBOX_TOKEN                                                     a plain access token (expires in 4 hours)

usage:
  python3 .claude/brain/video_drop_sync.py plan INDEX_HTML [--include-replaced]
      Lists the cards still "new" and where each goes, and prints the part ids to fetch (BLOBS line).
  python3 .claude/brain/video_drop_sync.py push INDEX_HTML PARTS_DIR [--only ID,ID] [--include-replaced] [--dry-run]
      Joins each card's parts from PARTS_DIR (files named by part id, with or without an extension), checks
      the sizes against the card, uploads to "<card folder>/<card filename>" and checks Dropbox's content
      hash against the local one. Prints a SAVED line per card that landed.
  python3 .claude/brain/video_drop_sync.py file LOCAL_FILE "Portfolio / 02 Service Ads / ..." [--name NAME]
      Uploads a local master straight to that folder (at hand-over, when the master is on this machine).
  python3 .claude/brain/video_drop_sync.py mark INDEX_HTML ID [ID ...]
      Sets those cards' state to "saved" in INDEX_HTML, ready to republish the page.

Uploads never overwrite: a file already at the path with the same content counts as saved, a different one
is reported as a conflict and left alone. Cards whose title says they were replaced ("don't post",
"replaced by") are skipped unless --include-replaced, so an old cut never lands in a "post these" folder.
A file sent this way carries no C2PA box (that comes only from claude.ai's save path), so it matches its
master byte for byte. Exit 0 when everything asked for landed, 1 otherwise, 2 on bad input. No model call.
"""
import glob, hashlib, json, os, re, ssl, sys, urllib.error, urllib.parse, urllib.request

API, CONTENT = "https://api.dropboxapi.com/2", "https://content.dropboxapi.com/2"
CHUNK = 8 << 20                                              # upload chunk; Dropbox takes up to 150 MiB
REPLACED = re.compile(r"don'?t post|replaced by", re.I)
CARD = re.compile(r'^\s*(\{"id":.*\}),?\s*$')


def cards(html):
    """The DROPS cards in the page source, one JSON object per line."""
    out = []
    for line in html.split("\n"):
        m = CARD.match(line)
        if m:
            out.append(json.loads(m.group(1)))
    return out


def dest(card):
    """Dropbox path for a card: its folder ("A / B / C") and filename."""
    return dropbox_folder(card["folder"]) + "/" + card["filename"]


def dropbox_folder(folder):
    return "/" + "/".join(p.strip() for p in folder.split(" / ") if p.strip())


def todo(all_cards, include_replaced=False):
    """(to save, skipped as replaced) among the cards still "new"."""
    new = [c for c in all_cards if c.get("state") == "new" and c.get("parts") and c.get("folder")]
    skipped = [c for c in new if not include_replaced and REPLACED.search(c.get("title", ""))]
    return [c for c in new if c not in skipped], skipped


def content_hash(chunks):
    """Dropbox's content_hash: SHA-256 of the concatenated SHA-256s of each 4 MiB block."""
    outer, block, fill = hashlib.sha256(), hashlib.sha256(), 0
    for data in chunks:
        while data:
            take = data[:(4 << 20) - fill]
            block.update(take)
            fill += len(take)
            data = data[len(take):]
            if fill == 4 << 20:
                outer.update(block.digest())
                block, fill = hashlib.sha256(), 0
    if fill:
        outer.update(block.digest())
    return outer.hexdigest()


def part_files(card, parts_dir):
    """Local file for each of the card's parts, in order. Raises ValueError on a missing or wrong-size part."""
    files = []
    for p in card["parts"]:
        pid = p["url"].rstrip("/").rsplit("/", 1)[-1]
        hits = [f for f in glob.glob(os.path.join(parts_dir, "**", pid + "*"), recursive=True) if os.path.isfile(f)]
        if not hits:
            raise ValueError(f"{card['id']}: part {pid} not in {parts_dir}")
        if os.path.getsize(hits[0]) != p["size"]:
            raise ValueError(f"{card['id']}: part {pid} is {os.path.getsize(hits[0])} B, the card says {p['size']}")
        files.append(hits[0])
    if card.get("total") and sum(p["size"] for p in card["parts"]) != card["total"]:
        raise ValueError(f"{card['id']}: parts add up to {sum(p['size'] for p in card['parts'])} B, not {card['total']}")
    return files


def read_chunks(files):
    for f in files:
        with open(f, "rb") as fh:
            while True:
                data = fh.read(CHUNK)
                if not data:
                    break
                yield data


# --- Dropbox API ------------------------------------------------------------------------------------------

def _ctx():
    bundle = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else None)
    return ssl.create_default_context(cafile=bundle)


def _post(url, data, headers):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=_ctx(), timeout=300) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


_token = None


def token():
    global _token
    if _token:
        return _token
    refresh, key = os.environ.get("DROPBOX_REFRESH_TOKEN"), os.environ.get("DROPBOX_APP_KEY")
    if refresh and key:
        form = {"grant_type": "refresh_token", "refresh_token": refresh, "client_id": key}
        if os.environ.get("DROPBOX_APP_SECRET"):
            form["client_secret"] = os.environ["DROPBOX_APP_SECRET"]
        code, body = _post("https://api.dropboxapi.com/oauth2/token", urllib.parse.urlencode(form).encode(),
                           {"Content-Type": "application/x-www-form-urlencoded"})
        if code != 200:
            raise RuntimeError(f"Dropbox refused the refresh token ({code}): {body[:200]!r}")
        _token = json.loads(body)["access_token"]
    elif os.environ.get("DROPBOX_TOKEN"):
        _token = os.environ["DROPBOX_TOKEN"]
    else:
        raise RuntimeError("no Dropbox key: set DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY (or DROPBOX_TOKEN) "
                           "in the cloud environment's settings, then start a new session")
    return _token


def api(endpoint, args=None, data=None):
    """Call one Dropbox endpoint. RPC calls send args as the body, content calls in the header. -> (status, dict)"""
    auth = {"Authorization": "Bearer " + token()}
    if data is None:
        code, body = _post(API + endpoint, json.dumps(args).encode() if args is not None else b"null",
                           {**auth, "Content-Type": "application/json"})
    else:
        code, body = _post(CONTENT + endpoint, data,
                           {**auth, "Content-Type": "application/octet-stream",
                            "Dropbox-API-Arg": json.dumps(args or {}, ensure_ascii=True)})
    try:
        return code, json.loads(body) if body else {}
    except ValueError:
        return code, {"error_summary": body[:200].decode("utf-8", "replace")}


def existing(path):
    code, meta = api("/files/get_metadata", {"path": path})
    return meta if code == 200 else None


def upload(files, path, local_hash):
    """Upload the joined files to path without overwriting. -> (status word, detail)."""
    there = existing(path)
    if there:
        if there.get("content_hash") == local_hash:
            return "already", there.get("id", "")
        return "conflict", f"a different file is already at {path}"
    code, res = api("/files/upload_session/start", {"close": False}, b"")
    if code != 200:
        return "failed", f"start {code} {res.get('error_summary')}"
    sid, offset = res["session_id"], 0
    for data in read_chunks(files):
        code, res = api("/files/upload_session/append_v2", {"cursor": {"session_id": sid, "offset": offset}}, data)
        if code != 200:
            return "failed", f"append at {offset} {code} {res.get('error_summary')}"
        offset += len(data)
    commit = {"path": path, "mode": "add", "autorename": False, "mute": True}
    code, res = api("/files/upload_session/finish", {"cursor": {"session_id": sid, "offset": offset}, "commit": commit}, b"")
    if code != 200:
        return "failed", f"finish {code} {res.get('error_summary')}"
    if res.get("content_hash") != local_hash:
        return "failed", f"landed but its content hash {res.get('content_hash')} isn't the local {local_hash}"
    return "saved", res.get("id", "")


# --- commands ---------------------------------------------------------------------------------------------

def cmd_plan(index, include_replaced):
    go, skipped = todo(cards(open(index, encoding="utf-8").read()), include_replaced)
    for c in go:
        print(f"SAVE  {c['id']}  {c.get('total', 0):,} B  ->  {dest(c)}")
    for c in skipped:
        print(f"SKIP  {c['id']}  (marked replaced: {c['title'][:80]})")
    print("BLOBS " + " ".join(p["url"].rsplit("/", 1)[-1] for c in go for p in c["parts"]))
    return 0


def cmd_push(index, parts_dir, only, include_replaced, dry):
    go, skipped = todo(cards(open(index, encoding="utf-8").read()), include_replaced)
    if only:
        go = [c for c in go + skipped if c["id"] in only]
    ok = True
    for c in go:
        try:
            files = part_files(c, parts_dir)
        except ValueError as e:
            print(f"MISSING  {e}")
            ok = False
            continue
        h = content_hash(read_chunks(files))
        if dry:
            print(f"WOULD  {c['id']}  ->  {dest(c)}  (content_hash {h[:12]}…)")
            continue
        status, detail = upload(files, dest(c), h)
        word = {"saved": "SAVED", "already": "SAVED"}.get(status, status.upper())
        print(f"{word}  {c['id']}  {dest(c)}  {detail}{'  (was already there)' if status == 'already' else ''}")
        ok &= status in ("saved", "already")
    for c in skipped:
        if not only:
            print(f"SKIP  {c['id']}  (marked replaced)")
    return 0 if ok else 1


def cmd_file(local, folder, name):
    path = dropbox_folder(folder) + "/" + (name or os.path.basename(local))
    h = content_hash(read_chunks([local]))
    status, detail = upload([local], path, h)
    print(f"{status.upper()}  {path}  {detail}")
    return 0 if status in ("saved", "already") else 1


def cmd_mark(index, ids):
    lines, done = open(index, encoding="utf-8").read().split("\n"), set()
    for i, line in enumerate(lines):
        m = CARD.match(line)
        if m and json.loads(m.group(1))["id"] in ids:
            # Cards come both spaced ("state": "new") and compact ("state":"new").
            line, n = re.subn(r'("state":\s*)"new"', r'\1"saved"', line)
            if n == 1:
                lines[i] = line
            done.add(json.loads(m.group(1))["id"])
    open(index, "w", encoding="utf-8").write("\n".join(lines))
    for i in ids:
        print(("MARKED  " if i in done else "NOT FOUND  ") + i)
    return 0 if done == set(ids) else 1


def main(argv):
    flags = {a for a in argv if a.startswith("--") and a not in ("--only", "--name")}
    def opt(name):
        return argv[argv.index(name) + 1] if name in argv else None
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--only", "--name"))]
    try:
        if pos[:1] == ["plan"] and len(pos) == 2:
            return cmd_plan(pos[1], "--include-replaced" in flags)
        if pos[:1] == ["push"] and len(pos) == 3:
            only = set(opt("--only").split(",")) if opt("--only") else None
            return cmd_push(pos[1], pos[2], only, "--include-replaced" in flags, "--dry-run" in flags)
        if pos[:1] == ["file"] and len(pos) == 3:
            return cmd_file(pos[1], pos[2], opt("--name"))
        if pos[:1] == ["mark"] and len(pos) >= 3:
            return cmd_mark(pos[1], pos[2:])
    except RuntimeError as e:
        print(f"ERROR  {e}")
        return 1
    except (OSError, ValueError) as e:
        print(f"ERROR  {e}")
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
