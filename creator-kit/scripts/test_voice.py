#!/usr/bin/env python3
"""Check voice_build.py, voice_check.py and script_write.py on made-up transcripts with known answers.

usage: python3 creator-kit/scripts/test_voice.py      (no network, no API key; the Claude call is faked)
"""
import json, os, subprocess, sys, tempfile, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voice_build as vb  # noqa: E402
import voice_check as vc  # noqa: E402
import script_write as sw  # noqa: E402

fails = total = 0


def check(label, ok, extra=""):
    global fails, total
    total += 1
    fails += not ok
    print(("PASS" if ok else "FAIL"), label, "" if ok else extra)


tmp = tempfile.mkdtemp(prefix="voice-")
LINES = ["Right, so this one's a big job.", "We're fitting the forged wheels today.", "Honestly it's lovely.",
         "You know what I mean?", "Right, so check the fitment first.", "It's all about the fitment, trust me.",
         "We don't rush this bit.", "Torque them by hand.", "Right, so that's the wheels done.",
         "Proper clean finish on this one.", "Does it sit right?", "It's all about the stance."]


def transcript(path, lines, wps=2.5):
    """transcribe.py shape: segments with words timed at wps words a second."""
    t, segs = 0.0, []
    for ln in lines:
        ws = []
        for w in ln.split():
            ws.append({"w": w, "s": t, "e": t + 1 / wps})
            t += 1 / wps
        segs.append({"text": ln, "words": ws})
    json.dump(segs, open(path, "w"))


for n in range(3):
    transcript(os.path.join(tmp, f"a{n:02d}.json"), LINES[n:] + LINES[:n])
open(os.path.join(tmp, "reel.srt"), "w").write(
    "1\n00:00:00,000 --> 00:00:02,000\nRight, so it's all about the fitment.\n\n2\n00:00:02,000 --> 00:00:04,000\nWe don't rush it.\n")
open(os.path.join(tmp, "captions.txt"), "w").write("Right, so the wheels are on.\nIt's all about the stance.\n\nNew week, new build.\n")

# profile
paths = vb.expand([tmp])
check("reads json, srt and txt from a folder", len(paths) == 5, paths)
p = vb.build(paths)
check("pace comes from the timed words (~150 wpm)", 145 <= p["wpm"] <= 155, p["wpm"])
check("finds his repeated phrases", "right so" in p["phrases"] and any("all about the" in g for g in p["phrases"]), p["phrases"])
check("finds how he opens sentences", "right so" in p["openers"], p["openers"])
check("questions are counted", 0.1 < p["question_rate"] < 0.3, p["question_rate"])
check("he contracts", p["contractions_per_100"] >= 2, p["contractions_per_100"])
check("a few hundred words is a thin profile", p["thin"])
check("example lines are his own sentences", p["examples"] and all(e in " ".join(LINES) + " Right, so the wheels are on. New week, new build. Right, so it's all about the fitment. We don't rush it." for e in p["examples"]))
md = vb.style_md(p)
check("STYLE.md names the pace and phrases", f"{p['wpm']} words a minute" in md and "\"right so\"" in md)
check("STYLE.md carries no dashes for the model to copy", "—" not in md)

voice = os.path.join(tmp, "voice")
r = subprocess.run([sys.executable, os.path.join(HERE, "voice_build.py"), tmp, "--out", voice], capture_output=True, text=True)
check("voice_build CLI writes style.json and STYLE.md", r.returncode == 0 and os.path.exists(os.path.join(voice, "style.json"))
      and os.path.exists(os.path.join(voice, "STYLE.md")), r.stdout + r.stderr)

# draft check
prof = vc.load_profile(os.path.join(voice, "style.json"))
good = "Right, so these are going on today. Forged, and they're light. We torque them by hand. It's all about the fitment. Get a quote."
r1 = vc.check(good, prof, 10)
check("a draft in his voice passes", r1["pass"], r1["flags"])
check("his phrases are spotted in a draft", "all about the" in " ".join(r1["his_phrases_used"]), r1["his_phrases_used"])
slop = ("Elevate your ride with our seamless, next-level wheel service — it's not just a wheel, it's a statement. "
        "Whether you're a seasoned enthusiast or new to the scene, we do not compromise on quality and craftsmanship ever.")
r2 = vc.check(slop, prof, 30)
f = " | ".join(r2["flags"])
check("AI words are flagged", all(w in f for w in ("elevate", "seamless", "next-level", "whether you're")), f)
check("\"not X, it's Y\" and the dash are flagged", ("it's not X" in f or "not just X" in f) and "dash" in f, f)
check("stiff \"do not\" is flagged when he contracts", "\"do not\"" in f, f)
check("long hook is flagged", "hook takes" in f, f)
check("read time off target is flagged", "read time" in f, f)
r3 = vc.check("We fitted 21 inch wheels for £2,400. It's the fastest car here.", prof)
check("figures go to the claims list, not the flags", r3["claims_to_source"] and not any("£" in x for x in r3["flags"]), r3)
r4 = subprocess.run([sys.executable, os.path.join(HERE, "voice_check.py"), "-", "--profile", os.path.join(voice, "style.json")],
                    input=slop, capture_output=True, text=True)
check("voice_check CLI exits 1 on flags", r4.returncode == 1 and r4.stdout.startswith("FLAGS"), r4.stdout + r4.stderr)

# brief
ideas = os.path.join(tmp, "ideas.json")
json.dump({"date": "2026-10-27", "ideas": {"fd": [{"title": "Why forged wheels cost more", "url": "https://youtu.be/x",
                                                   "pattern": "why"}], "se": []}}, open(ideas, "w"))
out = os.path.join(tmp, "out")
r = subprocess.run([sys.executable, os.path.join(HERE, "script_write.py"), "--from", ideas, "--brand", "fd", "--voice", voice,
                    "--seconds", "20", "--out", out], capture_output=True, text=True)
b = open(os.path.join(out, "brief.md")).read() if os.path.exists(os.path.join(out, "brief.md")) else ""
check("brief is written from a scraper idea", r.returncode == 0 and "Why forged wheels cost more" in b, r.stdout + r.stderr)
check("brief sets words from his pace (20s at ~150 wpm = ~50)", f"about {round(20 * prof['wpm'] / 60)} spoken words" in b)
check("brief carries his profile, brand CTAs and the facts rule", "right so" in b and "get a quote" in b and "[CHECK" in b)
check("brief has no other brand's CTAs", "book a car" not in b)
r = subprocess.run([sys.executable, os.path.join(HERE, "script_write.py"), "--from", ideas, "--brand", "se", "--out", out],
                   capture_output=True, text=True)
check("asking for a missing idea fails cleanly", r.returncode != 0 and "0 se idea" in r.stderr, r.stderr)

# the Claude call, faked: checks the request shape and the refusal path
sent = {}
DRAFT = {"angle": "the hand torque", "hook": "Right, so why by hand?", "body": "We torque every wheel by hand. It's all about the fitment.",
         "cta": "Get a quote.", "on_screen": ["Torqued by hand"], "shots": ["torque wrench close-up"]}


def fake(stop="end_turn", fallback=False):
    class Msgs:
        def create(self, **kw):
            sent.update(kw)
            blocks = [types.SimpleNamespace(type="fallback")] if fallback else []
            blocks.append(types.SimpleNamespace(type="text", text=json.dumps({"drafts": [DRAFT, dict(DRAFT, hook=slop)]})))
            return types.SimpleNamespace(stop_reason=stop, content=blocks, model="fallback-model")
    mod = types.ModuleType("anthropic")
    mod.Anthropic = lambda: types.SimpleNamespace(beta=types.SimpleNamespace(messages=Msgs()))
    sys.modules["anthropic"] = mod


fake()
drafts = sw.check_drafts(sw.call_claude("brief", "high"), prof, 8)
check("request: model, adaptive thinking, effort, schema", sent["model"] == "claude-opus-5-5" and sent["thinking"] == {"type": "adaptive"}
      and sent["output_config"]["effort"] == "high" and sent["output_config"]["format"]["type"] == "json_schema", sent)
check("request: server-side fallbacks on with their beta", sent["fallbacks"] == "default" and sent["betas"] == ["server-side-fallback-2026-07-01"])
check("request: no prefill, no temperature", len(sent["messages"]) == 1 and "temperature" not in sent)
check("each draft is checked: good passes, slop flagged", drafts[0]["check"]["pass"] and not drafts[1]["check"]["pass"],
      [d["check"]["flags"] for d in drafts])
fake("refusal")
try:
    sw.call_claude("brief", "high")
    refused = False
except SystemExit as e:
    refused = "declined" in str(e)
check("a refusal stops with a plain message", refused)

# --check re-runs the checker after hand edits
rec = os.path.join(tmp, "edit", "drafts.json")
os.makedirs(os.path.dirname(rec))
json.dump({"idea": "x", "brand": "fd", "seconds": 8, "drafts": [dict(DRAFT)]}, open(rec, "w"))
r = subprocess.run([sys.executable, os.path.join(HERE, "script_write.py"), "--check", rec, "--voice", voice], capture_output=True, text=True)
check("--check re-checks edited drafts and rewrites drafts.md", r.returncode == 0 and "PASS draft 1" in r.stdout
      and os.path.exists(os.path.join(tmp, "edit", "drafts.md")), r.stdout + r.stderr)

print(f"{total - fails}/{total} passed")
sys.exit(1 if fails else 0)
