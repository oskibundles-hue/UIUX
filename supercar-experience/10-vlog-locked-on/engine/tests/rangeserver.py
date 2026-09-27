#!/usr/bin/env python3
"""The tests import RangeServer from here; it lives in lib/rangeserver.py (local mode uses it too).
Run it:  rangeserver.py PORT FILE...   (prints one reusable URL per file under /file/<n>)"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.rangeserver import RangeServer  # noqa: E402,F401

if __name__ == '__main__':
    port = int(sys.argv[1])
    files = [os.path.abspath(f) for f in sys.argv[2:]]
    s = RangeServer(port, files)
    for i, f in enumerate(files):
        print(f'http://127.0.0.1:{s.port}/file/{i}  {f}')
    threading.Event().wait()
