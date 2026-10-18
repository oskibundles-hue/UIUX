#!/usr/bin/env python3
"""Check video_drop_sync.py against a fake Dropbox in memory (no network, no key, under 1 s).

usage: python3 .claude/brain/tests/test_video_drop_sync.py
"""
import hashlib, io, json, os, sys, tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import video_drop_sync as vds  # noqa: E402

TMP = tempfile.mkdtemp(prefix="vds-test-")
FAILS = []


def check(name, ok):
    print(("ok    " if ok else "FAIL  ") + name)
    if not ok:
        FAILS.append(name)


def card(cid, title, parts, state="new", folder="Portfolio / 02 Service Ads / Approved Ads / 01 Sound designed (post these)"):
    return {"id": cid, "title": title, "filename": cid + ".mp4", "folder": folder, "state": state,
            "total": sum(len(p) for p in parts),
            "parts": [{"url": "/_blob/" + hashlib.md5(p).hexdigest(), "size": len(p)} for p in parts]}


A = [os.urandom(5 << 20), os.urandom(1234)]                       # crosses a 4 MiB block, two parts
B = [os.urandom(999)]
C = [os.urandom(10)]
CARDS = [card("ad-a", "Ad A", A), card("ad-b", "Ad B", B), card("ad-old", "Ad old — replaced by v2 above, don't post", C),
         card("ad-done", "Ad done", C, state="saved")]
INDEX = os.path.join(TMP, "index.html")
with open(INDEX, "w") as f:
    f.write("<script>\nconst DROPS = [\n" + "\n".join("    " + json.dumps(c) + "," for c in CARDS) + "\n];\n</script>\n")
PARTS = os.path.join(TMP, "parts")
os.makedirs(PARTS)
for p in A + B + C:
    with open(os.path.join(PARTS, hashlib.md5(p).hexdigest() + ".bin"), "wb") as f:
        f.write(p)


class FakeDropbox:
    def __init__(self):
        self.files, self.sessions = {}, {}

    def post(self, url, data, headers):
        ep = url.split("/2", 1)[-1]
        args = json.loads(headers["Dropbox-API-Arg"]) if "Dropbox-API-Arg" in headers else json.loads(data or b"null")
        if ep == "/files/get_metadata":
            f = self.files.get(args["path"].lower())
            return (200, json.dumps({"id": "id:x", "content_hash": vds.content_hash([f])}).encode()) if f is not None \
                else (409, b'{"error_summary": "path/not_found/"}')
        if ep == "/files/upload_session/start":
            sid = "s%d" % len(self.sessions)
            self.sessions[sid] = bytearray(data)
            return 200, json.dumps({"session_id": sid}).encode()
        if ep == "/files/upload_session/append_v2":
            buf = self.sessions[args["cursor"]["session_id"]]
            if args["cursor"]["offset"] != len(buf):
                return 409, b'{"error_summary": "incorrect_offset/"}'
            buf += data
            return 200, b"null"
        if ep == "/files/upload_session/finish":
            path = args["commit"]["path"].lower()
            if path in self.files:
                return 409, b'{"error_summary": "path/conflict/"}'
            self.files[path] = bytes(self.sessions[args["cursor"]["session_id"]])
            return 200, json.dumps({"id": "id:new", "content_hash": vds.content_hash([self.files[path]])}).encode()
        return 400, b'{"error_summary": "unknown endpoint"}'


def run(*argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = vds.main(list(argv))
    return code, out.getvalue()


# content hash: one SHA-256 per 4 MiB block, however the data is chunked
data = A[0] + A[1]
want = hashlib.sha256(hashlib.sha256(data[:4 << 20]).digest() + hashlib.sha256(data[4 << 20:]).digest()).hexdigest()
check("content_hash matches Dropbox's block rule", vds.content_hash([data]) == want)
check("content_hash doesn't depend on chunking", vds.content_hash([data[:7], data[7:3 << 20], data[3 << 20:]]) == want)

check("folder maps to a Dropbox path",
      vds.dest(CARDS[0]) == "/Portfolio/02 Service Ads/Approved Ads/01 Sound designed (post these)/ad-a.mp4")

code, out = run("plan", INDEX)
check("plan lists the new cards and skips the replaced one",
      "SAVE  ad-a" in out and "SAVE  ad-b" in out and "SKIP  ad-old" in out and "ad-done" not in out)

fake = FakeDropbox()
vds._post, vds._token = fake.post, "test"
code, out = run("push", INDEX, PARTS)
check("push saves both cards, exit 0", code == 0 and out.count("SAVED") == 2)
check("the uploaded files are the parts joined, byte for byte",
      fake.files[vds.dest(CARDS[0]).lower()] == A[0] + A[1] and fake.files[vds.dest(CARDS[1]).lower()] == B[0])
check("the replaced card is not uploaded", vds.dest(CARDS[2]).lower() not in fake.files)

code, out = run("push", INDEX, PARTS)
check("a second push finds them already there, exit 0", code == 0 and out.count("was already there") == 2)

fake.files[vds.dest(CARDS[1]).lower()] = b"someone else's file"
code, out = run("push", INDEX, PARTS, "--only", "ad-b")
check("a different file at the path is a conflict and is left alone, exit 1",
      code == 1 and "CONFLICT" in out and fake.files[vds.dest(CARDS[1]).lower()] == b"someone else's file")

os.remove(os.path.join(PARTS, hashlib.md5(B[0]).hexdigest() + ".bin"))
code, out = run("push", INDEX, PARTS, "--only", "ad-b")
check("a missing part stops that card, exit 1", code == 1 and "MISSING" in out)

code, out = run("mark", INDEX, "ad-a", "ad-b")
cs = {c["id"]: c["state"] for c in vds.cards(open(INDEX).read())}
check("mark sets only those cards to saved", cs == {"ad-a": "saved", "ad-b": "saved", "ad-old": "new", "ad-done": "saved"})

vds._token = None
for k in ("DROPBOX_TOKEN", "DROPBOX_REFRESH_TOKEN", "DROPBOX_APP_KEY"):
    os.environ.pop(k, None)
code, out = run("file", os.path.join(PARTS, hashlib.md5(C[0]).hexdigest() + ".bin"), "Portfolio / Test")
check("no key gives a clear error, exit 1", code == 1 and "no Dropbox key" in out)

print(f"\n{len(FAILS)} failed" if FAILS else "\nall passed")
sys.exit(1 if FAILS else 0)
