"""Who is talking: HOST (Omarie, narrating to camera) or OTHER, per transcript piece, with a confidence.

Voice embeddings: WeSpeaker ResNet34-LM (VoxCeleb, 256-d) as ONNX on onnxruntime (already a faster-whisper
dependency), fed 80-bin Kaldi-style log-mel fbank computed here in numpy (25 ms / 10 ms, hamming, CMN), which
is what the model was trained on. The model downloads once from the Hugging Face hub (26 MB). If it cannot be
loaded, an MFCC-statistics embedding is used instead (weaker; noted in the output).

Labelling:
  1. pieces = transcript segments, split at word gaps >= 0.5 s so a question and its answer separate
  2. each piece gets an embedding from its own audio (short pieces are padded symmetrically to 1.2 s)
  3. host centroid = mean embedding of 2 s windows over the reference narration (--host-ref, or the saved
     voiceprint engine/voiceprints/host.npy learned on Sep 15), then re-estimated once from the day's most
     host-like pieces so the camera/mic of the day is taken into account
  4. score = cosine(piece, host); HOST if score >= threshold; confidence from the margin and the piece length
"""
import os

import numpy as np

SR = 16000
MODEL_REPO = 'Wespeaker/wespeaker-voxceleb-resnet34-LM'
MODEL_FILE = 'voxceleb_resnet34_LM.onnx'
ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICEPRINT = os.path.join(ENGINE, 'voiceprints', 'host.npy')


# ------------------------------------------------------------------ features
def _mel_banks(n_mels=80, n_fft=512, sr=SR, low=20.0, high=0.0):
    high = sr / 2 + high if high <= 0 else high
    mel = lambda f: 1127.0 * np.log(1.0 + np.asarray(f) / 700.0)  # noqa: E731
    nb = n_fft // 2
    fft_mel = mel(np.arange(nb) * sr / n_fft)
    ml, mh = mel(low), mel(high)
    d = (mh - ml) / (n_mels + 1)
    banks = np.zeros((n_mels, nb + 1), np.float32)
    for b in range(n_mels):
        l, c, r = ml + b * d, ml + (b + 1) * d, ml + (b + 2) * d
        up = (fft_mel - l) / (c - l)
        down = (r - fft_mel) / (r - c)
        banks[b, :nb] = np.maximum(0, np.minimum(up, down))
    return banks


_BANKS = None
_WIN = None


def fbank(wav16k):
    """80-dim log mel fbank (Kaldi conventions, snip_edges) of float audio in [-1, 1], CMN applied."""
    global _BANKS, _WIN
    if _BANKS is None:
        _BANKS = _mel_banks()
        n = np.arange(400)
        _WIN = (0.54 - 0.46 * np.cos(2 * np.pi * n / 399)).astype(np.float32)
    x = np.asarray(wav16k, np.float32) * 32768.0
    if len(x) < 400:
        x = np.pad(x, (0, 400 - len(x)))
    nf = 1 + (len(x) - 400) // 160
    idx = np.arange(400)[None, :] + 160 * np.arange(nf)[:, None]
    fr = x[idx]
    fr = fr - fr.mean(axis=1, keepdims=True)
    fr = np.concatenate([fr[:, :1] - 0.97 * fr[:, :1], fr[:, 1:] - 0.97 * fr[:, :-1]], axis=1)
    fr = fr * _WIN
    spec = np.abs(np.fft.rfft(fr, n=512, axis=1)) ** 2
    mel = spec.astype(np.float32) @ _BANKS.T
    feats = np.log(np.maximum(mel, np.finfo(np.float32).eps))
    return feats - feats.mean(axis=0, keepdims=True)


def mfcc_stats(wav16k):
    f = fbank(wav16k)
    n = f.shape[1]
    k = np.arange(n)
    dct = np.cos(np.pi / n * (k[None, :] + 0.5) * np.arange(20)[:, None])
    c = f @ dct.T
    d = np.diff(c, axis=0) if len(c) > 1 else np.zeros_like(c)
    return np.concatenate([c.mean(0), c.std(0), d.std(0)])


# ------------------------------------------------------------------ embedder
class Embedder:
    def __init__(self, threads=2):
        self.kind = 'wespeaker-resnet34-LM'
        self.sess = None
        try:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(MODEL_REPO, MODEL_FILE)
            so = ort.SessionOptions()
            so.intra_op_num_threads = threads
            so.inter_op_num_threads = 1
            # no busy-waiting threads: on shared cores spinning made the embeddings 5x slower
            so.add_session_config_entry('session.intra_op.allow_spinning', '0')
            self.sess = ort.InferenceSession(path, so, providers=['CPUExecutionProvider'])
        except Exception as e:  # pragma: no cover - fallback path
            self.kind = f'mfcc-stats (speaker model unavailable: {type(e).__name__})'

    def __call__(self, wav16k):
        if self.sess is None:
            v = mfcc_stats(wav16k)
        else:
            f = fbank(wav16k)[None].astype(np.float32)
            v = self.sess.run(None, {'feats': f})[0][0]
        return v / (np.linalg.norm(v) + 1e-9)


def load_audio(path):
    from faster_whisper.audio import decode_audio
    return decode_audio(path, sampling_rate=SR)


def cut(audio, t0, t1, min_len=1.2):
    if t1 - t0 < min_len:
        m = (t0 + t1) / 2
        t0, t1 = m - min_len / 2, m + min_len / 2
    a = max(0, int(t0 * SR))
    b = min(len(audio), int(t1 * SR))
    return audio[a:b]


# ------------------------------------------------------------------ pieces
def pieces_of(segments, gap=0.5):
    """Split whisper segments at word gaps >= gap. Returns [{seg, start, end, text, words}]."""
    out = []
    for si, s in enumerate(segments):
        ws = s.get('words') or []
        if not ws:
            out.append({'seg': si, 'start': s['start'], 'end': s['end'], 'text': s['text'], 'words': []})
            continue
        cur = [ws[0]]
        for w in ws[1:]:
            if w[0] - cur[-1][1] >= gap:
                out.append(_piece(si, cur))
                cur = [w]
            else:
                cur.append(w)
        out.append(_piece(si, cur))
    return out


def _piece(si, ws):
    return {'seg': si, 'start': ws[0][0], 'end': ws[-1][1], 'text': ''.join(w[2] for w in ws).strip(), 'words': ws}


def ref_windows(audio, t0, t1, win=2.0, hop=1.0):
    out = []
    t = t0
    while t + win <= t1 + 1e-6:
        out.append((t, t + win))
        t += hop
    if not out and t1 - t0 > 0.5:
        out.append((t0, t1))
    return out


def centroid(vs):
    c = np.mean(np.asarray(vs), axis=0)
    return c / (np.linalg.norm(c) + 1e-9)


def confidence(score, thr, dur, spread=0.12):
    """0.5 at the threshold, towards 1 with the margin; short pieces are trusted less."""
    m = abs(score - thr) / spread
    c = 1 - 0.5 * np.exp(-2.2 * m)
    c *= min(1.0, 0.55 + 0.45 * min(dur, 2.0) / 2.0)
    return float(round(max(0.5 if dur >= 0.3 else 0.4, c), 2))



WIN = 1.5
MIN_LEN = 0.5
BUCKET = 0.25


def piece_windows(p, dur_audio, win=WIN, max_windows=4):
    """Analysis windows for a piece. Pieces up to 1.25 x WIN: the piece itself (at least MIN_LEN), its length
    rounded up to a 0.25 s bucket so equal lengths batch together. Longer pieces: up to 4 tiled WIN windows."""
    a, b = p['start'], p['end']
    L = b - a
    if L <= win * 1.25:
        L2 = max(MIN_LEN, np.ceil(L / BUCKET - 1e-6) * BUCKET)
        m = (a + b) / 2
        a2 = min(max(0.0, m - L2 / 2), max(0.0, dur_audio - L2))
        return [(round(a2, 3), round(a2 + L2, 3))]
    n = min(max_windows, int(L // win))
    step = (L - win) / max(1, n - 1) if n > 1 else 0
    return [(a + i * step, a + i * step + win) for i in range(n)]


def embed_windows(E, audio, wins, batch=32):
    """Embeddings for windows, batched by equal length."""
    out = np.zeros((len(wins), 256), np.float32)
    if not wins:
        return out
    if E.sess is None:
        vs = [E(audio[int(a * SR):int(b * SR)]) for a, b in wins]
        return np.stack(vs)
    groups = {}
    for i, (a, b) in enumerate(wins):
        groups.setdefault(int(round((b - a) * SR)), []).append(i)
    for n, idx in groups.items():
        feats = []
        for i in idx:
            j = int(wins[i][0] * SR)
            x = audio[j:j + n]
            if len(x) < n:
                x = np.pad(x, (0, n - len(x)))
            feats.append(fbank(x))
        feats = np.stack(feats).astype(np.float32)
        for k in range(0, len(idx), batch):
            v = E.sess.run(None, {'feats': feats[k:k + batch]})[0]
            out[idx[k:k + batch]] = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
    return out


def embed_pieces(E, audio, pieces):
    dur = len(audio) / SR
    wins, owner = [], []
    for k, p in enumerate(pieces):
        for w in piece_windows(p, dur):
            wins.append(w)
            owner.append(k)
    V = embed_windows(E, audio, wins)
    out = np.zeros((len(pieces), V.shape[1] if len(V) else 256), np.float32)
    owner = np.array(owner)
    for k in range(len(pieces)):
        m = owner == k
        if m.any():
            c = V[m].mean(0)
            out[k] = c / (np.linalg.norm(c) + 1e-9)
    return out


# ------------------------------------------------------------------ labelling
TAU = 0.42          # cosine threshold host / other (calibrated on Sep 15: host narration ~0.5-0.8, others < 0.4)
SCALE = 0.07        # cosine units per logit unit
CAMERA_PRIOR = 0.3  # the camera (DJI) is on the host; phone clips get no prior
REPLY_PRIOR = -1.2  # short replies right after a host question are usually someone else answering


def weight(d):
    """How much a piece's own voice evidence counts: short pieces carry little speaker information."""
    return float(np.clip((d - 0.3) / 1.5, 0.15, 1.0))


def label_pieces(pieces, scores, camera=True, tau=TAU):
    """HOST/OTHER + confidence for the pieces of one clip (in time order)."""
    n = len(pieces)
    lac = [weight(p['end'] - p['start']) * (s - tau) / SCALE for p, s in zip(pieces, scores)]
    prior = [CAMERA_PRIOR if camera else 0.0] * n
    why = [''] * n
    for i, p in enumerate(pieces):
        txt = p['text'].strip()
        if not txt.endswith('?') or lac[i] + prior[i] <= 0.5:
            continue
        q_end = p['end']
        prev_end = None
        for j in range(i + 1, n):
            pj = pieces[j]
            d = pj['end'] - pj['start']
            # the first reply starts within 3 s of the question, later ones follow each other closely;
            # the run stops at anything long, anything clearly in the host's voice, or 3.5 s after the question
            if pj['start'] - q_end > 3.5 or d > 1.6:
                break
            if (prev_end is None and pj['start'] - q_end > 3.0) or (prev_end is not None and pj['start'] - prev_end > 1.5):
                break
            if lac[j] > 1.5:
                break
            prior[j] += REPLY_PRIOR
            why[j] = 'reply to a host question'
            prev_end = pj['end']
    out = []
    for i, p in enumerate(pieces):
        L = lac[i] + prior[i]
        conf = 1.0 / (1.0 + np.exp(-abs(L)))
        out.append({'speaker': 'HOST' if L > 0 else 'OTHER', 'conf': round(float(conf), 2), 'score': round(float(scores[i]), 3),
                    'logit': round(float(L), 2), 'why': why[i]})
    return out


def host_centroid_from_refs(E, audio_of, refs):
    """refs: [(clip, t0, t1)] -> (centroid, mean self-similarity of the reference windows)."""
    wins = []
    for cid, t0, t1 in refs:
        a = audio_of(cid)
        V = embed_windows(E, a, ref_windows(a, t0, t1, win=WIN, hop=0.75))
        wins.append(V)
    V = np.concatenate(wins)
    c = centroid(V)
    return c, float((V @ c).mean())


def adapt_centroid(c0, all_V, all_d, tau=TAU):
    """Re-estimate the host centroid from the day's clearly-host pieces (long, well above threshold)."""
    s = all_V @ c0
    m = (s >= tau + 0.13) & (all_d >= 2.0)
    if m.sum() < 10:
        return c0, int(m.sum())
    c2 = centroid(all_V[m])
    return centroid([c0, c2]), int(m.sum())
