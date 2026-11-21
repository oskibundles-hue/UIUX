#!/usr/bin/env python3
"""Blur a readable number plate in a still: plate_blur.py IN OUT x0,y0,x1,y1 [x0,y0,x1,y1 ...]
Boxes are in source pixels. Each box is padded 12%, pixelated then gaussian-blurred, with a feathered
rounded mask so the edge doesn't read as a sticker. Saves sRGB JPEG q92 (or PNG by extension)."""
import sys
from PIL import Image, ImageFilter, ImageDraw

def blur_boxes(im, boxes):
    im = im.convert("RGB")
    for (x0, y0, x1, y1) in boxes:
        w, h = x1 - x0, y1 - y0
        px, py = int(w * .12), int(h * .12)
        X0, Y0, X1, Y1 = max(0, x0 - px), max(0, y0 - py), min(im.width, x1 + px), min(im.height, y1 + py)
        reg = im.crop((X0, Y0, X1, Y1))
        small = reg.resize((max(1, reg.width // 28), max(1, reg.height // 28)), Image.BILINEAR)
        b = small.resize(reg.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(max(8, w // 14)))
        m = Image.new("L", reg.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((px // 2, py // 2, reg.width - px // 2, reg.height - py // 2), radius=min(px, py) * 2, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(max(3, min(px, py) // 2)))
        reg.paste(b, (0, 0), m)
        im.paste(reg, (X0, Y0))
    return im

if __name__ == "__main__":
    src, out, *bx = sys.argv[1:]
    boxes = [tuple(int(v) for v in b.split(",")) for b in bx]
    im = blur_boxes(Image.open(src), boxes)
    if out.lower().endswith((".jpg", ".jpeg")):
        im.save(out, quality=92, subsampling=0)
    else:
        im.save(out)
