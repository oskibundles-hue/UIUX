#!/usr/bin/env python3
"""words_medium.py -- the second ASR model for the test chapter: faster-whisper medium.en (beam 5, word timestamps,
int8 CPU) over every edl.json dialog piece [in - 1.5, out_asr + 2.0] of /home/user/day-owt/aud/<clip>.m4a, word times in
clip seconds -> words_medium.json, keyed "<clip>:<in, 2 decimals>". Word pops use only words small.en (the day index,
/home/user/day-owt/tr) and medium.en both hear (see render.py agree()). Only new keys are transcribed.
    python3 words_medium.py
"""
import json, os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'words_medium.json')
_IIO = '/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
FF = os.environ.get('FFMPEG', _IIO if os.path.exists(_IIO) else 'ffmpeg')   # test-ch3's imageio build when present, else the system ffmpeg
edl = json.load(open(os.path.join(HERE, 'edl.json')))
db = json.load(open(OUT)) if os.path.exists(OUT) else {}
todo = [d for d in edl['dialog'] if f"{d['src']}:{d['in']:.2f}" not in db]
if todo:
    from faster_whisper import WhisperModel
    m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=2)
for d in todo:
    a = max(0.0, d['in'] - 1.5); b = d['out_asr'] + 2.0
    wav = tempfile.mktemp(suffix='.wav')
    subprocess.run([FF, '-v', 'error', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i',
                    f"/home/user/day-owt/aud/{d['src']}.m4a", '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', wav], check=True)
    # the installed PyAV no longer takes faster-whisper's metadata_errors argument, so the 16 kHz mono wav is handed
    # over as a float32 array (same samples faster-whisper's own decoder would produce)
    import numpy as np, wave as _w
    with _w.open(wav) as r:
        pcm = np.frombuffer(r.readframes(r.getnframes()), '<i2').astype(np.float32) / 32768.0
    segs, _ = m.transcribe(pcm, language='en', beam_size=5, word_timestamps=True, vad_filter=False)
    ws = [[round(a + w.start, 2), round(a + w.end, 2), w.word.strip()] for s in segs for w in (s.words or [])]
    os.remove(wav)
    db[f"{d['src']}:{d['in']:.2f}"] = ws
    print(d['src'], d['in'], ' '.join(w[2] for w in ws), flush=True)
    json.dump(db, open(OUT, 'w'), indent=0)
print('words_medium done', flush=True)
