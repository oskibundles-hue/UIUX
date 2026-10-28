#!/usr/bin/env python3
"""
relay_ideas - turn the posts Muse relays into a ranked list of reel ideas for @nq.young.

Muse posts each Instagram or YouTube find as an issue comment on the private
channel repo: the account, the link, likes and comments, the caption and a
read of the media. This reads those comments (saved JSON from the GitHub API,
or fetched with --issue) and scores every reference out of 100:

  engagement  40  likes + comments against the account's followers when the
                  relay gives them (5% = full marks), else against a log scale
                  at a discount. Comments on a gated post ("comment X for the
                  guide") count a fifth, because they are mostly the keyword.
  brief fit   35  the lesson in Muse's latest weekly brief: a reference about
                  a car, that opens on its payoff, as a reel.
  footage     25  how many of the shots the format needs are in your footage
                  index (00 CARS BY CLIP.md), on a clip whose car is named.

A relay becomes an idea only when it matches a format in ideas/relay_rules.json;
the rest (tools, apps, agent set-ups) are listed as parked. Each idea carries
the hook (with the car from the clip that carries it), the format, the link,
a one-line reason and the clips.

Output: ideas/out/relay-ideas-DATE.md and .json. The output is built from
private relays, so ideas/out/ stays out of git. Nothing is posted, commented
or bought.

Usage:
    python3 relay_ideas.py --relays 58.json 59.json --footage "00 CARS BY CLIP.md"
    python3 relay_ideas.py --issue 2 --issue 58 --issue 59 --issue 61 --since 2026-10-25 --footage cars.md
"""

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
IDEAS = os.path.join(os.path.dirname(HERE), "ideas")
sys.path.insert(0, HERE)
from idea_scraper import hook_pattern  # noqa: E402

LINK = re.compile(r"https?://(?:www\.)?(?:instagram\.com/(?:reel|p)/[\w-]+|youtu\.be/[\w-]+|youtube\.com/watch\?v=[\w-]+)")
HANDLE = re.compile(r"(?<![\w.])@([A-Za-z0-9_.]*[A-Za-z0-9_])")
OWN = {"nq.young", "youngomarie"}


def num(s, unit=""):
    """'3,382' -> 3382, ('193', 'k') -> 193000, ('1.2', 'M') -> 1200000."""
    v = float(s.replace(",", ""))
    return int(v * {"k": 1e3, "m": 1e6}.get(unit.lower(), 1))


def fetch_issue(repo, n, token=None):
    """Every comment on one issue, via the GitHub API (paged)."""
    out, page = [], 1
    while True:
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues/{n}/comments?per_page=100&page={page}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "relay-ideas"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            got = json.load(r)
        out += got
        if len(got) < 100:
            return out
        page += 1


def is_relay(body):
    head = body.lstrip()[:120].lower()
    return not head.startswith(("**claude", "claude:", "claude (")) and ("relay" in head or "darkweb" in head)


def weekly_brief(comments):
    """The latest '@nq.young brief': its follower count and its 'One change' lesson."""
    briefs = [c for c in comments if re.search(r"weekly @nq\.young brief", c["body"], re.I)]
    if not briefs:
        return None
    c = max(briefs, key=lambda c: c["created_at"])
    f = re.search(r"([\d,]+)\s+followers", c["body"])
    lesson = re.search(r"One change:\s*(.+)", c["body"])
    return {"date": c["created_at"][:10], "followers": num(f.group(1)) if f else None,
            "lesson": lesson.group(1).strip() if lesson else "", "url": c.get("html_url", "")}


def split_posts(body):
    """One comment can carry a numbered list of posts; each item with its own link is its own post."""
    items = re.split(r"\n(?=\d+\.\s)", body)
    with_links = [i for i in items if LINK.search(i)]
    if len(with_links) > 1:
        head = items[0] if not LINK.search(items[0]) else ""
        return [(i, head) for i in with_links]
    return [(body, "")]


MUSE_NOTE = re.compile(r"\n\s*(?:\*\*)?(?:why it matters|edit[/ -]?(?:style|sfx|sound)? ?reference|tool reference|"
                       r"reference only|for claude|feeds straight|relevant to|same lane|worth noting|flagging this)", re.I)


def parse_post(text, head, comment):
    link = LINK.search(text)
    if not link:
        return None
    url = link.group(0)
    handles = [h for h in HANDLE.findall(text) if h.lower() not in OWN]
    bold = [b for b in re.findall(r"\*\*(.+?)\*\*", text)
            if not re.match(r"(darkweb|relay|claude|@)", b, re.I) and len(b) > 6]
    eng = re.search(r"([\d,]+)\s*likes?\s*[/,]\s*([\d,]+)\s*comments?", text)
    likes = re.search(r"([\d,]+)\s*likes?\b", text)
    fol = re.search(r"([\d.,]+)\s*([kKmM])?\s+followers", text)
    views = re.search(r"([\d.,]+)\s*([KkMm])?\s+views", text)
    subs = re.search(r"([\d.,]+)\s*([KkMm])?\s+subs", text)
    quotes = [q for q in re.findall(r"[\"“]([^\"”\n]{4,60})[\"”]", text)
              if not re.search(r"comment|https?:", q, re.I) and not q.isupper()]
    by = re.search(r"\*\*\s*\"?(.+?)\"?\s*\*\*\s*by\s+([^.\n]+)", text)
    account = ("@" + handles[0]) if handles else (by.group(2).strip() if by else "")
    return {
        "url": url if "youtu" in url else url.split("?")[0], "account": account,
        "title": title_of(text, bold, quotes, account),
        "date": comment["created_at"][:10], "relay": comment.get("html_url", ""),
        "kind": "youtube" if "youtu" in url else "instagram",
        "likes": num(eng.group(1)) if eng else (num(likes.group(1)) if likes else None),
        "comments": num(eng.group(2)) if eng else None,
        "followers": num(fol.group(1), fol.group(2) or "") if fol else None,
        "views": num(views.group(1), views.group(2) or "") if views else None,
        "subs": num(subs.group(1), subs.group(2) or "") if subs else None,
        "gated": bool(re.search(r"gated|behind comment", text, re.I)),
        "directive": bool(re.search(r"DIRECTIVE|make this template", text)),
        "on_screen": quotes[:3],
        "text": MUSE_NOTE.split(head + "\n" + text)[0].lower(),
    }


def title_of(text, bold, quotes, account):
    if bold:
        return bold[0].strip(" —-:")
    if quotes:
        return quotes[0]
    first = re.sub(r"^\d+\.\s*|\*\*.*?\*\*:?\s*", "", text.strip().split("\n")[0])
    first = re.sub(r"^@[\w.]+\s*(\([^)]*\))?\s*[—-]\s*", "", first)
    return (first[:80].rsplit(" ", 1)[0].rstrip(",;:.") + "…" if len(first) > 80 else first) or f"Post by {account}"


def statuses(comments):
    """Handles Claude's own replies say were picked, queued or built, so they show as already in hand."""
    taken = {}
    for c in comments:
        if is_relay(c["body"]):
            continue
        for sent in re.split(r"(?<=[.!?])\s+|\n", c["body"]):
            m = re.search(r"\b(picked|queued|built|on it now|tried)\b", sent, re.I)
            if m:
                for h in HANDLE.findall(sent):
                    taken.setdefault(h.lower(), m.group(1).lower())
    return taken


def car_key(md):
    """The colour key's cars as {model word: full name}: 'Maserati MC20' -> {'mc20': 'Maserati MC20'}."""
    names = {}
    for line in md.split("## Verified")[0].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) > 1 and re.search(r"[A-Za-z]", cells[0]) and cells[0].lower() != "car":
            name = re.sub(r"\s*\(.*?\)", "", cells[0]).strip()
            if not set(name) <= set("-: "):
                names[name] = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", name) if re.search(r"\d", w) or len(w) > 4]
    count = {}
    for words in names.values():
        for w in words:
            count[w] = count.get(w, 0) + 1
    return {w: name for name, words in names.items() for w in words if count[w] == 1}


def name_car(text, key):
    low = text.lower()
    for word, name in key.items():
        if re.search(r"\b" + re.escape(word) + r"\b", low):
            return name
    return ""


MAKES = r"\b(porsche|bmw|lamborghini|ferrari|mclaren|maserati|aston|mercedes|amg|rolls|audi|nissan|toyota)\b"
DOUBT = r"unknown|not seen|not confirmed|per codex|likely|\?"


def clean_car(raw, key):
    """A confirmed car name or ''. The brief says name the car, so a guess ('red Maserati per Codex') is no car."""
    named = name_car(raw, key)
    if named:
        return named
    first = re.split(r"\s+[—-]\s+|\(|;|,", raw)[0].strip()
    return first if re.search(MAKES, first, re.I) and not re.search(DOUBT, raw, re.I) else ""


def parse_footage(md, rules):
    """Rows of 00 CARS BY CLIP.md as [{day, clip, shows, car, tags}].

    The car comes from the row's car column, named by the colour key; a table with no car column takes the car
    its heading names. A car the file leaves blank, or marks as not that car, stays blank.
    """
    key = car_key(md)
    clips, day, head_car, cols = [], "", "", None
    for line in md.splitlines():
        h = re.match(r"#+\s*(.*)", line)
        if h:
            d = re.search(r"(\d{4})-(\d{2}-\d{2})", h.group(1))
            day = d.group(0) if d else day
            year = d.group(1) if d else day[:4]
            head_car, cols = name_car(re.sub(r"\bnot the \w+", "", h.group(1), flags=re.I), key), None
            continue
        if not line.startswith("|"):
            cols = None if not line.strip() else cols
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if re.match(r"-+$", cells[0].replace(":", "")):
            continue
        if cols is None:
            cols = [c.lower() for c in cells]
            continue
        if "shows" not in cols or len(cells) != len(cols):
            continue
        row = dict(zip(cols, cells))
        clip = re.sub(r"\*\*|`", "", row.get("clip") or row.get("clips", ""))
        shows = re.sub(r"\*\*", "", row["shows"])
        raw = re.sub(r"\*\*|`", "", row.get("car", ""))
        if "car" in row:
            car = "" if re.match(r"\s*(not\b|—|-|underside|partial|$)", raw, re.I) else clean_car(raw, key)
        else:
            car = head_car
        row_day = row.get("day") or day
        md_ = re.match(r"(\d{2})-(\d{2})\s", clip)
        if md_:
            row_day, clip = f"{year}-{md_.group(1)}-{md_.group(2)}", clip[6:]
        text = (shows + " " + row.get("role", "") + " " + row.get("length", "")).lower()
        tags = sorted(t for t, words in rules["shots"].items() if any(re.search(w, text) for w in words))
        clips.append({"day": row_day, "clip": clip, "shows": shows, "car": car, "tags": tags})
    return clips


def match_format(post, rules):
    for f in rules["formats"]:
        if any(re.search(w, post["text"]) for w in f["match"]):
            return f
    return None


# shot tags as the reason line says them
SHOT_WORDS = {"to_camera": "talking to camera", "part": "parts", "lift": "on the lift"}


def engagement_points(p):
    if p["kind"] == "youtube" and p["views"] and p["subs"]:
        return 40 * min(1, p["views"] / p["subs"] / 3), f"{p['views']:,} views on {p['subs']:,} subs"
    if p["likes"] is None:
        return 0, "no numbers in the relay"
    comments = (p["comments"] or 0) * (0.2 if p["gated"] else 1)
    eng = p["likes"] + comments
    shown = f"{p['likes']:,} likes" + (f" / {p['comments']:,} comments" if p["comments"] is not None else "")
    if p["gated"]:
        shown += " (gated post: comments counted at a fifth)"
    if p["followers"]:
        rate = eng / p["followers"]
        return 40 * min(1, rate / 0.05), f"{shown} on {p['followers']:,} followers ({rate:.1%})"
    return 40 * 0.75 * min(1, math.log10(eng + 1) / math.log10(25000)), f"{shown}, followers not given"


def fit_points(p, rules):
    t = p["text"]
    car = any(re.search(r"\b" + w + r"\b", t) for w in rules["cars"])
    first = any(re.search(w, t) for w in rules["car_first"])
    off = any(re.search(w, t) for w in rules["off_lane"])
    pts = 15 * car + 10 * first + 10 * (p["kind"] == "instagram")
    if off and not car:
        pts *= 0.3
    why = ("a car reference" if car else "no car named in the relay") + (" that leads with its payoff" if first else "")
    return pts, why


def footage_points(fmt, clips, used):
    """The named car whose clips cover most of the shots the format needs; a tie goes to the car used least so far."""
    by_car = {}
    for c in clips:
        if c["car"]:
            by_car.setdefault(c["car"], []).append(c)
    best = None
    for car, cs in by_car.items():
        have = {t for c in cs for t in c["tags"]}
        cover = [n for n in fmt["needs"] if n in have]
        k = (len(cover), -used.get(car, 0), len(cs))
        if cover and (not best or k > best[0]):
            best = (k, car, cover, cs)
    if not best:
        return 0, None, [], []
    _, car, cover, cs = best
    picks = []
    for n in cover:
        c = next(c for c in cs if n in c["tags"])
        if c not in picks:
            picks.append(c)
    return 25 * len(cover) / len(fmt["needs"]), car, cover, picks[:3]


def rank(comments, clips, rules, since=None, until=None):
    brief = weekly_brief(comments)
    taken = statuses(comments)
    ideas, parked, seen, used = [], [], set(), {}
    for c in sorted(comments, key=lambda c: c["created_at"]):
        d = c["created_at"][:10]
        if not is_relay(c["body"]) or (since and d < since) or (until and d > until):
            continue
        for text, head in split_posts(c["body"]):
            p = parse_post(text, head, c)
            if not p or p["url"] in seen:
                continue
            seen.add(p["url"])
            fmt = match_format(p, rules)
            if not fmt:
                parked.append({k: p[k] for k in ("title", "account", "url", "date")})
                continue
            e, e_why = engagement_points(p)
            f, f_why = fit_points(p, rules)
            g, car, cover, picks = footage_points(fmt, clips, used)
            if car:
                used[car] = used.get(car, 0) + 1
            status = taken.get(p["account"].lstrip("@").lower(), "")
            reason = f"{e_why}; {f_why}; " + (f"your {car} footage has {', '.join(SHOT_WORDS.get(n, n) for n in cover)}" if car else "no footage for it yet")
            ideas.append({
                "score": round(e + f + g), "parts": {"engagement": round(e), "fit": round(f), "footage": round(g)},
                "title": p["title"], "account": p["account"], "url": p["url"], "date": p["date"], "relay": p["relay"],
                "format": fmt["name"], "hook": fmt["hook"].format(car=car or "car"),
                "reference_hook": p["on_screen"][0] if p["on_screen"] else "",
                "pattern": hook_pattern(p["on_screen"][0]) if p["on_screen"] else "",
                "reason": reason, "car": car or "", "footage": picks, "gated": p["gated"],
                "directive": p["directive"], "status": status, "note": fmt.get("note", "")})
    ideas.sort(key=lambda i: (-i["score"], i["date"]))
    for n, i in enumerate(ideas, 1):
        i["rank"] = n
    return {"brief": brief, "ideas": ideas, "parked": parked}


def render_md(day, res, top):
    b = res["brief"]
    lines = [f"# Reel ideas for @nq.young, {day}", ""]
    if b:
        lines += [f"Weekly brief {b['date']}: {b['followers']:,} followers. Lesson: {b['lesson']}", ""]
    for i in res["ideas"][:top]:
        extra = "".join(f" · {x}" for x in (i["status"] and f"already {i['status']}", i["note"]) if x)
        lines += [f"{i['rank']}. **{i['hook']}**: {i['format']} ({i['score']}/100){extra}",
                  f"   ref: {i['title']} ({i['account']}, {i['date']}) {i['url']}",
                  f"   why: {i['reason']}"]
        for c in i["footage"]:
            lines.append(f"   clip: {c['day']} `{c['clip']}`: {c['shows']}")
        lines.append("")
    if res["parked"]:
        lines += ["## Parked (not a reel idea)", ""] + [f"- {p['title']} ({p['account']}) {p['url']}" for p in res["parked"]] + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--relays", nargs="*", default=[], help="saved issue-comment JSON files (GitHub API format)")
    ap.add_argument("--issue", type=int, action="append", default=[], help="fetch this issue's comments (repeatable)")
    ap.add_argument("--repo", default="oskibundles-hue/nq-agent-channel")
    ap.add_argument("--footage", help="00 CARS BY CLIP.md (or any file in its table format)")
    ap.add_argument("--rules", default=os.path.join(IDEAS, "relay_rules.json"))
    ap.add_argument("--since", help="only relays on or after YYYY-MM-DD")
    ap.add_argument("--until", help="only relays on or before YYYY-MM-DD")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(IDEAS, "out"))
    args = ap.parse_args()

    comments = []
    for f in args.relays:
        comments += json.load(open(f))
    for n in args.issue:
        comments += fetch_issue(args.repo, n, os.environ.get("GITHUB_TOKEN"))
    if not comments:
        ap.error("no relays: pass --relays or --issue")
    rules = json.load(open(args.rules))
    clips = parse_footage(open(args.footage).read(), rules) if args.footage else []
    res = rank(comments, clips, rules, args.since, args.until)

    day = dt.date.today().isoformat()
    os.makedirs(args.out, exist_ok=True)
    base = os.path.join(args.out, f"relay-ideas-{day}")
    open(base + ".md", "w").write(render_md(day, res, args.top))
    json.dump({"date": day, **res, "ideas": res["ideas"][:args.top], "all": len(res["ideas"])},
              open(base + ".json", "w"), indent=1)
    print(f"{len(res['ideas'])} ideas, {len(res['parked'])} parked, {len(clips)} clips -> {base}.md")


if __name__ == "__main__":
    main()
