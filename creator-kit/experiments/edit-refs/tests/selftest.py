#!/usr/bin/env python3
"""
SELF-TEST ONLY. Runs every edit-refs tool on synthetic clips made with ffmpeg
testsrc2 and checks the outputs. Nothing produced here is a cut, a preview or
a result on real footage; the outputs go to tests/out/ (git-ignored).

    python3 tests/selftest.py            # full-resolution run
    python3 tests/selftest.py --quick    # rapid_zoom at --work-res 1080x1920

Checks: kit-v2 files exist, 48 kHz, peak -1 dBFS; rapid_zoom and each
davinci_fx effect give the expected duration, 2160x3840, 29.97 fps; the
rapid-zoom land frame (<= 2.0 s) is sharper (Laplacian variance) than every
blurred cut frame; the master sits near -14 LUFS under the 0.84 limiter.
"""
import json, os, subprocess, sys, time, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import media as M  # noqa: E402

OUT = os.path.join(HERE, "out")
SRC = os.path.join(OUT, "synthetic_src")
PY = sys.executable
results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""), flush=True)


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print((r.stderr or r.stdout)[-1500:])
        raise SystemExit(f"command failed: {' '.join(cmd)[:300]}")
    return r.stdout


def synth(name, hue, dur=2.0, audio=False):
    p = os.path.join(SRC, name)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
           "-i", f"testsrc2=s=1080x1920:r=30000/1001:d={dur},hue=h={hue},format=gbrp,"
                 # a 16 px checker multiplied in: fine detail everywhere, so the
                 # Laplacian measures blur rather than encoder noise on flat colour
                 "geq=r='r(X,Y)*(0.55+0.45*mod(floor(X/16)+floor(Y/16),2))'"
                 ":g='g(X,Y)*(0.55+0.45*mod(floor(X/16)+floor(Y/16),2))'"
                 ":b='b(X,Y)*(0.55+0.45*mod(floor(X/16)+floor(Y/16),2))'"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=f=220:d={dur}:sample_rate=48000", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", p]
    sh(cmd)
    return p


def lapvar(frame):
    g = frame.astype(np.float32).mean(axis=2)
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var())


def check_spec(name, path, want_dur, tol=0.07):
    i = M.probe(path)
    ok(f"{name}: resolution 2160x3840", (i["width"], i["height"]) == (2160, 3840), f"{i['width']}x{i['height']}")
    ok(f"{name}: fps 29.97", abs(i["fps"] - M.FPS) < 0.01, f"{i['fps']:.3f}")
    ok(f"{name}: duration {want_dur:.3f}s", abs(i["duration"] - want_dur) <= tol, f"{i['duration']:.3f}s")
    return i


def frames_at(path, idxs, w=M.W, h=M.H):
    """Only the frames asked for, as {index: frame}; 4K frames are 25 MB each."""
    want, out = set(idxs), {}
    for k, fr in enumerate(M.FrameReader(path, w, h)):
        if k in want:
            out[k] = fr.copy()
        if k >= max(want):
            break
    return out


def lapvars(path, n):
    lv = []
    for k, fr in enumerate(M.FrameReader(path, M.W, M.H)):
        lv.append(lapvar(fr))
        if k + 1 >= n:
            break
    return lv


def test_kit():
    sh([PY, os.path.join(ROOT, "gen_sfx_kit.py")])
    meta = json.load(open(os.path.join(M.KIT, "kit.json")))["sounds"]
    need = ["rapid_click_3f", "mech_click_a", "mech_click_b", "button", "whoosh", "big_flash",
            "whoosh_flash", "glitch_1", "glitch_2", "glitch_3", "zoom_riser"]
    ok("kit: every required sound present", all(n in meta and os.path.exists(os.path.join(M.KIT, n + ".wav")) for n in need))
    bad = []
    for n in meta:
        with wave.open(os.path.join(M.KIT, n + ".wav")) as wf:
            if wf.getframerate() != 48000 or wf.getsampwidth() != 3:
                bad.append(n)
        pk = 20 * np.log10(np.abs(M.read_audio(os.path.join(M.KIT, n + ".wav"))).max())
        if abs(pk + 1.0) > 0.1:
            bad.append(f"{n} peak {pk:.2f}")
    ok("kit: 48 kHz 24-bit, peak -1 dBFS", not bad, ", ".join(bad))
    ok("kit: audition.wav exists", os.path.exists(os.path.join(M.KIT, "audition.wav")))


def test_rapid_zoom(quick):
    clips = [f"{synth(f'run{i:02d}.mp4', i * 36)}@{0.2 + 0.05 * i:.2f}" for i in range(10)]
    payoff = synth("payoff.mp4", 200, 3.0)
    rem = synth("remainder.mp4", 90, 3.0, audio=True)
    out = os.path.join(OUT, "selftest_rapid_zoom.mp4")
    cmd = [PY, os.path.join(ROOT, "rapid_zoom.py"), "--clips", *clips, "--payoff", payoff,
           "--payoff-in", "0.5", "--sfx", "--remainder", rem, "--remainder-in", "0", "--out", out]
    if quick:
        cmd += ["--work-res", "1080x1920"]
    t0 = time.time(); sh(cmd); took = time.time() - t0
    side = json.load(open(os.path.splitext(out)[0] + ".json"))
    want = side["opening_frames"] / M.FPS + 3.0
    check_spec("rapid_zoom (open + remainder)", out, want)
    ok("rapid_zoom: land at or before 2.0 s", side["land_time"] <= 2.0, f"land frame {side['land_frame']} at {side['land_time']}s")
    lv = lapvars(out, side["land_frame"] + 1)
    blurred = [r["frame"] for r in side["frames"] if r["strength"] >= 0.4]
    land = lv[side["land_frame"]]
    worst = max(lv[i] for i in blurred)
    ok("rapid_zoom: land frame sharper than every blurred cut frame", land > worst,
       f"land {land:.1f} vs max blurred {worst:.1f} over {len(blurred)} frames")
    ok("rapid_zoom: Add layer on 10 frames", sum(r["add"] for r in side["frames"]) == 10)
    loud = M.loudness(out)
    ok("rapid_zoom: integrated loudness -14 LUFS +/-1", abs(float(loud["input_i"]) + 14) <= 1.0, f"{loud['input_i']} LUFS")
    pk = np.abs(M.read_audio(os.path.join(os.path.splitext(out)[0] + "_work", "audio_master.wav"))).max()
    ok("rapid_zoom: master peak <= 0.84 limiter", pk <= 0.8401, f"peak {pk:.4f}")
    print(f"      rapid_zoom took {took:.1f}s ({'quick 1080x1920 work res' if quick else 'full res'})")

    out2 = os.path.join(OUT, "selftest_rapid_zoom_silent.mp4")
    sh([PY, os.path.join(ROOT, "rapid_zoom.py"), "--clips", *clips[:4], "--payoff", payoff,
        "--work-res", "540x960", "--hold", "0.5", "--out", out2])
    s2 = json.load(open(os.path.splitext(out2)[0] + ".json"))
    check_spec("rapid_zoom (open only, 4 clips cycled, no sfx)", out2, s2["opening_frames"] / M.FPS)
    return rem


def test_fx(src):
    cut = int(round(1.5 * M.FPS)); i0 = int(round(1.0 * M.FPS))
    idx = [5, 45, cut, cut - 1, i0, i0 + 1]
    base = frames_at(src, idx)
    cases = [
        ("flashbox white", ["flashbox", "--at", "1.5", "--frames", "5", "--mode", "white"]),
        ("flashbox box", ["flashbox", "--at", "1.5", "--frames", "6", "--mode", "box"]),
        ("inverted_flicker full", ["flicker", "--start", "1.0", "--end", "2.0", "--mode", "full"]),
        ("inverted_flicker luma", ["flicker", "--start", "1.0", "--end", "2.0", "--mode", "luma"]),
        ("difference_burn", ["burn", "--start", "0.5", "--end", "2.5"]),
    ]
    want = M.probe(src)["duration"]
    for name, args in cases:
        out = os.path.join(OUT, f"selftest_{name.replace(' ', '_')}.mp4")
        sh([PY, os.path.join(ROOT, "davinci_fx.py"), *args, "--in", src, "--out", out])
        check_spec(name, out, want)
        got = frames_at(out, idx)
        if name == "flashbox white":
            ok(f"{name}: cut frame is white", got[cut].mean() > 250, f"mean {got[cut].mean():.1f}")
        if name == "flashbox box":
            mid = got[cut - 1]
            ok(f"{name}: box grows from centre before the cut",
               mid[M.H // 2, M.W // 2].mean() > 250 and abs(float(mid[5, 5].mean()) - float(base[cut - 1][5, 5].mean())) < 30)
        if name.startswith("inverted_flicker"):
            d_in = np.abs(got[i0].astype(int) - (255 - base[i0].astype(int))).mean()
            d_out = np.abs(got[i0 + 1].astype(int) - base[i0 + 1].astype(int)).mean()
            if name.endswith("full"):
                ok(f"{name}: alternates inverted / normal", d_in < 6 and d_out < 6, f"{d_in:.1f}, {d_out:.1f}")
            else:
                ok(f"{name}: changes only part of the frame", 0 < (got[i0] != base[i0]).mean() < 0.9)
        if name == "difference_burn":
            d_win = np.abs(got[45].astype(int) - base[45].astype(int)).mean()
            d_pre = np.abs(got[5].astype(int) - base[5].astype(int)).mean()
            ok(f"{name}: changes the window, leaves outside it", d_win > 15 and d_pre < 3, f"{d_win:.1f} vs {d_pre:.1f}")


def test_teaser():
    """beats_to_spec -> ../kinetic/build_kinetic.py -> master_loudness, on synthetic clips.
    The bed is synthetic noise standing in for music; it is not a cut."""
    hits = os.path.join(OUT, "synthetic_hits.txt")
    open(hits, "w").write("# synthetic hit list for the self-test\n0.40\n0.90\n1.30\n1.65\n2.10\n2.50\n")
    bed = os.path.join(OUT, "synthetic_bed.wav")   # dense stand-in for a music bed: pink noise + 2 Hz kick
    sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.25:d=4:r=48000",
        "-f", "lavfi", "-i", "sine=f=55:d=4:r=48000,volume='0.9*exp(-12*mod(t,0.5))':eval=frame",
        "-filter_complex", "amix=inputs=2:normalize=0", "-ac", "2", bed])
    spec = os.path.join(OUT, "selftest_teaser_spec.json")
    sh([PY, os.path.join(ROOT, "beats_to_spec.py"), "--beats", hits, "--clips",
        "run00.mp4@0.2", "run03.mp4@0.4", "run06.mp4@0.1", "--audio-track",
        bed, "--flash", "--out", spec])
    sp = json.load(open(spec))
    total = sum(s.get("dur", s.get("frames", 0) / 30) for s in sp["shots"])
    ok("teaser spec: shots span 0 to last hit + 1.0 s tail", abs(total - 3.5) < 0.01, f"{total:.3f}s")
    ok("teaser spec: a flash on every hit, none on the lead-in",
       sum(1 for s in sp["shots"] if s.get("fx") == "flash") == 6 and "clip" in sp["shots"][0])
    kin = os.path.join(OUT, "selftest_teaser_kinetic.mp4")
    sh([PY, os.path.join(ROOT, "..", "kinetic", "build_kinetic.py"), "--spec", spec, "--footage", SRC,
        "--work", os.path.join(OUT, "teaser_work"), "--out", kin])
    fin = os.path.join(OUT, "selftest_teaser_mastered.mp4")
    sh([PY, os.path.join(ROOT, "master_loudness.py"), kin, fin])
    i = M.probe(fin)
    ok("teaser: build_kinetic output 1080x1920 at 30 fps, 3.5 s",
       (i["width"], i["height"]) == (1080, 1920) and abs(i["fps"] - 30) < 0.01 and abs(i["duration"] - 3.5) < 0.07,
       f"{i['width']}x{i['height']} {i['fps']:.2f} fps {i['duration']:.3f}s")
    j = M.loudness(fin)
    ok("teaser: mastered to -14 LUFS +/-1", abs(float(j["input_i"]) + 14) <= 1.0, f"{j['input_i']} LUFS")


def main():
    quick = "--quick" in sys.argv
    os.makedirs(SRC, exist_ok=True)
    test_kit()
    rem = test_rapid_zoom(quick)
    test_fx(rem)
    test_teaser()
    n_fail = sum(1 for _, c in results if not c)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
