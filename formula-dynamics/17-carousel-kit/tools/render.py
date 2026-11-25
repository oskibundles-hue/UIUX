#!/usr/bin/env python3
"""Render slides to 1080x1350 sRGB JPEGs: render.py OUT_DIR slide-01.html [slide-02.html ...]
Writes OUT_DIR/01.jpg ... (q95, sRGB profile) and OUT_DIR/_phone/01.png ... at 390 px wide, the size of a
phone feed, for the phone check. Uses the installed Chrome so fonts and colour match what the team sees."""
import io, sys, pathlib
from PIL import Image, ImageCms

W, H = 1080, 1350
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def open_browser(pw):
    b = pw.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
    return b, b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)


def render(pg, slides, out, phone=True):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    if phone: (out / "_phone").mkdir(exist_ok=True)
    for i, s in enumerate(slides, 1):
        pg.goto(pathlib.Path(s).resolve().as_uri()); pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        im = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGB")
        assert im.size == (W, H), (s, im.size)
        im.save(out / f"{i:02d}.jpg", quality=95, subsampling=0, icc_profile=SRGB)
        if phone:
            im.resize((390, round(390 * H / W)), Image.LANCZOS).save(out / "_phone" / f"{i:02d}.png")
    # a carousel that lost a slide must not keep the old last slide
    for old in out.glob("[0-9][0-9].jpg"):
        if int(old.stem) > len(slides): old.unlink()
    return len(slides)


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    out, *slides = sys.argv[1:]
    with sync_playwright() as pw:
        b, pg = open_browser(pw)
        n = render(pg, slides, out)
        b.close()
    print(f"{n} slides -> {out}")
