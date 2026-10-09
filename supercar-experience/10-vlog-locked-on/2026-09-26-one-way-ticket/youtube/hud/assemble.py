#!/usr/bin/env python3
"""One-way ticket: the 720p rough cut (opening + Ch1-8, the driving HUD burned in).

    python3 assemble.py audio      # concat mix / nomusic wavs sample-exactly, check lengths and joins
    python3 assemble.py video      # scale + concat + HUD overlay + AAC, one encode -> roughcut_720p.mp4 (+ NOMUSIC remux)
    python3 assemble.py loud       # ebur128 on the AAC of both files
    python3 assemble.py send       # chat copies under 29 MiB
    python3 assemble.py chapters   # roughcut/chapters.txt
    python3 assemble.py gate       # gate sheets: HUD runs, chapter joins

The HUD clips come from `render_hud.py OUT/hud720 720` (runs.json gives each clip's global frame and x, y).
"""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = '/home/user/day-owt'
OUT = f'{D}/roughcut'
HUDDIR = f'{OUT}/hud720'
NAME = f'{OUT}/one_way_ticket_roughcut_720p'
SPF = 48000 * 1001 / 30000          # samples per frame (1601.6)
PIECES = [  # name, picture, mix, nomusic, frames, chapter name (PLAN.md)
    ('opening', 'openwork/master_video.mp4', 'openwork/mix_B2.wav', 'openwork/nomusic_B2.wav', 1541, 'Running on empty'),
    ('ch1', 'ch1work/ch1_master.mp4', 'ch1work/mix.wav', 'ch1work/nomusic.wav', 1618, '4:30 a.m.'),
    ('ch2', 'ch2work/master_video.mp4', 'ch2work/mix.wav', 'ch2work/nomusic.wav', 1137, 'Seattle · morning'),
    ('ch3', 'ch3work/master_video.mp4', 'ch3work/mix.wav', 'ch3work/nomusic.wav', 4767, 'Seattle, WA · noon'),
    ('ch4', 'ch4work/master_video.mp4', 'ch4work/mix.wav', 'ch4work/nomusic.wav', 2174, 'Into Oregon'),
    ('ch5', 'ch5work/proxy_video.mp4', 'ch5work/mix.wav', 'ch5work/nomusic.wav', 1715, 'Nampa, Idaho · night'),
    ('ch6', 'ch6work/proxy_video.mp4', 'ch6work/mix.wav', 'ch6work/nomusic.wav', 1383, '1:29 a.m.'),
    ('ch7', 'ch7work/proxy_video.mp4', 'ch7work/mix.wav', 'ch7work/nomusic.wav', 2121, 'Sunrise · Nevada'),
    ('ch8', 'ch8work/proxy_video.mp4', 'ch8work/mix.wav', 'ch8work/nomusic.wav', 2495, 'Las Vegas'),
]
F0 = np.cumsum([0] + [p[4] for p in PIECES]).tolist()
TOTAL = F0[-1]


def sh(cmd, **kw):
    kw.setdefault('text', True)
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode:
        err = r.stderr if isinstance(r.stderr, str) else r.stderr.decode(errors='replace')
        sys.exit(f'FAILED: {" ".join(cmd)}\n{err[-2000:]}')
    return r


def read24(path):
    w = wave.open(path); assert w.getsampwidth() == 3 and w.getframerate() == 48000 and w.getnchannels() == 2
    b = np.frombuffer(w.readframes(w.getnframes()), np.uint8).reshape(-1, 3).astype(np.int32)
    x = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
    return np.where(x >= 1 << 23, x - (1 << 24), x).reshape(-1, 2)


def write24(path, x):
    x = x.reshape(-1).astype(np.int32) & 0xFFFFFF
    b = np.stack([x & 255, (x >> 8) & 255, (x >> 16) & 255], 1).astype(np.uint8)
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(3); w.setframerate(48000)
    w.writeframes(b.tobytes()); w.close()


def audio():
    rep = []
    for k, tag in ((2, 'mix'), (3, 'nomusic')):
        parts = []
        for i, p in enumerate(PIECES):
            x = read24(f'{D}/{p[k]}')
            want = round(F0[i + 1] * SPF) - round(F0[i] * SPF)     # cumulative rounding: the total is exact
            exp = p[4] * SPF
            note = 'ok' if abs(len(x) - exp) < 1 else f'{len(x) - exp:+.1f} samples vs frames*1001/30000*48000'
            if len(x) > want:
                tail = np.abs(x[want:]).max() / 2 ** 23 if len(x) > want else 0
                note += f'; trimmed {len(x) - want} (tail peak {20 * np.log10(tail + 1e-12):.0f} dBFS)' if len(x) - want > 1 else ''
                x = x[:want]
            elif len(x) < want:
                note += f'; padded {want - len(x)}' if want - len(x) > 1 else ''
                x = np.concatenate([x, np.zeros((want - len(x), 2), np.int32)])
            parts.append(x); rep.append(f'{tag} {p[0]}: {note}')
        y = np.concatenate(parts)
        assert len(y) == round(TOTAL * SPF)
        # a 5 ms fade-in on the incoming piece wherever the first sample steps harder than the audio around it
        for i in range(1, len(PIECES)):
            j = round(F0[i] * SPF)
            step = np.abs(y[j].astype(np.int64) - y[j - 1]).max()
            local = np.abs(np.diff(y[j - 480:j], axis=0)).max()
            if step > local:
                y[j:j + 240] = (y[j:j + 240] * np.linspace(0, 1, 240)[:, None]).astype(np.int32)
                rep.append(f'{tag} join {PIECES[i - 1][0]}->{PIECES[i][0]}: 5 ms fade-in applied (first-sample step {step / 2 ** 23:.5f})')
        # join check: the step across each join against the largest step in the 10 ms either side
        for i in range(1, len(PIECES)):
            j = round(F0[i] * SPF)
            step = np.abs(y[j].astype(np.int64) - y[j - 1]).max()
            local = max(np.abs(np.diff(y[j - 480:j], axis=0)).max(), np.abs(np.diff(y[j:j + 480], axis=0)).max())
            lvl = 20 * np.log10(np.abs(y[j - 480:j + 480]).max() / 2 ** 23 + 1e-12)
            rep.append(f'{tag} join {PIECES[i - 1][0]}->{PIECES[i][0]} @ {j / 48000:.3f}s: step {step / 2 ** 23:.5f} '
                       f'vs local max {local / 2 ** 23:.5f}, peak +-10 ms {lvl:.0f} dBFS -> {"CLICK?" if step > 2 * local and step > 2 ** 23 * 0.01 else "clean"}')
        write24(f'{OUT}/{tag}_full.wav', y)
    open(f'{OUT}/audio_report.txt', 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


def video():
    meta = json.load(open(f'{HUDDIR}/runs.json'))
    cmd = ['ffmpeg', '-v', 'error', '-y']
    for p in PIECES:
        cmd += ['-i', f'{D}/{p[1]}']
    for r in meta['runs']:
        cmd += ['-i', r['path']]
    cmd += ['-i', f'{OUT}/mix_full.wav']
    n = len(PIECES)
    g = ''.join(f'[{i}:v]scale=1280:720:flags=lanczos,setsar=1,format=yuv420p,settb=1/30000,setpts=PTS-STARTPTS[p{i}];'
                for i in range(n))
    g += ''.join(f'[p{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0[c0]'
    for k, r in enumerate(meta['runs']):
        g += (f";[{n + k}:v]format=rgba,settb=1/30000,setpts=PTS-STARTPTS+{r['f0'] * 1001}/30000/TB[h{k}]"
              f";[c{k}][h{k}]overlay={meta['x']}:{meta['y']}:eof_action=pass:format=auto[c{k + 1}]")
    g += f";[c{len(meta['runs'])}]format=yuv420p[v]"
    a = n + len(meta['runs'])
    cmd += ['-filter_complex', g, '-map', '[v]', '-map', f'{a}:a', '-frames:v', str(TOTAL),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            '-r', '30000/1001', '-video_track_timescale', '30000',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', NAME + '.mp4']
    sh(cmd)
    sh(['ffmpeg', '-v', 'error', '-y', '-i', NAME + '.mp4', '-i', f'{OUT}/nomusic_full.wav', '-map', '0:v', '-map', '1:a',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', NAME + '_NOMUSIC.mp4'])
    print('done', NAME + '.mp4')


def loud(paths=None):
    for f in paths or [NAME + '.mp4', NAME + '_NOMUSIC.mp4']:
        r = subprocess.run(['ffmpeg', '-nostats', '-i', f, '-map', '0:a', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                           capture_output=True, text=True).stderr
        tail = r[r.rfind('Summary:'):]
        I = [l.strip() for l in tail.splitlines() if l.strip().startswith(('I:', 'Peak:'))]
        print(os.path.basename(f), ' | '.join(I))


def send():
    # two parts split at the Ch3/Ch4 join (5:02), 960x540, 2-pass to about 27.5 MiB each
    cut = F0[4]
    for k, (a, b) in enumerate([(0, cut), (cut, TOTAL)]):
        dur = (b - a) * 1001 / 30000
        kbps = int(27.5 * 8 * 1024 * 1024 / dur / 1000) - 128
        out = f'{NAME}_send_part{k + 1}.mp4'
        base = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{a * 1001 / 30000:.6f}', '-i', NAME + '.mp4', '-frames:v', str(b - a),
                '-t', f'{dur:.6f}', '-vf', 'scale=960:540:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow',
                '-b:v', f'{kbps}k', '-maxrate', f'{int(kbps * 1.6)}k', '-bufsize', f'{kbps * 3}k', '-profile:v', 'high',
                '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                '-passlogfile', f'{OUT}/x264pass{k}']
        sh(base + ['-pass', '1', '-an', '-f', 'null', '-'])
        sh(base + ['-pass', '2', '-an', out + '.v.mp4'])
        # audio from the full-mix wav (one AAC generation), 0.4 dB down so the 128k AAC keeps true peak under -1.5 dBTP
        sh(['ffmpeg', '-v', 'error', '-y', '-i', out + '.v.mp4', '-ss', f'{a * 1001 / 30000:.6f}', '-t', f'{dur:.6f}',
            '-i', f'{OUT}/mix_full.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', 'volume=-0.4dB',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out])
        os.remove(out + '.v.mp4')
        print(out, os.path.getsize(out), kbps)


def chapters():
    lines = []
    for i, p in enumerate(PIECES):
        s = round(F0[i] * 1001 / 30000, 3)
        lines.append(f'{int(s // 60)}:{int(s % 60):02d} {p[5]}')
    open(f'{OUT}/chapters.txt', 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def tile(frames, path, label):
    """frames: list of (global frame, text); 640 px tiles, 4 across, stamped."""
    from PIL import Image, ImageDraw, ImageFont
    import io, math
    ft = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    tiles = []
    for f, txt in frames:
        pre = min(f, 30)   # accurate input seek to 30 frames before, then pick the frame by count
        b = sh(['ffmpeg', '-v', 'error', '-ss', f'{(f - pre) * 1001 / 30000:.6f}', '-i', NAME + '.mp4',
                '-vf', f'select=eq(n\\,{pre}),scale=640:-2', '-frames:v', '1',
                '-f', 'image2pipe', '-c:v', 'png', '-'], text=False).stdout
        im = Image.open(io.BytesIO(b)).convert('RGB'); d = ImageDraw.Draw(im)
        t = f * 1001 / 30000
        d.rectangle([0, 0, 640, 24], fill=(0, 0, 0)); d.text((5, 2), f'{int(t // 60)}:{t % 60:05.2f} f{f} {txt}', font=ft, fill=(255, 255, 255))
        tiles.append(im)
    for k in range(0, len(tiles), 12):
        ch = tiles[k:k + 12]
        sheet = Image.new('RGB', (640 * 4, 360 * math.ceil(len(ch) / 4)))
        for j, im in enumerate(ch):
            sheet.paste(im, ((j % 4) * 640, (j // 4) * 360))
        sheet.save(f'{path}_{k // 12 + 1}.jpg', quality=85)


def gate():
    os.makedirs(f'{OUT}/gate', exist_ok=True)
    plan = json.load(open(f'{HERE}/hud.json'))
    fr = []
    for i, r in enumerate(plan['runs']):
        fr += [(r['f0'] + 12, f'run{i} {r["piece"]} start'), ((r['f0'] + r['f1']) // 2, f'run{i} {r["piece"]} mid')]
    tile(fr, f'{OUT}/gate/hud_runs', 'hud')
    fr = []
    for i in range(1, len(PIECES)):
        fr += [(F0[i] - 1, f'{PIECES[i - 1][0]} last'), (F0[i], f'{PIECES[i][0]} first')]
    tile(fr, f'{OUT}/gate/joins', 'joins')


if __name__ == '__main__':
    dict(audio=audio, video=video, loud=loud, send=send, chapters=chapters, gate=gate)[sys.argv[1]]()
