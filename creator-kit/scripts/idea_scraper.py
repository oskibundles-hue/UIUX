#!/usr/bin/env python3
"""
idea_scraper - find what is over-performing for the creators and communities
you watch, and list it as ideas worth stealing the shape of.

For each brand in ideas/watchlist.json it pulls:

  1. the latest uploads from each YouTube channel (yt-dlp, free, no API key)
  2. this week's top posts from each subreddit (Reddit's public JSON)

and scores every item against its own source's normal: views divided by the
median views of that channel's recent uploads, or upvotes divided by the
subreddit's median. A video on 3x its channel's median is an outlier whatever
the channel's size, which is the signal worth copying. Topic words from the
watchlist add a small boost so on-brand outliers rise first.

Output is a dated Markdown list (and JSON) in ideas/out/. Items already shown
on an earlier run are skipped, so each run shows only what is new.

Requires yt-dlp on PATH for YouTube (brew install yt-dlp). Pure standard
library otherwise. Nothing is posted or logged into.

Usage:
    python3 idea_scraper.py                       # every brand, write ideas/out/
    python3 idea_scraper.py --brand formula-dynamics --top 15
    python3 idea_scraper.py --min-outlier 1.5 --per-channel 30
    python3 idea_scraper.py --offline fixture.json  # score a saved fetch, no network
"""

import argparse
import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
IDEAS = os.path.join(os.path.dirname(HERE), "ideas")
UA = "nq-idea-scraper/1.0 (personal research script)"


def fetch_youtube(channel, n, ytdlp="yt-dlp"):
    """Latest n uploads of a channel as [{title, url, views}] via yt-dlp's flat playlist (no downloads)."""
    url = channel.rstrip("/")
    if not re.search(r"/(videos|shorts|streams)$", url):
        url += "/videos"
    out = subprocess.run([ytdlp, "-J", "--flat-playlist", "--playlist-end", str(n), url],
                         capture_output=True, text=True, timeout=180)
    if out.returncode:
        raise RuntimeError(out.stderr.strip().splitlines()[-1] if out.stderr.strip() else "yt-dlp failed")
    data = json.loads(out.stdout)
    who = data.get("channel") or data.get("uploader") or channel
    return [{"title": e.get("title") or "", "url": e.get("url") or f"https://youtu.be/{e.get('id')}",
             "views": e.get("view_count"), "source": who, "kind": "youtube"}
            for e in data.get("entries") or [] if e.get("view_count") is not None]


def fetch_reddit(sub, n):
    """This week's top n posts of a subreddit as [{title, url, views}] (views = upvotes)."""
    req = urllib.request.Request(f"https://www.reddit.com/r/{sub}/top.json?t=week&limit={n}",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return [{"title": p["data"]["title"], "url": "https://www.reddit.com" + p["data"]["permalink"],
             "views": p["data"]["score"], "source": f"r/{sub}", "kind": "reddit"}
            for p in data["data"]["children"]]


def topic_hits(title, keywords):
    low = title.lower()
    return sorted({k for k in keywords if re.search(r"\b" + re.escape(k.lower()) + r"\b", low)})


def hook_pattern(title):
    """The title's reusable shape: numbers and money become N so 'I spent $4,000 on 3 wheels' -> 'I spent $N on N wheels'."""
    t = re.sub(r"\$\s?\d(?:[\d,.]*\d)?(?:\s?[kKmM]\b)?", "$N", title)
    return re.sub(r"\b\d(?:[\d,.]*\d)?\b", "N", t)


def score_source(items, keywords):
    """Outlier = item's views / median views of its source. Topic words add 15% each, up to +45%."""
    views = [i["views"] for i in items if i["views"]]
    if len(views) < 3:
        return []  # too few to know what normal is
    med = statistics.median(views) or 1
    out = []
    for i in items:
        hits = topic_hits(i["title"], keywords)
        outlier = (i["views"] or 0) / med
        out.append({**i, "median": med, "outlier": round(outlier, 2), "topics": hits,
                    "score": round(outlier * (1 + 0.15 * min(len(hits), 3)), 2), "pattern": hook_pattern(i["title"])})
    return out


def gather(brand, cfg, args, log):
    """Fetch every source of one brand; returns {source_key: items}. A failing source is logged, not fatal."""
    got = {}
    for ch in cfg.get("youtube", []):
        try:
            got[ch] = fetch_youtube(ch, args.per_channel, args.ytdlp)
        except Exception as e:
            log.append(f"{brand}: {ch}: {e}")
    for sub in cfg.get("subreddits", []):
        try:
            got[f"r/{sub}"] = fetch_reddit(sub, args.per_channel)
        except Exception as e:
            log.append(f"{brand}: r/{sub}: {e}")
    return got


def load_seen(path):
    try:
        return set(json.load(open(path)))
    except Exception:
        return set()


def render_md(day, picks, log):
    lines = [f"# Ideas, {day}", "",
             "Each idea is over-performing against its own channel or subreddit. Copy the shape (the pattern), "
             "not the content, and make it about your shop or your cars.", ""]
    for brand, items in picks.items():
        lines += [f"## {brand}", ""]
        if not items:
            lines += ["Nothing new over the bar this run.", ""]
        for n, i in enumerate(items, 1):
            topics = f" · topics: {', '.join(i['topics'])}" if i["topics"] else ""
            lines += [f"{n}. **{i['title']}** ({i['source']})",
                      f"   {i['outlier']}x its normal ({i['views']:,} vs median {int(i['median']):,}){topics}",
                      f"   pattern: `{i['pattern']}`",
                      f"   {i['url']}", ""]
    if log:
        lines += ["## Sources that failed", ""] + [f"- {l}" for l in log] + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--watchlist", default=os.path.join(IDEAS, "watchlist.json"))
    ap.add_argument("--brand", action="append", help="only these brands (repeatable)")
    ap.add_argument("--per-channel", type=int, default=20, help="uploads/posts to read per source (default 20)")
    ap.add_argument("--min-outlier", type=float, default=2.0, help="keep items at or above this many x normal")
    ap.add_argument("--top", type=int, default=10, help="ideas per brand (default 10)")
    ap.add_argument("--out", default=os.path.join(IDEAS, "out"))
    ap.add_argument("--offline", help="score a saved fetch {brand: {source: [items]}} instead of fetching")
    ap.add_argument("--save-fetch", help="also write the raw fetch here, for --offline re-runs")
    ap.add_argument("--all", action="store_true", help="include ideas already shown on earlier runs")
    ap.add_argument("--ytdlp", default="yt-dlp")
    args = ap.parse_args()

    brands = json.load(open(args.watchlist))["brands"]
    if args.brand:
        brands = {b: brands[b] for b in args.brand}
    log = []
    if args.offline:
        fetched = json.load(open(args.offline))
        fetched = {b: fetched.get(b, {}) for b in brands}
    else:
        fetched = {b: gather(b, cfg, args, log) for b, cfg in brands.items()}
    if args.save_fetch:
        json.dump(fetched, open(args.save_fetch, "w"), indent=1)

    os.makedirs(args.out, exist_ok=True)
    seen_path = os.path.join(args.out, "seen.json")
    seen = set() if args.all else load_seen(seen_path)
    picks = {}
    for b, sources in fetched.items():
        kw = brands[b].get("keywords", [])
        scored = [s for items in sources.values() for s in score_source(items, kw)]
        keep = sorted((s for s in scored if s["outlier"] >= args.min_outlier and s["url"] not in seen),
                      key=lambda s: -s["score"])
        picks[b] = keep[:args.top]

    day = dt.date.today().isoformat()
    md = render_md(day, picks, log)
    base = os.path.join(args.out, f"ideas-{day}")
    open(base + ".md", "w").write(md)
    json.dump({"date": day, "ideas": picks, "failed": log}, open(base + ".json", "w"), indent=1)
    if not args.all:
        json.dump(sorted(seen | {i["url"] for v in picks.values() for i in v}), open(seen_path, "w"), indent=0)
    total = sum(len(v) for v in picks.values())
    print(f"{total} ideas -> {base}.md" + (f" ({len(log)} sources failed)" if log else ""))
    for l in log:
        print("  failed:", l, file=sys.stderr)


if __name__ == "__main__":
    main()
