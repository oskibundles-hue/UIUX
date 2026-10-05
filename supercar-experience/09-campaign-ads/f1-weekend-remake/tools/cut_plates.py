"""Cut every footage plate for the F1 Weekend remake from the raw Dropbox clips.

Usage:
    python3 tools/cut_plates.py --raw /path/to/raw

`--raw` is a folder holding the source clips under the short names in RAW below
(copy them out of Dropbox; never move them). Plates land in public/plates/sNN.mp4,
1080x1920, 30 fps, no audio. Timings come from shots.json.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# short name -> Dropbox path of the original
RAW = {
    'sto.mp4': '/Supercar Experience/01 Car Footage/SCE_Lamborghini-Huracan-STO_green_no-branding.mp4',
    'amg.mov': '/Supercar Experience/01 Car Footage/SCE_Mercedes-AMG-GT-Black-Series_no-branding.mov',
    'mcl750.mov': '/Supercar Experience/01 Car Footage/SCE_McLaren-750S_no-branding.mov',
    'sf90.mov': '/Supercar Experience/01 Car Footage/SCE_Ferrari-SF90_gold_no-branding.mov',
    'urus.mp4': '/Supercar Experience/01 Car Footage/SCE_Lamborghini-Urus_purple_scottsdale_no-branding.mp4',
    'gt3_white.mov': '/Supercar Experience/01 Car Footage/SCE_Porsche-911-GT3RS_white_no-branding.mov',
    'gt3_livery.mov': '/Supercar Experience/01 Car Footage/SCE_Porsche-911-GT3RS_white-red-livery_no-branding.mov',
    'rally1.mov': '/Supercar Experience/02 Rally Footage/SCE_Rally_day-1_las-vegas-to-sedona_4k-vertical.mov',
}

VF = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True)
    ap.add_argument('--only', type=int, nargs='*', help='shot ids to cut (default: all)')
    a = ap.parse_args()
    shots = json.load(open(os.path.join(ROOT, 'shots.json')))
    out = os.path.join(ROOT, 'public', 'plates')
    os.makedirs(out, exist_ok=True)
    missing = sorted({s['src'] for s in shots if s.get('src') and not os.path.exists(os.path.join(a.raw, s['src']))})
    if missing:
        print('Missing raw clips (copy these from Dropbox into --raw):')
        for m in missing:
            print(f'  {m}  <-  {RAW[m]}')
        sys.exit(1)
    for s in shots:
        if not s.get('src') or s['id'] in (29, 30):
            continue
        if a.only and s['id'] not in a.only:
            continue
        speed = s.get('speed', 1)
        dur = s['t1'] - s['t0'] + 0.25  # small tail so the plate never runs out
        in_dur = dur * speed
        vf = (f'setpts=PTS/{speed},' if speed != 1 else '') + VF
        dst = os.path.join(out, f"s{s['id']:02d}.mp4")
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(s['ss']), '-t', f'{in_dur:.3f}', '-i', os.path.join(a.raw, s['src']),
               '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', '-pix_fmt', 'yuv420p', dst]
        subprocess.run(cmd, check=True)
        print('cut', os.path.basename(dst))


if __name__ == '__main__':
    main()
