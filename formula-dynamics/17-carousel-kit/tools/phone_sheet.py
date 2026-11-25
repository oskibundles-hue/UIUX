#!/usr/bin/env python3
"""Put a carousel's phone-size renders side by side in one picture, to look at as a phone user would:
phone_sheet.py OUT_DIR   (reads OUT_DIR/_phone/*.png from render.py, writes OUT_DIR/_phone/sheet.png)"""
import sys, pathlib
from PIL import Image
d = pathlib.Path(sys.argv[1]) / "_phone"
ims = [Image.open(p) for p in sorted(d.glob("[0-9][0-9].png"))]
g = 12
sheet = Image.new("RGB", (sum(i.width for i in ims) + g * (len(ims) + 1), ims[0].height + 2 * g), (40, 40, 46))
x = g
for im in ims:
    sheet.paste(im, (x, g)); x += im.width + g
sheet.save(d / "sheet.png")
print(d / "sheet.png")
