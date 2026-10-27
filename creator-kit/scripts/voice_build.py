#!/usr/bin/env python3
"""Build Omarie's text voice profile from things he has actually said or written.

Feed it his own words: transcribe.py JSON from his talking reels, .srt/.vtt
captions, or .txt files of past captions (one post per blank-line block). It
measures how he talks and writes two files:

    voice/style.json   numbers and lists that voice_check.py and script_write.py read
    voice/STYLE.md     the same profile in plain words, pasted into every script brief

What it measures: sentence length, words per minute (timed sources only),
questions, contractions, filler words, how his sentences open, the 2-4 word
phrases he keeps coming back to, his most used content words, and a bank of
his own short lines to copy the rhythm from.

This is the text profile. voice/omarie_profile.json is something else: the
audio speaker embedding who_speaks.py uses to tell his voice from others.

usage:
    python3 voice_build.py transcripts/*.json captions.txt
    python3 voice_build.py transcripts/ --out voice/      (reads every .json/.srt/.vtt/.txt in it)
"""
import argparse, collections, glob, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)

STOP = set("""a an the and or but so if then than that this these those there here it its it's i i'm me my
we we're us our you you're your he she they them their is are was were be been being am do does did done
have has had of to in on at by for with from up down out over into about as just not no yes very
what which who when where why how all any some more most can could will would should shall may might
must get got go going gonna come like really one two also too even still only own same s t don't
can't won't didn't isn't aren't wasn't that's what's there's let's ok okay oh um uh yeah""".split())

FILLERS = ["like", "literally", "honestly", "basically", "actually", "you know", "i mean", "kind of",
           "sort of", "bro", "man", "yeah", "obviously", "to be fair", "lowkey", "trust me"]

CONTRACTION = re.compile(r"\b\w+'(?:s|re|ve|ll|d|m|t)\b", re.I)
WORD = re.compile(r"[A-Za-z0-9']+")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
TIMECODE = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def words(text):
    return [w.lower().strip("'") for w in WORD.findall(text) if w.strip("'")]


def sentences(text):
    return [s.strip() for s in SENT_SPLIT.split(text) if len(words(s)) >= 2]


def read_source(path):
    """Return (blocks of text, spoken seconds or 0) for one file."""
    ext = os.path.splitext(path)[1].lower()
    raw = open(path, encoding="utf-8", errors="replace").read()
    if ext == ".json":
        segs = json.loads(raw)
        segs = segs.get("segments", segs) if isinstance(segs, dict) else segs
        text = " ".join(s.get("text", "").strip() for s in segs)
        secs = sum(max(0, w["e"] - w["s"]) for s in segs for w in s.get("words", []))
        if not secs:
            secs = sum(max(0, s.get("end", 0) - s.get("start", 0)) for s in segs)
        return [text], secs
    if ext in (".srt", ".vtt"):
        secs, lines = 0.0, []
        for ln in raw.splitlines():
            m = TIMECODE.search(ln)
            if m:
                g = [int(x) for x in m.groups()]
                secs += max(0, (g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000) - (g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000))
            elif ln.strip() and not ln.strip().isdigit() and not ln.startswith(("WEBVTT", "NOTE")):
                lines.append(re.sub(r"<[^>]+>", "", ln.strip()))
        return [" ".join(lines)], secs
    return [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()], 0


def ngrams(ws, n):
    return [" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)]


def build(paths):
    blocks, secs_total, timed_words = [], 0.0, 0
    for p in paths:
        bs, secs = read_source(p)
        blocks += [(p, b) for b in bs]
        if secs:
            secs_total += secs
            timed_words += sum(len(words(b)) for b in bs)
    sents = [(p, s) for p, b in blocks for s in sentences(b)]
    all_words = [w for _, b in blocks for w in words(b)]
    if not sents or not all_words:
        sys.exit("no usable text in those files")
    n = len(all_words)
    lens = sorted(len(words(s)) for _, s in sents)
    q = lambda f: lens[min(len(lens) - 1, int(f * len(lens)))]

    # phrases he repeats, across more than one source where there is more than one
    multi_src = len({p for p, _ in blocks}) > 1
    phrase_src, phrase_n = collections.defaultdict(set), collections.Counter()
    for p, s in sents:
        ws = words(s)
        for k in (2, 3, 4):
            for g in ngrams(ws, k):
                parts = g.split()
                if all(w in STOP for w in parts) or parts[0] in STOP and parts[-1] in STOP and k == 2:
                    continue
                phrase_n[g] += 1
                phrase_src[g].add(p)
    floor = 3 if n > 1500 else 2
    phrases = [g for g, c in phrase_n.most_common() if c >= floor and (not multi_src or len(phrase_src[g]) > 1)]
    # drop a phrase that only ever appears inside a longer kept one
    phrases = [g for g in phrases if not any(g != h and g in h and phrase_n[h] >= phrase_n[g] for h in phrases)][:25]

    low = " ".join(all_words)
    fillers = {f: round(100 * len(re.findall(r"\b" + re.escape(f) + r"\b", low)) / n, 2) for f in FILLERS}
    fillers = {f: v for f, v in sorted(fillers.items(), key=lambda kv: -kv[1]) if v > 0}
    openers = collections.Counter(" ".join(words(s)[:2]) for _, s in sents if len(words(s)) >= 4)
    content = collections.Counter(w for w in all_words if w not in STOP and len(w) > 2 and not w.isdigit())

    # his own short lines: 4-14 words, prefer ones carrying a signature phrase, no repeats
    seen, examples = set(), []
    ranked = sorted(sents, key=lambda ps: (-sum(g in " ".join(words(ps[1])) for g in phrases[:12]),
                                            abs(len(words(ps[1])) - statistics.median(lens))))
    for _, s in ranked:
        key = " ".join(words(s))
        if 4 <= len(key.split()) <= 14 and key not in seen:
            seen.add(key)
            examples.append(s)
        if len(examples) >= 20:
            break

    sent_text = [s for _, s in sents]
    return {
        "sources": len({p for p, _ in blocks}),
        "words": n,
        "sentences": len(sents),
        "thin": n < 1500,
        "sentence_words": {"median": statistics.median(lens), "p25": q(.25), "p75": q(.75), "p90": q(.9)},
        "wpm": round(60 * timed_words / secs_total) if secs_total > 30 else None,
        "question_rate": round(sum(s.rstrip().endswith("?") for s in sent_text) / len(sents), 3),
        "contractions_per_100": round(100 * sum(len(CONTRACTION.findall(b)) for _, b in blocks) / n, 2),
        "fillers_per_100": fillers,
        "openers": [o for o, c in openers.most_common(10) if c >= 2],
        "phrases": phrases,
        "top_words": [w for w, _ in content.most_common(30)],
        "examples": examples,
    }


def style_md(p):
    sw = p["sentence_words"]
    out = ["# Omarie's voice (built by voice_build.py; rebuild it, don't edit by hand)", "",
           f"From {p['words']} words over {p['sources']} source(s)."
           + (" **Thin profile: under 1,500 words. Add more transcripts before trusting it.**" if p["thin"] else ""), "",
           "## How he talks", "",
           f"- Sentences run {sw['p25']}-{sw['p75']} words, usually about {sw['median']:g}. Rarely over {sw['p90']}.",
           f"- Pace: about {p['wpm']} words a minute." if p["wpm"] else "- Pace: unknown (no timed transcripts); assume 160 words a minute.",
           f"- {round(100 * p['question_rate'])}% of his sentences are questions.",
           f"- Contractions: {p['contractions_per_100']} per 100 words"
           + (": he contracts, so write \"it's\", \"don't\", \"we're\"." if p["contractions_per_100"] >= 2 else "."), ""]
    if p["fillers_per_100"]:
        out += ["- Filler words he uses (per 100 words): " + ", ".join(f"\"{f}\" {v}" for f, v in p["fillers_per_100"].items()), ""]
    if p["openers"]:
        out += ["## How his sentences start", "", ", ".join(f"\"{o}…\"" for o in p["openers"]), ""]
    if p["phrases"]:
        out += ["## Phrases he keeps coming back to", "", ", ".join(f"\"{g}\"" for g in p["phrases"]), ""]
    out += ["## Words he uses most", "", ", ".join(p["top_words"]), "",
            "## His own lines (copy the rhythm, not the words)", ""] + [f"- {e}" for e in p["examples"]] + [""]
    return "\n".join(out)


def expand(items):
    out = []
    for it in items:
        if os.path.isdir(it):
            out += sorted(f for e in ("json", "srt", "vtt", "txt") for f in glob.glob(os.path.join(it, "**", "*." + e), recursive=True))
        else:
            out.append(it)
    return [f for f in out if os.path.basename(f) not in ("style.json", "omarie_profile.json")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", help="transcribe.py .json, .srt, .vtt or .txt files, or folders of them")
    ap.add_argument("--out", default=os.path.join(KIT, "voice"))
    a = ap.parse_args()
    paths = expand(a.sources)
    if not paths:
        sys.exit("no source files found")
    prof = build(paths)
    os.makedirs(a.out, exist_ok=True)
    json.dump(prof, open(os.path.join(a.out, "style.json"), "w"), indent=1)
    open(os.path.join(a.out, "STYLE.md"), "w").write(style_md(prof))
    print(f"{prof['words']} words, {prof['sentences']} sentences from {prof['sources']} source(s) -> {a.out}/style.json, STYLE.md")
    if prof["thin"]:
        print("thin profile: under 1,500 words. Transcribe more of his talking reels for a better match.")


if __name__ == "__main__":
    main()
