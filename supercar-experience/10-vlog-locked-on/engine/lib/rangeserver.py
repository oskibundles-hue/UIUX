"""Single-use links to files on this machine: the tests' stand-in for Dropbox links, and local mode's source
(files in the Dropbox desktop folder served to ingest and fetch through the same code path as real links).

  GET /once/<token>        the file the token maps to. The token is consumed by its first request of any kind
                           (HEAD and Range included); later requests get 410 Gone, like Dropbox.
  Range: bytes=a-b         one range -> 206 + Content-Range. Several ranges -> ignored, 200 with the whole file
                           (Dropbox does the same). No Range -> 200.

Use from Python:  srv = RangeServer(); url = srv.link('/path/file.mp4'); ...; srv.stop()
or run it:        rangeserver.py PORT FILE...   (prints one reusable URL per file under /file/<n>)
"""
import http.server
import os
import re
import secrets
import socketserver
import sys
import threading


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _serve(self, head):
        srv = self.server
        m = re.match(r'^/once/([A-Za-z0-9_-]+)$', self.path)
        path = None
        if m:
            with srv.lock:
                path = srv.tokens.pop(m.group(1), None)
                if path is None and m.group(1) in srv.spent:
                    return self._err(410, 'link already used')
                srv.spent.add(m.group(1))
        else:
            m = re.match(r'^/file/(\d+)$', self.path)
            if m and int(m.group(1)) < len(srv.files):
                path = srv.files[int(m.group(1))]
        if path is None:
            return self._err(404, 'no such link')
        size = os.path.getsize(path)
        rng = self.headers.get('Range')
        lo, hi, code = 0, size, 200
        if rng:
            mm = re.match(r'^bytes=(\d*)-(\d*)$', rng.strip())
            if mm:  # a single range; multi-range falls through to 200 like Dropbox
                a, b = mm.groups()
                if a == '':
                    lo, hi = max(0, size - int(b)), size
                else:
                    lo = int(a)
                    hi = min(size, int(b) + 1) if b else size
                if lo >= size or hi <= lo:
                    return self._err(416, 'bad range')
                code = 206
        with srv.lock:
            srv.log.append((self.command, os.path.basename(path), code, lo, hi))
        self.send_response(code)
        self.send_header('Content-Length', str(hi - lo))
        self.send_header('Accept-Ranges', 'bytes')
        if code == 206:
            self.send_header('Content-Range', f'bytes {lo}-{hi - 1}/{size}')
        self.end_headers()
        if head:
            return
        with open(path, 'rb') as f:
            off = lo
            use_sendfile = hasattr(os, 'sendfile')
            while off < hi:
                try:
                    if use_sendfile:
                        try:
                            n = os.sendfile(self.wfile.fileno(), f.fileno(), off, min(8 << 20, hi - off))
                        except OSError as e:
                            if isinstance(e, (BrokenPipeError, ConnectionResetError)):
                                raise
                            use_sendfile = False  # not supported here: plain reads from now on
                            continue
                    else:
                        f.seek(off)
                        buf = f.read(min(8 << 20, hi - off))
                        self.wfile.write(buf)
                        n = len(buf)
                except (BrokenPipeError, ConnectionResetError):
                    return
                if n <= 0:
                    return
                off += n
                if srv.throttle:
                    import time
                    time.sleep(n / srv.throttle)

    def _err(self, code, msg):
        body = msg.encode()
        self.send_response(code)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._serve(False)

    def do_HEAD(self):
        self._serve(True)


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class RangeServer:
    def __init__(self, port=0, files=(), throttle=None):
        self.httpd = _Server(('127.0.0.1', port), _Handler)
        self.httpd.tokens = {}
        self.httpd.spent = set()
        self.httpd.lock = threading.Lock()
        self.httpd.files = list(files)
        self.httpd.log = []
        self.httpd.throttle = throttle  # bytes/s per response, None = unthrottled
        self.port = self.httpd.server_address[1]
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.t.start()

    def link(self, path):
        tok = secrets.token_urlsafe(16)
        self.httpd.tokens[tok] = os.path.abspath(path)
        return f'http://127.0.0.1:{self.port}/once/{tok}'

    @property
    def log(self):
        return self.httpd.log

    def stop(self):
        self.httpd.shutdown()


if __name__ == '__main__':
    port = int(sys.argv[1])
    files = [os.path.abspath(f) for f in sys.argv[2:]]
    s = RangeServer(port, files)
    for i, f in enumerate(files):
        print(f'http://127.0.0.1:{s.port}/file/{i}  {f}')
    threading.Event().wait()
