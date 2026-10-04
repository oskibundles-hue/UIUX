"""Locked-On ABC v1 compositor: plate (graded R2, abc-mix v3's per-shot gamma match) -> the Locked-On edit FX (whips between
steps, impacts inside a step and on the drop, FD red leaks on #37 and the reveal) -> the layer's plate punch -> glass panels ->
vignette + grain -> the motion layer. v1 (LO_D=L): the hook (beats 0-4) and the end card (beat 55 on) sit on the card's #08080A ground; v2 (LO_D=M, default): the hook is over dimmed #36.

  python3 compose_lo.py video <layerdir>                 raw RGB24 frames on stdout (pipe to ffmpeg)
  python3 compose_lo.py still <layerdir> <name> <out>    one frame of a kcapture 'at' capture (name = t1.668)
  python3 compose_lo.py base <i> <out>                    footage + edit FX only (QA)

Flash rule (reviewer, 3 Oct): no harsh white flashes. An impact is a zoom punch, a short shake, a decaying RGB split and a
SOFT warm wash on its first two frames (10 % / 4 %; 14 % / 6 % on the drop), never an overexposure. Whips lift exposure 4 %.
"""
import json, math, os, sys
from functools import lru_cache
import numpy as np
import cv2

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{T}/lib"); sys.path.insert(0, T)
import fx  # noqa: E402
from compose30 import pplate, glass, GAMMA, load_layer, fx_of  # noqa: E402

W, H = 1080, 1920
OFPS = 30000 / 1001
LO_D = os.environ.get("LO_D", "M")                      # L = v1, M = v2
SC = json.loads((lambda s: s[s.index('{'):s.rindex('}') + 1])(open(f"{T}/.work/{LO_D}/scene.js").read()))
HOOK = SC.get("hook")
SHOTS, TRANS, LEAKS = SC["shots"], SC["trans"], SC["leaks"]
NF = SC["nf"]
GROUND = np.full((H, W, 3), np.float32([8, 8, 10]) / 255.0)
F_HOOK, F_CARD = TRANS[0]["f"], TRANS[-1]["f"]          # beat 4 and beat 55
LEAK = [(1.0, 0.42, 0.30), (1.0, 0.30, 0.16), (0.95, 0.10, 0.08)]   # FD red -> ember (the hook ad's palette)
WARM = np.float32([1.0, 0.97, 0.92])
WN = 3


def shot_of(i):
    return next((s for s in SHOTS if s["g0"] <= i < s["g1"]), None)


@lru_cache(maxsize=24)
def raw(i):
    if i < F_HOOK and HOOK:                              # v2: dimmed #36 under the hook panel, slow push
        img = pplate(HOOK["rel"], i)
        img = fx.transform(img, 0, 0, HOOK["push"][0] + (HOOK["push"][1] - HOOK["push"][0]) * i / max(1, F_HOOK - 1), 0)
        return img * HOOK["dim"]
    if i < F_HOOK or i >= F_CARD:
        return GROUND
    s = shot_of(i)
    img = pplate(s["rel"], s["off"] + (i - s["g0"]))
    gm = GAMMA.get(s["key"], 1.0)
    return np.power(np.clip(img, 0, 1), gm) if abs(gm - 1) > 1e-3 else img


@lru_cache(maxsize=3)
def whip(c, direction):
    return fx.whip([raw(c - WN + j) for j in range(WN)], [raw(c + j) for j in range(WN)], direction=direction, dist=0.9, blur=1.0, bright=0.04)


def impact(img, k, c, drop):
    s = 0.5 if drop else 0.4
    punch = 1 + 0.08 * s * (1 - fx.smootherstep(min(1.0, k / 10)))
    dx, dy, rot = fx.shake_offsets(k, amp=14 * s, seed=c)
    ca = 12 * s * math.exp(-k / 2.2)
    out = fx.transform(img, dx, dy, punch + 0.012 * min(1.0, ca / 6), rot * 0.5)
    if k < 3:
        out = fx.zoom_blur(out, 0.04 * s * (1 - k / 3), n=6)
    if ca > 0.3:
        out = fx.chroma_split(out, ca, radial=True)
    w = ((0.14, 0.06) if drop else (0.10, 0.04))[k] if k < 2 else 0.0
    return out * (1 - w) + WARM * w if w else out


def base(i):
    for tr in TRANS:
        c = tr["f"]
        if tr["kind"] == "whip" and c - WN <= i < c + WN:
            return whip(c, tr["dir"])[i - (c - WN)]
    img = raw(i)
    if img is GROUND:
        return img
    for tr in TRANS:
        k = i - tr["f"]
        if tr["kind"] == "impact" and 0 <= k < 12:
            img = impact(img, k, tr["f"], tr.get("drop", False))
    for L in LEAKS:
        tt = (i - L["f0"]) / OFPS
        if 0 <= tt < L["dur"]:
            st = 0.5 * math.exp(-max(0.0, tt - 0.12) * 2.6) * min(1.0, tt / 0.12 + 0.05) * (1 - fx.smootherstep(max(0.0, (tt - L["dur"] + 0.3) / 0.3)))
            img = fx.light_leak(img, tt + L["f0"] / 100, strength=st, seed=L["f0"], palette=LEAK, side=L["side"])
    return img


def finish(i, fxd, layer):
    img = base(i)
    on_ground = (i < F_HOOK - WN and not HOOK) or i >= F_CARD + WN
    if not on_ground:
        if fxd.get("punch"):
            p = fxd["punch"]; img = fx.transform(img, p.get("dx", 0), p.get("dy", 0), p.get("s", 1), 0)
        for g in fxd.get("glass", []):
            if g.get("dark", 0) > 0.003:
                img = glass(img, g)
        img = fx.vignette(img, 0.30)
        img = fx.grain(img, i, amount=0.024)
    if layer is not None:
        a = layer[..., 3:4].astype(np.float32) / 255.0
        img = np.clip(img, 0, 1) * (1 - a) + (layer[..., :3].astype(np.float32) / 255.0) * a
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "video":
        L = sys.argv[2]
        for i in range(NF):
            nm = f"{i:05d}"
            sys.stdout.buffer.write(finish(i, fx_of(f"{L}/fx_{nm}.json"), load_layer(f"{L}/{nm}.png")).tobytes())
    elif mode == "base":
        i, out = int(sys.argv[2]), sys.argv[3]
        cv2.imwrite(out, (np.clip(base(i), 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
    else:
        L, name, out = sys.argv[2], sys.argv[3], sys.argv[4]
        i = int(round(float(name[1:]) * OFPS))
        img = finish(i, fx_of(f"{L}/fx_{name}.json"), load_layer(f"{L}/{name}.png"))
        cv2.imwrite(out, img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 93])
        print(out, "frame", i)
