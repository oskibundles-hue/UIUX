#!/usr/bin/env python3
"""
relay_ideas_page - put a relay_ideas.py run on one page in the iPhone index layout.

Tabs: Ideas (the ranked list, each row opens to its hook, reason, reference and
clips), Footage (the clips the ideas use, by car), Parked (relays that are not
reel ideas) and How (the brief's lesson and how the score is made). The page is
self-contained: style.css and app.js are inlined from the iPhone index design
system, which lives on the default branch at design-systems/iphone-index/.

The page carries private relays, so write it outside the repo (or to ideas/out/,
which git ignores) and publish it as a private artifact. Run that folder's qa.js
on it before publishing.

Usage:
    python3 relay_ideas_page.py ideas/out/relay-ideas-2026-10-28.json --design ../UIUX/design-systems/iphone-index \\
        -o /tmp/ideas.html
"""
import argparse
import html
import json
import os

esc = html.escape


def svg(body, sw=2, cls="", vb="0 0 24 24"):
    return (f'<svg class="{cls}" viewBox="{vb}" fill="none" stroke="currentColor" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


CHEV = svg('<path d="M1.5 1.5l5.5 5.5-5.5 5.5"/>', cls="chev", vb="0 0 9 14", sw=2.2)
I = {
    "bolt": svg('<path d="M13 3.5L6 13.5h5l-1 7 7-10h-5z"/>', sw=1.9),
    "info": svg('<path d="M12 11v6M12 7.4v.01"/>', sw=2.8),
    "warn": svg('<path d="M12 7v6.5M12 17.2v.01"/>', sw=2.8),
    "done": svg('<path d="M6.5 12.5l3.6 3.6L17.5 8.6"/>', sw=2.6),
    "search": svg('<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>', sw=2.2),
    "x": svg('<path d="M8 8l8 8M16 8l-8 8"/>', sw=2.2),
    "film": svg('<rect x="4" y="4.5" width="16" height="15" rx="2.4"/><path d="M8 4.5v15M16 4.5v15M4 9.5h4M16 9.5h4M4 14.5h4M16 14.5h4"/>', sw=1.8),
    "car": svg('<path d="M5 15.5l1.6-5a2 2 0 0 1 1.9-1.4h7a2 2 0 0 1 1.9 1.4l1.6 5M4 15.5h16v3H4zM7 18.5v1.5M17 18.5v1.5"/>', sw=1.8),
    "park": svg('<rect x="4.5" y="4.5" width="15" height="15" rx="3"/><path d="M10 16.5v-9h2.8a2.6 2.6 0 0 1 0 5.2H10"/>', sw=1.9),
    "book": svg('<path d="M5 5.2A1.7 1.7 0 0 1 6.7 3.5H19v13.8H6.7A1.7 1.7 0 0 0 5 19zM5 19a1.7 1.7 0 0 0 1.7 1.7H19M9 7.5h6"/>', sw=1.9),
    "link": svg('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>', sw=1.9),
}


def band(score):
    return "green" if score >= 70 else "orange" if score >= 50 else "gray"


def pill(color, label):
    return f'<span class="pill p-{color}">{esc(label)}</span>'


def group(gid, title, detail, cells, footer="", cls=""):
    h = f'<div class="gh"><h2>{title}</h2>' + (f'<span class="gh-d">{detail}</span>' if detail else "") + "</div>"
    f = f'<p class="gfoot">{footer}</p>' if footer else ""
    return f'<section class="grp {cls}" id="{gid}">{h}<div class="list">{"".join(cells)}</div>{f}</section>'


def link(url, label):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def idea_row(i):
    p = i["parts"]
    flags = "".join(pill(*f) for f in (("blue", f"already {i['status']}") if i["status"] else None,
                                       ("orange", "costs credits") if i["note"] else None) if f)
    clips = "".join(f"<li><b>{esc(c['day'])}</b> <code>{esc(c['clip'])}</code>: {esc(c['shows'])}</li>" for c in i["footage"])
    ref_hook = f"<p>On screen in the reference: “{esc(i['reference_hook'])}”</p>" if i["reference_hook"] else ""
    body = (f"<p><b>Why #{i['rank']}:</b> {esc(i['reason'])}.</p>"
            f"<p><b>Score {i['score']}/100</b>: engagement {p['engagement']}/40, brief fit {p['fit']}/35, "
            f"footage {p['footage']}/25.</p>"
            f"<p><b>Reference:</b> " + (f"{esc(i['account'])}, relayed {esc(i['date'])} · " if i['title'] == f"Post by {i['account']}"
              else f"{esc(i['title'])} ({esc(i['account'])}, relayed {esc(i['date'])}) · ") +
            f"{link(i['url'], 'open post')} · {link(i['relay'], 'relay')}</p>{ref_hook}"
            + (f"<p><b>Note:</b> {esc(i['note'])}.</p>" if i["note"] else "")
            + (f"<p><b>Footage that could carry it ({esc(i['car'])}):</b></p><ul>{clips}</ul>" if clips
               else "<p><b>Footage:</b> nothing on hand yet.</p>"))
    return (f'<details class="cell dz wi s"><summary><span class="dot d-{band(i["score"])}">{I["bolt"]}</span>'
            f'<span class="dz-text"><span class="dz-title">{i["rank"]}. {esc(i["hook"])}</span>'
            f'<span class="dz-pv">{esc(i["format"])} · {i["score"]}/100 · {esc(i["account"])} {flags}</span></span>{CHEV}'
            f'</summary><div class="dz-body">{body}</div></details>')


def simple_row(icon, color, title, sub, href=None):
    t = f'<span class="row-title">{esc(title)}</span>'
    inner = (f'<span class="dot d-{color}">{I[icon]}</span><span class="row-text"><span class="row-top">{t}</span>'
             f'<span class="row-sub">{esc(sub)}</span></span>')
    if href:
        return f'<div class="cell pg s"><a class="row-main" href="{esc(href)}" target="_blank" rel="noopener">{inner}{CHEV}</a></div>'
    return f'<div class="cell pg s"><div class="row-main">{inner}</div></div>'


def build(data, design):
    ideas, parked, brief = data["ideas"], data["parked"], data.get("brief") or {}
    cars = {}
    for i in ideas:
        for c in i["footage"]:
            cars.setdefault(i["car"], {})[c["clip"]] = c
    tiles = ('<div class="tiles nosearch">'
             f'<button class="tl" data-go="todo" data-to="waiting"><span class="dot d-green">{I["bolt"]}</span><span class="tl-n" data-count="wait"></span><span class="tl-l">Reel ideas</span></button>'
             f'<button class="tl" data-go="pages"><span class="dot d-blue">{I["car"]}</span><span class="tl-n">{len(cars)}</span><span class="tl-l">Cars with footage</span></button>'
             f'<button class="tl" data-go="files"><span class="dot d-gray">{I["park"]}</span><span class="tl-n">{len(parked)}</span><span class="tl-l">Parked</span></button>'
             f'<button class="tl" data-go="rules"><span class="dot d-orange">{I["info"]}</span><span class="tl-n">{esc(f"{brief['followers']:,}" if brief.get("followers") else "–")}</span><span class="tl-l">Followers (brief)</span></button>'
             "</div>")
    lesson = (f'<div class="cell callout s c-orange"><span class="dot d-orange">{I["warn"]}</span><div>'
              f'<div class="co-title">This week’s lesson ({esc(brief.get("date", ""))})</div>'
              f'<div class="co-body">{esc(brief.get("lesson", "No weekly brief in these relays."))}</div></div></div>')
    p_ideas = (tiles + group("lesson", "From Muse’s brief", "", [lesson], cls="nosearch")
               + group("waiting", "Ranked ideas", f"top {len(ideas)} of {data.get('all', len(ideas))}",
                       [idea_row(i) for i in ideas], footer="Tap an idea for its reason, reference and clips. Nothing posts without your yes."))
    p_foot = "".join(group(f"car-{n}", esc(car), f"{len(cl)} clip{'s' * (len(cl) > 1)}",
                           [simple_row("film", "blue", f"{c['day']} · {c['clip']}", c["shows"]) for c in cl.values()])
                     for n, (car, cl) in enumerate(cars.items()))
    p_foot = (f'<p class="lede nosearch">Clips the ideas use, from <b>00 CARS BY CLIP.md</b> in Dropbox '
              f"<b>/NQ Studio/raw footage/</b>. A clip counts only when the index names its car; guesses are left out.</p>" + p_foot)
    p_park = group("parked-list", "Not reel ideas", f"{len(parked)} relays",
                   [simple_row("park", "gray", p["title"], " · ".join(x for x in (p["account"], p["date"]) if x), p["url"]) for p in parked],
                   footer="Tools, apps and set-ups Muse relayed. Kept as references.")
    how = ["<b>Engagement, 40.</b> Likes and comments against the account’s followers when the relay gives them (5% is full marks); otherwise a log scale at a discount. Comments on a gated post count a fifth, because most are the unlock keyword.",
           "<b>Brief fit, 35.</b> A car reference (15), one that leads with its payoff or hook (10), and an Instagram reel or post rather than a long video (10). A post about desktop tools, TVs or agents with no car in it keeps under a third of that. Every hook names the car, so open the caption with the hook and the lesson’s second half, naming the car in the caption, is done too.",
           "<b>Footage, 25.</b> The share of the shot types the format needs (say, a drive and a close-up) that your clips of one named car already cover. It counts shot types, not clips, so most ideas this week score full marks here and the order comes from the other two. Ties go to the car used least, so the list spreads across cars.",
           "<b>Sources.</b> Muse’s relays on the private channel repo, and the Dropbox footage index (read only). Nothing is scraped, commented on, posted or bought."]
    p_how = group("how-list", "How the score works", "", [f'<div class="cell rule s"><span class="bullet" aria-hidden="true"></span><p>{h}</p></div>' for h in how])
    # app.js knows four tab keys (todo, pages, files, rules); the titles are this page's own
    tabs = [("todo", "Ideas", I["bolt"], p_ideas), ("pages", "Footage", I["film"], p_foot),
            ("files", "Parked", I["park"], p_park), ("rules", "How", I["book"], p_how)]
    body = "".join(f'<section class="panel" id="p-{k}" data-title="{t}" aria-label="{t}"><h2 class="panel-h">{t}</h2>{c}</section>'
                   for k, t, _, c in tabs)
    tabbar = ('<nav class="tabbar" aria-label="Sections"><div class="tb-in">' + "".join(
        f'<button class="tab" data-tab="{k}" aria-controls="p-{k}">{ic}<span>{t}</span>'
        + ('<span class="badge" data-count="wait"></span>' if k == "todo" else "") + "</button>" for k, t, ic, _ in tabs)
        + "</div></nav>")
    css = open(os.path.join(design, "style.css"), encoding="utf-8").read()
    js = open(os.path.join(design, "app.js"), encoding="utf-8").read()
    return f'''<title>Reel Ideas</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<style>{css}
.dz-body ul{{margin:4px 0 0;padding-left:18px}}.dz-body li{{margin:2px 0}}.dz-body code{{font-size:13px;word-break:break-all}}
.dz-pv .pill{{margin-left:4px}}</style>
<header class="nav" id="nav"><div class="nav-in"><span></span><span class="nav-title" id="navTitle">Ideas</span>
<button class="nav-btn" id="navSearch" aria-label="Search">{I["search"]}</button></div></header>
<main class="main">
<div class="hero"><p class="over">@nq.young reel ideas · {esc(data["date"])}</p><h1 id="bigTitle">Ideas</h1>
<div class="search" role="search"><label class="sf">{I["search"]}<input id="q" type="search" placeholder="Search ideas, cars and references" autocomplete="off" spellcheck="false" aria-label="Search everything"></label>
<button class="sf-x" id="qx" aria-label="Clear search" hidden>{I["x"]}</button></div>
<p class="results" id="results" hidden></p></div>
{body}
<div class="empty" id="empty" hidden>{I["search"]}<p class="e-t">No results</p><p class="e-s">Nothing matches that.</p></div>
<footer class="foot"><p>Built by relay_ideas.py from Muse’s relays. Private: do not share.</p></footer>
</main>
{tabbar}
<script>{js}</script>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("json", help="a relay-ideas-DATE.json from relay_ideas.py")
    ap.add_argument("--design", required=True, help="the design-systems/iphone-index folder (style.css, app.js)")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    page = build(json.load(open(a.json)), a.design)
    open(a.out, "w", encoding="utf-8").write(page)
    print("wrote", a.out, len(page) // 1024, "KB")


if __name__ == "__main__":
    main()
