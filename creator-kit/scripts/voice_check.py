#!/usr/bin/env python3
"""Check a script draft against Omarie's voice profile before he reads it out.

Flags what would make it sound like someone else wrote it:
  - AI tells: words and shapes no one says out loud ("delve", "game-changer",
    "it's not just X, it's Y", "in today's world", em dashes)
  - sentences much longer than his, a hook that takes too long to land
  - stiff uncontracted forms ("do not", "it is") when he contracts
  - read time off the target length at his own pace
Figures (prices, specs, times, "we did X") are listed as claims to source,
not failed: they go through nq-facts before anything is posted.

usage:
    python3 voice_check.py draft.txt --seconds 30
    echo "script text" | python3 voice_check.py - --json
exit 1 when anything is flagged.
"""
import argparse, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from voice_build import CONTRACTION, sentences, words  # noqa: E402

PROFILE = os.path.join(os.path.dirname(HERE), "voice", "style.json")
DEFAULT = {"sentence_words": {"median": 9, "p25": 5, "p75": 13, "p90": 18}, "wpm": None,
           "contractions_per_100": 3.0, "phrases": [], "thin": True}

TELL_WORDS = ["delve", "elevate", "elevated", "unleash", "unlock", "game-changer", "game changer", "seamless",
              "seamlessly", "tapestry", "testament", "realm", "embark", "journey", "meticulous", "meticulously",
              "curated", "bespoke experience", "next level", "next-level", "cutting-edge", "cutting edge",
              "transformative", "revolutionize", "revolutionise", "synergy", "leverage", "robust", "pivotal",
              "furthermore", "moreover", "indeed", "boasts", "nestled", "vibrant", "crafted", "captivating",
              "breathtaking", "unparalleled", "elevating", "redefine", "redefining", "look no further",
              "whether you're", "in today's", "dive in", "let's dive", "buckle up", "picture this",
              "imagine a world", "say goodbye to", "say hello to", "ever wondered", "the secret sauce"]
TELL_SHAPES = [
    (r"\bnot (?:just|only|merely) [^.?!]{1,40}?,? (?:but|it's|it is)\b", "\"not just X, but Y\""),
    (r"\bit'?s not (?:about )?[^.?!]{1,30}[.,;] it'?s\b", "\"it's not X, it's Y\""),
    (r"—|–", "em/en dash (no one says a dash)"),
    (r"#\w+", "hashtag inside the spoken script"),
]
STIFF = {"do not": "don't", "does not": "doesn't", "did not": "didn't", "is not": "isn't", "are not": "aren't",
         "it is": "it's", "that is": "that's", "we are": "we're", "you are": "you're", "i am": "I'm",
         "cannot": "can't", "will not": "won't", "we have": "we've", "let us": "let's", "there is": "there's"}
CLAIM = re.compile(r"[£$€]\s?\d[\d,.]*k?|\b\d[\d,.]*\s?(?:hp|bhp|ps|nm|mph|km/h|kmh|%|k|grand|seconds|secs|s\b|mins?|"
                   r"hours?|days?|years?|miles|inch|in\b|mm|kg|lbs?)|\b(?:fastest|cheapest|only|first|best|number one|#1)\b"
                   r"[^.?!]{0,40}", re.I)


def load_profile(path=PROFILE):
    return json.load(open(path)) if path and os.path.exists(path) else dict(DEFAULT)


def check(text, prof, seconds=None):
    flags, low = [], text.lower()
    sents = sentences(text) or [text.strip()]
    lens = [len(words(s)) for s in sents]
    ws = words(text)
    sw = prof["sentence_words"]

    for w in TELL_WORDS:
        if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", low):
            flags.append(f"AI tell: \"{w}\"")
    for pat, name in TELL_SHAPES:
        for m in re.finditer(pat, text, re.I):
            flags.append(f"AI tell: {name} — \"{m.group(0).strip()}\"")
            break

    long_cap = max(sw["p90"] + 4, 16)
    for s, n in zip(sents, lens):
        if n > long_cap:
            flags.append(f"long sentence ({n} words, he tops out near {sw['p90']}): \"{s[:60]}…\"")
    if lens and statistics.median(lens) > sw["p75"] * 1.3:
        flags.append(f"sentences run long: median {statistics.median(lens):g} words, his is {sw['median']:g}")
    hook_cap = max(12, sw["p75"])
    if lens and lens[0] > hook_cap:
        flags.append(f"hook takes {lens[0]} words to land; keep the first line under {hook_cap}")

    if prof.get("contractions_per_100", 0) >= 2:
        for stiff, easy in STIFF.items():
            if re.search(r"\b" + stiff + r"\b", low):
                flags.append(f"stiff: \"{stiff}\" — he'd say \"{easy}\"")

    wpm = prof.get("wpm") or 160
    read_s = round(60 * len(ws) / wpm, 1)
    if seconds and not (0.8 * seconds <= read_s <= 1.15 * seconds):
        flags.append(f"read time {read_s}s at {wpm} wpm, target {seconds}s ({round(seconds * wpm / 60)} words)")

    used = [g for g in prof.get("phrases", []) if g in " ".join(ws)]
    claims = sorted({m.group(0).strip() for m in CLAIM.finditer(text)})
    return {"pass": not flags, "flags": flags, "words": len(ws), "read_seconds": read_s, "wpm": wpm,
            "his_phrases_used": used, "claims_to_source": claims, "thin_profile": prof.get("thin", True)}


def report(r, label=""):
    head = ("PASS" if r["pass"] else "FLAGS") + (f" {label}" if label else "")
    lines = [f"{head}  {r['words']} words, ~{r['read_seconds']}s at {r['wpm']} wpm"]
    lines += [f"  - {f}" for f in r["flags"]]
    if r["his_phrases_used"]:
        lines.append("  his phrases in it: " + ", ".join(r["his_phrases_used"]))
    if r["claims_to_source"]:
        lines.append("  claims to source before posting (nq-facts): " + "; ".join(r["claims_to_source"]))
    if r["thin_profile"]:
        lines.append("  note: voice profile is thin or missing; build it with voice_build.py")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", help="text file, or - for stdin")
    ap.add_argument("--seconds", type=float, help="target length in seconds")
    ap.add_argument("--profile", default=PROFILE)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    text = sys.stdin.read() if a.draft == "-" else open(a.draft).read()
    r = check(text, load_profile(a.profile), a.seconds)
    print(json.dumps(r, indent=1) if a.json else report(r))
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
