#!/usr/bin/env python3
"""doctor.py: is this machine ready to make SE vlogs? Checks the tools, then runs the pipeline end to end on a
generated test clip, and (with --write-env) saves this machine's settings to vlog.env.

  python3 doctor.py               checks + end-to-end test (about 1-2 min)
  python3 doctor.py --quick       checks only
  python3 doctor.py --write-env   also write vlog.env (setup-mac.sh does this)

The end-to-end test makes an 8 s camera-like clip (HEVC 10-bit with the moov at the end, like the DJI files) in a
temporary "Dropbox" folder, then runs vlog.py links -> ingest --local -> plan -> fetch --local on it. On a Mac it
also checks that VideoToolbox decodes HEVC to exactly the same pixels as the CPU decoder, and only then turns it on
(VLOG_HWACCEL) for fetch.
"""
import argparse
import glob
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, 'engine')
BUILD = os.path.join(HERE, '2026-09-15-rally-v2')
IS_MAC = platform.system() == 'Darwin'
RESULTS = []          # (ok: True/False/None, what, detail)
ENV = {}


def rec(ok, what, detail=''):
    RESULTS.append((ok, what, detail))
    mark = {True: 'ok  ', False: 'FAIL', None: 'note'}[ok]
    print(f'  {mark}  {what}' + (f'  ({detail})' if detail else ''), flush=True)
    return ok


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ------------------------------------------------------------------------------------------------ machine
def check_machine():
    print('machine')
    cores = os.cpu_count() or 1
    mem = None
    try:
        if IS_MAC:
            mem = int(run(['sysctl', '-n', 'hw.memsize']).stdout.strip()) / 2 ** 30
        else:
            for line in open('/proc/meminfo'):
                if line.startswith('MemTotal'):
                    mem = int(line.split()[1]) / 2 ** 20
    except Exception:
        pass
    chip = platform.machine()
    if IS_MAC:
        brand = run(['sysctl', '-n', 'machdep.cpu.brand_string']).stdout.strip()
        chip = brand or chip
    rec(True, f'{platform.system()} {platform.release()}, {chip}', f'{cores} cores' + (f', {mem:.0f} GB RAM' if mem else ''))
    ENV['NPROC'] = str(min(cores, 8))
    free = shutil.disk_usage(HERE).free / 1e9
    rec(True if free >= 40 else (None if free >= 12 else False), f'{free:.0f} GB free disk',
        'a day needs about 1 GB for the survey and up to ~12 GB while cutting mezzanines' if free >= 12
        else 'free at least 12 GB before a vlog')


# ------------------------------------------------------------------------------------------------ ffmpeg
def find_ffmpeg():
    cands = [os.environ.get('FFMPEG'), '/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg', shutil.which('ffmpeg')]
    for c in cands:
        if c and os.path.exists(c):
            return c
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def check_ffmpeg():
    print('ffmpeg')
    ff = find_ffmpeg()
    if not ff:
        rec(False, 'ffmpeg not found', 'brew install ffmpeg')
        return None
    ver = run([ff, '-hide_banner', '-version']).stdout.splitlines()[0]
    rec(True, ver[:60], ff)
    ENV['FFMPEG'] = ff
    enc = run([ff, '-hide_banner', '-encoders']).stdout
    dec = run([ff, '-hide_banner', '-decoders']).stdout
    fil = run([ff, '-hide_banner', '-filters']).stdout
    x264 = run([ff, '-hide_banner', '-h', 'encoder=libx264']).stdout
    rec(' libx264 ' in enc and 'yuv420p10le' in x264, 'libx264 with 10-bit', 'mezzanines are x264 High10')
    rec(' aac ' in enc, 'AAC encoder')
    rec(' hevc ' in dec and ' h264 ' in dec, 'HEVC and H.264 decoders')
    need = ['zscale', 'tonemap', 'lut3d', 'vignette', 'overlay', 'afftdn', 'loudnorm', 'ebur128', 'scale']
    missing = [f for f in need if f' {f} ' not in fil]
    rec(not missing, 'filters: ' + ', '.join(need), ('missing: ' + ', '.join(missing)) if missing else '')
    if IS_MAC:
        hw = run([ff, '-hide_banner', '-hwaccels']).stdout
        rec(None if 'videotoolbox' in hw else False, 'VideoToolbox hardware decode available' if 'videotoolbox' in hw
            else 'no VideoToolbox in this ffmpeg')
    return ff


# ------------------------------------------------------------------------------------------------ python
def check_python():
    print('python')
    rec(sys.version_info >= (3, 10), f'Python {platform.python_version()}', sys.executable)
    ENV['VLOG_PY'] = sys.executable
    ok = True
    for mod, pkg in [('numpy', 'numpy'), ('PIL', 'Pillow'), ('av', 'av'), ('faster_whisper', 'faster-whisper'),
                     ('onnxruntime', 'onnxruntime'), ('huggingface_hub', 'huggingface_hub')]:
        try:
            m = __import__(mod)
            rec(True, f'{pkg} {getattr(m, "__version__", "")}')
        except Exception as e:
            ok = rec(False, f'{pkg} missing', f'{type(e).__name__}; run setup-mac.sh') and ok
    return ok


# ------------------------------------------------------------------------------------------------ chromium
def check_chromium():
    print('motion-graphics layer (node + Playwright + Chromium)')
    node = shutil.which('node') or '/opt/node22/bin/node'
    if not os.path.exists(node):
        return rec(False, 'node not found', 'brew install node')
    rec(True, 'node ' + run([node, '--version']).stdout.strip())
    local = os.path.join(HERE, '.node', 'node_modules', 'playwright')
    if os.path.isdir(local):
        ENV['PLAYWRIGHT_MODULE'] = local
    env = dict(os.environ, **({'PLAYWRIGHT_MODULE': local} if os.path.isdir(local) else {}))
    js = ("const {chromium}=require(%s);(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:64,height:64}});"
          "await p.setContent('<body style=\"margin:0;background:#FBD101\"></body>');const s=await p.screenshot();"
          "console.log(s.length);await b.close();})().catch(e=>{console.error(e.message);process.exit(1)});"
          % json.dumps(os.path.join(BUILD, 'lib', 'playwright.js')))
    t = time.time()
    r = run([node, '-e', js], env=env, timeout=120)
    fonts = sorted(os.path.basename(f) for f in glob.glob(os.path.join(HERE, '..', '07-fonts', '*.ttf')))
    rec(r.returncode == 0, 'Chromium renders a frame', f'{time.time() - t:.1f}s' if r.returncode == 0 else r.stderr.strip()[-160:])
    rec(bool(fonts), 'brand fonts in 07-fonts', ', '.join(fonts[:4]))
    return r.returncode == 0


# ------------------------------------------------------------------------------------------------ end to end
def make_clip(ff, path, secs=8, w=1920, h=1080, hevc=True):
    v = (['-c:v', 'libx265', '-pix_fmt', 'yuv420p10le', '-preset', 'ultrafast', '-x265-params', 'keyint=60:log-level=error',
          '-tag:v', 'hvc1'] if hevc else ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'ultrafast', '-g', '60'])
    r = run([ff, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc2=size={w}x{h}:rate=60000/1001:duration={secs}',
             '-f', 'lavfi', '-i', f'sine=frequency=440:sample_rate=48000:duration={secs}'] + v +
            ['-c:a', 'aac', '-b:a', '128k', '-shortest', path])
    return r.returncode == 0


def framemd5(ff, path, hw=None, frames=30):
    cmd = [ff, '-hide_banner', '-loglevel', 'error'] + (['-hwaccel', hw] if hw else []) + \
          ['-i', path, '-frames:v', str(frames), '-vf', 'format=yuv420p10le', '-f', 'framemd5', '-']
    r = run(cmd)
    return [l.split(',')[-1].strip() for l in r.stdout.splitlines() if l and not l.startswith('#')] if r.returncode == 0 else None


def decode_fps(ff, path, hw=None):
    t = time.time()
    r = run([ff, '-hide_banner', '-loglevel', 'error'] + (['-hwaccel', hw] if hw else []) + ['-threads', '1', '-i', path, '-f', 'null', '-'])
    return None if r.returncode else time.time() - t


def end_to_end(ff):
    print('end-to-end test (generated camera clip, local mode)')
    tmp = tempfile.mkdtemp(prefix='vlog-doctor-')
    try:
        fx = run([ff, '-hide_banner', '-encoders']).stdout
        hevc = ' libx265 ' in fx
        folder = os.path.join(tmp, 'Dropbox', 'NQ Studio', 'raw footage', '2099-01-01')
        os.makedirs(folder)
        clip = os.path.join(folder, 'DJI_20990101120000_0001_D.MP4')
        if not make_clip(ff, clip, hevc=hevc):
            return rec(False, 'could not make the test clip')
        rec(True, f'test clip: 8 s 1080p {"HEVC 10-bit" if hevc else "H.264"}, moov at the end', f'{os.path.getsize(clip) / 1e6:.0f} MB')
        day = os.path.join(tmp, 'day')
        env = dict(os.environ, FFMPEG=ff, VLOG_FFMPEG=ff)
        vlog = [sys.executable, os.path.join(ENGINE, 'vlog.py')]
        t = time.time()
        r = run(vlog + ['links', day, '--local', folder], env=env)
        r2 = run(vlog + ['ingest', day, '--local'], env=env, timeout=900)
        st = run(vlog + ['status', day], env=env).stdout
        ok = r.returncode == 0 and r2.returncode == 0 and 'surveyed' in st and ' tr' in st
        rec(ok, 'ingest --local: survey + transcript', f'{time.time() - t:.0f}s' if ok else (r2.stdout + r2.stderr)[-300:])
        if not ok:
            return False
        edl = os.path.join(tmp, 'edl.json')
        json.dump({'shots': [{'src': '0001', 'in': 2.0, 'out': 4.0, 'speed': 1.0}], 'dialog': [], 'audio_extra': []}, open(edl, 'w'))
        mezz = os.path.join(tmp, 'mezz')
        t = time.time()
        r = run(vlog + ['plan', day, '--edl', edl], env=env)
        r2 = run(vlog + ['fetch', day, '--out', mezz, '--local'], env=env, timeout=900)
        outs = glob.glob(os.path.join(mezz, '*.mov'))
        ok = r.returncode == 0 and r2.returncode == 0 and len(outs) == 1
        rec(ok, 'plan + fetch --local: mezzanine cut', f'{time.time() - t:.0f}s' if ok else (r2.stdout + r2.stderr)[-300:])
        if IS_MAC and hevc and 'videotoolbox' in run([ff, '-hide_banner', '-hwaccels']).stdout:
            sw, hw = framemd5(ff, clip), framemd5(ff, clip, 'videotoolbox')
            same = bool(sw) and sw == hw
            rec(same if hw else None, 'VideoToolbox decode = CPU decode, frame for frame' if same else
                'VideoToolbox decode differs from CPU decode: left off', f'{len(sw or [])} frames compared')
            if same:
                ENV['VLOG_HWACCEL'] = 'videotoolbox'
                big = os.path.join(tmp, 'uhd.mp4')
                if make_clip(ff, big, secs=3, w=3840, h=2160, hevc=True):
                    a, b = decode_fps(ff, big), decode_fps(ff, big, 'videotoolbox')
                    if a and b:
                        n = 3 * 60000 / 1001
                        rec(None, f'4K HEVC 10-bit decode: CPU (1 thread) {n / a:.0f} fps, VideoToolbox {n / b:.0f} fps')
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def write_env():
    roots = []
    home = os.path.expanduser('~')
    roots += sorted(glob.glob(os.path.join(home, 'Library', 'CloudStorage', 'Dropbox*')))
    roots += [p for p in [os.path.join(home, 'Dropbox')] if os.path.isdir(p)]
    lines = ['# vlog.env: this machine\'s settings for the SE vlog pipeline (written by doctor.py --write-env; safe to edit).',
             '# ./vlog and the day builds\' render.sh read it.']
    for k in ('VLOG_PY', 'FFMPEG', 'PLAYWRIGHT_MODULE', 'NPROC', 'VLOG_HWACCEL'):
        if ENV.get(k):
            lines.append(f'export {k}={json.dumps(ENV[k])}')
    if ENV.get('FFMPEG'):
        lines.append('export VLOG_FFMPEG="$FFMPEG"')
    if roots:
        lines.append(f'# Dropbox desktop folder(s) found: {", ".join(roots)}')
        lines.append(f'export VLOG_DROPBOX_ROOT={json.dumps(roots[0])}')
    p = os.path.join(HERE, 'vlog.env')
    open(p, 'w').write('\n'.join(lines) + '\n')
    print(f'\nwrote {p}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--quick', action='store_true', help='checks only, no end-to-end test')
    ap.add_argument('--write-env', action='store_true', help='save this machine\'s settings to vlog.env')
    a = ap.parse_args()
    check_machine()
    ff = check_ffmpeg()
    py_ok = check_python()
    check_chromium()
    if ff and py_ok and not a.quick:
        end_to_end(ff)
    fails = [w for ok, w, _ in RESULTS if ok is False]
    if a.write_env:
        write_env()
    print('\n' + ('READY: this machine can run the vlog pipeline.' if not fails else
                  f'NOT READY ({len(fails)}): ' + '; '.join(fails)))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
