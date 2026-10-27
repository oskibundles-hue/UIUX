#!/usr/bin/env python3
"""Turn an idea into short-form scripts in Omarie's voice, then check them.

It always writes brief.md: the idea, the brand and its CTAs, the target
length in words at his pace, his voice profile (voice/STYLE.md) and the
rules. Paste that into Claude Code, or add --api to have it call Claude
directly (needs the anthropic package and ANTHROPIC_API_KEY, or `ant auth login`).
With --api it writes drafts.md and drafts.json, each draft run through
voice_check.py. Nothing is posted; Omarie reads, picks and records.

Ideas come from --idea "text", or from an idea_scraper.py run:
--from ideas/out/2026-10-27.json --brand fd --pick 1 (the first FD idea).

usage:
    python3 script_write.py --idea "why we torque wheels by hand" --brand fd --seconds 30
    python3 script_write.py --from ideas/out/2026-10-27.json --brand se --pick 2 --api
    python3 script_write.py --check scripts-out/<slug>/drafts.json      (re-check after editing)
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import voice_check as vc  # noqa: E402

MODEL = "claude-opus-5-5"
BRANDS = {
    "fd": {"name": "Formula Dynamics", "what": "the shop: wheels, exhaust, suspension, tuning, body kits, PPF, ceramic coating, paint correction, detailing",
           "ctas": ["book your build", "get a quote", "find your fitment", "we service what we build"]},
    "se": {"name": "Supercar Experience", "what": "the supercar rental side: pickups, drop-offs, customer handovers, the fleet, experience days",
           "ctas": ["book a car", "check availability", "book the experience"]},
    "vlog": {"name": "Omarie's personal page", "what": "his own day, behind the scenes, no hard sell",
             "ctas": ["follow for part 2", "say what you'd pick in the comments", "none, just end on the moment"]},
}
SCHEMA = {
    "type": "object",
    "properties": {"drafts": {"type": "array", "items": {
        "type": "object",
        "properties": {"angle": {"type": "string"}, "hook": {"type": "string"}, "body": {"type": "string"},
                       "cta": {"type": "string"}, "on_screen": {"type": "array", "items": {"type": "string"}},
                       "shots": {"type": "array", "items": {"type": "string"}}},
        "required": ["angle", "hook", "body", "cta", "on_screen", "shots"], "additionalProperties": False}}},
    "required": ["drafts"], "additionalProperties": False,
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "idea"


def idea_from(path, brand, pick):
    data = json.load(open(path))
    items = data.get("ideas", {}).get(brand) or []
    if not 1 <= pick <= len(items):
        sys.exit(f"{path} has {len(items)} {brand} idea(s); --pick 1..{len(items)}")
    i = items[pick - 1]
    extra = f" (hook pattern: {i['pattern']})" if i.get("pattern") else ""
    return f"{i['title']}{extra}\nSource: {i.get('url', '')}"


def style_text(profile_dir):
    p = os.path.join(profile_dir, "STYLE.md")
    if os.path.exists(p):
        return open(p).read()
    return ("No voice profile yet (run voice_build.py on his transcripts). Until then: short spoken sentences, "
            "contractions, plain words, how a guy in a shop talks to a mate, not an ad.")


def brief(idea, brand, seconds, variants, prof, style):
    b = BRANDS[brand]
    wpm = prof.get("wpm") or 160
    target = round(seconds * wpm / 60)
    sw = prof["sentence_words"]
    return f"""# Script brief: {b['name']}

## The idea
{idea}

## The job
Write {variants} different short-form video scripts that Omarie reads to camera or as voiceover, about {seconds} seconds each.
That is about {target} spoken words at his pace ({wpm} words a minute), hook + body + CTA together. Give each one a different angle.

- **Hook:** the first line, under {max(12, sw['p75'])} words. It has to stop the scroll on its own: a claim, a question he'd really ask, or the moment itself.
- **Body:** what happens, in the order it happens. Concrete: the car, the part, the job. One idea per sentence.
- **CTA:** one of these, said his way: {", ".join(b['ctas'])}.
- **on_screen:** 2-4 short text overlays (3-6 words each) that back up the voiceover, not repeat it.
- **shots:** the shots the script needs, so he knows what to film.

## Brand
{b['name']}: {b['what']}. Keep to this brand only; two brands never share a video.

## Rules (each one has a reason)
- Write it the way he talks, using the profile below: his sentence length, his openers, his phrases where they fit naturally. It goes out under his name, so it has to sound like him.
- Spoken words only: no em dashes, no hashtags, no emoji, no stage directions in the lines. They get read aloud.
- No ad-speak: no "elevate", "unleash", "game-changer", "seamless", "next level", "not just X but Y", "whether you're". People scroll past anything that sounds like an ad.
- Don't invent facts. Any price, spec, time, or "we did X" claim the idea doesn't give you goes in as [CHECK: what to confirm], because every figure is checked against a source before posting.

## His voice
{style}
"""


def call_claude(text, effort):
    """One request with server-side fallbacks on; returns the drafts list."""
    try:
        import anthropic
    except ImportError:
        sys.exit("--api needs the anthropic package: pip install anthropic")
    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": text}],
    )
    if resp.stop_reason == "refusal":
        sys.exit("Claude declined this one (after fallbacks). Reword the idea or write it from brief.md in Claude Code.")
    if resp.stop_reason == "max_tokens":
        sys.exit("ran out of tokens before the drafts were finished; try fewer --variants")
    if any(b.type == "fallback" for b in resp.content):
        print(f"note: served by fallback model {resp.model}")
    return json.loads(next(b.text for b in resp.content if b.type == "text"))["drafts"]


def spoken(d):
    return "\n".join(x.strip() for x in (d["hook"], d["body"], d["cta"]) if x.strip())


def check_drafts(drafts, prof, seconds):
    for d in drafts:
        d["check"] = vc.check(spoken(d), prof, seconds)
    return drafts


def drafts_md(drafts, idea, brand, seconds):
    out = [f"# Drafts: {BRANDS[brand]['name']}, ~{seconds:g}s", "", idea, ""]
    for n, d in enumerate(drafts, 1):
        out += [f"## {n}. {d['angle']}", "", f"**Hook:** {d['hook']}", "", d["body"], "", f"**CTA:** {d['cta']}", "",
                "On screen: " + " / ".join(d["on_screen"]), "", "Shots: " + "; ".join(d["shots"]), "",
                "```", vc.report(d["check"]), "```", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--idea", help="the idea in a sentence")
    src.add_argument("--from", dest="from_", metavar="IDEAS_JSON", help="an idea_scraper.py output file")
    src.add_argument("--check", metavar="DRAFTS_JSON", help="re-check an edited drafts.json and rewrite drafts.md")
    ap.add_argument("--brand", choices=sorted(BRANDS), default="fd")
    ap.add_argument("--pick", type=int, default=1, help="which idea from --from (1 = first for the brand)")
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--variants", type=int, default=3)
    ap.add_argument("--voice", default=os.path.join(KIT, "voice"), help="folder with style.json and STYLE.md")
    ap.add_argument("--api", action="store_true", help="call Claude to write the drafts")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--out", help="output folder (default scripts-out/<slug>)")
    a = ap.parse_args()
    prof = vc.load_profile(os.path.join(a.voice, "style.json"))

    if a.check:
        rec = json.load(open(a.check))
        check_drafts(rec["drafts"], prof, rec["seconds"])
        json.dump(rec, open(a.check, "w"), indent=1)
        open(os.path.join(os.path.dirname(a.check), "drafts.md"), "w").write(
            drafts_md(rec["drafts"], rec["idea"], rec["brand"], rec["seconds"]))
        for n, d in enumerate(rec["drafts"], 1):
            print(vc.report(d["check"], f"draft {n}"))
        sys.exit(0 if all(d["check"]["pass"] for d in rec["drafts"]) else 1)

    idea = a.idea or idea_from(a.from_, a.brand, a.pick)
    out = a.out or os.path.join(KIT, "scripts-out", slug(idea.splitlines()[0]))
    os.makedirs(out, exist_ok=True)
    text = brief(idea, a.brand, a.seconds, a.variants, prof, style_text(a.voice))
    open(os.path.join(out, "brief.md"), "w").write(text)
    print(f"brief -> {out}/brief.md")
    if prof.get("thin", True):
        print("note: voice profile is thin or missing; drafts will sound generic until voice_build.py has his transcripts")
    if not a.api:
        return
    print(f"writing {a.variants} drafts with {MODEL} (effort {a.effort}, server-side fallbacks on)…")
    drafts = check_drafts(call_claude(text, a.effort), prof, a.seconds)
    rec = {"idea": idea, "brand": a.brand, "seconds": a.seconds, "drafts": drafts}
    json.dump(rec, open(os.path.join(out, "drafts.json"), "w"), indent=1)
    open(os.path.join(out, "drafts.md"), "w").write(drafts_md(drafts, idea, a.brand, a.seconds))
    for n, d in enumerate(drafts, 1):
        print(vc.report(d["check"], f"draft {n}: {d['angle']}"))
    print(f"drafts -> {out}/drafts.md")


if __name__ == "__main__":
    main()
