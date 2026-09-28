"""Build example.html: every component of the iPhone index layout, filled with sample content.

Copy this file to start a new index page. Replace the SAMPLE data with real rows and run it; the page it writes is
self-contained (style.css and app.js are inlined), so it can be published as an artifact as it is.

    python3 example_page.py            # -> example.html
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
esc = html.escape


def svg(body, fill=False, sw=2, cls='', vb='0 0 24 24'):
    st = 'fill="currentColor" stroke="none"' if fill else (f'fill="none" stroke="currentColor" stroke-width="{sw}" '
                                                           'stroke-linecap="round" stroke-linejoin="round"')
    return f'<svg class="{cls}" viewBox="{vb}" {st} aria-hidden="true">{body}</svg>'


CHEV = svg('<path d="M1.5 1.5l5.5 5.5-5.5 5.5"/>', cls='chev', vb='0 0 9 14', sw=2.2)
I = {  # SF Symbols-like glyphs, drawn on a 24 px grid
    'urgent': svg('<path d="M12 6.5v7M12 17.6v.01"/>', sw=2.8),
    'question': svg('<path d="M9.3 9.2a2.8 2.8 0 1 1 4 2.5c-.8.4-1.3 1-1.3 1.9v.4M12 17.6v.01"/>', sw=2.5),
    'done': svg('<path d="M6.5 12.5l3.6 3.6L17.5 8.6"/>', sw=2.6),
    'info': svg('<path d="M12 11v6M12 7.4v.01"/>', sw=2.8),
    'warn': svg('<path d="M12 7v6.5M12 17.2v.01"/>', sw=2.8),
    'star': svg('<path d="M12 3.6l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.6 9.7l5.8-.8z"/>', fill=True),
    'box': svg('<path d="M4 13.5L6.4 6.5h11.2L20 13.5V18a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zM4 13.5h4.6l1.1 2h4.6l1.1-2H20"/>', sw=1.8),
    'chat': svg('<path d="M5.2 5h13.6A1.7 1.7 0 0 1 20.5 6.7v7.6A1.7 1.7 0 0 1 18.8 16H12l-4.2 3.4V16H5.2a1.7 1.7 0 0 1-1.7-1.7V6.7A1.7 1.7 0 0 1 5.2 5z"/>', sw=1.8),
    'search': svg('<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>', sw=2.2),
    'x': svg('<path d="M8 8l8 8M16 8l-8 8"/>', sw=2.2),
    'arrow': svg('<path d="M12 5v11M7.5 11.5L12 16l4.5-4.5M6 19.5h12"/>', sw=2.2),
    'page': svg('<rect x="7.5" y="3.5" width="12" height="14.5" rx="2.4"/><path d="M4.5 7.5v10.2a2.8 2.8 0 0 0 2.8 2.8h8.2"/>', sw=1.9),
    'folder': svg('<path d="M3.5 7.8A2.3 2.3 0 0 1 5.8 5.5h3.4l2 2.1h7A2.3 2.3 0 0 1 20.5 9.9v7.3a2.3 2.3 0 0 1-2.3 2.3H5.8a2.3 2.3 0 0 1-2.3-2.3z"/>', sw=1.9),
    'check': svg('<circle cx="12" cy="12" r="8.5"/><path d="M8.3 12.3l2.6 2.6 5-5.3"/>', sw=1.9),
    'book': svg('<path d="M5 5.2A1.7 1.7 0 0 1 6.7 3.5H19v13.8H6.7A1.7 1.7 0 0 0 5 19zM5 19a1.7 1.7 0 0 0 1.7 1.7H19M9 7.5h6"/>', sw=1.9),
}
DOT = {'urgent': 'red', 'question': 'orange', 'done': 'green', 'info': 'gray', 'warn': 'orange'}

# ------------------------------------------------------------------ SAMPLE data (replace with real rows)
SAMPLE_WAIT = [
    ('urgent', 'Back up the raw clips before Friday', 'The camera card is the only copy of the 12 clips from Tuesday. Copy them to the archive drive, then check the file count matches.'),
    ('question', 'Which cover frame for the spring reel?', 'Three candidates are on the Spring Campaign page. Pick one and it goes into the upload.'),
    ('question', 'Is the 20% launch code still running?', 'It is burned into two of the end cards. If it has ended, those two need a re-render.'),
]
SAMPLE_DONE = [('done', 'Music for the spring reel: licensed track B', 'Answered 22 Sept. Track B is licensed for paid social; the receipt is in the project folder.')]
SAMPLE_PAGES = [  # (day label, name, workstream tile, tile text, status class, status label, description, needs you)
    ('Mon 28 Sept', 'Spring Campaign', 'tl-blue', 'SC', 'orange', 'Decision open', 'Three cover frames and the cut list for the spring reel.', True),
    ('Mon 28 Sept', 'Brand Kit', 'tl-yellow', I['star'], 'green', 'Current', 'Logos, colours and type for every job.', False),
    ('Fri 25 Sept', 'Summer Recap', 'tl-gray', 'SR', 'gray', 'Superseded', 'The first cut of the recap, kept for the record.', False),
]
SAMPLE_FILES = [  # (index, name, detail, path or None, download href or None, where)
    ('01', 'Spring reel: 15 s cut', '0:15 · 18.2 MB · 9:16', 'in /Projects/Spring/Exports/', 'https://example.com/spring-15s.mp4', None),
    ('02', 'Spring reel: 30 s cut', '0:30 · 34.9 MB · 9:16', 'in /Projects/Spring/Exports/', None, 'Dropbox'),
    ('03', 'Poster: spring launch', '1.4 MB · 1080×1920', 'save to /Projects/Spring/Posters/', None, 'In chat'),
]
SAMPLE_RULES = ['<b>One file per edit</b>, ready for the platform it is going to.',
                '<b>Nothing is delivered until it is in the archive</b>, not just in a chat.',
                '<b>Archive, never delete.</b> Superseded work stays reachable with a note on what replaced it.']


# ------------------------------------------------------------------ components
def pill(color, label):
    return f'<span class="pill p-{color}">{esc(label)}</span>'


def group(gid, title, detail, cells, footer='', cls=''):
    h = f'<div class="gh"><h2>{title}</h2>' + (f'<span class="gh-d">{detail}</span>' if detail else '') + '</div>'
    f = f'<p class="gfoot">{footer}</p>' if footer else ''
    return f'<section class="grp {cls}" id="{gid}">{h}<div class="list">{"".join(cells)}</div>{f}</section>'


def item(kind, title, body, cls='wi'):
    """A tappable row: title and a two-line preview; tapping opens the full text (a native <details>)."""
    return (f'<details class="cell dz {cls} s"><summary><span class="dot d-{DOT[kind]}">{I[kind]}</span>'
            f'<span class="dz-text"><span class="dz-title">{title}</span><span class="dz-pv">{esc(body)}</span></span>{CHEV}'
            f'</summary><div class="dz-body"><p>{body}</p></div></details>')


def callout(color, icon, title, body):
    return (f'<div class="cell callout s c-{color}"><span class="dot d-{color}">{I[icon]}</span>'
            f'<div><div class="co-title">{title}</div><div class="co-body">{body}</div></div></div>')


def page_row(name, tile_cls, tile, st_color, st_label, desc, needs, href='#'):
    na = ' data-needs="1"' if needs else ''
    return (f'<div class="cell pg s" data-ws="etc"{na}><a class="row-main" href="{href}">'
            f'<span class="tile {tile_cls}" aria-hidden="true">{tile}</span><span class="row-text"><span class="row-top">'
            f'<span class="row-title">{esc(name)}</span>{pill(st_color, st_label)}</span><span class="row-sub">{esc(desc)}</span>'
            f'</span>{CHEV}</a></div>')


def file_row(ix, name, detail, path, href, where):
    if href:
        acc = f'<a class="get" href="{href}" aria-label="Download {esc(name)}">Download</a>'
    else:
        acc = f'<span class="loc">{I["box"] if where == "Dropbox" else I["chat"]}{esc(where)}</span>'
    p = f'<span class="path">{esc(path).replace("/", "/<wbr>")}</span>' if path else ''   # long paths break after a slash
    return (f'<div class="cell file s"><span class="ix ix-mix">{esc(ix)}</span><span class="row-text">'
            f'<span class="row-title">{esc(name)}</span><span class="row-sub">{esc(detail)}</span>{p}</span>{acc}</div>')


# ------------------------------------------------------------------ panels
todo = ('<div class="tiles nosearch">'
        f'<button class="tl" data-go="todo" data-to="waiting"><span class="dot d-orange">{I["question"]}</span><span class="tl-n" data-count="wait"></span><span class="tl-l">Waiting on you</span></button>'
        f'<button class="tl" data-go="pages"><span class="dot d-blue">{I["page"]}</span><span class="tl-n" data-count="pages"></span><span class="tl-l">Pages</span></button>'
        f'<button class="tl" data-go="files"><span class="dot d-green">{I["arrow"]}</span><span class="tl-n">{len(SAMPLE_FILES)}</span><span class="tl-l">Finished files</span></button>'
        f'<button class="tl" data-go="files" data-to="sec-01"><span class="dot d-red">{I["box"]}</span><span class="tl-n">1</span><span class="tl-l">Not archived</span></button>'
        '</div>'
        + group('waiting', 'Waiting on you', f'{len(SAMPLE_WAIT)} open', [item(*w) for w in SAMPLE_WAIT],
                footer='Tap an item to read it in full.')
        + group('answered', 'Answered', f'{len(SAMPLE_DONE)} closed', [item(*d, cls='') for d in SAMPLE_DONE]))
days = {}
for d, *row in SAMPLE_PAGES:
    days.setdefault(d, []).append(page_row(*row))
pages = ('<div class="chips nosearch" role="group" aria-label="Filter pages">'
         '<button class="chip on" data-f="all" aria-pressed="true">All<span class="chip-n"></span></button>'
         '<button class="chip" data-f="needs" aria-pressed="false">Needs you<span class="chip-n"></span></button></div>'
         + group('pinned', 'Pinned', 'in your sidebar',
                 [f'<a class="cell pin" href="#"><span class="tile tl-yellow">{I["star"]}</span><span class="row-title">Brand Kit</span>{CHEV}</a>'], cls='nosearch')
         + f'<p class="roster nosearch" id="roster" data-gallery="{len(SAMPLE_PAGES)}" data-swept="28 Sept 2026">Counting…</p>'
         + '<div id="chron">' + ''.join(
             f'<section class="grp day"><div class="gh gh-sm"><h3>{d}</h3><span class="gh-d">{len(r)} page{"s" if len(r) > 1 else ""}</span></div>'
             f'<div class="list">{"".join(r)}</div></section>' for d, r in days.items()) + '</div>')
files = ('<div class="stats nosearch">' + ''.join(
    f'<div class="st-c"><span class="st-n">{n}</span><span class="st-l">{k}</span></div>'
    for n, k in (('2', 'Reels'), ('1', 'Posters'), ('54<small> MB</small>', 'Total'))) + '</div>'
         + '<p class="lede nosearch">Every finished file: a <b>Download</b> button where there is a public link, otherwise the folder it lives in.</p>'
         + group('sec-01', '<span class="secno">01</span>Spring Campaign', f'{len(SAMPLE_FILES)} files · 54 MB',
                 [callout('red', 'urgent', 'One file is not archived yet', 'The poster exists only in the chat. Save it to the folder named on its row.'),
                  item('info', 'About this folder', 'The spring launch: two reel lengths and one poster, approved 26 Sept.', cls='')]
                 + [file_row(*f) for f in SAMPLE_FILES]))
rules = group('rules-0', 'House rules', '', [f'<div class="cell rule s"><span class="bullet" aria-hidden="true"></span><p>{r}</p></div>' for r in SAMPLE_RULES])

TABS = [('todo', 'To Do', I['check'], todo), ('pages', 'Pages', I['page'], pages), ('files', 'Files', I['folder'], files),
        ('rules', 'Rules', I['book'], rules)]
body = ''.join(f'<section class="panel" id="p-{k}" data-title="{t}" aria-label="{t}"><h2 class="panel-h">{t}</h2>{c}</section>'
               for k, t, _, c in TABS)
tabbar = ('<nav class="tabbar" aria-label="Sections"><div class="tb-in">' + ''.join(
    f'<button class="tab" data-tab="{k}" aria-controls="p-{k}">{ic}<span>{t}</span>'
    + ('<span class="badge" data-count="wait"></span>' if k == 'todo' else '') + '</button>' for k, t, ic, _ in TABS) + '</div></nav>')
css = open(os.path.join(HERE, 'style.css'), encoding='utf-8').read()
js = open(os.path.join(HERE, 'app.js'), encoding='utf-8').read()
page = f'''<title>Studio Index</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<style>{css}</style>
<header class="nav" id="nav"><div class="nav-in"><span></span><span class="nav-title" id="navTitle">To Do</span>
<button class="nav-btn" id="navSearch" aria-label="Search">{I['search']}</button></div></header>
<main class="main">
<div class="hero"><p class="over">Studio Index · example content</p><h1 id="bigTitle">To Do</h1>
<div class="search" role="search"><label class="sf">{I['search']}<input id="q" type="search" placeholder="Search pages, files and questions" autocomplete="off" spellcheck="false" aria-label="Search everything"></label>
<button class="sf-x" id="qx" aria-label="Clear search" hidden>{I['x']}</button></div>
<p class="results" id="results" hidden></p></div>
{body}
<div class="empty" id="empty" hidden>{I['search']}<p class="e-t">No results</p><p class="e-s">Nothing matches that.</p></div>
<footer class="foot"><p>Example content. Replace the SAMPLE rows in example_page.py with real ones.</p></footer>
</main>
{tabbar}
<script>{js}</script>
'''
open(os.path.join(HERE, 'example.html'), 'w', encoding='utf-8').write(page)
print('wrote example.html', len(page) // 1024, 'KB')
