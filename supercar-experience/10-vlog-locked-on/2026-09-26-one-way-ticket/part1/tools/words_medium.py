#!/usr/bin/env python3
"""words_medium.py -- Part 1 v2: medium.en word timings around every EDL dialog piece -> data/words_medium.json.

The second model for fix A (tools/tail_check.py, tools/make_edl.py `tail`) and for the two-model caption check. Each
piece is transcribed from the camera's own AAC stream (paths.aud/<clip>.m4a, full length) over [in - 1.5, out + 4.0]
with faster-whisper medium.en (beam 5, word timestamps, int8 on the CPU); word times are written in clip seconds,
keyed "<clip>:<in, 2 decimals>" (part2's format). Re-run after an EDL change: only new keys are transcribed.
    python3 tools/words_medium.py [--all]
"""
import json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from cfg import load_config  # noqa: E402

C = load_config()
OUT = os.path.join(ROOT, 'data', 'words_medium.json')
PRE, POST = 1.5, 4.0


def main():
    edl = json.load(open(C['paths']['edl']))
    db = json.load(open(OUT)) if os.path.exists(OUT) and '--all' not in sys.argv else {}
    todo = [d for d in edl['dialog'] if f"{d['src']}:{d['in']:.2f}" not in db]
    if not todo:
        print('words_medium: nothing new'); return
    from faster_whisper import WhisperModel
    m = WhisperModel('medium.en', device='cpu', compute_type='int8')
    for d in todo:
        a = max(0.0, d['in'] - PRE)
        b = d.get('out_asr', d['out']) + POST
        wav = tempfile.mktemp(suffix='.wav')
        subprocess.run([C['paths']['ffmpeg'], '-v', 'error', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i',
                        os.path.join(C['paths']['aud'], f"{d['src']}.m4a"), '-ac', '1', '-ar', '16000', wav], check=True)
        segs, _ = m.transcribe(wav, language='en', beam_size=5, word_timestamps=True, vad_filter=False)
        ws = [[round(a + w.start, 2), round(a + w.end, 2), w.word] for s in segs for w in (s.words or [])]
        os.remove(wav)
        db[f"{d['src']}:{d['in']:.2f}"] = ws
        print(d['src'], d['in'], ' '.join(w[2].strip() for w in ws), flush=True)
        json.dump(db, open(OUT, 'w'), indent=0)
    print(f'words_medium: {len(todo)} pieces -> {OUT}')


if __name__ == '__main__':
    main()
