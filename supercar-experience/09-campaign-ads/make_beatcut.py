"""
Cut a plate to the beat of a track, and use that track as the audio.

    python3 make_beatcut.py --car fall-rally --audio song.mp3 --dur 18 \
        --clip "a.mov@2.0" --clip "b.mp4@12.4" ...

Unlike make_montage.py, you give each clip only an IN point. The cut LENGTHS
come from the music: the script finds the beats, decides which of them to cut
on, and takes exactly that much from each clip in turn. The output plate
carries the track, not the footage's own sound.

Beat detection is spectral flux with no third-party audio library:

  1. decode to mono 22.05 kHz via ffmpeg
  2. short-time Fourier transform, magnitude
  3. spectral flux - sum of positive frame-to-frame change, which spikes on
     a transient (a drum hit) and stays flat through sustained tone
  4. adaptive peak pick over a local median, so a loud chorus does not
     swamp a quiet verse
  5. tempo from autocorrelation of the flux envelope, searched over 70-180
     BPM, then a phase-locked grid fitted to the detected onsets

Cutting on every onset gives a strobe. --every sets how many beats each cut
lasts (default 4, i.e. one bar of 4/4).
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SR = 22050
HOP = 512
WIN = 2048


def decode_mono(path: Path) -> np.ndarray:
    """Decode any audio/video file to a mono float array at SR."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn",
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    if not raw:
        sys.exit(f"no audio decoded from {path}")
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def spectral_flux(x: np.ndarray) -> np.ndarray:
    """Positive frame-to-frame spectral change: high on transients."""
    n = 1 + (len(x) - WIN) // HOP
    if n < 4:
        sys.exit("track too short to analyse")
    window = np.hanning(WIN).astype(np.float32)
    frames = np.lib.stride_tricks.as_strided(
        x, shape=(n, WIN), strides=(x.strides[0] * HOP, x.strides[0])) * window
    mag = np.abs(np.fft.rfft(frames, axis=1))
    # log compression keeps a loud section from dominating the envelope
    mag = np.log1p(mag * 8.0)
    diff = np.diff(mag, axis=0, prepend=mag[:1])
    flux = np.maximum(diff, 0).sum(axis=1)
    return flux / (flux.max() or 1.0)


def pick_onsets(flux: np.ndarray) -> np.ndarray:
    """Peaks that clear a local median, returned as frame indices."""
    w = 16
    pad = np.pad(flux, w, mode="edge")
    local = np.array([np.median(pad[i:i + 2 * w + 1]) for i in range(len(flux))])
    thresh = local + 0.10 * flux.std()
    peaks = []
    for i in range(1, len(flux) - 1):
        if flux[i] > thresh[i] and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1]:
            if not peaks or i - peaks[-1] > 4:      # ~93 ms refractory
                peaks.append(i)
    return np.array(peaks)


def estimate_bpm(flux: np.ndarray) -> float:
    """Autocorrelate the onset envelope and take the strongest musical lag."""
    f = flux - flux.mean()
    ac = np.correlate(f, f, mode="full")[len(f) - 1:]
    fps = SR / HOP
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70)     # 180 down to 70 BPM
    hi = min(hi, len(ac) - 1)
    if hi <= lo:
        return 120.0
    lag = lo + int(np.argmax(ac[lo:hi]))
    return float(60.0 * fps / lag)


def beat_grid(flux: np.ndarray, bpm: float, onsets: np.ndarray, total: float) -> np.ndarray:
    """A steady grid at bpm, phase-shifted to sit on as many onsets as it can."""
    period = 60.0 / bpm
    fps = SR / HOP
    onset_t = onsets / fps
    best_phase, best_score = 0.0, -1.0
    for phase in np.linspace(0, period, 48, endpoint=False):
        grid = np.arange(phase, total, period)
        if not len(grid) or not len(onset_t):
            continue
        # score = how close each onset sits to its nearest grid line
        d = np.abs(onset_t[:, None] - grid[None, :]).min(axis=1)
        score = float((d < 0.07).sum())
        if score > best_score:
            best_phase, best_score = phase, score
    return np.arange(best_phase, total, period)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


FILL = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--car", required=True)
    ap.add_argument("--audio", required=True, help="track to cut to and to use as the audio")
    ap.add_argument("--clip", action="append", required=True,
                    metavar="FILE@IN", help="source and in-point; lengths come from the beats")
    ap.add_argument("--dur", type=float, default=18.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--every", type=int, default=4,
                    help="beats per cut: 4 = one bar, 2 = half bar, 8 = two bars")
    ap.add_argument("--audio-start", type=float, default=0.0,
                    help="seconds into the track to start, to land on a chorus")
    ap.add_argument("--min-cut", type=float, default=0.6,
                    help="never make a cut shorter than this")
    args = ap.parse_args()

    audio = Path(args.audio).expanduser()
    if not audio.exists():
        sys.exit(f"missing audio: {audio}")

    print(f"analysing {audio.name} ...")
    x = decode_mono(audio)
    if args.audio_start:
        x = x[int(args.audio_start * SR):]
    x = x[: int((args.dur + 2) * SR)]
    flux = spectral_flux(x)
    onsets = pick_onsets(flux)
    bpm = estimate_bpm(flux)
    grid = beat_grid(flux, bpm, onsets, args.dur)
    print(f"  {bpm:.1f} BPM · {len(onsets)} onsets · {len(grid)} beats in {args.dur:.1f}s")

    cuts = [t for i, t in enumerate(grid) if i % args.every == 0 and t < args.dur]
    if not cuts or cuts[0] > 0.01:
        cuts = [0.0] + cuts
    bounds = cuts + [args.dur]
    # drop any segment the music made too short to read
    merged = [bounds[0]]
    for b in bounds[1:]:
        if b - merged[-1] >= args.min_cut:
            merged.append(b)
    merged[-1] = args.dur
    segs = [(merged[i], merged[i + 1] - merged[i]) for i in range(len(merged) - 1)]
    print(f"  {len(segs)} cuts, one every {args.every} beats "
          f"({60.0 / bpm * args.every:.2f}s)")

    specs = []
    for c in args.clip:
        f, _, t = c.rpartition("@")
        specs.append((Path(f).expanduser(), float(t)))

    car = HERE / args.car
    src = car / "source"
    src.mkdir(parents=True, exist_ok=True)
    work = src / "_beatcut"
    work.mkdir(exist_ok=True)

    parts = []
    for i, (start, dur) in enumerate(segs):
        path, seek = specs[i % len(specs)]
        # walk the in-point forward when a clip is reused, so a repeat is not identical
        seek = seek + dur * (i // len(specs))
        avail = probe_duration(path)
        if seek + dur > avail:
            seek = max(0.0, avail - dur - 0.05)
        out = work / f"{i:02d}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{seek:.3f}", "-i", str(path),
             "-t", f"{dur:.3f}", "-an", "-vf", f"{FILL},fps={args.fps}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(out)],
            check=True)
        parts.append(out)
        print(f"  {i + 1:2d}. {path.name} @{seek:6.2f}s  +{dur:.2f}s  -> cut at {start:.2f}s")

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    silent = work / "_video.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(silent)], check=True)

    plate = src / "plate-1080x1920.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-i", str(silent),
         "-ss", f"{args.audio_start:.3f}", "-i", str(audio),
         "-map", "0:v", "-map", "1:a",
         "-t", f"{args.dur:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k",
         "-af", "afade=t=out:st=%.2f:d=0.6" % max(0.0, args.dur - 0.6),
         "-movflags", "+faststart", str(plate)], check=True)

    (src / "beatcut.json").write_text(json.dumps({
        "audio": str(audio), "bpm": round(bpm, 2), "every": args.every,
        "audio_start": args.audio_start, "duration": args.dur,
        "cuts": [round(s, 3) for s, _ in segs],
        "clips": [f"{p}@{t}" for p, t in specs],
    }, indent=2) + "\n")

    mb = plate.stat().st_size / 1e6
    print(f"plate: {plate} ({mb:.1f} MB, {len(segs)} cuts, {args.dur:.1f}s, music track)")


if __name__ == "__main__":
    main()
