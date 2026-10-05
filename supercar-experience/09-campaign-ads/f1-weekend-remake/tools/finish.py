"""Master the sound and encode the one Instagram-ready file (HOUSE-STYLE.md rule 7 and 8).

Usage:
    python3 tools/finish.py                       # out/SCE_F1-Weekend_Remake_76s-9x16.mp4 -> ..._IG.mp4
    python3 tools/finish.py --name SCE_F1-Weekend_Remake_30s-9x16   # the 30 s cut
    python3 tools/finish.py --audio-only in.wav   # master the sound only and print the numbers

Sound: linked true-peak limiter (detector max(|L|, |R|, 0.707 |L+R|), 4x oversampled) at -2.0 dBTP,
gain iterated to -14.0 LUFS, last 50 ms silent. Same method as flash-special-showcase/audio/bed_music.py.
Picture: H.264 High, two-pass ~11.5 Mb/s, AAC 48 kHz, fast start. Needs numpy and ffmpeg.
"""
import argparse, json, os, re, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SR = 48000
NAME = 'SCE_F1-Weekend_Remake_76s-9x16'


def db(x):
    return 10 ** (x / 20)


def read_audio(path):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0', '-f', 'f32le', '-ac', '2',
                        '-ar', str(SR), '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, '<f4').reshape(-1, 2).astype(np.float64)


def write_wav24(path, x):
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR)
        w.writeframes(i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


def loudness(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af',
                        'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True)
    return json.loads(re.findall(r'\{[^{}]+\}', r.stderr)[-1])


def limit(x, ceiling_db):
    c = db(ceiling_db)
    n, os_ = len(x), 4
    up = np.fft.irfft(np.fft.rfft(x, axis=0), n * os_, axis=0) * os_
    det = np.maximum(np.abs(up).max(1), np.abs(up.sum(1)) * 0.7071)
    need = np.minimum(1, c / np.maximum(det.reshape(n, os_).max(1), 1e-9))
    L = int(round((0.0015 + 0.012) * SR))
    mm = np.lib.stride_tricks.sliding_window_view(np.concatenate([need, np.ones(L)]), L).min(1)[:n]
    g = np.convolve(np.concatenate([np.ones(L - 1), mm]), np.ones(L) / L, mode='valid')
    return x * np.minimum(g, 1)[:, None]


def master(src, dst):
    mix = read_audio(src)
    tail = int(0.05 * SR)
    gain_db = -1.5
    for _ in range(6):
        y = limit(mix * db(gain_db), -2.0)
        y[-tail:] = 0
        write_wav24(dst, y)
        m = loudness(dst)
        err = -14.0 - float(m['input_i'])
        if abs(err) < 0.05:
            break
        gain_db += err
    return dict(gain_db=round(gain_db, 2), I=m['input_i'], TP=m['input_tp'])


def check(path):
    m = loudness(path)
    x = read_audio(path)
    return dict(I=m['input_i'], TP=m['input_tp'], last_50ms_peak=float(np.abs(x[-int(0.05 * SR):]).max()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', default=NAME, help='render name in out/ (without .mp4); writes <name>_IG.mp4')
    ap.add_argument('--src', help='default: out/<name>.mp4')
    ap.add_argument('--audio-only')
    a = ap.parse_args()
    a.src = a.src or os.path.join(ROOT, 'out', a.name + '.mp4')
    out = os.path.join(ROOT, 'out')
    wav = os.path.join(out, '_mastered.wav')
    if a.audio_only:
        print('master', master(a.audio_only, wav))
        return
    print('master', master(a.src, wav))
    dst = os.path.join(out, a.name + '_IG.mp4')
    # the picture sets the length: pad the sound and cut at the video's end (-shortest lost the last frame)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration',
                                '-of', 'csv=p=0', a.src], capture_output=True, text=True, check=True).stdout)
    log = os.path.join(out, '_x264pass')
    v = ['-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-b:v', '11.5M',
         '-maxrate', '15M', '-bufsize', '23M', '-preset', 'slow', '-passlogfile', log]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.src, '-map', '0:v:0', *v, '-pass', '1', '-an',
                    '-f', 'mp4', os.devnull], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.src, '-i', wav, '-map', '0:v:0', '-map', '1:a:0',
                    *v, '-pass', '2', '-c:a', 'aac', '-b:a', '320k', '-ar', str(SR), '-movflags', '+faststart',
                    '-af', 'apad', '-t', f'{dur:.4f}', dst], check=True)
    for f in os.listdir(out):
        if f.startswith('_x264pass'):
            os.remove(os.path.join(out, f))
    print('wrote', dst, f'{os.path.getsize(dst) / 1e6:.1f} MB')
    frames = lambda f: subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
                                       'stream=nb_read_packets', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip()
    print('check', check(dst), 'frames', frames(dst), 'of', frames(a.src))


if __name__ == '__main__':
    main()
