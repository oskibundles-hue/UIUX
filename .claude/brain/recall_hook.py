#!/usr/bin/env python3
"""UserPromptSubmit hook (every session): look the prompt up in memory with recall.py's own index (no model, ~0.1 s)
and, only when the match is confident, hand Claude the answering lines as extra context.
Measured on the original NQ OS (fresh-session A/B): recall-first used fewer tokens and less time for the same accuracy.
Never blocks a prompt: any error -> prints nothing, exits 0.
Test by hand:  echo '{"prompt":"what folder does finished work go in"}' | python3 .claude/brain/recall_hook.py
Gate features:  python3 .claude/brain/recall_hook.py --features "question"
"""
import json, math, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nqos_config import WORK, HAVE_NOTES
# gate (tune by hand against real prompts): the prompt's own words (no synonyms) must hit the top note
MIN_WORDS, MIN_HITS, MIN_STRONG = 3, 2, 2   # >=2 real word hits, >=2 of them in the note's title/index line/headings
# filler that matched everything in an off-topic test set (stemmed at load)
FILLER = "what's whats set up use show way out like more good new help mean week make let need want know thing time get got see try work run write explain best many much long one two"
MAX_CHARS = 700
SKIP_NOTES = {"handoff.md"}
LOG = os.path.join(WORK, "recall", "hook_log.jsonl")  # read by recall_learn.py (misses, progress)
SKIP_PREFIXES = ("<", "This session is being continued")
def load():
    src = open(os.path.join(HERE, "recall.py"), encoding="utf-8").read()
    src = re.sub(r"\nmain\(\)\s*$", "\n", src)
    g = {"__name__": "recall_lib", "__file__": os.path.join(HERE, "recall.py")}
    exec(compile(src, "recall.py", "exec"), g); return g
def features(q, R=None):
    R = R or load(); notes, df, avg = R["index"](); N = len(notes)
    qs = R["qterms"](q)
    # handoff.md is current status, not a rule/fact (a standing rule: "Rules and facts only; current status is in the handoff")
    ranked = sorted(((R["score"](qs, n, df, N, avg), n) for n in notes if n["file"] not in SKIP_NOTES), key=lambda x: -x[0])
    if not ranked or ranked[0][0] <= 0: return None
    s0, n0 = ranked[0]
    orig = {w for w in R["words"](q) if len(w) > 1}
    have = set(n0["tf"]) | set(n0["title_t"]) | set(n0["hook_t"])
    filler = {R["stem"](w) for w in FILLER.split()} | set(FILLER.split())
    hit = (orig & have) - filler
    strong = hit & (set(n0["title_t"]) | set(n0["hook_t"]) | set(n0["head_t"]))
    idf = lambda w: math.log(1 + N / (df.get(w, 0) + 1))
    return dict(note=n0, score=s0, hits=sorted(hit), n_hits=len(hit), idf=round(sum(idf(w) for w in hit), 2),
                n_strong=len(strong), n_words=len(orig), qs=qs,
                runner=ranked[1][1] if len(ranked) > 1 and ranked[1][0] >= 0.8 * s0 else None, df=df, N=N, R=R)
def confident(f):
    return f is not None and f["n_words"] >= MIN_WORDS and f["n_hits"] >= MIN_HITS and f["n_strong"] >= MIN_STRONG
def context(f):
    R, n = f["R"], f["note"]
    body = re.sub(r"\A---.*?---\s*", "", open(os.path.join(R["MEM"], n["file"]), encoding="utf-8").read(), flags=re.S)
    sents = [s["text"] for s in R["scored_sentences"](n["hook"], body, f["qs"], f["df"], f["N"], k=3) if s["hits"]]
    txt = " | ".join(sents)[:MAX_CHARS]
    return (f"[memory lookup, automatic] Likely-relevant saved note: {n['title']} ({n['file']}). {txt}\n"
            + (f"Close second: {f['runner']['title']} ({f['runner']['file']}).\n" if f["runner"] else "")
            + f"Use it if it answers the request; for more, run python3 .claude/brain/recall.py \"<question>\". "
            f"Ignore it if it's off-topic.")
def main():
    if "--features" in sys.argv:
        q = " ".join(a for a in sys.argv[1:] if a != "--features"); f = features(q)
        print(json.dumps(None if f is None else {k: f[k] for k in ("score", "hits", "n_hits", "n_strong", "idf", "n_words")} | {"note": f["note"]["file"], "fires": confident(f)})); return
    if not HAVE_NOTES: return  # private notes repo not attached: stay silent
    try:
        data = json.load(sys.stdin); prompt = data.get("prompt", "") or ""
        if prompt.lstrip().startswith(SKIP_PREFIXES) or len(prompt.split()) < MIN_WORDS: return
        t = time.time(); f = features(prompt[:400]); fired = confident(f)
        if fired:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context(f)}}))
        try:
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            with open(LOG, "a") as fh:
                fh.write(json.dumps({"ts": round(t), "session": data.get("session_id"), "prompt": prompt[:300],
                                     "note": f and f["note"]["file"], "fired": fired, "hits": f and f["n_hits"],
                                     "strong": f and f["n_strong"], "ms": round(1000 * (time.time() - t), 1)}) + "\n")
        except Exception:
            pass
    except Exception:
        pass
main()
