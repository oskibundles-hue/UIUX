#!/usr/bin/env python3
"""Check posts_library.py on a small built clip with known answers (needs ffmpeg; no model, a few seconds).

usage: python3 .claude/brain/tests/test_posts_library.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="posts-library-test-")
sys.path.insert(0, HERE)
import posts_library as pl  # noqa: E402

SCRIPT = os.path.join(HERE, "posts_library.py")
CAPTION = "Line one.\n\nLine three, after a blank line. #tag"
FAILS = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def run(*args):
    return subprocess.run([sys.executable, SCRIPT] + list(args), capture_output=True, text=True)


def main():
    if not os.path.exists(pl.tool("ffmpeg")):
        print("SKIP  ffmpeg isn't on this machine")
        return
    video = os.path.join(TMP, "Clip one - INSTAGRAM 1080x1920.mp4")
    subprocess.run([pl.tool("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=270x480:rate=10:duration=2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", video], check=True)
    cap = os.path.join(TMP, "caption.md")
    with open(cap, "w", encoding="utf-8") as f:
        f.write(CAPTION + "\n")
    work = os.path.join(TMP, "work")
    base = ["add", video, "--brand", "fd", "--id", "t1", "--title", "Clip one", "--work", work]

    check("a caption with no source is refused", run(*base, "--caption-file", cap).returncode != 0)
    check("an unknown brand is refused", run("add", video, "--brand", "xx", "--id", "t1", "--title", "x", "--work", work).returncode != 0)
    check("a post id with a slash is refused", run("add", video, "--brand", "fd", "--id", "a/b", "--title", "x", "--work", work).returncode != 0)

    pl.PART = 4096                                            # small parts, so the clip splits into several
    pl.add([video], {"--brand": "fd", "--id": "t1", "--title": "Clip one", "--work": work, "--caption-file": cap,
                     "--caption-source": "test", "--still": [video]})
    folder = os.path.join(work, "t1")
    with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    size = os.path.getsize(video)
    joined = b"".join(open(os.path.join(folder, p["name"]), "rb").read() for p in m["parts"])
    check("the parts rejoin to the master byte for byte", joined == open(video, "rb").read())
    check("the parts add up to the master's size", sum(p["size"] for p in m["parts"]) == size == m["video"]["total"])
    check("the caption is kept byte for byte", m["doc"]["caption"] == CAPTION)
    check("one cover still and three frames", [s["kind"] for s in m["stills"]] == ["cover", "video", "video", "video"])
    check("frames carry the video's name", m["stills"][1]["filename"] == "Clip one - frame 1.jpg")
    check("a new post starts unposted", m["doc"]["steps"] == {"built": True, "checked": True, "dropbox": False, "posted": False})
    for n in ("poster.jpg", "preview.mp4", "frame1.jpg", "frame2.jpg", "frame3.jpg"):
        check(n + " was cut", os.path.getsize(os.path.join(folder, n)) > 0)

    names = ["poster.jpg", "preview.mp4"] + [s["name"] for s in m["stills"]] + [p["name"] for p in m["parts"]]
    pairs = [f"{n}={i:032x}" for i, n in enumerate(names, 1)]
    check("a missing asset id is refused", run("record", "t1", *pairs[:-1], "--work", work).returncode != 0)
    check("parts out of step with the master are refused",
          run("record", "t1", *pairs, "--part", "0" * 32 + ":5", "--work", work).returncode != 0)
    r = run("record", "t1", *pairs, "--work", work)
    call = json.loads(r.stdout) if r.returncode == 0 else {}
    check("record prints a set on posts/t1", (call.get("action"), call.get("collection"), call.get("doc_id")) == ("set", "posts", "t1"), r.stderr)
    if call:
        with open(call["file_path"], encoding="utf-8") as f:
            doc = json.load(f)
        check("the record lists every part in order", [p["size"] for p in doc["video"]["parts"]] == [p["size"] for p in m["parts"]])
        check("the record points at the uploaded poster", doc["poster"] == f"{1:032x}")
        check("the record keeps the four stills", len(doc["stills"]) == 4 and all(len(s["id"]) == 32 for s in doc["stills"]))
    print("\n" + ("all passed" if not FAILS else f"{len(FAILS)} failed: " + ", ".join(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
