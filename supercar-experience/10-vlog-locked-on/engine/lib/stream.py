"""HTTP through curl (one request per single-use link) and the streaming survey filter.

  http_range(url, lo, hi)          one Range request -> bytes (expects 206 and exactly hi-lo bytes)
  http_stream(url, sink)           one plain GET, body pushed to sink(memoryview) as it arrives
  StreamFilter(size, sparse, ...)  walks the top-level atoms of the whole-file stream and writes to a sparse
                                   file only: every non-mdat atom (ftyp/free/moov/...: the head and the moov),
                                   and inside mdat only the byte ranges it was told to keep (audio samples and
                                   a subset of video sync samples). Works with the moov known up front (from
                                   the tail request) or arriving before mdat (faststart .MOV). If neither, and
                                   the file is small, it keeps the whole mdat (spill) so nothing is lost.
curl is used (not urllib) so the proxy / CA settings the environment gives curl apply unchanged.
"""
import fcntl
import os
import struct
import subprocess
import tempfile
import time

from . import mp4

CHUNK = 1 << 20
F_SETPIPE_SZ = 1031


class HttpError(Exception):
    pass


def _curl(url, rng=None, extra=()):
    hdr = tempfile.NamedTemporaryFile(prefix='hdr', suffix='.txt', delete=False)
    hdr.close()
    cmd = ['curl', '-sS', '--fail', '-L', '--connect-timeout', '20', '--speed-time', '60', '--speed-limit', '200000',
           '-D', hdr.name, '-o', '-']
    if rng:
        cmd += ['-r', f'{rng[0]}-{rng[1] - 1}']
    cmd += list(extra) + [url]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    try:
        fcntl.fcntl(p.stdout.fileno(), F_SETPIPE_SZ, 1 << 20)
    except OSError:
        pass
    return p, hdr.name


def _status(hdrfile):
    code = None
    try:
        for line in open(hdrfile, errors='replace'):
            if line.startswith('HTTP/'):
                parts = line.split()
                if len(parts) > 1 and parts[1].isdigit():
                    code = int(parts[1])
    except OSError:
        pass
    try:
        os.unlink(hdrfile)
    except OSError:
        pass
    return code


def http_range(url, lo, hi, timeout=120):
    """Bytes [lo, hi) with a single Range request."""
    want = hi - lo
    p, hdr = _curl(url, (lo, hi))
    buf = bytearray(want)
    mv = memoryview(buf)
    got = 0
    t0 = time.time()
    while True:
        if got >= want:
            extra = p.stdout.read(1)
            if extra:  # server ignored Range and is sending the whole file: stop now
                p.kill(); p.wait()
                _status(hdr)
                raise HttpError('server ignored the Range request (200 with the whole file)')
            break
        n = p.stdout.readinto(mv[got:])
        if not n:
            break
        got += n
        if time.time() - t0 > timeout:
            p.kill()
            break
    err = p.stderr.read().decode(errors='replace').strip()
    rc = p.wait()
    code = _status(hdr)
    if rc != 0 or code not in (206, 200) or got != want:
        raise HttpError(f'range {lo}-{hi}: curl rc={rc} http={code} got={got}/{want} {err[:200]}')
    if code == 200 and not (lo == 0):
        raise HttpError('server answered 200 to a Range request')
    return bytes(buf)


def http_stream(url, sink, expect_size=None, rng=None, stop=None):
    """GET (or one Range) and hand the body to sink(memoryview) chunk by chunk. Returns (bytes, seconds)."""
    p, hdr = _curl(url, rng)
    buf = bytearray(CHUNK)
    mv = memoryview(buf)
    total = 0
    t0 = time.time()
    try:
        while True:
            n = p.stdout.readinto(buf)
            if not n:
                break
            sink(mv[:n])
            total += n
            if stop is not None and stop.is_set():
                raise HttpError('cancelled')
    except BaseException:
        p.kill()
        p.wait()
        _status(hdr)
        raise
    err = p.stderr.read().decode(errors='replace').strip()
    rc = p.wait()
    code = _status(hdr)
    ok_codes = (206,) if rng else (200, 206)
    if rc != 0 or code not in ok_codes:
        raise HttpError(f'stream: curl rc={rc} http={code} got={total} {err[:200]}')
    if expect_size is not None and total != expect_size:
        raise HttpError(f'stream: short body {total}/{expect_size}')
    return total, time.time() - t0


class SparseFile:
    def __init__(self, path, size):
        self.path = path
        self.fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o644)
        os.ftruncate(self.fd, size)
        self.written = 0

    def write(self, off, data):
        n = os.pwrite(self.fd, data, off)
        while n < len(data):
            n += os.pwrite(self.fd, data[n:], off + n)
        self.written += len(data)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class NeedMoov(Exception):
    pass


class StreamFilter:
    """Feed it the whole file in order (feed(memoryview)); call finish() at the end.

    plan(movie) -> (keep_ranges, kept_sync_indices) decides which mdat bytes survive.
    """

    MAX_BUFFERED_ATOM = 512 << 20

    def __init__(self, size, sparse, plan, movie=None, spill_under=0):
        self.size = size
        self.sp = sparse
        self.plan = plan
        self.movie = movie
        self.keep = None
        self.kept_sync = None
        if movie is not None:
            self.keep, self.kept_sync = plan(movie)
        self.spill_under = spill_under
        self.spill = False
        self.pos = 0
        self.atoms = []          # (type, offset, size)
        self.hdr = bytearray()
        self.cur = None          # (type, start, end, hdr_len)
        self.abuf = None         # buffered non-mdat atom
        self.moov_bytes = None
        self.head_end = None     # mdat payload start
        self.k = 0
        self.kept_bytes = 0

    # -------------------------------------------------------------- feeding
    def feed(self, mv):
        i = 0
        n = len(mv)
        while i < n:
            if self.cur is None:
                i = self._header(mv, i)
                continue
            typ, start, end, hl = self.cur
            take = min(n - i, end - self.pos)
            if typ == 'mdat' and not self.spill:
                self._filter(mv[i:i + take])
            else:
                self.sp.write(self.pos, mv[i:i + take])
                if self.spill and typ == 'mdat':
                    self.kept_bytes += take
                if self.abuf is not None:
                    self.abuf += mv[i:i + take]
            self.pos += take
            i += take
            if self.pos >= end:
                self._close_atom()

    def _header(self, mv, i):
        # collect 8 header bytes (16 for a 64-bit size) without advancing pos, which stays at the atom start
        need = 8 if len(self.hdr) < 8 else 16
        take = min(need - len(self.hdr), len(mv) - i)
        self.hdr += mv[i:i + take]
        i += take
        if len(self.hdr) < 8:
            return i
        size, typ = struct.unpack('>I4s', self.hdr[:8])
        if size == 1 and len(self.hdr) < 16:
            return i
        hl = 8
        if size == 1:
            size = struct.unpack('>Q', self.hdr[8:16])[0]
            hl = 16
        elif size == 0:
            size = self.size - self.pos          # last atom, runs to EOF
        start = self.pos
        typ = typ.decode('latin1')
        if size < hl or start + size > self.size:
            raise ValueError(f'bad atom {typ!r} size {size} at {start}')
        hb = bytes(self.hdr)
        self.hdr = bytearray()
        self.sp.write(start, hb)
        self.pos = start + hl
        self.cur = (typ, start, start + size, hl)
        self.atoms.append((typ, start, size))
        if typ == 'mdat':
            if self.head_end is None:
                self.head_end = start + hl
            if self.keep is None:
                if self.size <= self.spill_under:
                    self.spill = True
                else:
                    raise NeedMoov('mdat reached before any moov and the file is too big to keep whole')
            self.abuf = None
        else:
            if size > self.MAX_BUFFERED_ATOM:
                raise ValueError(f'atom {typ} too large to buffer ({size})')
            self.abuf = bytearray(hb)
        if self.pos >= self.cur[2]:
            self._close_atom()
        return i

    def _close_atom(self):
        typ, start, end, hl = self.cur
        if typ == 'moov' and self.abuf is not None:
            mb = bytes(self.abuf)
            if self.moov_bytes is None:
                self.moov_bytes = mb
            if self.movie is None:
                self.movie = mp4.parse_moov(mb)
                self.keep, self.kept_sync = self.plan(self.movie)
        self.abuf = None
        self.cur = None

    def _filter(self, chunk):
        a = self.pos
        b = a + len(chunk)
        keep = self.keep
        k = self.k
        while k < len(keep) and keep[k][1] <= a:
            k += 1
        j = k
        while j < len(keep) and keep[j][0] < b:
            lo = max(a, keep[j][0])
            hi = min(b, keep[j][1])
            if hi > lo:
                self.sp.write(lo, chunk[lo - a:hi - a])
                self.kept_bytes += hi - lo
            if keep[j][1] <= b:
                j += 1
            else:
                break
        self.k = j

    # -------------------------------------------------------------- result
    def finish(self):
        if self.pos != self.size:
            raise ValueError(f'stream ended at {self.pos} of {self.size}')
        if self.cur is not None:
            raise ValueError('stream ended inside an atom')
        return {'atoms': [list(a) for a in self.atoms], 'head_end': self.head_end, 'kept_bytes': self.kept_bytes,
                'spilled': self.spill}


def read_head(sparse_path, head_end):
    with open(sparse_path, 'rb') as f:
        return f.read(head_end)
