"""Local mode: footage that is already on this machine (the Dropbox desktop folder, a card, a drive).

ingest and fetch only know single-use links. Local mode serves the files on 127.0.0.1 and writes link files that
look exactly like the Dropbox tool's answer, so both commands run unchanged: nothing to request, no 15 min clock,
and NEED.json (a clip that failed and wants fresh links) is answered by itself.

A clip's path is either an absolute local path (`vlog.py links DAY --local FOLDER`) or a Dropbox path such as
/NQ Studio/raw footage/2026-09-15/X.MP4 that is found under one of the --local-root folders.
"""
import glob
import os
import threading
import time
import unicodedata

from .common import log, read_json, write_json
from .rangeserver import RangeServer

VIDEO_EXT = ('.mp4', '.mov', '.m4v')
TTL = 7 * 86400


def dropbox_roots():
    """Where the Dropbox desktop app keeps its folder on this machine (macOS File Provider first, then legacy)."""
    home = os.path.expanduser('~')
    cands = sorted(glob.glob(os.path.join(home, 'Library', 'CloudStorage', 'Dropbox*'))) + [os.path.join(home, 'Dropbox')]
    cands += sorted(glob.glob(os.path.join(home, 'Dropbox (*)')))
    return [c for c in cands if os.path.isdir(c)]


def scan_folder(folder, recursive=False):
    """Video files in a local folder -> clip entries with absolute paths."""
    folder = os.path.abspath(os.path.expanduser(folder))
    out = []
    walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
    for d, _, files in walker:
        for f in sorted(files):
            if f.startswith('.') or os.path.splitext(f)[1].lower() not in VIDEO_EXT:
                continue
            p = os.path.join(d, f)
            out.append({'path': p, 'name': f, 'size': os.path.getsize(p)})
    return out


SF_DATALESS = 0x40000000  # macOS: an online-only file (Dropbox / iCloud placeholder), downloaded in full when read


def online_only(path):
    """True for a cloud placeholder whose bytes are not on this disk yet (reading it downloads the whole file)."""
    try:
        st = os.stat(path)
    except OSError:
        return False
    if getattr(st, 'st_flags', 0) & SF_DATALESS:
        return True
    return st.st_size > (1 << 20) and getattr(st, 'st_blocks', 1) == 0


def disk_guard(files, reserve_gb=20):
    """Online-only files among `files` would be downloaded in full by the Dropbox app. Returns (ok, message)."""
    import shutil
    off = [f for f in set(files) if f and online_only(f)]
    if not off:
        return True, ''
    need = sum(os.path.getsize(f) for f in off)
    free = shutil.disk_usage(os.path.dirname(off[0])).free
    msg = (f'{len(off)} file(s), {need / 1e9:.1f} GB, are online-only in Dropbox: reading them makes the Dropbox app '
           f'download them in full ({free / 1e9:.0f} GB free).')
    if need > free - reserve_gb * 1e9:
        return False, msg + (' That does not fit: make room, use the files from the camera card/drive instead, '
                             'or survey this day from Dropbox links (no disk needed; see MAC-SETUP.md).')
    return True, msg + ' They stay on this Mac afterwards (Finder: right-click > Remove Download to free the space).'


def _ci_join(root, rel):
    """root/rel, matching each component case-insensitively (Dropbox paths are case-insensitive)."""
    cur = root
    for part in [p for p in rel.split('/') if p]:
        nxt = os.path.join(cur, part)
        if not os.path.exists(nxt):
            try:
                names = os.listdir(cur)
            except OSError:
                return None
            want = unicodedata.normalize('NFC', part).lower()
            hit = [n for n in names if unicodedata.normalize('NFC', n).lower() == want]
            if not hit:
                return None
            nxt = os.path.join(cur, hit[0])
        cur = nxt
    return cur


class LocalLinks:
    def __init__(self, links_dir, roots=()):
        self.dir = links_dir
        os.makedirs(links_dir, exist_ok=True)
        self.roots = [os.path.abspath(os.path.expanduser(r)) for r in roots]
        self.srv = RangeServer()
        self.n = 0
        self._stop = threading.Event()
        self._need_sig = None

    def resolve(self, path):
        if os.path.isfile(path):
            return path
        for r in self.roots:
            p = _ci_join(r, path)
            if p and os.path.isfile(p):
                return p
        return None

    def write(self, paths, tag='local'):
        """One link per entry in `paths` (repeat a path for more links). Returns (written, missing paths)."""
        recs, missing = [], []
        for p in paths:
            f = self.resolve(p)
            if not f:
                missing.append(p)
                continue
            recs.append({'download_url': self.srv.link(f), 'expiration_in_sec': TTL, 'path_display': p,
                         'name': os.path.basename(p), 'size': os.path.getsize(f)})
        if recs:
            self.n += 1
            write_json(os.path.join(self.dir, f'{tag}_{int(time.time())}_{self.n:03d}.json'), {'entries': recs})
        return len(recs), sorted(set(missing))

    def answer_need(self):
        """NEED.json appeared (a clip failed or links ran out): write links for exactly its entries."""
        p = os.path.join(self.dir, 'NEED.json')
        if not os.path.exists(p):
            return
        st = os.stat(p)
        sig = (st.st_mtime, st.st_size)
        if sig == self._need_sig:
            return
        self._need_sig = sig
        need = read_json(p, {}) or {}
        entries = need.get('entries') or []
        if entries:
            n, missing = self.write(entries, tag='need')
            log(f'local: answered NEED.json with {n} link(s)' + (f'; not on this machine: {missing}' if missing else ''))

    def watch(self, every=2.0):
        def loop():
            while not self._stop.wait(every):
                try:
                    self.answer_need()
                except Exception as e:  # never take the run down over this
                    log(f'local: NEED watcher: {e}')
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop.set()
        self.srv.stop()


def request_paths(request_json):
    """Every entry of a request.json (in order, repeats kept) -> list of paths."""
    obj = read_json(request_json, {}) or {}
    return [e for b in obj.get('batches', []) for e in b.get('entries', [])]

