#!/usr/bin/env python3
"""words_b2.py -- medium.en word edges (faster-whisper, beam 5, int8 CPU) over the montage-v2 bite ranges of
/home/user/day-owt/aud/<clip>.m4a -> words_medium_B2.json keyed "<clip>:<a>-<b>", word times in clip seconds.
Only new keys are transcribed.   python3 words_b2.py
"""
import json, os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'words_medium_B2.json')
FF = '/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
RANGES = [('0090', 19, 29), ('0091', 1, 11), ('0093', 2.5, 10), ('0100', 29, 40), ('0102', 0.5, 26.5), ('0105', 3, 15),
          ('0106', 172, 186), ('0107', 253, 264), ('0111', 45, 58.5), ('0112', 12, 21), ('0114', 2.5, 46),
          ('0115', 1.5, 38), ('0118', 68, 93), ('0123', 2, 14)]
db = json.load(open(OUT)) if os.path.exists(OUT) else {}
todo = [r for r in RANGES if f'{r[0]}:{r[1]:g}-{r[2]:g}' not in db]
if todo:
    from faster_whisper import WhisperModel
    m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=3)
for src, a, b in todo:
    wav = tempfile.mktemp(suffix='.wav')
    subprocess.run([FF, '-v', 'error', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', f'/home/user/day-owt/aud/{src}.m4a',
                    '-ac', '1', '-ar', '16000', wav], check=True)
    segs, _ = m.transcribe(wav, language='en', beam_size=5, word_timestamps=True, vad_filter=False)
    ws = [[round(a + w.start, 2), round(a + w.end, 2), w.word.strip()] for s in segs for w in (s.words or [])]
    os.remove(wav)
    db[f'{src}:{a:g}-{b:g}'] = ws
    print(src, ' '.join(f'{w[2]}@{w[0]:.2f}-{w[1]:.2f}' for w in ws), flush=True)
    json.dump(db, open(OUT, 'w'), indent=0)
print('words_b2 done', flush=True)
