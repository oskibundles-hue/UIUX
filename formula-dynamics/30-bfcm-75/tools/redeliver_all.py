#!/usr/bin/env python3
"""Re-render carousels from source/ straight into the Drive delivery folder, one browser, one slot at a time,
so every exports/<date>/<slot>/ matches source/<date>/<slot>/ exactly. Then sync the editable source, rebuild
PROGRESS.md and the merged ledger, and verify the delivery.

Usage: redeliver_all.py DELIVERY_DIR [--dates 2026-11-20,2026-11-21 ...] [--verify-only]
Verification: every slot has 01-03.jpg at 1080x1350 and a Caption.txt identical to source; no two slots share
a slide (md5); writes out/delivery-manifest.json (source hash -> export md5) for later drift checks."""
import sys, io, json, hashlib, pathlib, shutil, subprocess, argparse
from PIL import Image, ImageCms

HERE = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("delivery"); ap.add_argument("--dates", default=""); ap.add_argument("--verify-only", action="store_true")
a = ap.parse_args()
DEL = pathlib.Path(a.delivery)
want = set(filter(None, a.dates.split(",")))
slots = sorted(p for p in (HERE / "source").glob("2026-*/[1-5]_*") if p.is_dir() and (not want or p.parent.name in want))

def src_hash(p):
    h = hashlib.md5()
    for f in sorted(p.glob("slide-0[123].html")) + [p / "Caption.txt"]:
        h.update(f.read_bytes())
    return h.hexdigest()

if not a.verify_only:
    from playwright.sync_api import sync_playwright
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for p in slots:
            out = DEL / "exports" / p.parent.name / p.name
            out.mkdir(parents=True, exist_ok=True)
            for i in (1, 2, 3):
                pg.goto((p / f"slide-0{i}.html").resolve().as_uri()); pg.wait_for_load_state("networkidle")
                pg.evaluate("document.fonts.ready")
                im = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGB")
                assert im.size == (1080, 1350), (p, i, im.size)
                im.save(out / f"0{i}.jpg", quality=95, subsampling=0, icc_profile=srgb)
            shutil.copy(p / "Caption.txt", out / "Caption.txt")
            shutil.rmtree(out / "_phone", ignore_errors=True)
            print("delivered", p.parent.name, p.name, flush=True)
        b.close()
    subprocess.run(["rsync", "-a", "--exclude", ".DS_Store", "--exclude", "ref", "--exclude", "out",
                    "source", "assets", "tools", str(DEL / "editable source") + "/"], cwd=HERE, check=True)
    subprocess.run([sys.executable, str(HERE / "tools" / "build_meta.py"), str(DEL)], cwd=HERE, check=True,
                   stdout=subprocess.DEVNULL)

# verify every slot in source/ (not only the re-rendered ones)
allslots = sorted(p for p in (HERE / "source").glob("2026-*/[1-5]_*") if p.is_dir())
seen, problems, manifest = {}, [], {}
for p in allslots:
    key = f"{p.parent.name}/{p.name}"
    out = DEL / "exports" / key
    md5s = []
    for i in (1, 2, 3):
        f = out / f"0{i}.jpg"
        if not f.exists(): problems.append(f"{key}: 0{i}.jpg missing"); continue
        if Image.open(f).size != (1080, 1350): problems.append(f"{key}: 0{i}.jpg wrong size")
        m = hashlib.md5(f.read_bytes()).hexdigest(); md5s.append(m)
        if m in seen and seen[m] != key: problems.append(f"{key}: 0{i}.jpg identical to a slide of {seen[m]}")
        seen[m] = key
    cap = out / "Caption.txt"
    if not cap.exists() or cap.read_bytes() != (p / "Caption.txt").read_bytes(): problems.append(f"{key}: caption differs from source")
    manifest[key] = {"source": src_hash(p), "exports": md5s}
(HERE / "out").mkdir(exist_ok=True)
(HERE / "out" / "delivery-manifest.json").write_text(json.dumps(manifest, indent=1))
print(f"verified {len(allslots)} carousels, {sum(len(v['exports']) for v in manifest.values())} slides; "
      f"{len(problems)} problem(s)")
for x in problems: print("  PROBLEM", x)
sys.exit(1 if problems else 0)
