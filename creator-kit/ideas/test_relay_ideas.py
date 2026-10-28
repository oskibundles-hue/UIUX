#!/usr/bin/env python3
"""Check relay_ideas.py on a synthetic fixture with known answers (made-up accounts, links and numbers; no network).

usage: python3 creator-kit/ideas/test_relay_ideas.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "scripts", "relay_ideas.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import relay_ideas as r  # noqa: E402

RELAYS = os.path.join(HERE, "fixtures", "relays_synthetic.json")
FOOTAGE = os.path.join(HERE, "fixtures", "footage_synthetic.md")
rules = json.load(open(os.path.join(HERE, "relay_rules.json")))
comments = json.load(open(RELAYS))
fails = total = 0


def check(label, ok, extra=""):
    global fails, total
    total += 1
    fails += not ok
    print(("PASS" if ok else "FAIL"), label, "" if ok else extra)


# relays and the brief
check("Claude's own replies are not relays", not r.is_relay(comments[5]["body"]))
b = r.weekly_brief(comments)
check("brief: followers and lesson", b["followers"] == 1000 and b["lesson"].startswith("put the payoff car"), b)
check("numbered list splits into one post per link", len(r.split_posts(comments[4]["body"])) == 2)
p = r.parse_post(comments[2]["body"], "", comments[2])
check("likes, comments, followers, gated", (p["likes"], p["comments"], p["followers"], p["gated"]) == (20000, 30000, 50000, True), p)
y = r.parse_post(comments[6]["body"], "", comments[6])
check("YouTube keeps its video id; views and subs read", y["url"].endswith("v=FFF666") and (y["views"], y["subs"]) == (40000, 10000), y)
i = r.parse_post(comments[4]["body"].split("\n\n2.")[1], "", comments[4])
check("Instagram link drops its tracking query", i["url"] == "https://www.instagram.com/reel/EEE555", i["url"])
z = r.parse_post(comments[1]["body"], "", comments[1])
check("Muse's own suggestion is not scored as the post", "ferrari" not in z["text"], z["text"][-80:])
check("statuses: picked handle is marked", r.statuses(comments).get("zoom.maker") == "picked")

# Muse's relay format from 2026-10-28 on: "@account (N followers) — N likes / N comments", or "followers not shown"
def relay_line(line):
    c = {"created_at": "2026-10-29T00:00:00Z", "html_url": "", "body": ""}
    return r.parse_post(f"https://www.instagram.com/reel/NEW111/\n{line}", "", c)
for line, want in (("@grid.cars (193,000 followers) — 4,100 likes / 210 comments", (193000, 4100, 210)),
                   ("@grid.cars (577K followers) — 4,100 likes / 210 comments", (577000, 4100, 210)),
                   ("@grid.cars (1.2M followers) — 4,100 likes / 210 comments", (1200000, 4100, 210)),
                   ("@grid.cars (followers not shown) — 4,100 likes / 210 comments", (None, 4100, 210))):
    q = relay_line(line)
    check(f"relay format: {line.split('(')[1].split(')')[0]}", (q["followers"], q["likes"], q["comments"]) == want
          and q["account"] == "@grid.cars", q)
q = relay_line("@grid.cars (followers not shown) — 4,100 likes / 210 comments")
check("followers not shown scores like no count", r.engagement_points(q) == r.engagement_points({**q, "followers": None}))

# scoring parts
e, _ = r.engagement_points(p)
check("gated comments count a fifth: (20000 + 6000) / 50000 is over 5%, full marks", round(e) == 40, e)
e2, why = r.engagement_points({**p, "followers": None, "gated": False, "kind": "instagram"})
check("no followers: log scale at a discount, said so", 0 < e2 <= 30 and "followers not given" in why, (e2, why))
f, _ = r.fit_points(z, rules)
d = r.parse_post(comments[3]["body"], "", comments[3])
f2, _ = r.fit_points(d, rules)
check("car reel that leads with its payoff beats a desktop tool", f == 35 and f2 < 5, (f, f2))
check("'carousel' is not a car", not any(__import__("re").search(r"\b" + w + r"\b", "a carousel post") for w in rules["cars"]))

# footage
clips = r.parse_footage(open(FOOTAGE).read(), rules)
cars = {c["clip"]: c["car"] for c in clips}
check("colour key names the car", cars["CLIP_0001"] == "Test Motors Alpha GT", cars)
check("blank car stays blank; a guess is no car", cars["CLIP_0003"] == "" and cars["CLIP_0004"] == "", cars)
check("table with no car column takes its heading's car", cars["9 00 00 AM"] == "Test Motors Beta 99", cars)
day = {c["clip"]: c["day"] for c in clips}
check("clip prefix MM-DD sets its day", day.get("CLIP_0009") == "2026-01-04", day)
fmt = next(f for f in rules["formats"] if f["name"] == "Rapid-zoom open")
g, car, cover, picks = r.footage_points(fmt, clips, {})
check("footage: car covering every needed shot gets full marks", (g, car) == (25, "Test Motors Alpha GT"), (g, car, cover))

# whole run, offline
res = r.rank(comments, clips, rules, since="2026-01-01")
names = [i["account"] for i in res["ideas"]]
check("old relay filtered by --since", "@old.post" not in names, names)
check("tool is parked, not an idea", [x["account"] for x in res["parked"]] == ["@desk.tool"], res["parked"])
top = res["ideas"][0]
check("top idea: car-first rapid zoom, hook names the car",
      top["account"] == "@zoom.maker" and top["hook"] == "The Test Motors Alpha GT in 2 seconds", top)
check("top idea carries status, reason and clips", top["status"] == "picked" and "followers not given" in top["reason"]
      and top["footage"], top)
check("ranks are 1..n by score", [i["rank"] for i in res["ideas"]] == list(range(1, len(res["ideas"]) + 1))
      and all(a["score"] >= b["score"] for a, b in zip(res["ideas"], res["ideas"][1:])))

out = tempfile.mkdtemp(prefix="relay-ideas-")
run = subprocess.run([sys.executable, SCRIPT, "--relays", RELAYS, "--footage", FOOTAGE, "--since", "2026-01-01",
                      "--out", out], capture_output=True, text=True, timeout=30)
check("CLI writes md and json", run.returncode == 0 and sorted(os.path.splitext(f)[1] for f in os.listdir(out)) == [".json", ".md"],
      run.stdout + run.stderr)
md = open(next(os.path.join(out, f) for f in os.listdir(out) if f.endswith(".md"))).read()
check("markdown shows the lesson, the hook and parked tools",
      "Lesson: put the payoff car" in md and "The Test Motors Alpha GT in 2 seconds" in md and "## Parked" in md)

# the page: built from the CLI's json with a stub design folder (the real one lives on the default branch)
import relay_ideas_page as pg  # noqa: E402
design = tempfile.mkdtemp(prefix="relay-design-")
for f in ("style.css", "app.js"):
    open(os.path.join(design, f), "w").write("/* stub */")
data = json.load(open(next(os.path.join(out, f) for f in os.listdir(out) if f.endswith(".json"))))
html = pg.build(data, design)
check("page: one waiting row per idea, panels on app.js's tab keys",
      html.count('class="cell dz wi s"') == len(data["ideas"]) and all(f'id="p-{k}"' in html for k in ("todo", "pages", "files", "rules")))
check("page: hook shown, parked tool listed, text escaped", "The Test Motors Alpha GT in 2 seconds" in html and "@desk.tool" in html
      and "<script>alert" not in html)

print(f"{total - fails}/{total} passed")
sys.exit(1 if fails else 0)
