"""
Shared plumbing for the edit-refs tools: ffmpeg decode/encode pipes, WAV I/O,
and the Anti Stock loudness master.

Nothing here is an effect. The effects live in rapid_zoom.py and davinci_fx.py.
"""
import json, os, subprocess, sys, wave
import numpy as np

# Fast Cut spec (CLAUDE.md, Anti Stock section): 4K vertical, 29.97 fps.
W, H = 2160, 3840
FPS_NUM, FPS_DEN = 30000, 1001
FPS = FPS_NUM / FPS_DEN
FPS_STR = f"{FPS_NUM}/{FPS_DEN}"
SR = 48000

# The loudness chain from creator-kit/scripts/compose_reel.sh (which
# fastcut/build_reel.sh calls with --limit 0.84). Run here as two passes,
# because the footage-index notes found single-pass loudnorm lands ~1.3 LU low.
LOUD_I, LOUD_TP, LOUD_LRA = -14.0, -1.5, 11.0
LIMITER = "alimiter=limit=0.84:attack=5:release=60:level=false"

KIT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "sfx", "kit-v2"))


def run(cmd, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if r.returncode:
        tail = (r.stderr or "")[-1500:]
        sys.stderr.write(tail + "\n")
        raise SystemExit(f"failed: {' '.join(map(str, cmd))[:400]}")
    return r


def probe(path):
    """duration (s), width, height, fps (float), has_audio for a media file."""
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height,avg_frame_rate,nb_frames",
             "-of", "json", path])
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = any(s["codec_type"] == "audio" for s in j["streams"])
    out = {"duration": float(j["format"]["duration"]), "has_audio": a}
    if v:
        n, d = v["avg_frame_rate"].split("/")
        out.update(width=int(v["width"]), height=int(v["height"]),
                   fps=float(n) / float(d) if float(d) else 0.0,
                   nb_frames=int(v.get("nb_frames", 0) or 0))
    return out


def fill_vf(w, h):
    """Scale to cover the canvas and centre-crop: the 9:16 fill, no bars."""
    return (f"fps={FPS_STR},scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={w}:{h},setsar=1")


def read_frames(src, t_in, n, w, h):
    """Decode n frames from src starting at t_in, filled to w x h, as uint8 RGB."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t_in:.4f}", "-i", src,
                        "-vf", fill_vf(w, h), "-frames:v", str(n), "-an",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    if r.returncode:
        sys.stderr.write(r.stderr.decode(errors="replace")[-1500:])
        raise SystemExit(f"decode failed: {src} @ {t_in}")
    fs = w * h * 3
    got = len(r.stdout) // fs
    if got == 0:
        raise SystemExit(f"no frames decoded: {src} @ {t_in} (in-point past the end?)")
    frames = [np.frombuffer(r.stdout[i * fs:(i + 1) * fs], np.uint8).reshape(h, w, 3)
              for i in range(got)]
    while len(frames) < n:          # short clip: hold the last frame
        frames.append(frames[-1])
    return frames


class FrameReader:
    """Stream every frame of a clip (filled to w x h) without holding it all."""
    def __init__(self, src, w, h, t_in=None, dur=None):
        cmd = ["ffmpeg", "-v", "error"]
        if t_in is not None:
            cmd += ["-ss", f"{t_in:.4f}"]
        cmd += ["-i", src]
        if dur is not None:
            cmd += ["-t", f"{dur:.4f}"]
        cmd += ["-vf", fill_vf(w, h), "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.w, self.h, self.fs = w, h, w * h * 3

    def __iter__(self):
        done = False
        try:
            while True:
                b = self.p.stdout.read(self.fs)
                if len(b) < self.fs:
                    done = True
                    break
                yield np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        finally:
            if not done:            # caller stopped early: stop the decoder quietly
                self.p.kill()
            self.p.stdout.close()
            self.p.wait()


class FrameWriter:
    """Encode RGB frames to H.264 at the Fast Cut rate, optionally upscaling."""
    def __init__(self, out, w, h, out_w=W, out_h=H, crf=16, preset="medium"):
        vf = [] if (w, h) == (out_w, out_h) else [f"scale={out_w}:{out_h}:flags=lanczos"]
        vf.append("format=yuv420p")
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{w}x{h}", "-r", FPS_STR, "-i", "-", "-vf", ",".join(vf),
               "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
               "-profile:v", "high", "-r", FPS_STR, "-an", out]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.n = 0

    def write(self, frame):
        self.p.stdin.write(np.ascontiguousarray(frame, dtype=np.uint8).tobytes())
        self.n += 1

    def close(self):
        self.p.stdin.close()
        if self.p.wait():
            raise SystemExit("encode failed")


# ---------------------------------------------------------------- audio

def write_wav(path, x, sr=SR, bits=24):
    """x: float array (n,) or (n, ch) in [-1, 1]. 24-bit PCM by default."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    x = np.clip(x, -1.0, 1.0)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(x.shape[1]); wf.setsampwidth(bits // 8); wf.setframerate(sr)
        if bits == 24:
            i = np.round(x * 8388607).astype("<i4")
            b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
        else:
            b = np.round(x * 32767).astype("<i2").tobytes()
        wf.writeframes(b)


def read_audio(path, sr=SR, ch=2, t_in=None, dur=None):
    """Any file's audio as float32 (n, ch); empty array when it has none."""
    cmd = ["ffmpeg", "-v", "error"]
    if t_in is not None:
        cmd += ["-ss", f"{t_in:.4f}"]
    cmd += ["-i", path]
    if dur is not None:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-vn", "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, ch).copy()


def kit_sound(name):
    p = os.path.join(KIT, name + ".wav")
    if not os.path.exists(p):
        raise SystemExit(f"missing kit-v2 sound {p}: run gen_sfx_kit.py first")
    return read_audio(p)


def kit_meta():
    p = os.path.join(KIT, "kit.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def place(bed, snd, t, gain_db=0.0, sr=SR):
    """Mix snd into bed starting at t seconds (clipped to the bed's length)."""
    s = int(round(t * sr))
    if s < 0:
        snd, s = snd[-s:], 0
    e = min(len(bed), s + len(snd))
    if e > s:
        bed[s:e] += snd[:e - s] * (10 ** (gain_db / 20))
    return bed


def loudness(path):
    """Integrated LUFS, true peak dBTP, LRA of a file's audio (EBU R128 via loudnorm)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
                        f"loudnorm=I={LOUD_I}:TP={LOUD_TP}:LRA={LOUD_LRA}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    e = r.stderr
    j = json.loads(e[e.rfind("{"):e.rfind("}") + 1])
    return j


def master_audio(src_wav, out_wav):
    """Two-pass loudnorm to -14 LUFS, then the 0.84 limiter, back to 48 kHz."""
    m = loudness(src_wav)
    af = (f"loudnorm=I={LOUD_I}:TP={LOUD_TP}:LRA={LOUD_LRA}"
          f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true,aresample={SR},{LIMITER}")
    run(["ffmpeg", "-v", "error", "-y", "-i", src_wav, "-af", af,
         "-ar", str(SR), "-c:a", "pcm_s24le", out_wav])
    # Sparse, peaky audio (a bed of clicks) cannot reach -14 LUFS under the
    # 0.84 ceiling: loudnorm backs off to keep true peak. Forcing gain into the
    # limiter was tried and made +1.5 dBTP overs, so this only warns.
    got = float(loudness(out_wav)["input_i"])
    if abs(got - LOUD_I) > 1.0:
        print(f"warning: master landed at {got:.1f} LUFS, not {LOUD_I:.0f} (audio too peaky or "
              f"sparse to raise under the limiter)", file=sys.stderr)
    return m


def mux(video, audio_wav, out):
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio_wav,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
         "-ar", str(SR), "-shortest", "-movflags", "+faststart", out])
