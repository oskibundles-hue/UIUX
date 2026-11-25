#!/usr/bin/env python3
"""Render slide HTML to 1080x1350 sRGB JPEG with installed Chrome.
render.py OUT_DIR slide-01.html [slide-02.html ...]  -> OUT_DIR/01.jpg 02.jpg ...
Also writes OUT_DIR/_phone/NN.png at 390px wide for the phone-size check."""
import sys, pathlib, io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageCms
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "_phone").mkdir(exist_ok=True)
srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
    pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
    for i, f in enumerate(sys.argv[2:], 1):
        pg.goto(pathlib.Path(f).resolve().as_uri()); pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        im = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGB")
        assert im.size == (1080, 1350), im.size
        im.save(out / f"{i:02d}.jpg", quality=95, subsampling=0, icc_profile=srgb)
        im.resize((390, 488), Image.LANCZOS).save(out / "_phone" / f"{i:02d}.png")
        print(out / f"{i:02d}.jpg")
    b.close()
