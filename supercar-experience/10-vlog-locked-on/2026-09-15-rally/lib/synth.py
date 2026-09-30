"""
synth.py -- numpy-only DSP + instrument library for the Supercar Experience showcase sound bed.

No scipy, no samples, no downloads: every sound is generated here from sines, noise and
FFT-domain filters, so the bed is 100% original and cleared for paid social.

Building blocks
  fft_filter(x, lo, hi, slope)      zero-phase high/low-pass on a whole buffer (time-invariant)
  bandpass(x, fc, q)                zero-phase resonant band-pass
  stft_mask(x, fn)                  time-varying filter: fn(times, freqs) -> gain matrix (sweeps, whooshes)
  conv(x, ir)                       FFT convolution (reverbs, resonator bodies)
  reverb_ir(t60, ...) / reverb(x)   synthetic stereo plate/hall (decorrelated decaying noise, HF damping)
  varispeed(x, rate)                playback-rate curve (tape stop, pitch drops)
  pan(x, p) / saturate(x, drive)    equal-power pan, tanh saturation
  limiter(x, ceiling_db)            4x-oversampled true-peak look-ahead brickwall (numpy, no loop)

Instruments (all return float64 mono unless noted, SR = 48000)
  kick, e808, clap, snare, hat, impact (stereo), braam (stereo), whoosh (stereo), riser (stereo),
  pad (stereo), pluck, bell, engine (stereo: flat-six or cross-plane V8 physical-ish model), rpm_sim

Everything is deterministic for a given numpy Generator seed.
"""
import numpy as np

SR = 48000


# ----------------------------------------------------------------- helpers
def n_of(sec):
    return int(round(sec * SR))


def tax(n):
    return np.arange(n) / SR


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def db(x):
    return 10 ** (x / 20)


def _freqs(n):
    return np.fft.rfftfreq(n, 1 / SR)


def fft_filter(x, lo=None, hi=None, slope=4):
    """Zero-phase Butterworth-shaped HP (lo) and/or LP (hi) magnitude response. x: (n,) or (n,ch)."""
    n = x.shape[0]
    X = np.fft.rfft(x, axis=0)
    f = _freqs(n)
    g = np.ones_like(f)
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * slope))
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (2 * slope))
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n=n, axis=0)


def bandpass(x, fc, q=1.0):
    n = x.shape[0]
    X = np.fft.rfft(x, axis=0)
    f = np.maximum(_freqs(n), 1e-3)
    g = 1 / np.sqrt(1 + q * q * (f / fc - fc / f) ** 2)
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n=n, axis=0)


def stft_mask(x, fn, n_fft=2048, hop=512):
    """Time-varying spectral gain. fn(times[F], freqs[B]) -> gain[F, B]. Mono in, mono out."""
    n = len(x)
    win = np.sqrt(np.hanning(n_fft + 1)[:-1])
    pad = np.concatenate([np.zeros(n_fft), x, np.zeros(n_fft + hop)])
    starts = np.arange(0, len(pad) - n_fft, hop)
    frames = np.lib.stride_tricks.sliding_window_view(pad, n_fft)[starts] * win
    X = np.fft.rfft(frames, axis=1)
    times = (starts + n_fft / 2 - n_fft) / SR
    X *= fn(times, _freqs(n_fft))
    y = np.fft.irfft(X, n=n_fft, axis=1) * win
    out = np.zeros(len(pad))
    norm = np.zeros(len(pad))
    for i, s in enumerate(starts):
        out[s:s + n_fft] += y[i]
        norm[s:s + n_fft] += win ** 2
    out /= np.maximum(norm, 1e-6)
    return out[n_fft:n_fft + n]


def conv(x, ir):
    """FFT convolution; x (n,) or (n,c); ir (m,) or (m,c). Output length n+m-1."""
    n = x.shape[0] + ir.shape[0] - 1
    N = 1 << int(np.ceil(np.log2(n)))
    X = np.fft.rfft(x, N, axis=0)
    H = np.fft.rfft(ir, N, axis=0)
    if X.ndim == 1 and H.ndim == 2:
        X = X[:, None]
    if X.ndim == 2 and H.ndim == 1:
        H = H[:, None]
    return np.fft.irfft(X * H, N, axis=0)[:n]


def reverb_ir(rng, t60=2.2, predelay=0.012, damp=0.35, width=1.0, dur=None):
    """Stereo synthetic hall. damp = fraction of T60 the >4 kHz band keeps (darker tail when small)."""
    dur = dur or t60 * 1.1
    n = n_of(dur)
    t = tax(n)
    irs = []
    for _ in range(2):
        w = rng.standard_normal(n)
        lo = fft_filter(w, hi=4000, slope=2) * np.exp(-6.9 * t / t60)
        hi = fft_filter(w, lo=4000, slope=2) * np.exp(-6.9 * t / (t60 * damp))
        irs.append(lo + hi)
    L, R = irs
    M = (L + R) / 2
    L, R = M + width * (L - M), M + width * (R - M)
    ir = np.stack([L, R], 1)
    ir *= np.minimum(1, t / 0.004)[:, None]           # soften onset
    ir = np.concatenate([np.zeros((n_of(predelay), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum() / 2)


def reverb(x, ir, wet=0.3):
    xs = x if x.ndim == 2 else np.stack([x, x], 1)
    xm = xs.mean(1)
    tail = conv(xm, ir)
    out = np.zeros_like(tail)
    out[:len(xs)] += xs * (1 - wet)
    return out + tail * wet


def varispeed(x, rate):
    """Read x with a per-output-sample playback rate curve (1 = normal, 0 = stopped)."""
    pos = np.concatenate([[0], np.cumsum(rate[:-1])])
    pos = np.clip(pos, 0, x.shape[0] - 1)
    idx = np.arange(x.shape[0])
    if x.ndim == 1:
        return np.interp(pos, idx, x)
    return np.stack([np.interp(pos, idx, x[:, c]) for c in range(x.shape[1])], 1)


def pan(x, p):
    """p in [-1, 1] (scalar or per-sample); equal power."""
    a = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def saturate(x, drive=2.0):
    return np.tanh(drive * x) / np.tanh(drive)


def place(bus, x, t, gain=1.0):
    """Add x (mono->centre or stereo) into stereo bus at time t (sec). Clips at bus end."""
    if x.ndim == 1:
        x = np.stack([x, x], 1) * db(-3)
    s = n_of(t)
    if s >= len(bus):
        return
    if s < 0:
        x = x[-s:]
        s = 0
    e = min(len(bus), s + len(x))
    bus[s:e] += x[:e - s] * gain


def env(n, a=0.002, d=0.2, curve=1.0):
    t = tax(n)
    return np.minimum(1, t / max(a, 1e-5)) * np.exp(-t / d) ** curve


def limiter(x, ceiling_db=-2.0, look=0.0015, release=0.012, os=4):
    """True-peak (os-x oversampled) brickwall. Gain curve = moving-min then moving-average, which
    guarantees the gain never exceeds the requirement at any sample (no overshoot)."""
    c = db(ceiling_db)
    n = x.shape[0]
    X = np.fft.rfft(x, axis=0)
    up = np.fft.irfft(X, n * os, axis=0) * os
    peak = np.abs(up).max(1).reshape(n, os).max(1)
    need = np.minimum(1, c / np.maximum(peak, 1e-9))
    L = n_of(look + release)
    padded = np.concatenate([need, np.ones(L)])
    mm = np.lib.stride_tricks.sliding_window_view(padded, L).min(1)[:n]   # min over [i, i+L)
    k = np.ones(L) / L
    g = np.convolve(np.concatenate([np.ones(L - 1), mm]), k, mode='valid')    # mean over (i-L, i]
    g = np.minimum(g, 1)
    # g[i] = mean(mm[i-L+1..i]) and each mm[j] (j in window) covers sample i => g[i] <= need[i]
    return x * g[:, None] if x.ndim == 2 else x * g


# ----------------------------------------------------------------- drums
def kick(rng, dur=0.55, punch=1.0):
    n = n_of(dur)
    t = tax(n)
    f = 50 + 120 * np.exp(-t / 0.03) + 260 * np.exp(-t / 0.004)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
    click = fft_filter(rng.standard_normal(n), lo=1500, hi=9000) * np.exp(-t / 0.0025) * 0.35 * punch
    return saturate(body + click, 1.6) * np.minimum(1, (dur - t) / 0.01)


def e808(rng, freq, dur, glide_from=None, glide_t=0.07, drive=3.2):
    """Long 808 sub; saturated so phones still hear the 2nd/3rd harmonics."""
    n = n_of(dur)
    t = tax(n)
    f = np.full(n, freq)
    if glide_from:
        f = freq + (glide_from - freq) * np.exp(-t / glide_t)
    f = f * (1 + 0.6 * np.exp(-t / 0.012))                   # punch transient
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.9) * np.minimum(1, t / 0.003)
    x = saturate(x * 1.3, drive) * np.minimum(1, (dur - t) / 0.03)
    return x


def clap(rng, dur=0.45):
    n = n_of(dur)
    t = tax(n)
    x = np.zeros(n)
    for i, off in enumerate([0, 0.009, 0.019, 0.028]):
        s = n_of(off)
        dec = 0.006 if i < 3 else 0.11
        x[s:] += rng.standard_normal(n - s) * np.exp(-t[:n - s] / dec) * (0.8 if i < 3 else 1.0)
    x = bandpass(x, 1250, 0.9) + 0.25 * fft_filter(x, lo=5000)
    return x / np.abs(x).max()


def snare(rng, dur=0.25, tone=190):
    n = n_of(dur)
    t = tax(n)
    nz = fft_filter(rng.standard_normal(n), lo=900, hi=11000) * np.exp(-t / 0.07)
    tn = np.sin(2 * np.pi * tone * t * (1 + 0.3 * np.exp(-t / 0.01))) * np.exp(-t / 0.05)
    x = nz * 0.8 + tn * 0.6
    return x / np.abs(x).max()


_HAT_F = [205.3, 304.4, 369.6, 522.7, 540.0, 800.0]


def hat(rng, dur=0.05, open_=False):
    n = n_of(0.35 if open_ else dur + 0.02)
    t = tax(n)
    m = sum(np.sign(np.sin(2 * np.pi * f * 1.9 * t + rng.uniform(0, 6.28))) for f in _HAT_F)
    m = m + 1.2 * rng.standard_normal(n)
    x = fft_filter(m, lo=7200, hi=16000, slope=3)
    x *= np.exp(-t / (0.12 if open_ else dur / 2.2))
    return x / np.abs(x).max()


# ----------------------------------------------------------------- cinematic fx
def impact(rng, ir, size=1.0, dur=3.5):
    """Trailer hit: sub drop + body thud + noise crack + inharmonic metal ring, into a hall. Stereo."""
    n = n_of(dur)
    t = tax(n)
    f = 28 + 34 * np.exp(-t / 0.35)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.9 * size)) * np.minimum(1, t / 0.002)
    thud = np.sin(2 * np.pi * 95 * t * (1 + 0.8 * np.exp(-t / 0.015))) * np.exp(-t / 0.12)
    crack = fft_filter(rng.standard_normal(n), lo=400, hi=7000) * np.exp(-t / 0.05)
    metal = np.zeros(n)
    for fr, dc, a in [(173, 1.4, 1), (419, 1.0, .7), (887, .8, .5), (1511, .55, .35), (2317, .4, .25), (3310, .3, .15)]:
        metal += a * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6.3)) * np.exp(-t / (dc * size))
    metal *= 0.16
    dry = 0.75 * saturate(sub * 1.1, 1.5) + 0.7 * thud + 0.5 * crack + metal
    wet = conv(0.35 * crack + metal + 0.3 * thud, ir)[:n]
    out = np.stack([dry, dry], 1) * 0.8 + wet * 0.55
    return out * np.minimum(1, (dur - t) / 0.2)[:, None]


def braam(rng, root=midi(29), dur=2.2):
    """Low brass-ish 'braam': detuned saw stack, filter opens then closes. Stereo."""
    n = n_of(dur)
    t = tax(n)
    L = np.zeros(n)
    R = np.zeros(n)
    for mult in (1, 2, 3, 4):                       # root, octave, twelfth, two octaves
        for det, side in ((-9, 0), (0, 0.5), (9, 1)):
            f = root * mult * 2 ** (det / 1200)
            ph = (f * t + rng.uniform()) % 1
            saw = 2 * ph - 1
            L += saw * (1 - side) / mult
            R += saw * side / mult
    cutoff = lambda tt, ff: 1 / np.sqrt(1 + (ff[None, :] / (180 + 2200 * np.exp(-tt[:, None] / 0.35))) ** 6)
    L = stft_mask(L, cutoff)
    R = stft_mask(R, cutoff)
    e = np.minimum(1, t / 0.03) * np.exp(-t / 0.9) * np.minimum(1, (dur - t) / 0.3)
    x = np.stack([L, R], 1) * e[:, None]
    return saturate(x / np.abs(x).max(), 1.8)


def whoosh(rng, dur=0.8, peak=0.6, direction=1, f0=250, f1=5000):
    """Air-past-camera whoosh; band sweeps up to the peak then falls, pans across. Stereo."""
    n = n_of(dur)
    t = tax(n)
    tp = dur * peak
    fc_of = lambda tt: f0 * (f1 / f0) ** np.clip(np.where(tt < tp, tt / tp, 1 - 0.6 * (tt - tp) / (dur - tp)), 0, 1)
    mask = lambda tt, ff: 1 / np.sqrt(1 + 2.0 * (ff[None, :] / fc_of(tt)[:, None] - fc_of(tt)[:, None] / np.maximum(ff[None, :], 1)) ** 2)
    x = stft_mask(rng.standard_normal(n), mask)
    a = np.where(t < tp, (t / tp) ** 2.5, np.exp(-(t - tp) / ((dur - tp) * 0.35)))
    x = x * a
    x /= np.abs(x).max()
    return pan(x, direction * np.clip((t / dur) * 1.6 - 0.8, -0.9, 0.9)) * 1.3


def riser(rng, dur, top=9000):
    """Noise band sweep + Shepard-ish rising saw stack + accelerating snare roll. Stereo, ends hard."""
    n = n_of(dur)
    t = tax(n)
    u = t / dur
    fcf = lambda tt: 350 * (top / 350) ** (np.clip(tt / dur, 0, 1) ** 1.3)
    mask = lambda tt, ff: 1 / np.sqrt(1 + 3.0 * (ff[None, :] / fcf(tt)[:, None] - fcf(tt)[:, None] / np.maximum(ff[None, :], 1)) ** 2)
    nz = np.stack([stft_mask(rng.standard_normal(n), mask) for _ in range(2)], 1)
    nz /= np.abs(nz).max()
    # tonal rise: F2 -> F4 over the riser, three detuned saws
    base = midi(41) * 2 ** (2 * u ** 1.6)
    tone = np.zeros((n, 2))
    for det, p in ((-12, -0.7), (0, 0), (12, 0.7)):
        ph = np.cumsum(base * 2 ** (det / 1200)) / SR
        s = 2 * (ph % 1) - 1
        tone += pan(s, p)
    tone = fft_filter(tone, lo=120, hi=4500, slope=2)
    tone /= np.abs(tone).max()
    # snare roll: 8ths -> 16ths -> 32nds, velocity rising
    roll = np.zeros(n)
    s1 = snare(rng, 0.2, tone=210)
    t_hit = 0.0
    while t_hit < dur - 0.02:
        uu = t_hit / dur
        step = dur / 8 if uu < 0.5 else (dur / 16 if uu < 0.75 else dur / 32)
        i = n_of(t_hit)
        m = min(len(s1), n - i)
        roll[i:i + m] += s1[:m] * (0.25 + 0.75 * uu ** 1.5)
        t_hit += step
    ampl = (u ** 2.2)[:, None]
    out = nz * ampl * 0.9 + tone * (u ** 1.6)[:, None] * 0.35 + np.stack([roll, roll], 1) * 0.5
    return out


def reverse_swell(rng, ir, dur, root=midi(53)):
    """Reversed reverb bloom of a minor chord + cymbal; ends at full level exactly at the boundary."""
    n = n_of(dur)
    src_n = n_of(0.35)
    t = tax(src_n)
    x = np.zeros(src_n)
    for semi in (0, 3, 7, 12):
        x += np.sin(2 * np.pi * root * 2 ** (semi / 12) * t) * np.exp(-t / 0.2)
    x += 0.5 * hat(rng, open_=True)[:src_n]
    wet = conv(x, ir)
    wet = wet[:n][::-1]
    wet /= np.abs(wet).max()
    tt = tax(len(wet))
    return wet * (tt / tt[-1])[:, None] ** 1.5


def pad(rng, chord_midi, dur, cutoff=1800, width=0.8):
    """Detuned saw pad (3 voices/note), low-passed, slow attack. Stereo."""
    n = n_of(dur)
    t = tax(n)
    out = np.zeros((n, 2))
    for m in chord_midi:
        f = midi(m)
        for det, p in ((-11, -width), (0, 0), (11, width)):
            ph = (f * 2 ** (det / 1200) * t + rng.uniform()) % 1
            out += pan(2 * ph - 1, p)
    out = fft_filter(out, lo=60, hi=cutoff, slope=3)
    e = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.3)
    return out * e[:, None] / (len(chord_midi) * 3)


def pluck(rng, freq, dur=0.5, bright=1.0):
    """Additive pluck: harmonic k decays faster (tau/k^0.8) -> plucked-string brightness fall-off."""
    t = tax(n_of(dur))
    x = np.zeros_like(t)
    for k in range(1, 24):
        if freq * k > 12000:
            break
        x += np.sin(2 * np.pi * freq * k * t * (1 + 0.0004 * k)) / k ** (1.2 / bright) * np.exp(-t * (3 + 9 * k ** 0.8))
    return x * np.minimum(1, t / 0.001) / np.abs(x).max()


def bell(rng, freq, dur=1.6):
    """2-op FM bell for the logo sting."""
    t = tax(n_of(dur))
    mod = np.sin(2 * np.pi * freq * 3.5 * t) * 2.2 * np.exp(-t / 0.25)
    return np.sin(2 * np.pi * freq * t + mod) * np.exp(-t / 0.55) * np.minimum(1, t / 0.002)


# ----------------------------------------------------------------- engine
def rpm_sim(dur, events, idle=1100, redline=9000, up=7.0, down=2.2, limiter_bounce=True, ctrl=1000, r0=None):
    """Tiny engine model at `ctrl` Hz. events: list of (t0, t1, throttle 0..1) and ('shift', t, ratio).
    Returns (rpm[n], throttle[n]) at audio rate. Limiter cuts throttle for 45 ms when redline is hit."""
    m = int(dur * ctrl)
    thr = np.zeros(m)
    shifts = []
    for ev in events:
        if ev[0] == 'shift':
            shifts.append((int(ev[1] * ctrl), ev[2]))
        else:
            a, b, v = ev
            thr[int(a * ctrl):int(b * ctrl)] = v
    rpm = np.empty(m)
    r = r0 or idle
    cut = 0
    thr_eff = thr.copy()
    sdict = dict(shifts)
    for i in range(m):
        if i in sdict:
            r *= sdict[i]
            cut = int(0.07 * ctrl)
        th = thr[i] if cut <= 0 else 0.0
        cut -= 1
        if limiter_bounce and r >= redline:
            cut = int(0.045 * ctrl)
        target = idle + th * (redline * 1.08 - idle)
        k = up if target > r else down
        r += (target - r) * k / ctrl
        rpm[i] = r
        thr_eff[i] = th
    ta = np.arange(n_of(dur)) / SR
    tc = np.arange(m) / ctrl
    return np.interp(ta, tc, rpm), np.interp(ta, tc, thr_eff)


def engine(rng, rpm, thr, kind='flat6'):
    """Firing-pulse engine model -> exhaust resonator bank -> saturation, plus intake noise,
    valvetrain whine and overrun pops. kind: 'flat6' (GT3 RS) or 'v8' (cross-plane, AMG burble)."""
    n = len(rpm)
    if kind == 'flat6':
        cyl, pattern = 6, np.array([1.0, .93, 1.04, .96, 1.02, .9])
        forms = [(95, .05, .7), (230, .03, 1.0), (470, .02, .9), (960, .012, .6), (2100, .006, .35), (3400, .004, .2)]
    else:
        cyl, pattern = 8, np.array([1.0, .62, 1.12, .78, .95, .58, 1.18, .72])
        forms = [(70, .07, 1.0), (160, .04, .9), (340, .025, .8), (720, .014, .5), (1500, .008, .3), (2900, .004, .15)]
    ff = rpm / 60 * cyl / 2
    ph = np.cumsum(ff) / SR
    idx = np.floor(ph).astype(np.int64)
    frac = ph - idx
    ts = frac / np.maximum(ff, 1)
    jit = 1 + 0.12 * rng.standard_normal(idx.max() + 2)
    jscale = 1 - 0.75 * np.clip(rpm / 9000, 0, 1)          # cleaner, more tonal scream up top
    load = 0.35 + 0.65 * thr
    amp = pattern[idx % cyl] * (1 + (jit[idx] - 1) * jscale) * load
    pulse = (np.exp(-ts * 2200) - np.exp(-ts * 11000)) * amp
    # exhaust body: resonator bank IR
    tir = tax(n_of(0.25))
    ir = sum(a * np.sin(2 * np.pi * f * tir) * np.exp(-tir * f / 1.6) for f, _, a in forms)   # low-Q (~5) exhaust formants
    body = conv(pulse, ir)[:n]
    body = fft_filter(body, lo=35)
    body /= np.abs(body).max() + 1e-9
    # combustion / intake roar: noise gated by the firing pulse, brighter with rpm
    nz = fft_filter(rng.standard_normal(n), lo=700, hi=6000) * np.sqrt(np.clip(pulse / (np.abs(pulse).max() + 1e-9), 0, 1))
    nz *= (rpm / 9000) * (0.3 + 0.7 * thr)
    whine = np.sin(2 * np.pi * np.cumsum(rpm / 60 * 12) / SR) * 0.03 * (rpm / 9000) ** 2
    x = body * (0.6 + 0.5 * (rpm / 9000)) + nz * 0.22 + whine
    x = saturate(x * (0.8 + 0.6 * thr), 1.5)
    # overrun pops: throttle released while rpm high
    pops = np.zeros(n)
    off = np.where((thr < 0.05) & (rpm > 3500))[0]
    if len(off):
        cand = off[rng.random(len(off)) < (22 if kind == 'v8' else 10) / SR]
        pt = tax(n_of(0.06))
        pop = (fft_filter(rng.standard_normal(len(pt)), lo=150, hi=5000) * np.exp(-pt / 0.012)
               + np.sin(2 * np.pi * 70 * pt) * np.exp(-pt / 0.02))
        for c in cand:
            m = min(len(pop), n - c)
            pops[c:c + m] += pop[:m] * rng.uniform(0.5, 1.2)
    x = x + 0.55 * pops
    # stereo: tiny Haas on the right for width
    d = n_of(0.0007)
    R = np.concatenate([np.zeros(d), x[:-d]])
    return np.stack([x, 0.85 * R + 0.15 * x], 1)
