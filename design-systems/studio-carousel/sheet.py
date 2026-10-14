"""One contact sheet of the slides, for nq-check (or for preview.png).

    python3 sheet.py out.jpg label=path [label=path ...]
"""
import sys

from PIL import Image, ImageDraw

out = sys.argv[1]
items = [a.split('=', 1) for a in sys.argv[2:]]
W, H = 360, 450
cols = min(5, len(items))
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * (H + 30)), 'white')
d = ImageDraw.Draw(sheet)
for i, (lab, p) in enumerate(items):
    im = Image.open(p).convert('RGB')
    im.thumbnail((W, H))
    x, y = (i % cols) * W, (i // cols) * (H + 30)
    sheet.paste(im, (x + (W - im.width) // 2, y + 30))
    d.text((x + 8, y + 8), lab, fill='black')
sheet.save(out, **({'quality': 88} if out.lower().endswith(('.jpg', '.jpeg')) else {'optimize': True}))
print(out, sheet.size)
