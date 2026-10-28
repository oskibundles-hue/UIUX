#!/usr/bin/env python3
"""Sound for the opt-in glitch intro (remotion/src/GlitchIntro.tsx): the reel's own sound turned down, plus Celina's
approved pack (celfstudies, 28 sounds) placed by the sound guide's glitch-hook rules. Nothing is synthesised.

Cues (picture clock 30 fps; glitch = frames 0-29, IntroCut title from 1.0 s, glitch out at 5.33 s):
  the glitch second, 7 sounds: sway to open, shutter on inverted frames 9 and 22, quiet ticks on hard frames 5 and 17,
  reverse rise into the white flash and the Deep Sway landing it (its one use in the video);
  the title, IntroCut's typing schedule moved to 1.0 s: a key per letter, plus a thock per big-line letter and space;
  a rise under the light leak, a shutter and a sway on the glitch out.
Every pack sound is raised (at most 9 dB) until it sits 1 dB above the reel's sound at its hit; the mix is limited and
set to -14 LUFS with the true peak at or under -1.5 dBTP, then muxed onto the silent render (picture copied).

usage: uv run --offline --no-project --with numpy --with soundfile --with scipy python glitch_intro_sound.py \
         silent.mp4 reel.mp4 out.mp4 --small "NQ.YOUNG PRESENTS" --big "My Saturday at the shop"
       [--bed-db -10] [--bed-ss 0] [--pack DIR]   (pack: $NQ_CELF_PACK, else the research folder below)
writes out.mp4 and out.mp4.cues.json (every cue with its reason, how many were raised, loudness).
"""
import argparse, json, math, os, re, subprocess
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

PACK = os.environ.get("NQ_CELF_PACK", os.path.expanduser("~/.local/vlogtools/work/research/2026-10-18-sfx-sound-design/celf_pack"))
FF = os.path.expanduser("~/.local/bin/ffmpeg"); FP = os.path.expanduser("~/.local/bin/ffprobe")
SR = 48000; F = 1 / 30; T0 = 1.0
TARGET_I = -14.0
# Seconds from each sound's start to its hit, measured on the pack (trial_reels/sound_pass/pack_measure.json).
HIT = {"Whoosh_01_Sway": 0.035, "Camera_02_Shutter_Click": 0.08, "UI_01_Tiny_Bleep": 0.02, "Typing_04_Single_Key": 0.045,
       "Whoosh_03_Reverse_Rise": 0.695, "Whoosh_04_Deep_Sway": 0.045, "Mouse_Click_02_Tactile": 0.025}


def cues(small, big):
    c = []
    def add(t, key, db, why, align="hit"): c.append(dict(t=round(t, 4), key=key, db=db, align=align, why=why))
    # the glitch second: 7 sounds
    add(0.0, "Whoosh_01_Sway", -9, "opening hit, soft sway (Deep Sway saved for the landing)", "start")
    add(9 * F, "Camera_02_Shutter_Click", -9, "inverted frame 9")
    add(22 * F, "Camera_02_Shutter_Click", -9, "inverted frame 22")
    add(5 * F, "UI_01_Tiny_Bleep", -16, "hard glitch frame 5, quiet", "start")
    add(17 * F, "Typing_04_Single_Key", -16, "hard glitch frame 17, quiet", "start")
    add(1.0, "Whoosh_03_Reverse_Rise", -8, "rises into the white flash where the picture clears")
    add(1.0, "Whoosh_04_Deep_Sway", -4, "lands the clear (once per video)", "start")
    # title typing: IntroCut's linear schedule (small 0.15-0.95 s, big 1.05-2.55 s) moved to start at 1.0 s
    def typed(text, a, b): n = len(text); return [(T0 + a + (b - a) * (k + 1) / n, ch) for k, ch in enumerate(text)]
    for t, ch in typed(small, 0.15, 0.95):
        if ch != " ": add(t, "Typing_04_Single_Key", -15, "small line, one key per letter")
    for t, ch in typed(big, 1.05, 2.55):
        if ch != " ": add(t, "Typing_04_Single_Key", -11, "big line key"); add(t, "Mouse_Click_02_Tactile", -13, "big line thock")
        else: add(t, "Mouse_Click_02_Tactile", -10, "space bar")
    # light leak and the glitch out
    add(T0 + 4.127, "Whoosh_03_Reverse_Rise", -11, "light leak rise (kit timing)")
    add(160 * F, "Camera_02_Shutter_Click", -11, "title glitches out")
    add(162 * F, "Whoosh_01_Sway", -10, "title clears, reel runs on", "start")
    return c


_cache = {}
def load(key):
    """Pack sound by name, stereo float32 at 48 kHz, normalised to 0 dBFS peak so cue levels compare."""
    if key in _cache: return _cache[key]
    path = os.path.join(PACK, key + ".wav")
    if not os.path.exists(path): raise SystemExit(f"missing pack sound {path} (set --pack or NQ_CELF_PACK)")
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    a = a[:, :2]
    if sr != SR: a = resample_poly(a, SR, sr, axis=0).astype(np.float32)
    a /= max(1e-9, np.abs(a).max())
    _cache[key] = a; return a


def render(cs, n):
    out = np.zeros((n, 2), np.float32)
    for c in cs:
        a = load(c["key"]); off = {"hit": HIT[c["key"]], "start": 0.0, "end": len(a) / SR}[c["align"]]
        p = int(round((c["t"] - off) * SR)); s0 = max(0, -p); s1 = min(len(a), n - p)
        if s1 > s0: out[p + s0:p + s1] += a[s0:s1] * 10 ** (c["db"] / 20)
    return out


def lift(cs, b, n, over_db=1.0, max_up=9.0):
    """Raise any pack sound that would sit under the reel's sound at its hit until it is 1 dB over (at most 9 dB, never past full level)."""
    done = 0
    for x in cs:
        s = render([x], n)
        pk = int(np.abs(s).max(1).argmax()); lo, hi = max(0, pk - int(0.02 * SR)), min(n, pk + int(0.10 * SR))
        r = lambda v: math.sqrt(float(np.mean(v ** 2))) + 1e-12
        under = 20 * math.log10(r(b[lo:hi]) / r(s[lo:hi])) + over_db
        if under > 0:
            up = min(max_up, under, -x["db"])
            if up > 0.5:
                x["db"] = round(x["db"] + up, 1); x["why"] += f" (raised {up:.0f} dB so it sits above the camera sound)"; done += 1
    return done


def read_audio(src, ss, dur):
    """dur seconds of src from ss as 48 kHz stereo float32 (silence if the file has no sound)."""
    p = subprocess.run([FF, "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", src, "-vn", "-ac", "2", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy(); n = int(round(dur * SR))
    return np.vstack([a, np.zeros((max(0, n - len(a)), 2), np.float32)])[:n]


def ebur(a, tmp):
    sf.write(tmp, a, SR, subtype="FLOAT")
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1)), float(re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", tail).group(1))


def limit(a, ceil_lin):
    """Look-ahead peak limiter: gain never above what keeps |x| <= ceil, smoothed over ~4 ms, 80 ms release."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    L = int(0.002 * SR)
    need = np.minimum(1.0, ceil_lin / np.maximum(np.abs(a).max(1), 1e-9))
    g = uniform_filter1d(minimum_filter1d(need, 4 * L + 1), 2 * L + 1)
    rel = 1 - math.exp(-1 / (0.08 * SR)); out = np.empty_like(g); cur = 1.0
    for i in range(len(g)):
        cur = g[i] if g[i] < cur else cur + (g[i] - cur) * rel
        out[i] = cur
    return a * out[:, None].astype(np.float32)


def master(mix, tmp):
    """Limit, then gain to -14 LUFS; pull the limiter ceiling down until the true peak leaves room for the AAC encode."""
    I0, _ = ebur(mix, tmp); gain = TARGET_I - I0; ceil = -1.9; best = None
    for _ in range(16):
        y = limit(mix, 10 ** ((ceil - gain) / 20)) * 10 ** (gain / 20)
        I, P = ebur(y, tmp)
        if P <= -1.5 and (best is None or abs(I - TARGET_I) < abs(best[1] - TARGET_I)): best = (y, I, P)
        if abs(I - TARGET_I) <= 0.3 and P <= -1.5: break
        if P > -1.5: ceil -= P + 1.5 + 0.1
        gain += TARGET_I - I
    y, I, P = best if best else (y, I, P)
    return y.astype(np.float32), I, P


def main():
    global PACK
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("picture"); ap.add_argument("reel"); ap.add_argument("out")
    ap.add_argument("--small", required=True); ap.add_argument("--big", required=True)
    ap.add_argument("--bed-db", type=float, default=-10); ap.add_argument("--bed-ss", type=float, default=0)
    ap.add_argument("--pack", default=PACK)
    a = ap.parse_args(); PACK = a.pack
    dur = float(subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0",
                                a.picture], capture_output=True, text=True).stdout.strip())
    n = int(round(dur * SR))
    bed = read_audio(a.reel, a.bed_ss, dur) * 10 ** (a.bed_db / 20)
    cs = cues(a.small, a.big); lifted = lift(cs, bed, n)
    tmp = a.out + ".tmp.wav"
    y, I, P = master(bed + render(cs, n), tmp)
    sf.write(tmp, y, SR, subtype="FLOAT")
    part = a.out + ".part.mp4"
    r = subprocess.run([FF, "-v", "error", "-y", "-i", a.picture, "-i", tmp, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", "-map_metadata", "0", "-movflags", "+faststart", part],
                       capture_output=True, text=True)
    os.remove(tmp)
    if r.returncode: raise SystemExit(f"mux failed: {r.stderr[-400:]}")
    os.replace(part, a.out)
    json.dump({"cues": cs, "lifted": lifted, "lufs": round(I, 1), "true_peak": round(P, 1)}, open(a.out + ".cues.json", "w"), indent=1)
    print(f"mixed {os.path.basename(a.out)}: {len(cs)} pack cues ({lifted} lifted), {I:.1f} LUFS, peak {P:.1f} dBTP")


if __name__ == "__main__":
    main()
