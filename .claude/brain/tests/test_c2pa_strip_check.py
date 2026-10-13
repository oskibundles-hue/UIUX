#!/usr/bin/env python3
"""Check c2pa_strip_check.py on small built MP4s with known answers (no ffmpeg, no model, under 1 s).

usage: python3 .claude/brain/tests/test_c2pa_strip_check.py
"""
import hashlib, os, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="c2pa-strip-test-")
sys.path.insert(0, HERE)
import c2pa_strip_check as csc  # noqa: E402


def box(kind, body):
    return struct.pack(">I4s", 8 + len(body), kind) + body


FTYP = box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2avc1mp41")           # 32 bytes, as ffmpeg writes it
FREE = box(b"free", b"")
STAMP = box(b"uuid", csc.C2PA + b"c2pa manifest " * 400)               # stands in for claude.ai's box
OTHER = box(b"uuid", bytes(range(16)) + b"a uuid box the master came with")
PAYLOAD = bytes(range(256)) * 64
VIDEO, AUDIO = [0, 4096, 9000], [2048, 12000]                          # chunk offsets into the mdat payload


def trak(offsets, wide):
    kind, fmt = (b"co64", ">Q") if wide else (b"stco", ">I")
    table = box(kind, struct.pack(">II", 0, len(offsets)) + b"".join(struct.pack(fmt, o) for o in offsets))
    stbl = box(b"stbl", box(b"stsd", b"\0" * 8) + table)
    return box(b"trak", box(b"tkhd", b"\0" * 84) + box(b"mdia", box(b"mdhd", b"\0" * 24) + box(b"minf", stbl)))


def movie(wide=(False, False), moov_last=False, big=False, lead=b"", tail=b""):
    """ftyp, lead, then moov and mdat in either order, then tail. The offset tables are true for that layout."""
    def moov(base):
        return box(b"moov", box(b"mvhd", b"\0" * 100) + trak([base + o for o in VIDEO], wide[0])
                   + trak([base + o for o in AUDIO], wide[1]))
    mdat = (struct.pack(">I4sQ", 1, b"mdat", 16 + len(PAYLOAD)) if big else struct.pack(">I4s", 8 + len(PAYLOAD), b"mdat")) + PAYLOAD
    data_at = len(FTYP) + len(lead) + len(FREE) + (0 if moov_last else len(moov(0))) + len(mdat) - len(PAYLOAD)
    return FTYP + lead + (FREE + mdat + moov(data_at) if moov_last else moov(data_at) + FREE + mdat) + tail


def save(name, data):
    path = os.path.join(TMP, name)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def run(master, copy):
    return subprocess.run([sys.executable, os.path.join(HERE, "c2pa_strip_check.py"), master, copy],
                          capture_output=True, text=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


CHECKS = []
plain = movie()
master = save("master.mp4", plain)
stamped = save("stamped.mp4", movie(lead=STAMP))
got = csc.restore(stamped)
CHECKS.append(("the stamped copy is bigger by the box and its whole-file hash differs",
               os.path.getsize(stamped) - len(plain) == len(STAMP) and csc.sha256(stamped) != sha(plain)))
CHECKS.append(("box out and offsets back gives the master's hash",
               got == (sha(plain), len(plain), [(len(FTYP), len(STAMP))], len(VIDEO) + len(AUDIO))))
r = run(master, stamped)
CHECKS.append(("CLI prints PASS and exits 0", r.returncode == 0 and "\nPASS" in r.stdout and "5,624 bytes" in r.stdout))
CHECKS.append(("the copy is left as it was", csc.sha256(stamped) == sha(movie(lead=STAMP)) and len(os.listdir(TMP)) == 2))
CHECKS.append(("the master can be given as its SHA-256", run(sha(plain).upper(), stamped).returncode == 0))

for label, kw in [("moov after mdat (the Showreel layout)", {"moov_last": True}),
                  ("co64 tables", {"wide": (True, True)}),
                  ("one stco and one co64 track", {"wide": (False, True)}),
                  ("an mdat with a 64-bit size", {"big": True})]:
    want = movie(**kw)
    CHECKS.append((label, csc.restore(save("case.mp4", movie(lead=STAMP, **kw)))[:2] == (sha(want), len(want))))

want = movie(moov_last=True)
got = csc.restore(save("case.mp4", movie(moov_last=True, tail=STAMP)))
CHECKS.append(("a stamp after mdat moves no offsets", got[0] == sha(want) and got[3] == 0))
want = movie(lead=OTHER)
got = csc.restore(save("case.mp4", movie(lead=OTHER + STAMP)))
CHECKS.append(("another uuid box stays in", got[0] == sha(want) and got[2] == [(len(FTYP) + len(OTHER), len(STAMP))]))

bad = bytearray(movie(lead=STAMP))
bad[-100] ^= 1
r = run(master, save("case.mp4", bytes(bad)))
CHECKS.append(("one changed byte in mdat is a FAIL, exit 1", r.returncode == 1 and "\nFAIL" in r.stdout))
bad = bytearray(movie(lead=STAMP))
bad[-len(PAYLOAD) - 8 - len(FREE) - 1] ^= 1                             # the last chunk offset's low byte
r = run(master, save("case.mp4", bytes(bad)))
CHECKS.append(("one wrong chunk offset is a FAIL", r.returncode == 1))
r = run(master, save("case.mp4", plain))
CHECKS.append(("no stamp and the same bytes is a PASS", r.returncode == 0 and "no stamp found" in r.stdout))
r = run(master, save("case.mp4", plain[:-1] + b"\0"))
CHECKS.append(("no stamp and different bytes is a FAIL", r.returncode == 1 and "no stamp found" in r.stdout))
r = run(master, save("case.mp4", b"this is not a video"))
CHECKS.append(("a file that isn't an MP4 exits 2", r.returncode == 2 and "can't check" in r.stderr))
r = run(master, save("case.mp4", movie(lead=STAMP)[:-10]))
CHECKS.append(("a cut-off file exits 2", r.returncode == 2))
CHECKS.append(("a missing master exits 2", run(os.path.join(TMP, "nope.mp4"), stamped).returncode == 2))

bad = 0
for label, ok in CHECKS:
    bad += not ok
    print(("ok  " if ok else "FAIL") + "  " + label)
print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} passed")
sys.exit(1 if bad else 0)
