"""Find number plates and faces in a photo, for the carousel engine. Local only: OpenCV, nothing generated.

    python3 finder.py <photo> [<photo> ...]          # print what it finds in each photo
    python3 finder.py --sheet out.jpg <photo> ...    # and draw every box on one sheet, to test it by eye

It proposes; a person approves on the finished contact sheet (LAYOUT.md, "Photos"). It misses plates, so
"none found" is never a pass: README.md has the measured miss rate.

Plates: lines of four to nine same-height characters on a plain plate-shaped ground, read both ways
(dark on light, light on dark) at up to three sizes. Faces: OpenCV's YuNet model when its file is on the machine
(set YUNET to its path), and no face finding at all without it: the engine then flags every photo.
Needs numpy, Pillow and opencv-python-headless.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photos import photo  # noqa: E402

YUNET = os.environ.get('YUNET') or os.path.expanduser('~/.local/vlogtools/models/face_detection_yunet_2023mar.onnx')
SIZES = (1100, 2000, 3200)   # long sides the plate search runs at: near plates first, far ones last
GROW = 2.0                   # a small photo is enlarged by up to this much, so far plates have letters to read
SURE = 0.6               # a plate under this score is still covered, and its photo is flagged
FACE_SURE = 0.8


def overlap(a, b):
    """How much of the smaller box the two share."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    return w * h / float(min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])))


def glyph_lines(gray, invert):
    """Rows of character-sized blobs: [(box, score)] in this image's pixels."""
    h, w = gray.shape
    k = max(15, (w // 40) | 1)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY if invert else cv2.THRESH_BINARY_INV, k, 9)
    n, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    chars = []
    for x, y, cw, ch, area in stats[1:]:
        if not (7 <= ch <= h * 0.2) or cw > ch * 4.5 or ch > cw * 9 or area < cw * ch * 0.15:
            continue
        if cw > ch * 1.3 and area > cw * ch * 0.8:   # a wide blob may be letters blurred together; a solid bar isn't
            continue
        chars.append((int(x), int(y), int(cw), int(ch), max(1, round(cw / (0.72 * ch)))))
    chars.sort()
    lines, used = [], set()
    for i, a in enumerate(chars):
        if i in used:
            continue
        row = [a]
        for j in range(i + 1, len(chars)):
            b, last = chars[j], row[-1]
            if j in used or b[0] < last[0] + last[2] * 0.5:
                continue
            if b[0] - (last[0] + last[2]) > a[3] * 1.4:
                break
            if abs(b[3] - a[3]) < a[3] * 0.22 and abs((b[1] + b[3] / 2) - (last[1] + last[3] / 2)) < a[3] * 0.25:
                row.append(b)
                used.add(j)
        letters = sum(c[4] for c in row)
        if not 4 <= letters <= 9:
            continue
        x0, y0 = row[0][0], min(c[1] for c in row)
        x1, y1 = row[-1][0] + row[-1][2], max(c[1] + c[3] for c in row)
        ch = y1 - y0
        if (x1 - x0) < ch * 2.0 or (x1 - x0) > ch * 9:
            continue
        # a plate is a plain field round the characters: grow the row to plate size and look at that field
        box = [int(x0 - ch * 0.6), int(y0 - ch * 0.7), int(x1 + ch * 0.6), int(y1 + ch * 0.7)]
        box = [max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])]
        field = gray[box[1]:box[3], box[0]:box[2]]
        ink = binary[box[1]:box[3], box[0]:box[2]] > 0
        if field.size == 0 or ink.all() or not ink.any():
            continue
        ground, glyph = field[~ink], field[ink]
        contrast = abs(float(ground.mean()) - float(glyph.mean())) / 255
        plain = 1 - min(1.0, float(ground.std()) / 60)
        even = 1 - min(1.0, float(np.std([c[3] for c in row])) / max(1.0, ch * 0.15))
        count = 1.0 if 5 <= letters <= 8 else 0.6
        score = round(0.35 * min(1, contrast / 0.45) + 0.25 * plain + 0.2 * even + 0.2 * count, 2)
        if contrast < 0.12:
            continue
        lines.append((box, score))
    return lines


def find_plates(rgb):
    """Every plate-like line of characters, in the photo's pixels:
    [{"box": [x0, y0, x1, y1], "score": 0..1, "reads": n, "sure": bool}]."""
    gray_full = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    long_side = max(gray_full.shape)
    found, done = [], []
    for size in SIZES:
        s = min(GROW, size / long_side)
        if any(abs(s - t) < 0.05 for t in done):
            continue
        done.append(s)
        gray = cv2.resize(gray_full, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        gray = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
        for invert in (False, True):
            for box, score in glyph_lines(gray, invert):
                found.append({'box': [int(round(v / s)) for v in box], 'score': score})
    found.sort(key=lambda f: -f['score'])
    keep = []
    for f in found:
        hit = next((k for k in keep if overlap(k['box'], f['box']) > 0.4), None)
        if hit:   # the same plate read again, at another size or the other way round
            hit['reads'] += 1
            hit['box'] = [min(hit['box'][0], f['box'][0]), min(hit['box'][1], f['box'][1]),
                          max(hit['box'][2], f['box'][2]), max(hit['box'][3], f['box'][3])]
        else:
            keep.append({**f, 'reads': 1})
    for k in keep:   # sure only when it scored well and was read more than once
        k['sure'] = k['score'] >= SURE and k['reads'] >= 2
    return keep


def find_faces(rgb):
    """[{"box", "score"}], or None when the face model isn't on this machine."""
    if not os.path.exists(YUNET):
        return None
    h, w = rgb.shape[:2]
    s = min(1.0, 1280 / max(h, w))
    small = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else rgb
    det = cv2.FaceDetectorYN.create(YUNET, '', (small.shape[1], small.shape[0]), 0.5, 0.3, 50)
    _, faces = det.detect(cv2.cvtColor(small, cv2.COLOR_RGB2BGR))
    out = []
    for f in (faces if faces is not None else []):
        x, y, fw, fh = (float(v) / s for v in f[:4])
        pad = 0.25 * max(fw, fh)
        out.append({'box': [max(0, int(x - pad)), max(0, int(y - pad)), min(w, int(x + fw + pad)),
                            min(h, int(y + fh + pad))], 'score': round(float(f[14]), 2)})
    return out


def face_free_crop(size, faces, keep=0.5):
    """The largest crop of the photo with every face outside it, or None when that leaves under `keep` of it."""
    w, h = size
    best = None
    for x0, y0, x1, y1 in ((0, 0, min(f['box'][0] for f in faces), h), (max(f['box'][2] for f in faces), 0, w, h),
                           (0, 0, w, min(f['box'][1] for f in faces)), (0, max(f['box'][3] for f in faces), w, h)):
        area = max(0, x1 - x0) * max(0, y1 - y0)
        if area >= keep * w * h and (best is None or area > best[0]):
            best = (area, [x0, y0, x1, y1])
    return best[1] if best else None


def find(path):
    """What the finder sees in one photo, and whether a person has to look closely.
    status: "clear" (nothing found), "covered" (plates found and sure of them), "check" (anything it is unsure of)."""
    im = photo(path)
    rgb = np.array(im)
    plates, faces = find_plates(rgb), find_faces(rgb)
    why = []
    if any(not p['sure'] for p in plates):
        why.append('a possible plate it is not sure of')
    crop = None
    if faces is None:
        why.append('faces were not looked for (no face model on this machine)')
    elif faces:
        crop = face_free_crop(im.size, faces)
        why.append('a face, cropped out' if crop else 'a face it could not crop out')
    status = 'check' if why else ('covered' if plates else 'clear')
    return {'size': list(im.size), 'plates': plates, 'faces': faces or [], 'crop': crop, 'status': status, 'why': why}


def draw(path, found, width=520):
    """The photo with every box outlined: red for a sure plate, amber for an unsure one, blue for a face."""
    from PIL import ImageDraw
    im = photo(path)
    d = ImageDraw.Draw(im)
    t = max(4, im.width // 150)
    for p in found['plates']:
        d.rectangle(p['box'], outline=(230, 30, 30) if p['sure'] else (255, 170, 0), width=t)
    for f in found['faces']:
        d.rectangle(f['box'], outline=(40, 110, 255), width=t)
    if found.get('crop'):
        d.rectangle(found['crop'], outline=(40, 200, 90), width=t)
    im.thumbnail((width, width))
    return im


if __name__ == '__main__':
    args = sys.argv[1:]
    sheet = args.pop(args.index('--sheet') + 1) if '--sheet' in args else None
    paths = [a for a in args if a != '--sheet']
    if not paths:
        sys.exit(__doc__)
    tiles = []
    for i, p in enumerate(paths):
        r = find(p)
        print(f'{i + 1:02d} {os.path.basename(p)}: {r["status"]}; plates {[(q["box"], q["score"], q["sure"]) for q in r["plates"]]}; '
              f'faces {len(r["faces"])}')
        if sheet:
            tiles.append(draw(p, r))
    if sheet:
        from PIL import Image, ImageDraw
        cols = min(5, len(tiles))
        rows = (len(tiles) + cols - 1) // cols
        out = Image.new('RGB', (cols * 530, rows * 560), 'white')
        for i, t in enumerate(tiles):
            x, y = (i % cols) * 530, (i // cols) * 560
            out.paste(t, (x + 5, y + 34))
            ImageDraw.Draw(out).text((x + 8, y + 10), f'{i + 1:02d}', fill='black')
        out.save(sheet, quality=85)
        print(sheet, out.size)
