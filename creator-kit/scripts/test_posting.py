#!/usr/bin/env python3
"""Check post_queue.py and ig_graph.py end to end against a fake Instagram Graph API on localhost.

usage: python3 creator-kit/scripts/test_posting.py      (no network, no token; nothing reaches Instagram)
"""
import http.server, json, os, re, subprocess, sys, tempfile, threading

HERE = os.path.dirname(os.path.abspath(__file__))
fails = total = 0


def check(label, ok, extra=""):
    global fails, total
    total += 1
    fails += not ok
    print(("PASS" if ok else "FAIL"), label, "" if ok else extra)


tmp = tempfile.mkdtemp(prefix="posting-")
QUEUE = os.path.join(tmp, "queue")
CFG = os.path.join(tmp, "instagram.json")
TOKEN = "EAAG-test-token-123"
json.dump({"accounts": {"fd": {"ig_user_id": "1784", "token": TOKEN}}}, open(CFG, "w"))
ENV = dict(os.environ, POST_QUEUE=QUEUE, IG_CONFIG=CFG)
ENV.pop("IG_USER_ID", None), ENV.pop("IG_ACCESS_TOKEN", None)


def pq(*args):
    r = subprocess.run([sys.executable, os.path.join(HERE, "post_queue.py"), *args], env=ENV, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def posts():
    out = {}
    for d in os.listdir(QUEUE) if os.path.isdir(QUEUE) else []:
        p = json.load(open(os.path.join(QUEUE, d, "post.json")))
        out[p["id"]] = p
    return out


def save(p):
    json.dump(p, open(os.path.join(QUEUE, p["id"], "post.json"), "w"), indent=1)


def add(*args):
    """queue a post; returns (rc, output, post) with the post read back by the id add printed"""
    rc, out = pq("add", *args)
    m = re.search(r"queued (\S+)", out)
    return rc, out, posts()[m.group(1)] if m else None


# media: a 3 s test video and two photos
VID, PH1, PH2 = (os.path.join(tmp, n) for n in ("reel.mp4", "01.jpg", "02.jpg"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=360x640:rate=30:duration=3",
                "-pix_fmt", "yuv420p", VID], check=True)
from PIL import Image  # noqa: E402
Image.new("RGB", (1080, 1350), (200, 20, 20)).save(PH1)
Image.new("RGB", (1080, 1350), (20, 20, 200)).save(PH2)


# the fake Graph API: records every request, answers like Instagram does
class Fake(http.server.BaseHTTPRequestHandler):
    log, n = [], 0

    def log_message(self, *a):
        pass

    def answer(self, body):
        b = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        Fake.log.append({"m": "GET", "path": self.path, "auth": self.headers.get("Authorization")})
        if "status_code" in self.path:
            self.answer({"status_code": "FINISHED"})
        else:
            self.answer({"permalink": "https://www.instagram.com/reel/FAKE/"})

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        rec = {"m": "POST", "path": self.path, "auth": self.headers.get("Authorization"),
               "offset": self.headers.get("offset"), "file_size": self.headers.get("file_size"), "len": len(body)}
        if self.path.startswith("/up/"):
            Fake.log.append(rec)
            return self.answer({"success": True})
        from urllib.parse import parse_qs
        rec["form"] = {k: v[0] for k, v in parse_qs(body.decode()).items()}
        Fake.log.append(rec)
        Fake.n += 1
        if self.path.endswith("/media_publish"):
            return self.answer({"id": f"media{Fake.n}"})
        self.answer({"id": f"c{Fake.n}"})


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_port}/g"
LIVE = ["publish", "--live", "--graph-base", BASE, "--upload-base", f"http://127.0.0.1:{srv.server_port}/up", "--poll", "0"]

# 1. add a reel, then the digest
rc, out, reel = add("--brand", "fd", "--kind", "reel", "--media", VID, "--cover-time", "1.5",
                    "--caption", "Forged wheels day. #fd", "--title", "Wheels")
check("add reel queues it pending", rc == 0 and reel["status"] == "pending", out)
check("reel cover frame stored in ms", reel["thumb_offset_ms"] == 1500, reel.get("thumb_offset_ms"))
check("digest is 64 hex", len(reel["digest"]) == 64)

# 2. bad adds
rc, out = pq("add", "--brand", "xx", "--kind", "reel", "--media", VID, "--caption", "x")
check("unknown brand refused", rc != 0 and "--brand is one of" in out, out)
rc, out = pq("add", "--brand", "fd", "--kind", "reel", "--media", PH1, "--caption", "x")
check("photo as reel refused", rc != 0 and "one video" in out, out)
rc, out = pq("add", "--brand", "fd", "--kind", "image", "--media", PH1)
check("no caption refused", rc != 0 and "needs a caption" in out, out)

# 3. nothing approved: publish posts nothing
rc, out = pq(*LIVE)
check("pending post does not publish", "nothing approved" in out and not Fake.log, out)

# 4. page: builds the mockup with the posts and previews
page = os.path.join(tmp, "approve")
rc, out = pq("page", "--out", page)
html = open(os.path.join(page, "index.html")).read() if rc == 0 else ""
check("page builds", rc == 0, out)
check("page carries the post and its digest", reel["id"] in html and reel["digest"] in html)
check("page title filled", "<title>Posts to approve</title>" in html and "PAGE_TITLE" not in html)
check("FD tokens on the page", "#FE0F13" in html and "Bebas+Neue" in html)
check("reel cover preview written", os.path.exists(os.path.join(page, reel["id"], "01.jpg")))

# 5. two brands never share a page
rc, out, se = add("--brand", "se", "--kind", "image", "--media", PH2, "--url", "https://cdn.example/02.jpg",
                  "--caption", "SE drop")
rc, out = pq("page", "--out", page)
check("mixed brands refused", rc != 0 and "two brands never share a page" in out, out)
rc, out = pq("page", "--out", os.path.join(tmp, "approve-se"), "--brand", "se")
check("--brand picks one brand", rc == 0 and se["id"] in open(os.path.join(tmp, "approve-se", "index.html")).read(), out)


def decide(pid, decision, dig, note=""):
    f = os.path.join(tmp, "approvals.json")
    json.dump({"decisions": [{"id": pid, "decision": decision, "digest": dig, "note": note, "at": "2026-10-27T12:00"}]},
              open(f, "w"))
    return pq("approvals", f)


# 6. an approval for different content is ignored
rc, out = decide(reel["id"], "approve", "0" * 64)
check("stale approval sends it back to pending", posts()[reel["id"]]["status"] == "pending" and "different content" in out, out)

# 7. a real approval, then a dry run
reel = posts()[reel["id"]]
rc, out = decide(reel["id"], "approve", reel["digest"])
check("approval imported", posts()[reel["id"]]["status"] == "approved", out)
rc, out = pq("publish")
check("dry run says would post, calls nothing", "would post " + reel["id"] in out and not Fake.log, out)

# 8. caption edited after the yes: refused, back to pending
p = posts()[reel["id"]]
p["caption"] += " edited"
save(p)
rc, out = pq(*LIVE)
check("edited caption refused", rc == 1 and "REFUSED" in out and posts()[reel["id"]]["status"] == "pending", out)
check("refused post made no API call", not Fake.log, Fake.log)

# 9. re-approve the edit, then post for real against the fake
pq("page", "--out", page, "--brand", "fd")  # a fresh page shows the edited post's new digest
p = posts()[reel["id"]]
decide(p["id"], "approve", p["digest"])
rc, out = pq(*LIVE, "--id", p["id"])
p = posts()[p["id"]]
check("live run posts the reel", rc == 0 and p["status"] == "posted" and p["permalink"].endswith("/FAKE/"), out)
steps = [(r["m"], r["path"].split("?")[0].replace(BASE.split("/g")[0], "")) for r in Fake.log]
check("request order: container, upload, status, publish, permalink",
      [s[0] for s in steps] == ["POST", "POST", "GET", "POST", "GET"] and steps[1][1].startswith("/up/")
      and steps[3][1].endswith("/media_publish"), steps)
c = Fake.log[0]["form"]
check("reel container fields", c.get("media_type") == "REELS" and c.get("upload_type") == "resumable"
      and c.get("thumb_offset") == "1500" and c.get("share_to_feed") == "true" and c.get("caption", "").endswith("edited"), c)
up = Fake.log[1]
check("resumable upload headers", up["offset"] == "0" and up["file_size"] == str(os.path.getsize(VID))
      and up["len"] == os.path.getsize(VID), up)
check("token only in the Authorization header", all(r["auth"] == f"OAuth {TOKEN}" and TOKEN not in r["path"]
                                                    and TOKEN not in json.dumps(r.get("form", {})) for r in Fake.log))

# 10. a posted post never posts again
n = len(Fake.log)
rc, out = decide(p["id"], "approve", p["digest"])
rc, out2 = pq(*LIVE)
check("posted post stays posted", posts()[p["id"]]["status"] == "posted" and "already posted" in out
      and not any(x["path"].endswith("/media_publish") for x in Fake.log[n:]), out)

# 11. rejected and future posts are skipped
se = posts()[se["id"]]
decide(se["id"], "reject", se["digest"], "wrong car")
rc, out = pq(*LIVE)
check("rejected post skipped", posts()[se["id"]]["status"] == "rejected" and len(Fake.log) == n, out)
_, _, later = add("--brand", "fd", "--kind", "image", "--media", PH1, "--url", "https://cdn.example/01.jpg",
                  "--caption", "Later post", "--at", "2099-01-01 18:00")
decide(later["id"], "approve", later["digest"])
rc, out = pq(*LIVE)
check("future post held until its time", "later   " + later["id"] in out and posts()[later["id"]]["status"] == "approved", out)

# 12. carousel: photo without a URL fails cleanly, then retry; photo with URL and video post fine
_, _, car = add("--brand", "fd", "--kind", "carousel", "--media", PH1, VID, "--caption", "Carousel")
decide(car["id"], "approve", car["digest"])
rc, out = pq(*LIVE, "--id", car["id"])
check("carousel photo without URL fails, not posted", rc == 1 and posts()[car["id"]]["status"] == "failed"
      and "public URL" in out, out)
rc, out = pq("retry", car["id"])
check("retry sends a failed post back to approved", posts()[car["id"]]["status"] == "approved", out)
_, _, car2 = add("--brand", "fd", "--kind", "carousel", "--media", PH1, VID, "--url", "https://cdn.example/01.jpg", "-",
   "--caption", "Carousel 2")
decide(car2["id"], "approve", car2["digest"])
n = len(Fake.log)
rc, out = pq(*LIVE, "--id", car2["id"])
forms = [r.get("form", {}) for r in Fake.log[n:] if "form" in r]
check("carousel posts", rc == 0 and posts()[car2["id"]]["status"] == "posted", out)
check("carousel children then parent", forms[0].get("is_carousel_item") == "true" and forms[0].get("image_url")
      and forms[1].get("media_type") == "VIDEO" and forms[2].get("media_type") == "CAROUSEL"
      and len(forms[2].get("children", "").split(",")) == 2, forms)

# 13. caption problems hold a post
_, _, held = add("--brand", "fd", "--kind", "image", "--media", PH2, "--url", "https://cdn.example/02.jpg",
   "--caption", "Spec is [CHECK: hp figure] today")
decide(held["id"], "approve", held["digest"])
rc, out = pq(*LIVE, "--id", held["id"])
check("unsourced [CHECK] holds the post", rc == 1 and "HELD" in out and posts()[held["id"]]["status"] == "approved", out)

# 14. no credentials: fails, never posts
os.remove(CFG)
_, _, nc = add("--brand", "fd", "--kind", "reel", "--media", VID, "--caption", "No creds")
decide(nc["id"], "approve", nc["digest"])
rc, out = pq(*LIVE, "--id", nc["id"])
check("missing credentials fail cleanly", rc == 1 and posts()[nc["id"]]["status"] == "failed" and "credentials" in out, out)

# 15. the page in a browser: no script errors, no sideways scroll on a phone (Node Playwright, if installed)
JS = """
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 390, height: 844 } });
  const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.goto('file://' + process.argv[1]); await pg.waitForTimeout(500);
  const r = { errs, sw: await pg.evaluate(() => document.documentElement.scrollWidth),
              approve: await pg.locator('button', { hasText: 'Approve' }).count() };
  console.log(JSON.stringify(r)); await b.close();
})().catch(e => { console.log(JSON.stringify({ fail: String(e) })); });
"""
try:
    r = subprocess.run(["node", "-e", JS, os.path.join(page, "index.html")], capture_output=True, text=True, timeout=60)
    res = json.loads(r.stdout.strip().splitlines()[-1])
except Exception as e:
    res = {"fail": str(e)}
if "fail" in res:
    print("skip browser checks:", res["fail"][:120])
else:
    check("page runs without script errors", not res["errs"], res["errs"])
    check("no sideways scroll at 390 px", res["sw"] <= 390, res["sw"])
    check("approve buttons render", res["approve"] >= 1, res)

srv.shutdown()
print(f"\n{total - fails}/{total} passed")
sys.exit(1 if fails else 0)
