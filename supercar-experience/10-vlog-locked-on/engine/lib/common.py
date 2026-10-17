"""Shared bits: ffmpeg location, logging, clip ids and camera clocks, the day registry, atomic writes."""
import datetime as _dt
import json
import os
import re
import shutil
import sys
import threading
import time

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ffmpeg_path():
    p = os.environ.get('VLOG_FFMPEG')
    if p and os.path.exists(p):
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return shutil.which('ffmpeg') or 'ffmpeg'


FF = ffmpeg_path()

_log_lock = threading.Lock()
_log_file = None


def set_log(path):
    global _log_file
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _log_file = open(path, 'a', buffering=1)


def log(*a):
    line = time.strftime('%H:%M:%S') + ' ' + ' '.join(str(x) for x in a)
    with _log_lock:
        print(line, flush=True)
        if _log_file:
            _log_file.write(line + '\n')


def write_json(path, obj, indent=1):
    tmp = path + '.tmp%d' % os.getpid()
    with open(tmp, 'w') as f:
        json.dump(obj, f, indent=indent)
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def fmt_t(t):
    return f'{int(t // 60)}:{t % 60:04.1f}'


def fmt_clock(s):
    s = int(round(s)) % 86400
    return f'{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}'


# ------------------------------------------------------------------ clip names -> ids and camera clocks
DJI_RE = re.compile(r'DJI_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})_(\d{4})_D', re.I)
UPLOAD_RE = re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2})\.(\d{2})\.(\d{2})')
VIDEO_RE = re.compile(r'Video (\w{3}) (\d{1,2}) (\d{4}), (\d{1,2}) (\d{2}) (\d{2}) ?(AM|PM)', re.I)
MONTHS = {m: i + 1 for i, m in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split())}


def name_clock(name):
    """(YYYY-MM-DD, seconds since local midnight) from a camera / Dropbox upload file name, or None."""
    base = os.path.basename(name)
    m = DJI_RE.search(base)
    if m:
        y, mo, d, hh, mm, ss = (int(x) for x in m.groups()[:6])
        return f'{y:04d}-{mo:02d}-{d:02d}', hh * 3600 + mm * 60 + ss
    m = UPLOAD_RE.search(base)
    if m:
        y, mo, d, hh, mm, ss = (int(x) for x in m.groups())
        return f'{y:04d}-{mo:02d}-{d:02d}', hh * 3600 + mm * 60 + ss
    m = VIDEO_RE.search(base)
    if m:
        mon, d, y, hh, mm, ss, ap = m.groups()
        hh = int(hh) % 12 + (12 if ap.upper() == 'PM' else 0)
        return f'{int(y):04d}-{MONTHS.get(mon[:3].lower(), 1):02d}-{int(d):02d}', hh * 3600 + int(mm) * 60 + int(ss)
    return None


def assign_ids(names):
    """Stable short ids: DJI clips -> their 4-digit counter; everything else -> P<hhmm>, with a/b/c... when
    several start in the same minute (the Sep 15 convention: P2236, P2140a..e)."""
    names = list(dict.fromkeys(names))
    ids = {}
    phone = {}
    for n in names:
        m = DJI_RE.search(os.path.basename(n))
        if m:
            ids[n] = m.group(7)
            continue
        c = name_clock(n)
        if c:
            key = 'P%02d%02d' % (c[1] // 3600, c[1] % 3600 // 60)
            phone.setdefault(key, []).append((c[1], n))
        else:
            stem = re.sub(r'[^A-Za-z0-9]+', '', os.path.splitext(os.path.basename(n))[0])[-12:] or 'clip'
            ids[n] = 'X' + stem
    for key, lst in phone.items():
        lst.sort()
        if len(lst) == 1:
            ids[lst[0][1]] = key
        else:
            for i, (_, n) in enumerate(lst):
                ids[n] = key + 'abcdefghijklmnopqrstuvwxyz'[i]
    # de-duplicate anything left colliding
    seen = {}
    for n in names:
        i = ids[n]
        if i in seen and seen[i] != n:
            k = 2
            while f'{i}_{k}' in seen:
                k += 1
            ids[n] = f'{i}_{k}'
        seen[ids[n]] = n
    return ids


def clock_from_movie(movie, tz_offset_s=None):
    """Seconds since local midnight from the moov: Apple creationdate (local, with offset) or mvhd UTC time."""
    if movie.creation_time:
        off = tz_offset_s
        if off is None and movie.apple_creationdate:
            m = re.search(r'([+-])(\d{2})(\d{2})$', movie.apple_creationdate)
            if m:
                off = (1 if m.group(1) == '+' else -1) * (int(m.group(2)) * 3600 + int(m.group(3)) * 60)
        if off is not None:
            t = _dt.datetime.fromtimestamp(movie.creation_time + off, _dt.timezone.utc)
            return t.strftime('%Y-%m-%d'), t.hour * 3600 + t.minute * 60 + t.second
    if movie.apple_creationdate:
        m = re.match(r'(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})', movie.apple_creationdate)
        return m.group(1), int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4))
    return None


# ------------------------------------------------------------------ the day directory
class Day:
    """A working directory for one shoot day. Layout:
      clips.json            id -> {name, path, size, clock, date}
      links/                request.json (what to ask the Dropbox tool for), *.json tool results, NEED.json, used.log
      idx/<id>.head|.moov|.json   everything needed to range-fetch full quality later
      aud/<id>.m4a          camera audio, stream-copied (written as aud/.<id>.m4a.part, then renamed)
      kf/<id>/<ms>.jpg      survey thumbnails (270 px wide, display-rotated) + kf/<id>/stats.json
      tr/<id>.json|.txt     transcripts (faster-whisper, word timings)
      state/<id>.json       per-clip progress, timings, errors
      sparse/               transient sparse files (deleted after each clip)
    """

    def __init__(self, root):
        self.root = os.path.abspath(root)
        for d in ('links', 'idx', 'aud', 'kf', 'tr', 'state', 'sparse', 'logs'):
            os.makedirs(os.path.join(self.root, d), exist_ok=True)

    def p(self, *a):
        return os.path.join(self.root, *a)

    @property
    def clips(self):
        return read_json(self.p('clips.json'), {})

    def save_clips(self, clips):
        write_json(self.p('clips.json'), clips)

    def register(self, entries):
        """entries: [{path, name, size}] -> merged into clips.json; returns the registry."""
        clips = self.clips
        by_path = {c['path'].lower(): cid for cid, c in clips.items()}
        names = [c['path'] for c in clips.values()]
        new = [e for e in entries if e['path'].lower() not in by_path]
        if new:
            allnames = names + [e['path'] for e in new]
            ids = assign_ids(allnames)
            # existing ids never change
            for e in new:
                cid = ids[e['path']]
                while cid in clips:
                    cid = cid + '_'
                c = name_clock(e['path'])
                clips[cid] = {'path': e['path'], 'name': e.get('name') or os.path.basename(e['path']),
                              'size': e.get('size'), 'date': c[0] if c else None, 'clock': c[1] if c else None}
        for e in entries:
            cid = {c['path'].lower(): k for k, c in clips.items()}[e['path'].lower()]
            if e.get('size') and not clips[cid].get('size'):
                clips[cid]['size'] = e['size']
        self.save_clips(clips)
        return clips

    def state(self, cid):
        return read_json(self.p('state', cid + '.json'), {'id': cid})

    def set_state(self, cid, **kw):
        st = self.state(cid)
        st.update(kw)
        write_json(self.p('state', cid + '.json'), st)
        return st


def free_disk(path):
    s = os.statvfs(path)
    return s.f_bavail * s.f_frsize


def die(msg):
    print('error:', msg, file=sys.stderr)
    sys.exit(2)
