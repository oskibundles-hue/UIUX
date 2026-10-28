#!/usr/bin/env python3
"""Check idea_scraper.py with no network: a fake yt-dlp and a saved fetch with known answers.

usage: python3 creator-kit/ideas/test_idea_scraper.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "scripts", "idea_scraper.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import idea_scraper as s  # noqa: E402

fails = 0


def check(label, ok, extra=""):
    global fails
    fails += not ok
    print(("PASS" if ok else "FAIL"), label, "" if ok else extra)


# pure functions
check("pattern swaps money and numbers", s.hook_pattern("I spent $4,000 on 3 wheels") == "I spent $N on N wheels",
      s.hook_pattern("I spent $4,000 on 3 wheels"))
check("topic words match whole words only", s.topic_hits("PPF install on a GT3", ["ppf", "install", "gt"]) == ["install", "ppf"])
items = [{"title": t, "url": u, "views": v, "source": "c", "kind": "youtube"} for t, u, v in
         [("a", "u1", 1000), ("b", "u2", 1200), ("c", "u3", 900), ("Ceramic coating gone wrong", "u4", 5000)]]
sc = {i["url"]: i for i in s.score_source(items, ["ceramic", "coating"])}
check("outlier is views / source median", sc["u4"]["outlier"] == round(5000 / 1100, 2), sc["u4"]["outlier"])
check("topic boost lifts score", sc["u4"]["score"] > sc["u4"]["outlier"])
check("fewer than 3 items is skipped", s.score_source(items[:2], []) == [])

# fake yt-dlp: the real fetch path, no network
tmp = tempfile.mkdtemp(prefix="ideas-")
fake = os.path.join(tmp, "yt-dlp")
open(fake, "w").write("#!/usr/bin/env python3\nimport json\nprint(json.dumps({'channel': 'Test Garage', 'entries': ["
                      "{'id': 'a1', 'title': 'Shop tour', 'view_count': 2000},"
                      "{'id': 'a2', 'title': 'Oil change', 'view_count': 1800},"
                      "{'id': 'a3', 'title': 'Forged wheels fitment fail', 'view_count': 9000},"
                      "{'id': 'a4', 'title': 'Live', 'view_count': None}]}))\n")
os.chmod(fake, 0o755)
got = s.fetch_youtube("https://www.youtube.com/@test", 10, fake)
check("yt-dlp entries parsed, null views dropped", [g["url"] for g in got] == ["https://youtu.be/a1", "https://youtu.be/a2", "https://youtu.be/a3"], got)
check("channel name carried", got[0]["source"] == "Test Garage")

# whole run, offline
wl = os.path.join(tmp, "watch.json")
json.dump({"brands": {"formula-dynamics": {"youtube": ["x"], "subreddits": [], "keywords": ["wheels", "fitment"]}}}, open(wl, "w"))
fx = os.path.join(tmp, "fetch.json")
json.dump({"formula-dynamics": {"x": got}}, open(fx, "w"))
out = os.path.join(tmp, "out")
run = lambda *a: subprocess.run([sys.executable, SCRIPT, "--watchlist", wl, "--offline", fx, "--out", out, *a],
                                capture_output=True, text=True, timeout=30)
r1 = run()
check("first run finds the outlier", r1.returncode == 0 and r1.stdout.startswith("1 ideas"), r1.stdout + r1.stderr)
md = open([os.path.join(out, f) for f in os.listdir(out) if f.endswith(".md")][0]).read()
check("markdown names it with its pattern", "Forged wheels fitment fail" in md and "pattern:" in md)
r2 = run()
check("second run skips what was shown", r2.stdout.startswith("0 ideas"), r2.stdout)
r3 = run("--all")
check("--all shows it again", r3.stdout.startswith("1 ideas"), r3.stdout)

total = 12
print(f"{total - fails}/{total} passed")
sys.exit(1 if fails else 0)
