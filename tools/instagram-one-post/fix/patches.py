"""Frame patches for "The floor goes down" (1080x1920 RGB frames, 29.97 fps).

A. Lower third 1:48-1:51: "TWO-POST LIFTS" -> "SCISSOR LIFTS" (same typewriter timing).
B. Capacity callout 2:17-2:19: add "= 7,716 LB" under "3500 KG" once the count lands.
C. Caption 2:11-2:13: "3 ,500 KILOGRAMS." -> "3,500 KILOGRAMS." (close the stray gap).
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30000 / 1001
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
SS = 4  # supersampling for text rendering


def frame_at(t):
    return int(round(t * FPS))


def layout(text, size, track, x0, cap_top):
    """Pen x for each char so glyph ink matches the calibrated original.

    Returns (font, [(char, pen_x)], y_draw) with the first glyph's ink starting at x0
    and the cap tops at cap_top.
    """
    font = ImageFont.truetype(FONT, size)
    bb = font.getbbox(text[0])
    pen = x0 - bb[0]
    out = []
    for c in text:
        out.append((c, pen))
        pen += font.getlength(c) + track
    hb = font.getbbox("H")
    return font, out, cap_top - hb[1]


def render_alpha(chars, size, y, shape, track=0.0):
    """Antialiased coverage (0..1) of the given (char, pen_x) glyphs."""
    h, w = shape
    font = ImageFont.truetype(FONT, size * SS)
    img = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(img)
    for c, x in chars:
        d.text((x * SS, y * SS), c, font=font, fill=255)
    return np.asarray(img.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0


def inpaint(frame, mask, radius=3):
    return cv2.inpaint(frame, (mask > 0).astype(np.uint8) * 255, radius, cv2.INPAINT_TELEA)


def dilate(mask, px):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    return cv2.dilate((mask > 0).astype(np.uint8), k)


# ---------------------------------------------------------------- A. lower third
A_START, A_END = frame_at(108.10), frame_at(111.45)
# Ink measured at x=131, cap tops at y=1227; -1.33 px corrects PIL rounding against the fit.
A_SIZE, A_TRACK, A_X0, A_TOP = 43.5, 5.0, 131 - 1.33, 1227
A_PREFIX = "FORMULA DYNAMICS · "
A_OLD, A_NEW = "TWO-POST LIFTS", "SCISSOR LIFTS"
A_BOX = (1212, 1272, 110, 900)  # y0, y1, x0, x1 working region


class LowerThird:
    def __init__(self):
        font, chars, y = layout(A_PREFIX + A_OLD, A_SIZE, A_TRACK, A_X0, A_TOP)
        y0, y1, x0, x1 = A_BOX
        self.y = y - y0
        self.chars = [(c, x - x0) for c, x in chars]
        # per-glyph masks for the whole original line (ink only, spaces skipped)
        self.glyphs = []
        for c, x in self.chars:
            if c.strip():
                self.glyphs.append(render_alpha([(c, x)], A_SIZE, self.y, (y1 - y0, x1 - x0)))
        self.n_prefix = sum(1 for c in A_PREFIX if c.strip())
        start_pen = self.chars[len(A_PREFIX)][1]
        font_new = ImageFont.truetype(FONT, A_SIZE)
        pen, self.new_chars = start_pen, []
        for c in A_NEW:
            self.new_chars.append((c, pen))
            pen += font_new.getlength(c) + A_TRACK
        self.n_new = sum(1 for c in A_NEW if c.strip())

    def visible_count(self, g):
        n = 0
        for a in self.glyphs:
            core = a > 0.6
            if g[core].max() > 160:
                n += 1
            else:
                break
        return n

    def apply(self, frame, idx):
        if not (A_START <= idx <= A_END):
            return frame
        y0, y1, x0, x1 = A_BOX
        reg = frame[y0:y1, x0:x1].copy()
        g = reg.mean(axis=2)
        n = self.visible_count(g)
        k_old = n - self.n_prefix
        if k_old <= 0:
            return frame
        old = np.zeros(g.shape, np.float32)
        for a in self.glyphs[self.n_prefix:self.n_prefix + k_old]:
            old = np.maximum(old, a)
        clean = inpaint(reg, dilate(old > 0.05, 2), 3)
        k_new = min(self.n_new, k_old)
        shown, count = [], 0
        for c, x in self.new_chars:
            if c.strip():
                if count >= k_new:
                    break
                count += 1
            shown.append((c, x))
        alpha = render_alpha(shown, A_SIZE, self.y, g.shape)[..., None]
        # text colour from this frame's own prefix glyph cores
        core = self.glyphs[0] > 0.8
        for a in self.glyphs[1:self.n_prefix]:
            core |= a > 0.8
        color = np.percentile(reg[core], 75, axis=0).astype(np.float32)
        out = clean.astype(np.float32) * (1 - alpha) + color * alpha
        frame = frame.copy()
        frame[y0:y1, x0:x1] = np.clip(out + 0.5, 0, 255).astype(np.uint8)
        return frame


# ---------------------------------------------------------------- B. callout
B_ON = frame_at(138.20)  # just after the count-up lands on 3500
B_WIN = (frame_at(137.0), frame_at(139.60))
B_X0 = 498
B_TOP = 836
B_NUM_SIZE, B_NUM_TRACK = 90.0, 1.5  # cap ~62 px
B_UNIT_SIZE = 66.0  # cap ~46 px, same as "KG"
RED = np.array([226, 30, 36], np.float32)
B_NUM_BOX = (676, 816, 490, 778)  # y0, y1, x0, x1 around the original "3500"


class Callout:
    def __init__(self):
        self.ref = None  # (digit mask, ring mask, full-opacity contrast) of "3500"
        self.cut = False
        font_num = ImageFont.truetype(FONT, B_NUM_SIZE)
        font_unit = ImageFont.truetype(FONT, B_UNIT_SIZE)
        hb = font_num.getbbox("H")
        self.y_num = B_TOP - hb[1]
        self.y_unit = B_TOP + (hb[3] - hb[1]) - font_unit.getbbox("H")[3]  # baseline-aligned with the number
        pen = B_X0 - font_num.getbbox("=")[0]
        self.eq = [("=", pen)]
        pen += font_num.getlength("=") + 14
        self.num = []
        for c in "7,716":
            self.num.append((c, pen))
            pen += font_num.getlength(c) + B_NUM_TRACK
        pen += 10
        self.unit = [("LB", pen)]
        self.h, self.w = 110, 420

    @staticmethod
    def _number_gray(frame):
        y0, y1, x0, x1 = B_NUM_BOX
        return frame[y0:y1, x0:x1].astype(np.float32).mean(axis=2)

    def learn(self, frame):
        """Record where the "3500" digits are, from a frame where it is fully on screen."""
        g = self._number_gray(frame)
        digits = g > 235
        ring = dilate(digits, 5).astype(bool) & ~dilate(digits, 2).astype(bool)
        self.ref = (digits, ring, max(g[digits].mean() - g[ring].mean(), 1.0))

    def opacity(self, frame):
        """How strongly the original "3500" stands out from what is around it, 0..1.

        Follows the callout's own fade and drops to 0 when it is gone. (The red rule is
        no good for this: red floor tiles pass under it.)
        """
        digits, ring, full = self.ref
        g = self._number_gray(frame)
        return float(np.clip((g[digits].mean() - g[ring].mean()) / full, 0, 1))

    def apply(self, frame, idx):
        lo, hi = B_WIN
        if not (lo <= idx <= hi) or self.cut:
            return frame
        if idx < B_ON:
            if idx >= frame_at(138.0) and self.ref is None:
                self.learn(frame)  # "3500" has landed and is at full opacity
            return frame
        if self.ref is None:
            self.learn(frame)
        fade = self.opacity(frame)
        if fade < 0.12:  # the callout is gone: never draw again (next shot)
            self.cut = True
            return frame
        # 6-frame ease-out: fade in while sliding up 14 px
        t = min(1.0, max(0.0, (idx - B_ON) / 6.0))
        ease = 1 - (1 - t) ** 3
        dy = int(round((1 - ease) * 14))
        y0 = B_TOP - 20 + dy
        x0 = B_X0 - 20
        h, w = self.h, self.w

        def loc(chars):
            return [(c, x - x0) for c, x in chars]
        a_num = render_alpha(loc(self.num), B_NUM_SIZE, self.y_num - (B_TOP - 20), (h, w))
        a_eq = render_alpha(loc(self.eq), B_NUM_SIZE, self.y_num - (B_TOP - 20), (h, w))
        a_unit = render_alpha(loc(self.unit), B_UNIT_SIZE, self.y_unit - (B_TOP - 20), (h, w))
        a_white = np.maximum(a_num, a_unit)
        a_all = np.maximum(a_white, a_eq)
        shadow = cv2.GaussianBlur(a_all, (0, 0), 5) * 0.55
        k = ease * fade
        region = frame[y0:y0 + h, x0:x0 + w].astype(np.float32)
        region = region * (1 - (shadow * k)[..., None])
        white = np.array([255, 255, 255], np.float32)
        region = region * (1 - (a_white * k)[..., None]) + white * (a_white * k)[..., None]
        region = region * (1 - (a_eq * k)[..., None]) + RED * (a_eq * k)[..., None]
        frame = frame.copy()
        frame[y0:y0 + h, x0:x0 + w] = np.clip(region + 0.5, 0, 255).astype(np.uint8)
        return frame


# ---------------------------------------------------------------- C. caption
C_WIN = (frame_at(131.45), frame_at(133.0))
# Ink measured at x=75, cap tops at y=1404; same rounding correction as the lower third.
C_SIZE, C_TRACK, C_X0, C_TOP = 82.0, 2.5, 75 - 1.73, 1405
C_TEXT = "3 ,500 KILOGRAMS."
# The stray gap is one space plus tracking; moving ",500 KILOGRAMS." left by that closes it.
C_SHIFT = round(ImageFont.truetype(FONT, C_SIZE).getlength(" ") + C_TRACK)
C_BOX = (1380, 1500, 60, 700)
C_UNDERLINE = (1469, 1479)  # rows of the red karaoke underline (measured 1471-1477)


class Caption:
    def __init__(self):
        font, chars, y = layout(C_TEXT, C_SIZE, C_TRACK, C_X0, C_TOP)
        y0, y1, x0, x1 = C_BOX
        self.y = y - y0
        shape = (y1 - y0, x1 - x0)
        # the two karaoke words after the stray gap: ",500" then "KILOGRAMS."
        self.words = []
        for part in (chars[2:6], chars[7:]):
            a = render_alpha([(c, x - x0) for c, x in part], C_SIZE, self.y, shape)
            ink = a > 0.05
            ring = dilate(ink, 6).astype(bool) & ~dilate(ink, 3).astype(bool)
            cols = np.where(ink.any(axis=0))[0]
            underline = np.zeros(shape, bool)  # the red bar under the word when it is being spoken
            underline[C_UNDERLINE[0] - y0:C_UNDERLINE[1] - y0 + 1, cols[0] - 5:cols[-1] + 7] = True
            self.words.append({"ink": ink, "core": a > 0.6, "ring": ring, "underline": underline})
        self.latched = []

    @staticmethod
    def contrast(g, word):
        return g[word["core"]].mean() - g[word["ring"]].mean()

    def apply(self, frame, idx):
        lo, hi = C_WIN
        if not (lo <= idx <= hi):
            return frame
        y0, y1, x0, x1 = C_BOX
        reg = frame[y0:y1, x0:x1].copy()
        g = reg.mean(axis=2)
        shown = [w for w in self.words if self.contrast(g, w) > 25]
        if not shown:
            # not on screen, or the last frame or two of the fade-out: under ~15% opacity the
            # old position can't be seen, and moving or erasing it would disturb the floor
            self.latched = []
            return frame
        if all(any(w is seen for seen in self.latched) for w in shown):
            shown = self.latched  # fading: keep moving every word that was on screen
        self.latched = shown
        # the words' own shapes (not a brightness threshold, so fading frames are covered),
        # plus the underline under the word being spoken (the last one on screen)
        text = shown[-1]["underline"].copy()
        for w in shown:
            text |= w["ink"]
        text = dilate(text, 2)
        halo = dilate(text, 6)
        # erase only the old ink; the soft shadow around it moves with the matte below
        clean = inpaint(reg, text, 5)
        # soft matte of the moved text (ink + underline + shadow halo)
        matte = cv2.GaussianBlur(halo.astype(np.float32), (0, 0), 1.5)
        matte = np.maximum(matte, text.astype(np.float32))
        src = np.roll(reg, -C_SHIFT, axis=1).astype(np.float32)
        m = np.roll(matte, -C_SHIFT, axis=1)[..., None]
        out = clean.astype(np.float32) * (1 - m) + src * m
        frame = frame.copy()
        frame[y0:y1, x0:x1] = np.clip(out + 0.5, 0, 255).astype(np.uint8)
        return frame
