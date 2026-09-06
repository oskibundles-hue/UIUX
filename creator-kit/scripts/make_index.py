#!/usr/bin/env python3
"""
make_index.py - write the delivery index in three forms from one manifest:
Markdown (for the repo and Dropbox) and a single HTML page.

  make_index.py manifest.json --md out.md --html out.html

manifest.json:
{ "title": "...", "date": "...", "grade": {...}, "sections": [
    {"name": "...", "note": "...", "items": [{"label": "...", "meta": "...", "url": "..."}]} ] }
"""
import argparse, html, json

def md(m):
    out = [f"# {m['title']}", "", m.get("intro", ""), ""]
    g = m.get("grade")
    if g:
        out += ["## The grade", "", g["note"], ""]
        for k, v in g.get("facts", {}).items(): out.append(f"- **{k}**: {v}")
        out.append("")
    for s in m["sections"]:
        out += [f"## {s['name']}", ""]
        if s.get("note"): out += [s["note"], ""]
        out += ["| # | what | details | link |", "|---|---|---|---|"]
        for i, it in enumerate(s["items"], 1):
            link = f"[download]({it['url']})" if it.get("url") else "not hosted"
            out.append(f"| {i} | {it['label']} | {it.get('meta','')} | {link} |")
        out.append("")
    return "\n".join(out)

def page(m):
    e = html.escape
    css = """<style>:root{--bg:#0f1014;--ink:#fdfdfd;--mute:#a9abb3;--gold:#fbd101;--card:#171920;--line:#262932}
    body{background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,sans-serif;margin:0;padding:28px 18px 60px}
    main{max-width:820px;margin:0 auto}h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:34px 0 10px;color:var(--gold);text-transform:uppercase;letter-spacing:.06em}
    .sub{color:var(--mute);margin-bottom:8px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:8px 0;display:flex;gap:12px;align-items:center;justify-content:space-between}
    .card .l{min-width:0}.card b{display:block}.card small{color:var(--mute)}a.btn{background:var(--gold);color:#111;font-weight:700;text-decoration:none;padding:9px 14px;border-radius:7px;white-space:nowrap}
    a.btn.off{background:var(--line);color:var(--mute)}.note{color:var(--mute);font-size:14px;margin:0 0 10px}ul{margin:6px 0 0 18px;color:var(--mute)}</style>"""
    h = [f"<title>{e(m['title'])}</title>", css, "<main>", f"<h1>{e(m['title'])}</h1>", f"<div class=sub>{e(m.get('date',''))}</div>", f"<p class=note>{e(m.get('intro',''))}</p>"]
    g = m.get("grade")
    if g:
        h += ["<h2>The grade</h2>", f"<p class=note>{e(g['note'])}</p>", "<ul>"] + [f"<li><b>{e(k)}</b>: {e(v)}</li>" for k, v in g.get("facts", {}).items()] + ["</ul>"]
    for s in m["sections"]:
        h.append(f"<h2>{e(s['name'])}</h2>")
        if s.get("note"): h.append(f"<p class=note>{e(s['note'])}</p>")
        for it in s["items"]:
            btn = f"<a class=btn href=\"{e(it['url'])}\">Download</a>" if it.get("url") else "<a class='btn off'>Not hosted</a>"
            h.append(f"<div class=card><div class=l><b>{e(it['label'])}</b><small>{e(it.get('meta',''))}</small></div>{btn}</div>")
    h.append("</main>")
    return "\n".join(h)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("manifest"); ap.add_argument("--md"); ap.add_argument("--html")
    a = ap.parse_args(); m = json.load(open(a.manifest))
    if a.md: open(a.md, "w").write(md(m))
    if a.html: open(a.html, "w").write(page(m))
    print("ok")
