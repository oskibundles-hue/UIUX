#!/usr/bin/env python3
"""Build the two stand-alone pages of the Supercar Experience site from the main page.

  11-website/fleet/index.html    every rental car, the car bay, compare, the trip builder, the car ads, booking
  11-website/vlogs/index.html    Behind the Wheel: every episode, the full player, the moments and the route maps

Both pages take their look (the whole <style> block), their data (EP[], cars[], DEAL, the ads list) and their
scripts straight out of ../11-website/index.html, so the rates, the cars and the episodes can't drift from the
main page. Only the page frame (nav, hero, section order, the start-up lines) lives here.

    python3 make_section_pages.py

Run it after any change to index.html (a rate, a car, an episode, a style) and commit fleet/ and vlogs/ with it.
No Chrome or ffmpeg needed. It stops with an error if a piece it cuts out of index.html has moved or changed.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, '..', '11-website'))
BASE = 'https://supercar-experience-garage.onrender.com'
SRC = open(os.path.join(SITE, 'index.html'), encoding='utf-8').read()
JS = SRC[SRC.index('<script>\nconst M="media/";'):]  # the main page's script; the CSS reuses its section titles


def cut(start, end, src=JS):
    """The text from `start` up to (not including) `end`. Fails loudly if either marker is missing."""
    i = src.find(start)
    if i < 0:
        sys.exit(f'make_section_pages: marker not found in index.html: {start[:60]!r}')
    j = src.find(end, i + len(start))
    if j < 0:
        sys.exit(f'make_section_pages: end marker not found in index.html: {end[:60]!r}')
    return src[i:j]


def swap(text, old, new):
    if old not in text:
        sys.exit(f'make_section_pages: expected text not found: {old[:70]!r}')
    return text.replace(old, new)


def section(sid):
    """One <section ... id="sid"> ... </section> block of the main page, as written there."""
    m = re.search(r'<section[^>]*\bid="%s"[^>]*>.*?\n</section>\n' % re.escape(sid), SRC, re.S)
    if not m:
        sys.exit(f'make_section_pages: section #{sid} not found in index.html')
    return m.group(0)


# ---------- shared pieces ----------
FONTS = cut('<link rel="preconnect" href="https://fonts.googleapis.com">', '<style>', SRC)
CSS = cut('<style>', '</style>', SRC) + '</style>'
JS_DATA = swap(cut('const M="media/";', '/* ---------- kinetic type'), 'const M="media/";', 'const M="../media/";')
JS_CORE = swap(cut('/* ---------- kinetic type', '/* ---------- ticker + marquee + stats'),
               'document.getElementById("deal-all").textContent=DEAL;',
               '{const d=document.getElementById("deal-all");if(d)d.textContent=DEAL}')
JS_WALL = cut('/* ---------- hero wall', '/* ---------- latest episode card')
JS_TAIL = cut('/* ---------- copy number, menu, active section, side tab', '/* ---------- on the road: two runs')
# the main page observes a fixed list of section ids; each page here has only some of them
JS_TAIL = re.sub(r'\]\.forEach\(id=>(secIO|sideIO)\.observe\(document\.getElementById\(id\)\)\)',
                 r'].map(id=>document.getElementById(id)).filter(Boolean).forEach(el=>\1.observe(el))', JS_TAIL)
if JS_TAIL.count('.filter(Boolean)') != 2:
    sys.exit('make_section_pages: the section observers in index.html have changed')

BOOK = swap(section('book'), 'href="posts/', 'href="../posts/')
BAY_TRAY = cut('<div class="tray" id="tray"', '<script>\nconst M=', SRC)

PAGE_CSS = """<style>
/* stand-alone pages (fleet/, vlogs/): made by website-tools/make_section_pages.py */
.hero.page{min-height:min(78vh,820px)}
.nav .links a.here{color:#fff}
.nav .links a.here::after{transform:scaleX(1)}
.epgrid{grid-auto-flow:row;grid-template-columns:repeat(auto-fill,minmax(min(100%,236px),1fr));overflow:visible;scroll-snap-type:none;cursor:auto;gap:34px 22px}
.cross{background:var(--carbon);padding:clamp(64px,8vw,104px) 0;border-top:1px solid var(--d-line)}
.cross .wrap{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:clamp(24px,4vw,56px);align-items:end}
.cross h2{font-size:clamp(2.4rem,5vw,4.6rem);margin:16px 0 18px}
.cross .acts{display:flex;gap:12px;flex-wrap:wrap;justify-self:end}
@media (max-width:900px){.cross .wrap{grid-template-columns:1fr}.cross .acts{justify-self:start}}
@media (max-width:560px){.epgrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:28px 14px}.epgrid .epc .num{font-size:3.4rem;left:-6px;bottom:60px}.epgrid .epc h3{font-size:1.05rem}.epgrid .epc .watch{right:8px;bottom:10px;padding:7px 10px 7px 8px;font-size:11px}.epgrid .epc .meta{left:8px;right:8px;top:8px}}
</style>
"""


def head(path, title, desc, og_title, og_desc, og_img='media/share/series.jpg'):
    url = f'{BASE}/{path}'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Supercar Experience">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:image" content="{BASE}/{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="{BASE}/{og_img}">
<meta name="theme-color" content="#0A0A0C">
<script>document.documentElement.classList.add("js")</script>
{FONTS}{CSS}
{PAGE_CSS}</head>
<body>
"""


def nav(here, links, sheet, cta):
    cur = ' class="here" aria-current="page"'
    lk = ''.join(f'<a href="{h}"{cur if n == here else ""}>{n}</a>' for n, h in links)
    sh = ''.join(f'<a href="{h}">{n} <span>{i + 1:02d}</span></a>' for i, (n, h) in enumerate(sheet))
    return f"""<header class="nav">
  <div class="wrap">
    <a class="logo" href="../" aria-label="Supercar Experience, home"><img src="../media/brand/sce-primary-horizontal--white.png" alt="Supercar Experience" width="185" height="26"></a>
    <nav class="links" aria-label="Pages">{lk}</nav>
    <div class="nav-r">
      {cta}
      <button class="menu-b" id="menu-b" type="button" aria-expanded="false" aria-controls="sheet" aria-label="Menu"><span></span></button>
    </div>
  </div>
  <div class="wrap sheet" id="sheet" hidden>
    {sh}
  </div>
</header>
"""


def footer():
    return """<footer><div class="wrap"><img src="../media/brand/sce-primary-horizontal--white.png" alt="Supercar Experience" width="156" height="22" loading="lazy"><nav aria-label="Footer"><a href="../">Home</a><a href="../vlogs/">All episodes</a><a href="../fleet/">The fleet</a><a href="../posts/renting-a-supercar-in-las-vegas/">Renting guide</a><a href="../#rally">Rally</a></nav><span>Filmed and cut by Omarie Young · <a href="https://www.instagram.com/nq.young/" target="_blank" rel="noopener">@nq.young</a></span></div></footer>

<a class="side off" id="side" href="#book">Text to book<svg class="i" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 12 12 4M5.5 4H12v6.5"/></svg></a>
"""


ARW = '<span class="ar" aria-hidden="true"><svg class="i" viewBox="0 0 16 16"><path d="M4 12 12 4M5.5 4H12v6.5"/></svg></span>'
PLAY_AR = '<span class="ar" aria-hidden="true"><svg class="i" viewBox="0 0 16 16" style="fill:currentColor;stroke:none"><path d="M5 3.2v9.6L13 8z"/></svg></span>'
LINKS = [('Home', '../'), ('All episodes', '../vlogs/'), ('The fleet', '../fleet/'), ('Price a drive', '../fleet/#build'), ('Book', '#book')]


# ---------- fleet/ ----------
def fleet():
    fleet_sec = section('fleet')
    ads_sec = swap(section('ads'), 'Cut from the same footage. Tap a reel to play it with sound.',
                   'The cars on air. Tap a reel to play it with sound.')
    html = head('fleet/', 'The Fleet · Exotic Car Rental Las Vegas · Supercar Experience',
                'Every exotic, super SUV and luxury car Supercar Experience rents in Las Vegas, with day and 5-hour rates, videos, a side-by-side compare and a trip price. Text to book.',
                'The Fleet · Supercar Experience Las Vegas',
                'Every car we rent in Las Vegas, with the rates. Pick one and text to book.')
    html += """<a class="skip" href="#fleet">Skip to the cars</a>
<div class="sprog" id="sprog" aria-hidden="true"></div>

<div class="util"><div class="wrap"><span class="u-l new"><b>New</b><span id="u-new"></span></span><span>Rentals: <a href="#book">Text (725) 425-3583</a></span></div></div>

"""
    html += nav('The fleet', LINKS, LINKS[:4] + [('Book', '#book')],
                f'<a class="btn" href="#book"><span class="t">Text to book</span><span class="t2">Book</span>{ARW}</a>')
    html += f"""
<section class="hero page" id="top" aria-label="The fleet">
  <div class="wall" id="wall" aria-hidden="true"></div>
  <div class="grain" aria-hidden="true"></div>
  <div class="wrap">
    <div>
      <div class="eyebrow rv">[ Exotic car rental <b>·</b> Las Vegas ]</div>
      <h1 class="kin">The <span class="o">fleet.</span></h1>
      <p class="lede rv">Exotics, super SUVs and luxury cars out of Las Vegas, by the hour or the day. Every car we rent, with the rates. Tap one for its video and price, or compare two side by side.</p>
      <div class="ctas rv">
        <a class="btn" href="#fleet">See the cars<span class="ar" aria-hidden="true"><svg class="i" viewBox="0 0 16 16"><path d="M4 12 12 4M5.5 4H12v6.5"/></svg></span></a>
        <a class="btn ghost" href="#build">Price a drive{ARW}</a>
      </div>
      <div class="stats rv" id="stats"></div>
    </div>
    <aside class="showing rv" aria-label="Featured car">
      <div class="scr" id="sh-scr">
        <img id="sh-img" alt="">
        <div class="lk on"><i></i><i></i><i></i><i></i></div>
        <div class="top"><span class="tag">Featured</span><span class="tag dim" id="sh-len"></span></div>
        <button class="pplay" type="button" id="sh-play" aria-label="Open the featured car"><svg viewBox="0 0 16 16"><path d="M4 2.5v11L13.5 8z"/></svg></button>
        <div class="cap"><small id="sh-meta"></small><b id="sh-title"></b></div>
      </div>
    </aside>
  </div>
  <div class="scroll-cue" aria-hidden="true">Scroll<i></i></div>
</section>

<main id="main">
{fleet_sec}
{ads_sec}
<section class="cross" id="series" aria-label="The vlog series">
  <div class="wrap">
    <div>
      <div class="eyebrow">[ Behind the wheel <b>·</b> the vlog series ]</div>
      <h2 class="kin">See what it takes to <span class="o">hand over the keys.</span></h2>
      <p class="lede">The pickups, the deliveries, a flat tyre at night and a rally, filmed on the day and shown in full.</p>
    </div>
    <div class="acts"><a class="btn" href="../vlogs/">Watch the episodes{PLAY_AR}</a></div>
  </div>
</section>

{BOOK}</main>

{footer()}
{BAY_TRAY}"""
    wall = swap(JS_WALL, 'const pool=[...EP.map(e=>({v:M+"ep/"+e.k+"-loop.mp4",p:M+"ep/"+e.k+".jpg",n:"EP "+pad(e.n)})),...CARS_STILL.map(id=>({p:M+"stills/"+id+".jpg"}))];',
                '/* fleet/: only the clean driving frames of the cars, no vlog footage on the rentals (Omarie, 29 Sept) */\n  const pool=CARS_STILL.map(id=>({p:M+"stills/"+id+".jpg"}));')
    html += f"""<script>
{JS_DATA}/* fleet/ has no episode player: the ads row and the car bay only check whether it is playing */
const pv={{paused:true,pause(){{}}}};function pvBusy(){{return false}}

{JS_CORE}{cut('/* ---------- ads', '/* ---------- car bay')}{cut('/* ---------- car bay', '/* ---------- rally countdown')}{wall}
/* ---------- newest episode, stats, featured car ---------- */
$("#u-new").innerHTML=`Episode ${{LATEST.n}}: <a href="../vlogs/#watch-${{LATEST.k}}">${{LATEST.t}}</a>`;
const FEAT=cars.find(c=>c.id==="gt3")||cars[0];
const lowDay=Math.min(...cars.map(c=>c.day));
$("#stats").innerHTML=[[String(cars.length),"Cars in Las Vegas"],[money(lowDay),"Lowest day rate"],["25+","To drive"]].map(s=>`<div><b${{/\\d/.test(s[0])?` data-reel="${{s[0]}}"`:""}}>${{s[0]}}</b><small>${{s[1]}}</small></div>`).join("");
$("#sh-img").src=FEAT.photo?M+FEAT.photo:M+"stills/"+FEAT.id+".jpg";
$("#sh-len").textContent=money(FEAT.day)+"/day";
$("#sh-meta").textContent=FEAT.yr+" · "+FEAT.make;$("#sh-title").textContent=FEAT.name;
$("#sh-play").onclick=()=>openBay(FEAT.id);

{JS_TAIL}/* ---------- start ---------- */
renderGarage();calc();watch();
/* a link straight to one car: fleet/#car-gt3 (or ?car=gt3) opens its bay */
const deepCar=(location.hash.match(/^#car-([a-z0-9]+)/)||[])[1]||new URLSearchParams(location.search).get("car");
if(deepCar&&cars.some(c=>c.id===deepCar))setTimeout(()=>{{$("#fleet").scrollIntoView({{block:"start"}});openBay(deepCar)}},120);
</script>
</body>
</html>
"""
    return html


# ---------- vlogs/ ----------
def vlogs():
    rail_sec = section('episodes')
    rail_sec = re.sub(r'\s*<div class="rail-nav rv">.*?</div>\n', '\n', rail_sec, flags=re.S)
    rail_sec = swap(rail_sec, '<div class="rail" id="rail" role="list">', '<div class="rail epgrid" id="rail" role="list">')
    rail_sec = swap(rail_sec, '<div class="wrap rail-wrap">', '<div class="wrap">')
    cross = f"""<section class="cross" id="rent" aria-label="Rent the cars">
  <div class="wrap">
    <div>
      <div class="eyebrow">[ Rentals <b>·</b> Las Vegas ]</div>
      <h2 class="kin">Seen a car you like? <span class="o">Drive it.</span></h2>
      <p class="lede">Every car we rent in Las Vegas, by the hour or the day, with the rates. Pick one and text to book.</p>
    </div>
    <div class="acts"><a class="btn" href="../fleet/">See the fleet{ARW}</a></div>
  </div>
</section>
"""
    html = head('vlogs/', 'Behind the Wheel · Every Episode · Supercar Experience Las Vegas',
                'Behind the Wheel, the Supercar Experience vlog series: every episode in full, with chapters, from the pickups and hand-overs to a flat tyre at night and rally day.',
                'Behind the Wheel · Every Episode',
                'What it takes to put the keys in your hand. Every episode, filmed on the day and shown in full.')
    html += """<a class="skip" href="#watch">Skip to the episode player</a>
<div class="sprog" id="sprog" aria-hidden="true"></div>

<div class="util"><div class="wrap"><span class="u-l new"><b>New</b><span id="u-new"></span></span><span>Rentals: <a href="#book">Text (725) 425-3583</a></span></div></div>

"""
    links = [('Home', '../'), ('All episodes', '../vlogs/'), ('Watch', '#watch'), ('Routes', '#routes'), ('The fleet', '../fleet/')]
    html += nav('All episodes', links, links + [('Book', '#book')],
                f'<a class="btn play" href="#watch" data-ep="latest"><span class="t">Watch the latest</span><span class="t2">Watch</span>{PLAY_AR}</a>')
    html += f"""
<section class="hero page" id="top" aria-label="Behind the Wheel, every episode">
  <div class="wall" id="wall" aria-hidden="true"></div>
  <div class="grain" aria-hidden="true"></div>
  <div class="wrap">
    <div>
      <div class="eyebrow rv">[ Behind the wheel <b>·</b> the vlog series ]</div>
      <h1 class="kin">Every <span class="o">episode.</span></h1>
      <p class="lede rv">What it takes to put the keys in your hand. The pickups, the hand-overs, a flat tyre at night and a rally, filmed on the day and shown in full.</p>
      <div class="ctas rv">
        <a class="btn play" href="#watch" data-ep="latest">Watch the latest{PLAY_AR}</a>
        <a class="btn ghost down" href="#episodes">All episodes<span class="ar" aria-hidden="true"><svg class="i" viewBox="0 0 16 16"><path d="M4 12 12 4M5.5 4H12v6.5"/></svg></span></a>
      </div>
      <div class="stats rv" id="stats"></div>
    </div>
    <aside class="showing rv" aria-label="Latest episode">
      <div class="scr" id="sh-scr">
        <img id="sh-img" alt="">
        <video id="sh-vid" muted loop playsinline preload="none" aria-hidden="true"></video>
        <div class="lk on"><i></i><i></i><i></i><i></i></div>
        <div class="top"><span class="tag">Latest</span><span class="tag dim" id="sh-len"></span></div>
        <button class="pplay" type="button" id="sh-play" aria-label="Play the latest episode"><svg viewBox="0 0 16 16"><path d="M4 2.5v11L13.5 8z"/></svg></button>
        <div class="cap"><small id="sh-meta"></small><b id="sh-title"></b></div>
      </div>
    </aside>
  </div>
  <div class="scroll-cue" aria-hidden="true">Scroll<i></i></div>
</section>

<div class="marq" aria-label="Episode titles"><div class="mq-track" id="mq"></div></div>

<main id="main">
{rail_sec}
{section('watch')}
{section('bts')}
{section('routes')}
{cross}
{BOOK}</main>

{footer()}
"""
    theatre = swap(cut('/* ---------- theatre: full episodes', '/* ---------- behind the scenes'),
                   'new URL("ep/"+cur.k+"/",', 'new URL("../ep/"+cur.k+"/",')
    html += f"""<script>
{JS_DATA}{JS_CORE}{cut('/* ---------- ticker + marquee + stats', '/* ---------- hero wall')}{JS_WALL}{cut('/* ---------- latest episode card', '/* ---------- episodes rail')}{cut('/* ---------- episodes rail', '/* drag to scroll the rail')}/* vlogs/ shows every episode in a grid, so there is no rail to drag */
let railDragged=false;

/* the rent links in the chapter list open that car on the fleet page */
function openBay(id){{location.href="../fleet/#car-"+id}}
{theatre}{cut('/* ---------- behind the scenes', '/* ---------- ads')}{JS_TAIL}{cut('/* ---------- on the road: two runs', '/* ---------- start')}/* ---------- start ---------- */
renderRail();watch();
const deep=(location.hash.match(/^#watch-([a-z0-9]+)/)||[])[1];
openEp(EP.some(e=>e.k===deep)?deep:LATEST.k,{{quiet:true}});
if(deep)setTimeout(()=>$("#watch").scrollIntoView({{block:"center"}}),50);
$("#th-title").classList.add("in");
</script>
</body>
</html>
"""
    return html


for name, build in (('fleet', fleet), ('vlogs', vlogs)):
    out = os.path.join(SITE, name)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(build())
    print(f'wrote {name}/index.html')
