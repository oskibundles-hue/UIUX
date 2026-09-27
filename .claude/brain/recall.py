#!/usr/bin/env python3
"""Deterministic memory lookup (no model): keywords -> score every note from a cached index WITHOUT opening notes ->
open only the best note -> print only the lines that answer -> mention one pointer.
v2: the cached index now holds each note's title, index line, description,
headings, bold phrases and body word counts, scored BM25-style so rare words count more; a small synonym list covers
words the owner uses that the notes phrase differently; output is the best few lines, not whole sections.
usage: python3 .claude/brain/recall.py "how do I deliver finished work" [--top 1] [--full] [--json]
  --json prints {query, top:{file,title,hook,score,units:[{text,score}]}, runner_up} for tools (Jarvis).
"""
import glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nqos_config import MEM
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".memory_cache.json")
VERSION = 3
STOP = set("""a an and are as at be but by do does for from how i if in is it its me my of on or so that the their then there
this to was we what when where which who why will with you your about into over under should can could would any all our
he him his she her they them us has have had get gets did done make makes go goes going just also one ones""".split())
# words the owner uses -> words the notes use (add your own) (both directions are added at query time)
SYN = {
    "delete": ["archive", "remove", "trash"], "dashboard": ["control", "room", "os"], "link": ["url", "artifact"],
    "agent": ["model", "mesh", "subagent"], "model": ["mesh", "router", "lane", "class"], "cost": ["token", "usage", "spend"], "remember": ["memory", "note", "save"],
    "morning": ["report", "daily", "day"], "voice": ["speak", "speech", "jarvis"], "fast": ["speed", "latency", "second"],
    "script": ["tool", "gate", "py"], "time": ["pm", "am", "schedule", "nightly"], "check": ["verify", "gate", "confirm"],
}
def stem(w):
    for suf, rep in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("ly", ""), ("s", "")):
        if len(w) > len(suf) + 2 and w.endswith(suf): w = w[: -len(suf)] + rep; break
    return w[:-1] if len(w) > 4 and w.endswith("e") else w
def words(s):
    """Each word, plus joined-up names (nightly-memory-compile, endcard_9x16_dark.png) both whole and in parts."""
    out = []
    for tok in re.findall(r"[a-z0-9]+(?:['._:/-][a-z0-9]+)*", s.lower()):
        parts = re.split(r"['._:/-]", tok)
        if len(parts) > 1: out.append(tok)
        out += [stem(w) for w in parts if w and w not in STOP]
    return out
def qterms(q):
    base = words(q); out = set(base)
    for w in base:
        for k, vs in SYN.items():
            sk = stem(k)
            if w == sk or w in (stem(v) for v in vs): out |= {sk, *(stem(v) for v in vs)}
    return out
def split_units(body):
    """Paragraphs, with bullet lists split into one unit per bullet (continuation lines stay with their bullet)."""
    units = []
    for block in re.split(r"\n\s*\n", body):
        cur = []
        for ln in block.splitlines():
            if re.match(r"\s*([-*]|\d+\.)\s+", ln) and cur and re.match(r"\s*([-*]|\d+\.)\s+", cur[0]):
                units.append("\n".join(cur)); cur = []
            elif re.match(r"\s*([-*]|\d+\.)\s+", ln) and cur:
                units.append("\n".join(cur)); cur = []
            cur.append(ln)
        if cur: units.append("\n".join(cur))
    return [u.strip() for u in units if u.strip()]
def index():
    files = glob.glob(MEM + "/*.md")
    sig = [max(os.path.getmtime(f) for f in files), len(files), VERSION]
    try:
        c = json.load(open(CACHE))
        if c.get("sig") == sig: return c["notes"], c["df"], c["avg"]
    except Exception: pass
    idx = {}
    for ln in open(MEM + "/MEMORY.md", encoding="utf-8"):
        m = re.match(r"- \[([^\]]+)\]\(([^)]+)\)\s*[—-]?\s*(.*)", ln)
        if m: idx[m[2]] = (m[1], m[3])
    notes, df = [], {}
    for f, (title, hook) in idx.items():
        p = os.path.join(MEM, f)
        if not os.path.exists(p): continue
        txt = open(p, encoding="utf-8").read()
        mm = re.search(r'description:\s*"?(.*?)"?\s*\n', txt); desc = mm[1] if mm else ""
        body = re.sub(r"\A---.*?---\s*", "", txt, flags=re.S)
        heads = " ".join(re.findall(r"(?m)^#+\s*(.*)$", body) + re.findall(r"\*\*(.+?)\*\*", body))
        tf = {}
        for w in words(body): tf[w] = tf.get(w, 0) + 1
        for w in tf: df[w] = df.get(w, 0) + 1
        notes.append(dict(file=f, title=title, hook=hook, desc=desc, title_t=sorted(set(words(title + " " + f.replace("-", " ").replace(".md", "")))),
                          hook_t=sorted(set(words(hook + " " + desc))), head_t=sorted(set(words(heads))), tf=tf, n=sum(tf.values())))
    avg = sum(n["n"] for n in notes) / max(1, len(notes))
    json.dump(dict(sig=sig, notes=notes, df=df, avg=avg), open(CACHE, "w"))
    return notes, df, avg
def score(qs, n, df, N, avg):
    s = 0.0
    for w in qs:
        idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
        tf = n["tf"].get(w, 0)
        s += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * n["n"] / avg)) if tf else 0
        s += idf * (3.0 * (w in n["title_t"]) + 2.0 * (w in n["hook_t"]) + 1.0 * (w in n["head_t"]))
    return s
def unit_score(u, qs, df, N):
    ws = set(words(u)); return sum(math.log(1 + N / (df.get(w, 0) + 1)) for w in qs & ws)
def scored_units(body, qs, df, N, k=3):
    units = split_units(body)
    return sorted(({"text": u, "score": round(unit_score(u, qs, df, N), 2)} for u in units), key=lambda x: -x["score"])[:k]
def clean(s):
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s); s = re.sub(r"[*`#>]", "", s); s = re.sub(r"(?m)^\s*([-\u2022]|\d+\.)\s+", "", s)
    return re.sub(r"\s+", " ", s).strip()
def scored_sentences(hook, body, qs, df, N, k=5):
    """Best short sentences for a spoken answer: the index line's clauses and the note's sentences, scored by how many
    rare question words they hold (distinct matches reported separately so a caller can demand two or more)."""
    cands = [c.strip() for c in re.split(r";\s+", hook) if c.strip()]
    for u in split_units(body):
        cands += [x for x in re.split(r"(?<=[.!?])\s+|\n+", clean(u)) if len(x) > 12]
    w_idf = lambda w: math.log(1 + N / (df.get(w, 0) + 1))
    pool, seen = [], set()
    for c in cands:
        key = c.lower()
        if key in seen: continue
        seen.add(key); hit = qs & set(words(c)); idf = sum(w_idf(w) for w in hit)
        pool.append({"text": c[:300], "idf": round(idf, 2), "hits": len(hit), "score": round(idf / (1 + len(c) / 250), 2), "_hit": hit})
    pool.sort(key=lambda x: -x["score"])
    # first pick = best sentence; after that, prefer sentences covering question words not yet covered,
    # so a two-part question ("the first and the second") gets evidence for both parts
    out, covered = [], set()
    while pool and len(out) < k:
        gain = lambda x: sum(w_idf(w) for w in x["_hit"] - covered) / (1 + len(x["text"]) / 250)
        pick = pool[0] if not out else max(pool, key=lambda x: (gain(x), x["score"]))
        pool.remove(pick); covered |= pick["_hit"]; out.append({k2: v for k2, v in pick.items() if k2 != "_hit"})
    return out
def best_units(body, qs, df, N, limit, max_units):
    units = split_units(body)
    def us(u): return unit_score(u, qs, df, N)
    ranked = sorted(range(len(units)), key=lambda i: -us(units[i]))
    keep, used = [], 0
    for i in ranked[:max_units]:
        if us(units[i]) <= 0: break
        u = units[i] if len(units[i]) <= limit else units[i][:limit].rsplit(" ", 1)[0] + " …"
        if used + len(u) > limit * max_units: break
        keep.append(i); used += len(u)
    return "\n\n".join(units[i] if len(units[i]) <= limit else units[i][:limit].rsplit(" ", 1)[0] + " …" for i in sorted(keep))
def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--") and not (sys.argv[sys.argv.index(x) - 1] == "--top")]
    if not a: sys.exit(__doc__)
    q = " ".join(a); full = "--full" in sys.argv
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 1
    notes, df, avg = index(); N = len(notes); qs = qterms(q)
    ranked = sorted(((score(qs, n, df, N, avg), n) for n in notes), key=lambda x: -x[0])
    ranked = [(s, n) for s, n in ranked if s > 0]
    if "--json" in sys.argv:
        out = {"query": q, "top": None, "runner_up": None}
        if ranked:
            s0, n0 = ranked[0]
            body = re.sub(r"\A---.*?---\s*", "", open(os.path.join(MEM, n0["file"]), encoding="utf-8").read(), flags=re.S)
            out["top"] = {"file": n0["file"], "title": n0["title"], "hook": n0["hook"], "score": round(s0, 2), "units": scored_units(body, qs, df, N), "sentences": scored_sentences(n0["hook"], body, qs, df, N)}
            if len(ranked) > 1: out["runner_up"] = {"file": ranked[1][1]["file"], "title": ranked[1][1]["title"], "score": round(ranked[1][0], 2)}
        print(json.dumps(out)); return
    if not ranked: print("no memory note matches:", q); return
    shown = ranked[:top]
    # a close runner-up often holds the other half of the answer: show its best line too
    if top == 1 and len(ranked) > 1 and ranked[1][0] >= 0.8 * ranked[0][0]: shown = ranked[:2]
    for i, (s, n) in enumerate(shown):
        body = re.sub(r"\A---.*?---\s*", "", open(os.path.join(MEM, n["file"]), encoding="utf-8").read(), flags=re.S)
        print(f"## {n['title']}  ({n['file']}, score {s:.1f})\n{n['hook']}\n")
        if full: print(body)
        else: print(best_units(body, qs, df, N, 600, 3 if i == 0 else 1) + "\n")
        ptr = re.findall(r"\[\[([^\]]+)\]\]", body)
        if ptr and i == 0: print("See also:", ", ".join(sorted(set(ptr))[:4]), "\n")
main()
