#!/usr/bin/env python3
"""cmpmaster.py: compare a new render against an approved one (render-loop verification).

    python3 lib/cmpmaster.py --approved <dir with the approved mp4s + front/ + mix.wav> [--every 10] [--out cmp.json]

  layer    every layer frame (.work/front vs approved/front): identical frames, max difference, PSNR of the layer
  video    master vs approved master, and each against its own lossless source (plate + vignette + its layer, the
           exact compose graph) on every Nth frame: SSIM (all planes) and PSNR (average)
  preview  the same for the 720x1280 previews (source scaled with lanczos)
  audio    mix.wav / mix_nomusic.wav bit-identical?, and the AAC tracks decoded: loudness of both masters
"""
import argparse, hashlib, json, os, re, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from cfg import load_config  # noqa: E402
CFG = load_config()
FF = os.environ.get('FFMPEG', CFG['paths']['ffmpeg'])
WORK = os.path.join(ROOT, '.work')
NAME = CFG['name']
GRAPH = ('[0:v]scale=in_color_matrix=bt709:in_range=tv,format=gbrp,vignette=angle=0.55:mode=forward:eval=init[b];'
         '[1:v]format=rgba[o];[b][o]overlay=format=gbrp:eof_action=pass:shortest=0,'
         'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]')


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def layer_cmp(a_dir, b_dir, n):
    same, worst, diffpx, mse = 0, 0, 0, 0.0
    for i in range(n):
        a = np.asarray(Image.open(os.path.join(a_dir, f'{i:05d}.png')).convert('RGBA'), np.int16)
        b = np.asarray(Image.open(os.path.join(b_dir, f'{i:05d}.png')).convert('RGBA'), np.int16)
        d = np.abs(a - b)
        m = int(d.max())
        if m == 0:
            same += 1
            continue
        worst = max(worst, m)
        diffpx += int((d.max(2) > 0).sum())
        # premultiplied difference (what the composite sees)
        pa = a[..., :3] * (a[..., 3:4] / 255.0); pb = b[..., :3] * (b[..., 3:4] / 255.0)
        mse += float(((pa - pb) ** 2).mean())
    ps = 10 * np.log10(255 ** 2 / (mse / n)) if mse > 0 else float('inf')
    return dict(frames=n, identical=same, differing=n - same, max_abs_diff=worst, differing_pixels_per_differing_frame=round(diffpx / max(1, n - same)),
                premultiplied_psnr_db=round(ps, 2))


def metrics(enc, ref_args, every, nf, scale=None):
    """ssim/psnr of enc against a reference built by ref_args (ffmpeg inputs + graph producing [v]) on every Nth frame."""
    sel = f"select='not(mod(n\\,{every}))',setpts=N/FRAME_RATE/TB"
    sc = f',scale={scale}:flags=lanczos' if scale else ''
    fc = (ref_args['graph'] + f';[v]{sel.replace(chr(39), chr(39))}{sc},split[r1][r2];'
          f'[{ref_args["n_in"]}:v]{sel},split[e1][e2];[e1][r1]ssim;[e2][r2]psnr')
    cmd = [FF, '-hide_banner'] + ref_args['inputs'] + ['-i', enc, '-filter_complex_threads', '4', '-filter_complex', fc, '-f', 'null', '-']
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    s = re.findall(r'All:([0-9.]+)', out); p = re.findall(r'average:([0-9.inf]+)', out)
    return dict(ssim=float(s[-1]) if s else None, psnr=float(p[-1]) if p else None, frames=len(range(0, nf, every)))


def pair_metrics(a, b, every, nf):
    sel = f"select='not(mod(n\\,{every}))',setpts=N/FRAME_RATE/TB"
    fc = f'[0:v]{sel},split[a1][a2];[1:v]{sel},split[b1][b2];[a1][b1]ssim;[a2][b2]psnr'
    out = subprocess.run([FF, '-hide_banner', '-i', a, '-i', b, '-filter_complex_threads', '4', '-filter_complex', fc, '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    s = re.findall(r'All:([0-9.]+)', out); p = re.findall(r'average:([0-9.inf]+)', out)
    return dict(ssim=float(s[-1]) if s else None, psnr=float(p[-1]) if p else None)


def loud(path):
    out = subprocess.run([FF, '-hide_banner', '-i', path, '-map', '0:a', '-af', 'loudnorm=print_format=json', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    j = json.loads(out[out.rindex('{'):out.rindex('}') + 1])
    return dict(I=float(j['input_i']), TP=float(j['input_tp']), LRA=float(j['input_lra']))


def audio_md5(path):
    out = subprocess.run([FF, '-v', 'error', '-i', path, '-map', '0:a', '-c', 'copy', '-f', 'md5', '-'], capture_output=True, text=True).stdout
    return out.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--approved', required=True)
    ap.add_argument('--every', type=int, default=10)
    ap.add_argument('--out', default=os.path.join(WORK, 'cmp_approved.json'))
    ap.add_argument('--skip-layer', action='store_true')
    a = ap.parse_args()
    exp = os.path.join(ROOT, 'exports')
    nf = len([f for f in os.listdir(os.path.join(WORK, 'front')) if re.match(r'\d{5}\.png$', f)])
    res = {}
    if not a.skip_layer:
        res['layer'] = layer_cmp(os.path.join(a.approved, 'front'), os.path.join(WORK, 'front'), nf)
        print('layer', res['layer'], flush=True)
    new_m = os.path.join(exp, f'{NAME} - 1080x1920.mp4'); old_m = os.path.join(a.approved, f'{NAME} - 1080x1920.mp4')
    new_p = os.path.join(exp, f'{NAME} - PREVIEW 720x1280.mp4'); old_p = os.path.join(a.approved, f'{NAME} - PREVIEW 720x1280.mp4')
    src = lambda front: dict(inputs=['-i', os.path.join(WORK, 'plate.mov'), '-framerate', '30000/1001', '-i', os.path.join(front, '%05d.png')],
                             graph=GRAPH, n_in=2)
    res['master_new_vs_approved'] = pair_metrics(new_m, old_m, a.every, nf); print('new vs approved', res['master_new_vs_approved'], flush=True)
    res['master_new_vs_its_source'] = metrics(new_m, src(os.path.join(WORK, 'front')), a.every, nf); print('new vs source', res['master_new_vs_its_source'], flush=True)
    res['master_approved_vs_its_source'] = metrics(old_m, src(os.path.join(a.approved, 'front')), a.every, nf); print('approved vs source', res['master_approved_vs_its_source'], flush=True)
    res['preview_new_vs_its_source'] = metrics(new_p, src(os.path.join(WORK, 'front')), a.every, nf, scale='720:1280')
    res['preview_approved_vs_its_source'] = metrics(old_p, src(os.path.join(a.approved, 'front')), a.every, nf, scale='720:1280')
    print('preview', res['preview_new_vs_its_source'], res['preview_approved_vs_its_source'], flush=True)
    au = {}
    for fn in ('mix.wav', 'mix_nomusic.wav'):
        if os.path.exists(os.path.join(a.approved, fn)):
            au[fn + '_identical'] = md5(os.path.join(WORK, fn)) == md5(os.path.join(a.approved, fn))
    for tag, n_, o_ in (('master', new_m, old_m), ('no_music', os.path.join(exp, f'{NAME} - NO MUSIC - 1080x1920.mp4'), os.path.join(a.approved, f'{NAME} - NO MUSIC - 1080x1920.mp4')),
                        ('preview', new_p, old_p)):
        au[tag] = dict(new=loud(n_), approved=loud(o_), aac_stream_identical=audio_md5(n_) == audio_md5(o_),
                       MiB_new=round(os.path.getsize(n_) / 2 ** 20, 2), MiB_approved=round(os.path.getsize(o_) / 2 ** 20, 2))
    res['audio'] = au
    print('audio', json.dumps(au), flush=True)
    json.dump(res, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
