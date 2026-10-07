"""Synthesize the music bed and SFX for the Race Weekend spot. All original, generated here."""
import numpy as np, wave, os

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'audio')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x, stereo=None):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    peak = np.max(np.abs(x)) or 1
    x = x / peak * 0.89
    d = (x * 32767).astype('<i2')
    with wave.open(os.path.join(OUT, name), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())


def env(n, a=0.002, d=0.2, curve=4):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d * curve / 4)
    return e


def lp(x, cutoff):
    # one-pole low-pass, cutoff may be array
    y = np.zeros_like(x)
    c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - lp(x, cutoff)


# ---------------- drums ----------------
def kick(n=int(0.45 * SR)):
    t = np.arange(n) / SR
    f = 48 + 120 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.25 * np.tanh(4 * np.sin(ph)) * np.exp(-t * 18)


def clap(n=int(0.3 * SR)):
    nz = rng.standard_normal(n)
    e = np.zeros(n)
    for o in (0, 0.011, 0.022):
        i = int(o * SR)
        e[i:] += np.exp(-np.arange(n - i) / SR * 38)
    x = nz * e
    return hp(lp(x, 4000), 700)


def hat(n=int(0.06 * SR), open_=False):
    if open_:
        n = int(0.25 * SR)
    nz = rng.standard_normal(n)
    return hp(nz, 7000) * np.exp(-np.arange(n) / SR * (14 if open_ else 70))


K, C, H, OH = kick(), clap(), hat(), hat(open_=True)

# ---------------- music bed ----------------
BPM = 122
beat = 60 / BPM
DUR = 76.5
N = int(DUR * SR)
mix = np.zeros(N)
bass = np.zeros(N)
pad = np.zeros(N)
hats = np.zeros(N)


def put(buf, s, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(s))
    buf[i:j] += s[: j - i] * g


# sections: (start, end, drums level, hats, bass, pad)
sections = [
    (0.0, 2.3, 0.0, 0, 0.0, 0.7),     # title
    (2.3, 8.0, 0.8, 1, 0.8, 0.6),     # open
    (8.0, 12.7, 0.55, 0, 0.6, 0.6),   # the text (pull back)
    (12.7, 22.0, 0.9, 2, 0.9, 0.4),   # mascot gags, bouncy
    (22.0, 37.0, 1.0, 2, 1.0, 0.5),   # build the badge
    (37.0, 49.6, 1.0, 2, 1.0, 0.5),   # map
    (49.6, 60.0, 1.0, 2, 1.0, 0.6),   # poster
    (60.0, 64.5, 0.0, 0, 0.6, 0.9),   # tension (drop drums, riser)
    (64.5, 72.5, 0.7, 1, 0.8, 0.7),   # relief
    (72.5, 76.5, 0.0, 0, 0.0, 0.5),   # end card
]
# chord roots (A minor-ish): Am F C G
roots = [55.0, 43.65, 65.41, 49.0]
chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 261.6, 329.6], [196, 246.9, 293.7]]

t = 0.0
step = 0
while t < DUR:
    sec = next(s for s in sections if s[0] <= t < s[1])
    _, _, dl, hl, bl, pl = sec
    b16 = step % 16
    bar = int(t / (beat * 4))
    if dl > 0:
        if b16 in (0, 8) or (b16 == 10 and bar % 2):
            put(mix, K, t, dl)
        if b16 in (4, 12):
            put(mix, C, t, 0.55 * dl)
    if hl >= 1 and b16 % 2 == 0:
        put(hats, OH if b16 % 4 == 2 else H, t, 0.22 if b16 % 4 == 2 else 0.28)
    if hl >= 2 and b16 % 2 == 1:
        put(hats, H, t, 0.16)
    # bass: 8th-note pulse on root
    if bl > 0 and b16 % 2 == 0:
        r = roots[bar % 4] * (2 if b16 % 4 == 2 else 1)
        n = int(beat / 2 * SR * 0.9)
        tt = np.arange(n) / SR
        saw = 2 * ((tt * r) % 1) - 1
        s = lp(np.tanh(2.5 * saw) * env(n, 0.003, 0.18), 600) * bl
        put(bass, s, t)
    # pad: one chord per bar
    if pl > 0 and b16 == 0:
        n = int(beat * 4 * SR)
        tt = np.arange(n) / SR
        ch = chords[bar % 4]
        s = sum(np.sin(2 * np.pi * f * tt + np.sin(2 * np.pi * 0.3 * tt) * 0.4) + 0.4 * np.sin(2 * np.pi * f * 2.003 * tt) for f in ch)
        e = np.minimum(1, tt / 0.4) * np.minimum(1, (tt[-1] - tt) / 0.3 + 0.02)
        put(pad, s * e * 0.08 * pl, t)
    t += beat / 4
    step += 1

# riser for tension 60.0 -> 64.5
rn = int(4.5 * SR)
rt = np.arange(rn) / SR
rf = 200 * (2 ** (rt * 1.1))
riser = np.sin(2 * np.pi * np.cumsum(rf) / SR) * (rt / 4.5) ** 2 * 0.35 + hp(rng.standard_normal(rn), 3000) * (rt / 4.5) ** 3 * 0.25
put(mix, riser, 60.0)

music = mix + 0.9 * bass + pad + hats
# gentle master: soft clip + fade in/out
music = np.tanh(music * 0.9)
fade = np.ones(N)
fade[: int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR))
tail = int(2.5 * SR)
fade[-tail:] = np.linspace(1, 0, tail)
save('music.wav', music * fade)

# ---------------- SFX ----------------
def pop():
    n = int(0.16 * SR); tt = np.arange(n) / SR
    f = 380 + 900 * np.exp(-tt * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.08)


def blip():  # pixel / chiptune square blip
    n = int(0.12 * SR); tt = np.arange(n) / SR
    f = np.where(tt < 0.05, 880, 1320)
    return np.sign(np.sin(2 * np.pi * f * tt)) * env(n, 0.001, 0.1) * 0.5


def whoosh(d=0.6):
    n = int(d * SR); tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    c = 300 + 5000 * np.sin(np.pi * tt / d) ** 2
    s = lp(nz, c) * np.sin(np.pi * tt / d) ** 1.5
    return s


def tick():
    n = int(0.03 * SR)
    return hp(rng.standard_normal(n), 2500) * np.exp(-np.arange(n) / SR * 160) * 0.6


def send():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    f = 600 + 900 * tt / 0.35
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.005, 0.25) * 0.6


def chime():
    n = int(0.9 * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in ((1046.5, 4), (1568, 5), (2093, 7)))
    return s * np.minimum(1, tt / 0.004)


def boom():
    n = int(1.1 * SR); tt = np.arange(n) / SR
    f = 40 + 90 * np.exp(-tt * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.5)
    crack = lp(rng.standard_normal(n), 2500) * np.exp(-tt * 6) * 0.7
    # chiptune crunch
    crunch = np.round(crack * 6) / 6
    return body + crunch


def impact():
    n = int(1.6 * SR); tt = np.arange(n) / SR
    f = 35 + 70 * np.exp(-tt * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2) + lp(rng.standard_normal(n), 900) * np.exp(-tt * 5) * 0.5


def message():  # incoming text: two soft tones
    n = int(0.45 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * 1318.5 * tt) * env(n, 0.002, 0.12)
    s2 = np.zeros(n); i = int(0.11 * SR)
    s2[i:] = np.sin(2 * np.pi * 1760 * tt[: n - i]) * env(n - i, 0.002, 0.2)
    return s + s2


def stamp():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (90 + 200 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) + hp(rng.standard_normal(n), 1500) * np.exp(-tt * 40) * 0.6


for name, fn in dict(pop=pop, blip=blip, whoosh=whoosh, tick=tick, send=send, chime=chime, boom=boom, impact=impact, message=message, stamp=stamp).items():
    save(f'{name}.wav', fn())
save('whoosh_long.wav', whoosh(1.1))
print('audio ok')
