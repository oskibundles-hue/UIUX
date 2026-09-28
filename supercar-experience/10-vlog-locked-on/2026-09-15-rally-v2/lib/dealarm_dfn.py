"""dealarm_dfn.py -- the car-alarm removal for one clip span (rally vlog v2.4). Runs in the DeepFilterNet3 venv
(config paths.dfnPython: torch, DeepFilterNet, scipy, pyloudnorm), never in the build's own python; lib/mix.py calls
it as a subprocess and caches the result (.work/dealarm/).

    python dealarm_dfn.py clean job.json      clean one span (job: see mix.py prepare_dealarm)
    python dealarm_dfn.py voice job.json      voice-only loudness of dialog pieces (the level check, lib/audiocheck.py)

clean, on the clip's own camera audio, BEFORE the dialog chain (filter, compressor, levelling):
  voice  = DeepFilterNet3(span)                               (speech only; weights HF fal/DeepFilterNet3)
  rest   = span - voice                                       (ambience, handling, and the alarm)
  rest'  = rest with the alarm bands cut (2.85-3.75 kHz and 6.0-7.25 kHz, -45 dB, 80 Hz raised skirts)
  voice' = voice tone-matched to the same clip's clean pieces (DeepFilterNet voice of those, 1/3-octave long-term
           spectrum over the speech frames, smoothed, limited to -6..+6 dB), then any tone left in the alarm bands
           clamped to at most `clampDb` above the neighbouring bands (the alarm residue DeepFilterNet leaves in the
           voice), then the 4.5-9 kHz range the clamp took from the "s" sounds measured again and given back
  out    = voice' x lift + rest'                              (lift: the ~1.5 dB DeepFilterNet takes off the voice)
This is the v2.1-v2.3 treatment (scratchpad clarity/fix_v22.py, fix23/fix_v23.py), done once on the source span
instead of patched into the finished masters, so every dialog piece is levelled on its voice, not on the alarm.
"""
import json
import os
import sys
import types
import wave

import numpy as np

SR = 48000
CS = 1000 * 2 ** (np.arange(-13, 14) / 3)          # 1/3-octave centres, 62.5 Hz - 16 kHz


# ------------------------------------------------------------------ io (float32 WAV, the format mix.py writes)
def read_wav(p):
    w = wave.open(p)
    sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
    b = w.readframes(n)
    assert sr == SR, (p, sr)
    if sw == 2:
        x = np.frombuffer(b, '<i2').astype(np.float32) / 32768
    elif sw == 3:
        u = np.frombuffer(b, np.uint8).reshape(-1, 3).astype(np.int32)
        x = ((u[:, 0] | (u[:, 1] << 8) | (u[:, 2] << 16)) << 8 >> 8).astype(np.float32) / 8388608
    else:
        raise SystemExit(f'{p}: {sw * 8}-bit wav not supported (mix.py writes 24-bit)')
    return x.reshape(-1, ch)


def write_wav24(p, x):
    x = np.clip(np.asarray(x, np.float64), -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    tmp = p + '.part.wav'
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(3); w.setframerate(SR); w.writeframes(b)
    os.replace(tmp, p)


# ------------------------------------------------------------------ DeepFilterNet3
_M = None


def model():
    """DeepFilterNet3, weights from Hugging Face (fal/DeepFilterNet3: config.ini + model.safetensors). torchaudio.backend
    (gone from new torchaudio) is only imported by df/io.py for a type name, so a stand-in module is registered first."""
    global _M
    if _M is None:
        mb = types.ModuleType('torchaudio.backend'); mc = types.ModuleType('torchaudio.backend.common')

        class AudioMetaData:
            pass
        mc.AudioMetaData = AudioMetaData; mb.common = mc
        sys.modules.setdefault('torchaudio.backend', mb); sys.modules.setdefault('torchaudio.backend.common', mc)
        import torch
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        from df.enhance import init_df, enhance
        cfg = hf_hub_download('fal/DeepFilterNet3', 'config.ini'); wts = hf_hub_download('fal/DeepFilterNet3', 'model.safetensors')
        m, state, _ = init_df(model_base_dir=os.path.dirname(cfg), epoch='none', log_level='ERROR')
        res = m.load_state_dict(load_file(wts), strict=False)
        assert not res.missing_keys and not res.unexpected_keys, res
        m.eval()
        assert state.sr() == SR
        _M = (m, state, enhance, torch)
    return _M


def dfn(x):
    m, state, enhance, torch = model()
    with torch.no_grad():
        return enhance(m, state, torch.from_numpy(np.ascontiguousarray(x.T, np.float32))).numpy().T[:len(x)].astype(np.float32)


# ------------------------------------------------------------------ dsp
def bandstop(x, bands, depth_db=-45, N=2048, H=256):
    """cut the alarm bands (80 Hz raised skirts) out of x, STFT overlap-add (fix_vlog.py, v2.1)."""
    win = np.hanning(N).astype(np.float32); f = np.fft.rfftfreq(N, 1 / SR)
    g = np.ones(len(f), np.float32); floor = 10 ** (depth_db / 20)
    for a, b in bands:
        k = np.clip(np.minimum(f - (a - 80), (b + 80) - f) / 80, 0, 1)
        g = np.minimum(g, 1 - k * (1 - floor))
    out = np.zeros_like(x)
    for c in range(x.shape[1]):
        s = np.concatenate([np.zeros(N, np.float32), x[:, c], np.zeros(N, np.float32)]); n = 1 + (len(s) - N) // H
        y = np.zeros(len(s), np.float32); ws = np.zeros(len(s), np.float32)
        for i in range(n):
            fr = np.fft.rfft(s[i * H:i * H + N] * win) * g
            y[i * H:i * H + N] += np.fft.irfft(fr, N).astype(np.float32) * win; ws[i * H:i * H + N] += win ** 2
        ok = ws > 1e-3; y[ok] /= ws[ok]; y[~ok] = s[~ok]
        out[:, c] = y[N:N + len(x)]
    return out


def ltas(x, gate_db=-12):
    """1/3-octave long-term spectrum over the speech frames (within gate_db of the loudest), 200 Hz-5 kHz mean = 0 dB."""
    m = x.mean(1); N, H = 4096, 2048; win = np.hanning(N)
    fr = np.array([np.abs(np.fft.rfft(m[i:i + N] * win)) ** 2 for i in range(0, len(m) - N, H)])
    e = 10 * np.log10(fr.sum(1) + 1e-12); fr = fr[e > e.max() + gate_db]; f = np.fft.rfftfreq(N, 1 / SR)
    out = np.array([10 * np.log10(fr[:, (f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].mean() + 1e-15) for c in CS])
    sp = (CS >= 200) & (CS <= 5000)
    return out - out[sp].mean()


def smooth3(d):
    return np.convolve(np.pad(d, 1, mode='edge'), np.ones(3) / 3, mode='valid')


def limit_eq(d):
    return np.where(CS < 120, 0, np.where(CS < 250, np.clip(d, -6, 4), np.where(CS > 12000, np.clip(d, -6, 3), np.clip(d, -6, 6))))


def fir(d):
    from scipy.signal import firwin2
    f = np.concatenate([[0], CS[CS < SR / 2], [SR / 2]])
    g = 10 ** (np.concatenate([[0], d[CS < SR / 2], [d[CS < SR / 2][-1]]]) / 20)
    return firwin2(4095, f, g, fs=SR)


def apply(x, h):
    from scipy.signal import fftconvolve
    return np.stack([fftconvolve(x[:, c], h, mode='same') for c in range(x.shape[1])], 1).astype(np.float32)


def clamp_tones(x, clamps, margin_db=4.0):
    """any tone in an alarm band that stands more than margin_db above the mean of its two neighbouring bands is
    pulled down to that (per STFT frame, gain smoothed over 3 frames so it does not warble)."""
    from scipy.signal import stft, istft
    out = np.empty_like(x)
    for c in range(x.shape[1]):
        f, t, Z = stft(x[:, c], SR, nperseg=2048, noverlap=1536); P = np.abs(Z) ** 2; G = np.ones_like(P)
        for (lo, hi), (l0, l1), (r0, r1) in clamps:
            ref = 0.5 * (P[(f >= l0) & (f <= l1)].mean(0) + P[(f >= r0) & (f <= r1)].mean(0)) * 10 ** (margin_db / 10)
            s = (f >= lo) & (f <= hi); G[s] = np.minimum(1, np.sqrt(ref[None, :] / np.maximum(P[s], 1e-20)))
        G = np.apply_along_axis(lambda r: np.convolve(r, np.ones(3) / 3, mode='same'), 1, G)
        out[:, c] = istft(Z * G, SR, nperseg=2048, noverlap=1536)[1][:len(x)]
    return out


def tone_excess(x, clamps, mask=None, q=95):
    """per alarm band: the q-th percentile, over the band's STFT bins in the speech frames, of each bin's power above the
    mean of the two neighbouring bands, dB (the quantity the clamp limits to clampDb; same STFT as the clamp)."""
    from scipy.signal import stft
    res = []
    for (lo, hi), (l0, l1), (r0, r1) in clamps:
        vals = []
        for c in range(x.shape[1]):
            f, t, Z = stft(x[:, c], SR, nperseg=2048, noverlap=1536); P = np.abs(Z) ** 2
            keep = np.ones(len(t), bool) if mask is None else mask(t)
            nb = 0.5 * (P[(f >= l0) & (f <= l1)].mean(0) + P[(f >= r0) & (f <= r1)].mean(0))
            e = 10 * np.log10(P[(f >= lo) & (f <= hi)][:, keep] + 1e-20) - 10 * np.log10(nb[keep] + 1e-20)[None, :]
            vals.append(e.ravel())
        v = np.concatenate(vals)
        res.append(round(float(np.percentile(v, q)), 2) if len(v) else None)
    return res


def band_db(x, lo, hi):
    X = np.fft.rfft(x.mean(1)); f = np.fft.rfftfreq(len(x), 1 / SR)
    return round(float(10 * np.log10((np.abs(X[(f >= lo) & (f <= hi)]) ** 2).sum() / len(x) + 1e-20)), 2)


# ------------------------------------------------------------------ jobs
def clean(job):
    x = read_wav(job['in'])
    bands = [tuple(b) for b in job['bands']]
    clamps = [(tuple(c[0]), tuple(c[1]), tuple(c[2])) for c in job['clamps']]
    voice = dfn(x)
    refs = [read_wav(p) for p in job['refs']]
    ref_voice = np.concatenate([dfn(r)[int(0.4 * SR):] for r in refs])       # 0.4 s pre-roll per piece (DeepFilterNet settles)
    rest = x - voice
    rest2 = bandstop(rest, bands, job.get('depthDb', -45))
    sp = np.zeros(len(x), bool)
    for a, b in job['speech']:
        sp[int(a * SR):int(b * SR)] = True
    d = limit_eq(smooth3(ltas(ref_voice) - ltas(voice[sp]))) if job.get('tone', True) else np.zeros(len(CS))
    vcl = clamp_tones(apply(voice, fir(d)), clamps, job.get('clampDb', 4.0))
    if job.get('tone', True):
        d2 = smooth3(ltas(ref_voice) - ltas(vcl[sp]))
        d2 = np.where((CS >= 4500) & (CS <= 9000), np.clip(d2, -3, 3), 0)
        d = limit_eq(d + d2)
        vcl = clamp_tones(apply(voice, fir(d)), clamps, job.get('clampDb', 4.0))
    out = vcl * 10 ** (job.get('liftDb', 1.5) / 20) + rest2
    write_wav24(job['out'], out)
    in_sp = lambda tt: np.array([sp[min(len(sp) - 1, int(v * SR))] for v in tt])  # noqa: E731
    rep = dict(out=job['out'], seconds=round(len(x) / SR, 3),
               tone_eq_db={f'{c:.0f}': round(float(v), 2) for c, v in zip(CS, d) if 100 <= c <= 16000},
               alarm_band_db_rest_before=[band_db(rest, *b) for b in bands], alarm_band_db_rest_after=[band_db(rest2, *b) for b in bands],
               tone_excess_voice_before_db=tone_excess(voice, clamps, in_sp), tone_excess_voice_after_db=tone_excess(vcl, clamps, in_sp),
               tone_excess_ref_db=tone_excess(ref_voice, clamps),
               alarm_band_db_span_before=[band_db(x, *b) for b in bands], alarm_band_db_span_after=[band_db(out, *b) for b in bands])
    json.dump(rep, open(job['out'] + '.json', 'w'), indent=1)
    print(json.dumps(rep))


def voice_loudness(job):
    """DeepFilterNet voice of each piece of a dialog stem -> BS.1770 integrated loudness (pyloudnorm), dB."""
    import pyloudnorm as pyln
    x = read_wav(job['stem']) * job.get('gain', 1.0)
    meter = pyln.Meter(SR)
    out = []
    for p in job['pieces']:
        a, b = int((p['t0'] - 0.4) * SR), int(p['t1'] * SR)
        v = dfn(x[max(0, a):b])[int(0.4 * SR) if a >= 0 else 0:]
        whole = x[int(p['t0'] * SR):b]
        out.append(dict(p, voice_lufs=round(float(meter.integrated_loudness(v.astype(np.float64))), 2),
                        piece_lufs=round(float(meter.integrated_loudness(whole.astype(np.float64))), 2)))
    json.dump(out, open(job['out'], 'w'), indent=1)
    print(json.dumps(out))


if __name__ == '__main__':
    mode, jp = sys.argv[1], sys.argv[2]
    job = json.load(open(jp))
    {'clean': clean, 'voice': voice_loudness}[mode](job)
