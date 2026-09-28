"""Dropbox single-use links: what to request, how to read the tool's answer, and a pool that never reuses a link.

The Dropbox MCP tool (download_link) takes up to 25 `entries` (paths) and answers
  {"entries": [{"download_url", "expiration_in_sec", "path", "path_display", "name", "id", "size", ...}, ...]}
in request order. A link is consumed by its first HTTP request (HEAD and Range included) and expires.
We ask for each clip's path twice in the same call (tail + stream), so link count = 2 x clips.

Any JSON the parent pastes into links/*.json is accepted: the raw tool result, several results concatenated,
a list of them, or an MCP wrapper whose text content is that JSON. Every dict with a download_url counts.
"""
import glob
import hashlib
import json
import os
import time

from .common import read_json, write_json

MAX_PER_CALL = 25
DEFAULT_TTL_MARGIN = 90  # seconds of safety before the stated expiry (the file is saved a little after issue)


def _walk(o, out):
    if isinstance(o, dict):
        if 'download_url' in o:
            out.append(o)
            return
        for v in o.values():
            _walk(v, out)
    elif isinstance(o, list):
        for v in o:
            _walk(v, out)
    elif isinstance(o, str):
        s = o.strip()
        if s.startswith('{') or s.startswith('['):
            try:
                _walk(json.loads(s), out)
            except ValueError:
                pass


def parse_link_text(text):
    """All link records in a text holding one or more JSON values."""
    out = []
    dec = json.JSONDecoder()
    i = 0
    n = len(text)
    while i < n:
        while i < n and text[i] not in '{[':
            i += 1
        if i >= n:
            break
        try:
            obj, j = dec.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        _walk(obj, out)
        i = j
    return out


def url_key(url):
    return hashlib.sha1(url.encode()).hexdigest()[:16]


class LinkPool:
    """Links from DAY/links/*.json. used.log records every link the moment before it is requested, so a
    restarted ingest never touches a consumed link."""

    SKIP = {'request.json', 'NEED.json'}

    def __init__(self, links_dir, ttl_margin=DEFAULT_TTL_MARGIN):
        self.dir = links_dir
        self.ttl_margin = ttl_margin
        self.links = {}      # key -> record
        self.seen_files = {}
        self.used = set()
        self.used_log = os.path.join(links_dir, 'used.log')
        if os.path.exists(self.used_log):
            for line in open(self.used_log):
                if line.strip():
                    self.used.add(line.split()[0])

    def scan(self):
        """Pick up new or changed link files. Returns the number of new links."""
        new = 0
        for f in sorted(glob.glob(os.path.join(self.dir, '*.json'))):
            b = os.path.basename(f)
            if b in self.SKIP or b.startswith('.'):
                continue
            st = os.stat(f)
            sig = (st.st_mtime, st.st_size)
            if self.seen_files.get(f) == sig:
                continue
            self.seen_files[f] = sig
            try:
                recs = parse_link_text(open(f).read())
            except OSError:
                continue
            for i, r in enumerate(recs):
                k = url_key(r['download_url'])
                if k in self.links:
                    continue
                path = r.get('path_display') or r.get('path') or r.get('name')
                self.links[k] = {
                    'key': k, 'url': r['download_url'], 'path': path, 'name': r.get('name') or os.path.basename(path or ''),
                    'size': r.get('size') or (r.get('file') or {}).get('size') if isinstance(r.get('file'), dict) or 'size' in r else None,
                    'issued': st.st_mtime,
                    'expires': st.st_mtime + int(r.get('expiration_in_sec') or 600) - self.ttl_margin,
                    'file': b, 'i': i}
                new += 1
        return new

    def fresh(self, path):
        now = time.time()
        pl = path.lower()
        return sorted((r for r in self.links.values()
                       if r['key'] not in self.used and r['expires'] > now and (r['path'] or '').lower() == pl),
                      key=lambda r: (r['issued'], r['file'], r['i']))

    def expired_unused(self):
        now = time.time()
        return [r for r in self.links.values() if r['key'] not in self.used and r['expires'] <= now]

    def take(self, path, role):
        lst = self.fresh(path)
        if not lst:
            return None
        r = lst[0]
        self.used.add(r['key'])
        with open(self.used_log, 'a') as f:
            f.write(f"{r['key']} {time.strftime('%Y-%m-%dT%H:%M:%S')} {role} {r['path']}\n")
        return r

    def entries(self):
        """Distinct (path, name, size) seen in link files, for auto-registering clips."""
        seen = {}
        for r in self.links.values():
            if r['path'] and r['path'].lower() not in seen:
                seen[r['path'].lower()] = {'path': r['path'], 'name': r['name'], 'size': r['size']}
        return list(seen.values())


def request_batches(paths_needed, per_call=MAX_PER_CALL):
    """paths_needed: [(path, n_links)] in priority order -> list of entry lists (a clip's links stay together)."""
    batches = [[]]
    for path, k in paths_needed:
        if k <= 0:
            continue
        if len(batches[-1]) + k > per_call:
            batches.append([])
        batches[-1].extend([path] * k)
    return [b for b in batches if b]


def write_request(links_dir, batches, name='request.json', expiration=900, note=''):
    obj = {'tool': 'Dropbox download_link', 'expiration_in_sec': expiration, 'note': note,
           'batches': [{'batch': i + 1, 'entries': b} for i, b in enumerate(batches)]}
    write_json(os.path.join(links_dir, name), obj)
    return obj


def read_need(links_dir):
    return read_json(os.path.join(links_dir, 'NEED.json'))
