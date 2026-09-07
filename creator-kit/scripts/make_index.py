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
    css = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;600;700&display=swap">
<style>
:root{--bg:#f3f2ef;--panel:#ffffff;--ink:#141518;--mute:#5d6068;--line:#dcdbd5;--gold:#c9a400;--goldink:#141518;--red:#e75522}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#101114;--panel:#17181d;--ink:#fdfdfd;--mute:#a4a7b0;--line:#272931;--gold:#fbd101;--goldink:#141518;--red:#e75522}}
:root[data-theme="dark"]{--bg:#101114;--panel:#17181d;--ink:#fdfdfd;--mute:#a4a7b0;--line:#272931;--gold:#fbd101;--goldink:#141518;--red:#e75522}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Archivo,Helvetica,Arial,sans-serif}
main{max-width:860px;margin:0 auto;padding:36px 20px 80px}
h1{font:400 44px/1 Anton,Impact,sans-serif;text-transform:uppercase;letter-spacing:.01em;margin:0 0 6px;text-wrap:balance}
.sub{color:var(--mute);font-size:14px;margin:0 0 4px}.intro{max-width:62ch;margin:14px 0 0}
h2{font:400 22px/1.1 Anton,Impact,sans-serif;text-transform:uppercase;letter-spacing:.03em;margin:44px 0 6px}
.note{color:var(--mute);max-width:65ch;margin:0 0 14px}
.grade{background:var(--panel);border:1px solid var(--line);padding:16px 18px;border-radius:6px}
.grade dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px;margin:10px 0 0}.grade dt{font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}.grade dd{margin:0}
.row{display:grid;grid-template-columns:38px 1fr auto;gap:0 14px;align-items:center;padding:12px 0;border-top:1px solid var(--line)}
.row:last-child{border-bottom:1px solid var(--line)}.row .n{font:400 22px/1 Anton,Impact,sans-serif;color:var(--red);font-variant-numeric:tabular-nums}
.row b{display:block}.row small{color:var(--mute);display:block;font-variant-numeric:tabular-nums}
a.btn{background:var(--gold);color:var(--goldink);font-weight:700;text-decoration:none;padding:9px 14px;border-radius:4px;white-space:nowrap;font-size:14px}
a.btn:focus-visible{outline:3px solid var(--red);outline-offset:2px}.off{color:var(--mute);font-size:13px}
.singles .row .n{color:var(--mute);font-size:18px}
@media (max-width:520px){.row{grid-template-columns:32px 1fr}.row a.btn{grid-column:2;justify-self:start;margin-top:8px}}
</style>"""
    h = [f"<title>{e(m['title'])}</title>", css, "<main>", f"<h1>{e(m['title'])}</h1>", f"<p class=sub>{e(m.get('date',''))}</p>", f"<p class=intro>{e(m.get('intro',''))}</p>"]
    g = m.get("grade")
    if g:
        h += ["<h2>The grade</h2>", "<div class=grade>", f"<div>{e(g['note'])}</div>", "<dl>"] + [f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in g.get("facts", {}).items()] + ["</dl></div>"]
    for s in m["sections"]:
        cls = "singles" if "Singles" in s["name"] else "series"
        h.append(f"<section class={cls}><h2>{e(s['name'])}</h2>")
        if s.get("note"): h.append(f"<p class=note>{e(s['note'])}</p>")
        for i, it in enumerate(s["items"], 1):
            btn = f"<a class=btn href=\"{e(it['url'])}\">Download</a>" if it.get("url") else "<span class=off>not hosted</span>"
            h.append(f"<div class=row><span class=n>{i:02d}</span><div><b>{e(it['label'])}</b><small>{e(it.get('meta',''))}</small></div>{btn}</div>")
        h.append("</section>")
    h.append("</main>")
    return "\n".join(h)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("manifest"); ap.add_argument("--md"); ap.add_argument("--html")
    a = ap.parse_args(); m = json.load(open(a.manifest))
    if a.md: open(a.md, "w").write(md(m))
    if a.html: open(a.html, "w").write(page(m))
    print("ok")
