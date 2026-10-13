#!/usr/bin/env python3
"""Check a video saved through the Video Drop page against its master, leaving claude.ai's stamp out of it.

usage: python3 .claude/brain/c2pa_strip_check.py MASTER DROPBOX_COPY

claude.ai's save path adds a C2PA Content Credentials box to the file: a top-level MP4 `uuid` box, type
d8fec3d6-1b0e-483c-9297-5828877ec481, put right after `ftyp`. The saved copy is bigger than the master by
that box, and because the box sits before `mdat`, every chunk offset in `stco` / `co64` is higher by the
same amount. Nothing else changes, so the whole-file SHA-256 never matches the master's.

This reads the copy with the box left out and the chunk offsets moved back, and compares the SHA-256 of
that with the master's. MASTER is the master file, or its SHA-256 (64 hex characters) when the master
isn't on this machine. Prints PASS or FAIL: exit 0 on PASS, 1 on FAIL, 2 on a file it can't read.
It writes nothing and never changes the copy. The file is read in blocks, so a multi-GB master is fine.
No model call.
"""
import hashlib, os, struct, sys

C2PA = bytes.fromhex("d8fec3d61b0e483c92975828877ec481")    # the usertype of a C2PA uuid box
DOWN = (b"trak", b"mdia", b"minf", b"stbl")                  # the way down from moov to the chunk offset tables
BLOCK = 1 << 20


def boxes(peek, start, end):
    """Yield (type, offset, size, header length) for each box from start to end. peek(pos) returns 16 bytes."""
    pos = start
    while pos < end:
        head = peek(pos)
        if len(head) < 8:
            raise ValueError(f"not an MP4 box at byte {pos}")
        size, kind = struct.unpack(">I4s", head[:8])
        hlen = 8
        if size == 1:                                        # the real size is in the next 8 bytes
            if len(head) < 16:
                raise ValueError(f"not an MP4 box at byte {pos}")
            size, hlen = struct.unpack(">Q", head[8:16])[0], 16
        elif size == 0:                                      # the box runs to the end
            size = end - pos
        if size < hlen or pos + size > end:
            raise ValueError(f"not an MP4 box at byte {pos}")
        yield kind, pos, size, hlen
        pos += size


def shift_offsets(moov, start, end, cuts):
    """Move each stco / co64 entry in moov[start:end] back by the bytes cut ahead of it. Returns how many moved."""
    moved = 0
    for kind, pos, size, hlen in boxes(lambda p: bytes(moov[p:p + 16]), start, end):
        if kind in DOWN:
            moved += shift_offsets(moov, pos + hlen, pos + size, cuts)
        elif kind in (b"stco", b"co64"):
            fmt, width = (">I", 4) if kind == b"stco" else (">Q", 8)
            count = struct.unpack_from(">I", moov, pos + hlen + 4)[0]
            first = pos + hlen + 8
            if first + count * width > pos + size:
                raise ValueError(f"{kind.decode()} table runs past its box")
            for at in range(first, first + count * width, width):
                offset = struct.unpack_from(fmt, moov, at)[0]
                back = sum(n for cut, n in cuts if cut < offset)
                if back:
                    struct.pack_into(fmt, moov, at, offset - back)
                    moved += 1
    return moved


def restore(path):
    """Hash the copy as it was before the stamp. Returns (sha256, size, cuts, offsets moved); cuts = [(offset, size)]."""
    total = os.path.getsize(path)
    with open(path, "rb") as f:
        def peek(pos):
            f.seek(pos)
            return f.read(16)
        top = list(boxes(peek, 0, total))
        cuts = []
        for kind, pos, size, hlen in top:
            if kind == b"uuid":
                f.seek(pos + hlen)
                if f.read(16) == C2PA:
                    cuts.append((pos, size))
        digest, moved = hashlib.sha256(), 0
        for kind, pos, size, hlen in top:
            if (pos, size) in cuts:
                continue
            f.seek(pos)
            if kind == b"moov" and cuts:                     # moov is small; mdat is never read whole
                moov = bytearray(f.read(size))
                moved += shift_offsets(moov, hlen, size, cuts)
                digest.update(moov)
                continue
            left = size
            while left:
                block = f.read(min(left, BLOCK))
                if not block:
                    raise ValueError("the file ends early")
                digest.update(block)
                left -= len(block)
    return digest.hexdigest(), total - sum(n for _, n in cuts), cuts, moved


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(BLOCK), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    master, copy = argv
    try:
        if os.path.isfile(master):
            want, want_size = sha256(master), f"{os.path.getsize(master):,} bytes"
        elif len(master) == 64 and all(c in "0123456789abcdefABCDEF" for c in master):
            want, want_size = master.lower(), "size not given"
        else:
            raise ValueError(f"{master}: not a file and not a SHA-256")
        got, size, cuts, moved = restore(copy)
    except (OSError, ValueError, struct.error) as e:
        print(f"can't check: {e}", file=sys.stderr)
        return 2
    print(f"copy      {os.path.getsize(copy):,} bytes  {os.path.basename(copy)}")
    for pos, n in cuts:
        print(f"stamp     C2PA Content Credentials box at byte {pos:,}, {n:,} bytes")
    if cuts:
        print(f"offsets   {moved:,} chunk offsets moved back")
    print(f"master    {want_size}  sha256 {want}")
    print(f"restored  {size:,} bytes  sha256 {got}")
    stamp = "with the stamp left out" if cuts else "no stamp found"
    if got == want:
        print(f"PASS  {stamp}, and the copy is the master byte for byte")
        return 0
    print(f"FAIL  {stamp}, and the copy is not the master")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
