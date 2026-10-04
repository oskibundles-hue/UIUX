"""Music-only sound for one ad (Omarie 2026-09-29: "take the animation sounds out ... add some music instead").

  python3 music.py <ad> <track file> [--drop S]     -> .work/<ad>/mix.wav (+ mix_music.json)

The track plays continuously (never chopped at a cut). Its drop lands on the reveal shot's first frame, which sits on a
bar line of the 128 BPM edit (ads.py). The drop is found automatically -- the biggest rise in kick/bass energy from one
bar to the next -- unless --drop gives it (seconds into the track). Fades out under the end card; last 50 ms silent;
-14 LUFS integrated, true peak <= -2 dBTP before AAC (the delivered file is measured again after encoding).
"""
import argparse, json, os, sys
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{T}/lib"); sys.path.insert(0, T)
import synth as S  # noqa: E402
import bedlib as BL  # noqa: E402
from full30 import ADS, BEAT, OFPS, timeline  # noqa: E402  (FD PPF 30 rail v1)

FF = os.path.expanduser("~/.local/vlogtools/bin/ffmpeg")
SR = 48000


def band_env(x, lo, hi, hop):
    m = x.mean(1)
    y = S.fft_filter(m, lo=lo, hi=hi)
    n = len(y) // hop
    return np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)


def beat_phase(x):
    """Phase (s) of the 128 BPM beat grid: correlate the low-band onset strength with a pulse train."""
    hop = 240                                            # 5 ms
    e = band_env(x, 40, 200, hop)
    on = np.maximum(0, np.diff(np.log(e)))
    per = BEAT * SR / hop
    best, bp = -1, 0.0
    for ph in np.arange(0, per, 0.25):
        idx = (ph + per * np.arange(int(len(on) / per) - 1)).astype(int)
        sc = on[idx].sum()
        if sc > best:
            best, bp = sc, ph
    return bp * hop / SR


def find_drop(x, phase, min_t):
    """Bar-start time (s) with the largest rise in kick/bass energy from the previous bar."""
    bar = 4 * BEAT
    e = band_env(x, 35, 160, 480)                        # 10 ms
    t = np.arange(len(e)) * 0.01
    cands = []
    for k in range(4):                                   # try each beat as the downbeat
        starts = np.arange(phase + k * BEAT, t[-1] - bar, bar)
        energy = [e[(t >= s) & (t < s + bar)].mean() for s in starts]
        for i in range(1, len(starts)):
            if starts[i] >= min_t:
                cands.append((20 * np.log10(energy[i] / energy[i - 1]), starts[i]))
    cands.sort(reverse=True)
    return cands[0][1], cands[:5]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ad"); ap.add_argument("track"); ap.add_argument("--drop", type=float)
    ap.add_argument("--splice", help="bar-line edit 'drop1,build,drop2' (track bar numbers): open on drop1, play its bars up to "
                    "one bar before the reveal, then the build bar, then drop2 lands on the reveal")
    ap.add_argument("--bar0", type=float, default=None, help="track time (s) of bar 0 of the bar grid")
    a = ap.parse_args()
    ad = ADS[a.ad]
    shots, nf = timeline(ad)
    dur = nf / OFPS
    rev = next(s for s in shots if s.get("reveal"))
    reveal = rev["beat0"] * BEAT                         # on the beat grid (the frame is the nearest to it)
    x = BL.read_audio(FF, a.track)
    phase = beat_phase(x)
    if a.drop is not None:
        drop, cands = a.drop, []
    else:
        drop, cands = find_drop(x, phase, min_t=reveal)
    off = drop - reveal
    splice = None
    if a.splice:
        # GLIDE: 8-bar breakdowns sit before every drop, which put all six PPF steps over a kick-less stretch (v2 check).
        # Instead: open on drop 1, keep the kick under the steps, jump to the last breakdown bar (the build) one bar
        # before the reveal, and land drop 2 on it. Joins sit on downbeats with 15 ms equal-power crossfades.
        bar = 4 * BEAT
        b0 = a.bar0 if a.bar0 is not None else (drop % bar)
        d1, build, d2 = (int(v) for v in a.splice.split(","))
        R = int(round(reveal / bar))                     # reveal bar in the ad
        plan = [(0, d1, R - 1), (R - 1, build, 1), (R, d2, int(np.ceil(dur / bar)) - R + 1)]
        n = int(round(dur * SR)); seg = np.zeros((n, 2)); xf = int(0.015 * SR)
        for ad_bar, tr_bar, nb in plan:
            s0 = int(round(ad_bar * bar * SR)); t0 = int(round((b0 + tr_bar * bar) * SR))
            L = min(int(round(nb * bar * SR)), n - s0)
            piece = x[t0 - xf:t0 + L].copy()               # fade out INSIDE the bar: never carry the next downbeat's kick
            ramp = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
            piece[:xf] *= ramp[:, None]; piece[-xf:] *= ramp[::-1][:, None]
            a_ = s0 - xf; lo = max(0, -a_)
            seg[max(0, a_):max(0, a_) + len(piece) - lo][:n - max(0, a_)] += piece[lo:lo + n - max(0, a_)]
        seg[:xf] = x[int(round((b0 + d1 * bar) * SR)):int(round((b0 + d1 * bar) * SR)) + xf]   # clean first downbeat
        splice = {"bar0_s": round(b0, 3), "plan_ad_bar_track_bar_nbars": plan}
    else:
        seg = x[int(round(off * SR)):int(round(off * SR)) + int(round(dur * SR))].copy()
    if len(seg) < int(dur * SR):
        seg = np.concatenate([seg, np.zeros((int(dur * SR) - len(seg), 2))])
    fi = int(0.012 * SR)
    seg[:fi] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi)))[:, None]
    card = next(s for s in shots if s["id"] == "end")["t0"]
    fo0 = card + 1.2                                     # the card has landed; ease the music out under it
    t = np.arange(len(seg)) / SR
    g = np.clip(1 - (t - fo0) / (dur - 0.06 - fo0), 0, 1) ** 1.5
    seg *= g[:, None]
    seg[-int(0.05 * SR):] = 0
    wd = f"{T}/.work/{a.ad}"; os.makedirs(wd, exist_ok=True)
    if os.path.exists(f"{wd}/mix.wav") and not os.path.exists(f"{wd}/mix_v1_score.wav"):
        os.rename(f"{wd}/mix.wav", f"{wd}/mix_v1_score.wav")   # keep v1's built score beside it
    y, pre, m1 = BL.master(seg, FF, wd, target=-14.0, pre_ceiling=-2.4)
    y[-int(0.05 * SR):] = 0
    y[:fi] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi)))[:, None]
    BL.write_wav24(pre, y)
    pass2, verify = BL.finalize(FF, pre, f"{wd}/mix.wav", m1)
    info = {"track": os.path.basename(a.track), "beat_phase_s": round(phase, 4), "drop_in_track_s": round(drop, 3),
            "reveal_in_ad_s": round(reveal, 3), "track_offset_s": None if splice else round(off, 3), "splice": splice, "drop_candidates_db_s": [(round(d, 1), round(s, 3)) for d, s in cands],
            "master": {"I": verify["input_i"], "TP": verify["input_tp"], "LRA": verify["input_lra"]}}
    json.dump(info, open(f"{wd}/mix_music.json", "w"), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
