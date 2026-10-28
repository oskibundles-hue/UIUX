"""MP4 / QuickTime structure: top-level atoms, moov sample tables, the moov inside a file tail, byte spans.

Everything here works on bytes (a saved moov, a tail buffer), never on a whole original file.

  parse_moov(buf)            -> Movie: tracks with per-sample dts/pts, sizes, file offsets, sync flags
  find_moov_in_tail(tail, n) -> (offset, moov bytes, [atoms from the moov to EOF]) or None
  Movie.video / .audio       -> the tracks ffmpeg maps as 0:v:0 and 0:a:0 (first vide / first soun trak)
  select_sync(track, step)   -> sync samples about `step` seconds apart (thumbnails, keyframe timelapse)
  span(movie, t0, t1)        -> (lo, hi) bytes that hold video from the sync sample before t0 through t1,
                                plus the audio over the same window
  annexb_header(track)       -> VPS/SPS/PPS (HEVC) or SPS/PPS (AVC) as an Annex-B byte string
"""
import re
import struct

import numpy as np

CONTAINERS = {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'dinf', b'udta'}


def iter_boxes(buf, off, end):
    """Yield (type:str, payload_start, box_end, box_start) for the boxes in buf[off:end]."""
    while off + 8 <= end:
        size, typ = struct.unpack('>I4s', buf[off:off + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack('>Q', buf[off + 8:off + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - off
        if size < hdr or off + size > end:
            return
        yield typ.decode('latin1'), off + hdr, off + size, off
        off += size


def child(buf, s, e, name):
    for t, a, b, _ in iter_boxes(buf, s, e):
        if t == name:
            return a, b
    return None


def _u32(buf, a):
    return struct.unpack('>I', buf[a:a + 4])[0]


def _arr(buf, a, n, dt):
    return np.frombuffer(bytes(buf[a:a + n * np.dtype(dt).itemsize]), dtype=dt).astype(np.int64)


class Track:
    def __init__(self):
        self.handler = None
        self.codec = None
        self.timescale = 1
        self.width = self.height = 0
        self.rotation = 0          # display rotation in degrees (clockwise, as players apply it)
        self.extradata = b''       # hvcC / avcC payload
        self.dts = None            # np.int64 per sample (media timescale)
        self.pts = None            # dts + ctts - edit shift
        self.sizes = None
        self.offsets = None
        self.sync = None           # np array of sample indices, None = every sample is sync
        self.track_id = 0

    @property
    def n(self):
        return 0 if self.sizes is None else len(self.sizes)

    def t(self, i):
        return float(self.pts[i]) / self.timescale

    def times(self):
        return self.pts / float(self.timescale)

    def dtimes(self):
        return self.dts / float(self.timescale)

    def duration(self):
        if not self.n:
            return 0.0
        return float(self.dts[-1] + (self.dts[-1] - self.dts[-2] if self.n > 1 else 0)) / self.timescale

    def sync_indices(self):
        return np.arange(self.n) if self.sync is None else self.sync


def _rotation_from_matrix(m):
    a, b, _, c, d = m[0], m[1], m[2], m[3], m[4]
    # 16.16 fixed point; QuickTime matrix [a b u; c d v; x y w]
    a, b, c, d = (x / 65536.0 for x in (a, b, c, d))
    if abs(a) < 0.5 and abs(d) < 0.5:
        return 90 if b > 0 else 270
    if a < -0.5 and d < -0.5:
        return 180
    return 0


def parse_track(buf, s, e):
    tr = Track()
    tkhd = child(buf, s, e, 'tkhd')
    if tkhd:
        a = tkhd[0]
        if buf[a] == 1:   # version 1: 64-bit times
            tr.track_id = _u32(buf, a + 20)
            mo = a + 52
        else:
            tr.track_id = _u32(buf, a + 12)
            mo = a + 40
        tr.rotation = _rotation_from_matrix(struct.unpack('>9i', buf[mo:mo + 36]))
    mdia = child(buf, s, e, 'mdia')
    hdlr = child(buf, *mdia, 'hdlr')
    tr.handler = bytes(buf[hdlr[0] + 8:hdlr[0] + 12]).decode('latin1')
    mdhd = child(buf, *mdia, 'mdhd')
    ver = buf[mdhd[0]]
    tr.timescale = _u32(buf, mdhd[0] + (20 if ver == 1 else 12))
    minf = child(buf, *mdia, 'minf')
    stbl = child(buf, *minf, 'stbl')
    tab = {}
    for t, a, b, _ in iter_boxes(buf, *stbl):
        tab.setdefault(t, (a, b))
    # stsd: codec fourcc, dimensions, hvcC/avcC
    a, b = tab['stsd']
    ent = a + 8
    esize, fourcc = struct.unpack('>I4s', buf[ent:ent + 8])
    tr.codec = fourcc.decode('latin1')
    if tr.handler == 'vide':
        tr.width, tr.height = struct.unpack('>HH', buf[ent + 32:ent + 36])
        for t, pa, pb, _ in iter_boxes(buf, ent + 86, ent + esize):
            if t in ('hvcC', 'avcC'):
                tr.extradata = bytes(buf[pa:pb])
                tr.extra_type = t
    # stsz
    a, _ = tab.get('stsz') or tab.get('stz2')
    fixed, cnt = struct.unpack('>II', buf[a + 4:a + 12])
    sizes = np.full(cnt, fixed, dtype=np.int64) if fixed else _arr(buf, a + 12, cnt, '>u4')
    # chunk offsets
    if 'stco' in tab:
        a, _ = tab['stco']
        chunks = _arr(buf, a + 8, _u32(buf, a + 4), '>u4')
    else:
        a, _ = tab['co64']
        chunks = _arr(buf, a + 8, _u32(buf, a + 4), '>u8')
    # stsc -> samples per chunk
    a, _ = tab['stsc']
    m = _u32(buf, a + 4)
    runs = _arr(buf, a + 8, 3 * m, '>u4').reshape(-1, 3)
    nch = len(chunks)
    firsts = runs[:, 0] - 1
    lasts = np.append(runs[1:, 0] - 1, nch)
    spc = np.repeat(runs[:, 1], np.maximum(lasts - firsts, 0))[:nch]
    if len(spc) < nch:
        spc = np.append(spc, np.full(nch - len(spc), runs[-1, 1]))
    chunk_of = np.repeat(np.arange(nch), spc)[:cnt]
    first_in_chunk = np.concatenate([[0], np.cumsum(spc)[:-1]])
    csz = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    within = csz - csz[first_in_chunk[chunk_of]]
    tr.offsets = chunks[chunk_of] + within
    tr.sizes = sizes[:len(tr.offsets)]
    # stts -> dts
    a, _ = tab['stts']
    n = _u32(buf, a + 4)
    st = _arr(buf, a + 8, 2 * n, '>u4').reshape(-1, 2)
    deltas = np.repeat(st[:, 1], st[:, 0])[:len(tr.sizes)]
    tr.dts = np.concatenate([[0], np.cumsum(deltas)[:-1]]) if len(deltas) else np.zeros(0, np.int64)
    if len(tr.dts) < len(tr.sizes):
        tr.sizes = tr.sizes[:len(tr.dts)]
        tr.offsets = tr.offsets[:len(tr.dts)]
    # ctts -> pts
    pts = tr.dts.copy()
    if 'ctts' in tab:
        a, _ = tab['ctts']
        n = _u32(buf, a + 4)
        ct = _arr(buf, a + 8, 2 * n, '>u4').reshape(-1, 2)
        off = ct[:, 1]
        # signed in version 1; Apple also writes negative offsets into version 0 boxes
        off = np.where(off >= 2 ** 31, off - 2 ** 32, off)
        pts = pts + np.repeat(off, ct[:, 0])[:len(pts)]
    # edit list: the first non-empty edit's media_time is the presentation zero
    shift = 0
    edts = child(buf, s, e, 'edts')
    if edts:
        elst = child(buf, *edts, 'elst')
        if elst:
            a = elst[0]
            ever = buf[a]
            n = _u32(buf, a + 4)
            p = a + 8
            empty = 0
            for _ in range(n):
                if ever == 1:
                    dur, mt = struct.unpack('>Qq', buf[p:p + 16]); p += 16
                else:
                    dur, mt = struct.unpack('>Ii', buf[p:p + 8]); p += 8
                p += 4
                if mt == -1:
                    empty += dur  # movie timescale; ignored (rare, sub-frame)
                    continue
                shift = mt
                break
    tr.pts = pts - shift
    if 'stss' in tab:
        a, _ = tab['stss']
        tr.sync = _arr(buf, a + 8, _u32(buf, a + 4), '>u4') - 1
        tr.sync = tr.sync[tr.sync < len(tr.sizes)]
    return tr


class Movie:
    def __init__(self, moov):
        self.moov = bytes(moov)
        buf = memoryview(self.moov)
        # accept either a whole moov box or its payload
        if self.moov[4:8] == b'moov':
            s, e = 8, len(self.moov)
            if struct.unpack('>I', self.moov[:4])[0] == 1:
                s = 16
        else:
            s, e = 0, len(self.moov)
        self.tracks = []
        self.timescale = 1000
        self.duration = 0.0
        self.creation_time = None
        for t, a, b, _ in iter_boxes(buf, s, e):
            if t == 'mvhd':
                ver = buf[a]
                if ver == 1:
                    ct, = struct.unpack('>Q', buf[a + 4:a + 12])
                    self.timescale, dur = struct.unpack('>IQ', buf[a + 20:a + 32])
                else:
                    ct, = struct.unpack('>I', buf[a + 4:a + 8])
                    self.timescale, dur = struct.unpack('>II', buf[a + 12:a + 20])
                self.creation_time = ct - 2082844800 if ct > 2082844800 else None  # unix seconds (UTC)
                self.duration = dur / float(self.timescale or 1)
            elif t == 'trak':
                try:
                    self.tracks.append(parse_track(buf, a, b))
                except Exception:  # an odd metadata track must not sink the clip
                    pass
        m = re.search(rb'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})', self.moov)
        self.apple_creationdate = m.group(1).decode() if m else None

    @property
    def video(self):
        for t in self.tracks:
            if t.handler == 'vide' and t.codec not in ('jpeg', 'mjpg'):
                return t
        return None

    @property
    def audio(self):
        for t in self.tracks:
            if t.handler == 'soun':
                return t
        return None


def parse_moov(moov):
    return Movie(moov)


def top_atoms(buf, base, end_abs):
    """Walk top-level atoms in buf (which starts at absolute offset `base`). Return [(type, off, size)] or None."""
    out = []
    off = 0
    n = len(buf)
    while off < n:
        if off + 8 > n:
            return None
        size, typ = struct.unpack('>I4s', buf[off:off + 8])
        if size == 1:
            if off + 16 > n:
                return None
            size = struct.unpack('>Q', buf[off + 8:off + 16])[0]
        elif size == 0:
            size = end_abs - (base + off)
        if size < 8 or not re.match(rb'^[\x20-\x7e]{4}$', typ):
            return None
        out.append((typ.decode('latin1'), base + off, size))
        off += size
    return out if off == n else None


def find_moov_in_tail(tail, file_size):
    """Locate a complete moov inside the last len(tail) bytes of a file.

    A candidate is accepted when its size chains through any following atoms exactly to EOF and its first
    child is mvhd. Returns (moov_offset, moov_bytes, atoms_from_moov_to_eof) or None (moov not in the tail,
    e.g. a faststart .MOV with moov at the front)."""
    base = file_size - len(tail)
    pos = len(tail)
    while True:
        p = tail.rfind(b'moov', 0, pos)
        if p < 4:
            return None
        pos = p
        st = p - 4
        size = struct.unpack('>I', tail[st:st + 4])[0]
        hdr = 8
        if size == 1:
            size = struct.unpack('>Q', tail[st + 8:st + 16])[0]
            hdr = 16
        if size < 16 or st + size > len(tail):
            continue
        if tail[st + hdr + 4:st + hdr + 8] != b'mvhd':
            continue
        rest = top_atoms(tail[st:], base + st, file_size)
        if rest is None:
            continue
        return base + st, bytes(tail[st:st + size]), rest


def select_sync(track, step):
    """Sync samples nearest to a grid of `step` seconds (every sync sample if step <= 0)."""
    idx = track.sync_indices()
    if step <= 0 or len(idx) == 0:
        return list(map(int, idx))
    t = track.pts[idx] / float(track.timescale)
    out = []
    g = 0.0
    j = 0
    end = t[-1] + step
    while g <= end and j < len(idx):
        k = int(np.searchsorted(t, g))
        cands = [c for c in (k - 1, k) if 0 <= c < len(idx)]
        best = min(cands, key=lambda c: abs(t[c] - g))
        if not out or best > out[-1]:
            out.append(best)
        j = best
        g += step
    return [int(idx[c]) for c in out]


def merge_ranges(rs, gap=0):
    rs = sorted(rs)
    out = []
    for a, b in rs:
        if out and a <= out[-1][1] + gap:
            if b > out[-1][1]:
                out[-1][1] = b
        else:
            out.append([a, b])
    return out


def keep_ranges(movie, kf_step=2.0, audio=True):
    """Byte ranges the survey keeps: every sample of the first audio track + sync samples ~kf_step apart.
    Returns (ranges [[lo, hi)], kept_sync_sample_indices)."""
    rs = []
    a = movie.audio
    if audio and a is not None and a.n:
        rs.extend(zip(a.offsets.tolist(), (a.offsets + a.sizes).tolist()))
    v = movie.video
    ks = []
    if v is not None and v.n:
        ks = select_sync(v, kf_step)
        rs.extend((int(v.offsets[i]), int(v.offsets[i] + v.sizes[i])) for i in ks)
    return merge_ranges([list(r) for r in rs]), ks


def span(movie, t0, t1, pad=0.0, audio_pad=0.5):
    """Bytes [lo, hi) covering video from the sync sample at/before t0-pad through t1+pad, plus audio."""
    lo = hi = None
    for tr in (movie.video, movie.audio):
        if tr is None or not tr.n:
            continue
        tm = tr.dtimes()
        if tr is movie.video:
            i = max(0, int(np.searchsorted(tm, t0 - pad, 'right')) - 1)
            if tr.sync is not None and len(tr.sync):
                j = int(np.searchsorted(tr.sync, i, 'right')) - 1
                i = int(tr.sync[max(j, 0)])
            k = min(tr.n - 1, int(np.searchsorted(tm, t1 + pad)) + 8)  # a few frames of reorder slack
        else:
            i = max(0, int(np.searchsorted(tm, t0 - pad - audio_pad, 'right')) - 1)
            k = min(tr.n - 1, int(np.searchsorted(tm, t1 + pad + audio_pad)))
        s = int(tr.offsets[i:k + 1].min())
        e = int((tr.offsets[i:k + 1] + tr.sizes[i:k + 1]).max())
        lo = s if lo is None else min(lo, s)
        hi = e if hi is None else max(hi, e)
    return lo, hi


def sync_span_samples(movie, t0, t1):
    """Video sync sample indices with pts in [t0, t1]."""
    v = movie.video
    idx = v.sync_indices()
    t = v.pts[idx] / float(v.timescale)
    return [int(i) for i, x in zip(idx, t) if t0 - 1e-6 <= x <= t1 + 1e-6]


def annexb_header(track):
    """Parameter sets from hvcC/avcC as Annex-B, and the NAL length size."""
    ex = track.extradata
    out = b''
    if not ex:
        return out, 4
    if getattr(track, 'extra_type', 'hvcC') == 'hvcC':
        nal_len = (ex[21] & 3) + 1
        narr = ex[22]
        p = 23
        for _ in range(narr):
            p += 1
            cnt = struct.unpack('>H', ex[p:p + 2])[0]; p += 2
            for _ in range(cnt):
                ln = struct.unpack('>H', ex[p:p + 2])[0]; p += 2
                out += b'\x00\x00\x00\x01' + ex[p:p + ln]; p += ln
        return out, nal_len
    nal_len = (ex[4] & 3) + 1
    nsps = ex[5] & 31
    p = 6
    for _ in range(nsps):
        ln = struct.unpack('>H', ex[p:p + 2])[0]; p += 2
        out += b'\x00\x00\x00\x01' + ex[p:p + ln]; p += ln
    npps = ex[p]; p += 1
    for _ in range(npps):
        ln = struct.unpack('>H', ex[p:p + 2])[0]; p += 2
        out += b'\x00\x00\x00\x01' + ex[p:p + ln]; p += ln
    return out, nal_len


def to_annexb(sample, nal_len=4):
    out = bytearray()
    p = 0
    n = len(sample)
    while p + nal_len <= n:
        ln = int.from_bytes(sample[p:p + nal_len], 'big')
        p += nal_len
        if ln <= 0 or p + ln > n:
            break
        out += b'\x00\x00\x00\x01'
        out += sample[p:p + ln]
        p += ln
    return bytes(out)
