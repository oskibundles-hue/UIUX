"""
Build the Supercar Experience deliverables page + DELIVERY.md from one list.

Kit bundles and stills are served straight from GitHub (raw links resolve
without auth). Rendered MP4s are gitignored, so they are hosted separately;
their URLs come from 09-campaign-ads/hosted.json when it exists, otherwise
the rows say "hosting pending". Re-run after hosting to fill them in.
"""
import json, html
from pathlib import Path
K = Path(__file__).resolve().parent
RAW = "https://raw.githubusercontent.com/oskibundles-hue/UIUX/claude/skills-download-ai3m6a/supercar-experience"
TREE = "https://github.com/oskibundles-hue/UIUX/tree/claude/skills-download-ai3m6a/supercar-experience"
hosted = json.loads((K / "09-campaign-ads/hosted.json").read_text()) if (K / "09-campaign-ads/hosted.json").exists() else {}

def mb(p): return f"{p.stat().st_size/1048576:.1f} MB"
def gh(rel): return f"{RAW}/{rel}"

BUNDLES = [
 ("SCE-00-VERTICAL-STARTER-PACK.zip", "The 9:16 set on its own - bugs, lower thirds, CTAs, titles, end cards"),
 ("SCE-08-ALL-OVERLAYS.zip", "Every overlay in every format, plus the safe-zone guides"),
 ("SCE-10-rental-overlays.zip", "Price stacks and pills for all 18 cars, requirements, locations, promos, Tempesta specs, Rally plate"),
 ("SCE-02-lower-thirds.zip", "Car name + listed price, 18 cars, 9:16 and 16:9"),
 ("SCE-01-logo-bugs.zip", "Wordmark and mark, white and black, every corner, four canvases"),
 ("SCE-05-cta-captions.zip", "16 CTAs in panel and bar styles"),
 ("SCE-03-title-cards.zip", "Ten stacked titles, white over gold"),
 ("SCE-04-end-cards.zip", "Stacked lockup, tagline, site, handle"),
 ("SCE-06-service-badges.zip", "Chips for the three priority cars"),
 ("SCE-07-accent-bars.zip", "The gold/white rule at every width"),
 ("SCE-09-logos.zip", "12 PNG lockups: horizontal, mark, wordmark, stacked - white, black, gold"),
]
ADS = [("a-price","$1,299. Four hours.","Price leads. For the viewer who wants the car and needs the figure."),
       ("b-experience","A ride of a lifetime.","The site's tagline. Identity over arithmetic."),
       ("c-occasion","Vegas this weekend? Arrive in this.","Weddings, race week, photoshoots - the uses the site names."),
       ("d-offer","50% off day two. Or day three free.","The promo exactly as the site prints it."),
       ("e-engage","4 hours or 24?","A question that earns comments. Not a sales CTA.")]
STILLS = ["still-02_60s.jpg","still-06_50s.jpg","still-11_50s.jpg","still-13_80s.jpg"]
STILL_CAP = ["2.6s - hook","6.5s - the deal","11.5s - CTA","13.8s - end card"]

def row(name, desc, size, url, pending=False):
    btn = (f'<a class="dl" href="{url}" target="_blank" rel="noopener">Download</a>' if url
           else '<span class="dl pending">Hosting pending</span>')
    return f'<li class="row"><div class="f"><code>{html.escape(name)}</code><p>{html.escape(desc)}</p></div><span class="sz">{size}</span>{btn}</li>'

kit_rows = [row(n, d, mb(K/"08-download-bundles"/n), gh(f"08-download-bundles/{n}")) for n,d in BUNDLES]
ad_rows = []
for v, hook, angle in ADS:
    fn = f"supercar-experience-porsche-gt3rs-15s-9x16{'' if v=='a-price' else '-'+v}.mp4"
    p = K/"09-campaign-ads/porsche-gt3rs/exports"/fn
    ad_rows.append(row(fn, f"{hook}  {angle}", mb(p) if p.exists() else "-", hosted.get(v)))
def inline(rel, w=420):
    """Stills are embedded as data URIs (the artifact viewer blocks images from other hosts)."""
    import base64, io
    from PIL import Image
    im = Image.open(K/rel).convert("RGB"); im.thumbnail((w, w*2))
    b = io.BytesIO(); im.save(b, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
stills = "".join(f'<figure><img src="{inline("09-campaign-ads/porsche-gt3rs/exports/"+s)}" alt="{c}"><figcaption>{c}</figcaption></figure>' for s,c in zip(STILLS,STILL_CAP))
n_ov = sum(1 for _ in (K/"03-overlays").rglob("*.png"))

page = f'''<title>Supercar Experience Deliverables</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--ground:#08080A;--panel:#111114;--rule:#26262C;--ink:#F3F2EF;--ink-2:#B4B3AE;--ink-3:#77767F;--gold:#FBD101;--display:'Bebas Neue','Arial Narrow',sans-serif;--body:'Barlow','Helvetica Neue',Arial,sans-serif;--mono:'IBM Plex Mono',Consolas,monospace}}
body{{background:var(--ground);color:var(--ink);font:16px/1.6 var(--body);margin:0;padding:0 clamp(18px,4vw,48px) 96px}}
.wrap{{max-width:1080px;margin:0 auto}}
header{{padding:clamp(36px,6vw,72px) 0 0;border-bottom:1px solid var(--rule)}}
.eyebrow{{font:11px var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--ink-3);margin:0 0 14px}}.eyebrow b{{color:var(--gold);font-weight:500}}
h1{{font:400 clamp(48px,9vw,104px)/.9 var(--display);margin:0;text-wrap:balance}}h1 .sub{{display:block;color:var(--ink-3)}}
.stripe{{display:flex;height:10px;width:min(100%,520px);margin:22px 0 26px}}.stripe span:first-child{{width:78%;background:var(--gold)}}.stripe span:last-child{{width:22%;background:#fff}}
.lede{{max-width:66ch;font-size:18px;color:var(--ink-2);margin:0 0 34px}}
.readout{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));border-top:1px solid var(--rule);border-left:1px solid var(--rule)}}
.readout div{{border-right:1px solid var(--rule);border-bottom:1px solid var(--rule);padding:14px 16px}}.readout .n{{font:400 38px/1 var(--display);font-variant-numeric:tabular-nums;display:block}}.readout .k{{font:10.5px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3);display:block;margin-top:6px}}
section{{padding:clamp(40px,6vw,64px) 0 0}}
.shead{{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid var(--rule);padding-bottom:10px;margin-bottom:8px}}.shead .tag{{font:11px var(--mono);letter-spacing:.18em;color:var(--gold);text-transform:uppercase;flex:none}}
h2{{font:400 clamp(28px,4.4vw,42px)/1 var(--display);margin:0}}
.dest{{font:12px var(--mono);color:var(--ink-3);margin:0 0 18px}}.dest b{{color:var(--ink-2);font-weight:500}}
ul.list{{list-style:none;margin:0;padding:0}}
.row{{display:grid;grid-template-columns:1fr auto auto;gap:18px;align-items:center;padding:14px 0;border-bottom:1px solid var(--rule)}}
.row .f{{min-width:0}}.row code{{font:500 14px var(--mono);color:var(--ink);word-break:break-all}}.row p{{margin:3px 0 0;font-size:14px;color:var(--ink-2)}}
.sz{{font:13px var(--mono);color:var(--ink-3);font-variant-numeric:tabular-nums;white-space:nowrap}}
.dl{{font:600 13px var(--body);letter-spacing:.06em;text-transform:uppercase;background:var(--gold);color:#000;padding:10px 18px;border-radius:999px;text-decoration:none;white-space:nowrap}}.dl:hover{{background:#fff}}.dl:focus-visible{{outline:2px solid #fff;outline-offset:3px}}
.dl.pending{{background:transparent;color:var(--ink-3);border:1px solid var(--rule)}}
.stills{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0 6px}}.stills figure{{margin:0}}.stills img{{width:100%;display:block;border:1px solid var(--rule)}}.stills figcaption{{font:11px var(--mono);color:var(--ink-3);margin-top:6px;letter-spacing:.06em}}
.note{{border-left:3px solid var(--gold);background:var(--panel);padding:16px 20px;margin:22px 0;max-width:66ch}}.note .lab{{font:10.5px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:6px}}.note p{{margin:0 0 .6em;color:var(--ink-2)}}.note p:last-child{{margin:0}}.note b{{color:var(--ink);font-weight:600}}
footer{{margin-top:64px;border-top:1px solid var(--rule);padding-top:18px;font:11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);display:flex;flex-wrap:wrap;gap:8px 24px}}footer a{{color:var(--ink-2);text-decoration-color:var(--gold)}}
@media(max-width:560px){{.row{{grid-template-columns:1fr auto}}.sz{{display:none}}}}
</style>
<div class="wrap">
<header>
<p class="eyebrow">Supercar Experience <b>//</b> Brand kit &amp; rental ads <b>//</b> 9 Sept 2026</p>
<h1>Deliverables<span class="sub">Kit &amp; GT3 RS ads</span></h1>
<div class="stripe" aria-hidden="true"><span></span><span></span></div>
<p class="lede">A brand kit built on the same toolkit as the Formula Dynamics kit, and five rental ads for the GT3 RS cut from your own footage. Every price, spec and promo on screen was read off supercarexp.vip. One tap per file, real filenames, filed by the Dropbox folder each belongs in.</p>
<div class="readout"><div><span class="n">{n_ov}</span><span class="k">Overlays</span></div><div><span class="n">18</span><span class="k">Cars priced</span></div><div><span class="n">15</span><span class="k">Ad cues</span></div><div><span class="n">5</span><span class="k">GT3 RS spots</span></div><div><span class="n">11</span><span class="k">Bundles</span></div></div>
</header>

<section>
<div class="shead"><span class="tag">01 / Ads</span><h2>Porsche 911 GT3 RS - five angles</h2></div>
<p class="dest">File under <b>Portfolio / 01 Business Ads / Supercar Experience</b></p>
<div class="stills">{stills}</div>
<ul class="list">{"".join(ad_rows)}</ul>
<div class="note"><span class="lab">What is on screen</span><p><b>$1,299 / 4 hrs and $1,799 / 24 hrs</b> are the GT3 RS's listed prices. Locations, the text number, 21+ / licence / insurance, and "50% off 2nd day or 3rd day free" are all from the site. Plate is 84-99s of "gt3 rolling in", graded with your NQ Signature LUT; the four-look A/B and the zone measurements are in the repo under exports/decision.</p><p>750S Spider and Tempesta cues are written and dry-run clean; they render the moment their plates exist. The 750S runs on the 765LT footage and the Tempesta on the Roma, named as the site lists them.</p></div>
</section>

<section>
<div class="shead"><span class="tag">02 / Kit</span><h2>Overlays, logos, bundles</h2></div>
<p class="dest">File under <b>Portfolio / 04 Brand and Creative Systems / Supercar Experience</b></p>
<ul class="list">{"".join(kit_rows)}</ul>
<div class="note"><span class="lab">Using it</span><p>Drop any PNG onto a CapCut timeline at 1080x1920 and it is already in position. Lower thirds carry each car's listed price; the rental folder has the price stacks where the price is the headline. Gold #FBD101 is the one accent - the same gold as your reel highlights.</p></div>
</section>

<footer><span><b>Repo</b> <a href="{TREE}" target="_blank" rel="noopener">supercar-experience/</a></span><span><b>Rebuild</b> 99-toolkit/build_all.py</span><span><b>Re-cut</b> 09-campaign-ads/make_cues.py</span></footer>
</div>
'''
out = Path("/tmp/claude-0/-home-user-UIUX/bca660b1-ddd0-53c0-87e3-b329cd9a583e/scratchpad/sce/deliverables.html")
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(page); print("page:", out, f"{len(page)/1024:.0f} KB")

md = ["# Supercar Experience - DELIVERY", "", "Filed 2026-09-09. Kit and GT3 RS ads. Every on-screen figure from supercarexp.vip.", "",
      "## 01 Business Ads / Supercar Experience", ""]
for v, hook, angle in ADS:
    fn = f"supercar-experience-porsche-gt3rs-15s-9x16{'' if v=='a-price' else '-'+v}.mp4"
    md.append(f"- `{fn}` - {hook} - {angle}" + (f" - {hosted[v]}" if v in hosted else " - hosting pending"))
md += ["", "## 04 Brand and Creative Systems / Supercar Experience", ""]
md += [f"- `{n}` ({mb(K/'08-download-bundles'/n)}) - {d} - {gh('08-download-bundles/'+n)}" for n,d in BUNDLES]
md += ["", "## Source", "", f"- {TREE}", "- Rebuild the kit: `python3 99-toolkit/build_all.py`", "- Re-cut an ad: edit `09-campaign-ads/make_cues.py`, then `python3 build_ad.py --car <slug> --all`", ""]
(K / "DELIVERY.md").write_text("\n".join(md)); print("DELIVERY.md written")
