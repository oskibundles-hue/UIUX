"""Filmstrip thumbnails for the editor timelines (shots 13 and 19), cut from the ad's own plates.

For each plate: public/thumbs/sNN_strip.jpg (6 frames across the clip, 9:16, side by side),
public/thumbs/sNN.jpg (one 360 x 640 frame from the middle, for the program monitor) and
public/thumbs/clips.json (each plate's duration, for clip widths).

  python3 tools/filmstrips.py        (needs ffmpeg and ffprobe on PATH)
"""
import json, os, subprocess

PLATES = ['s02', 's03', 's04', 's05', 's12', 's15', 's20', 's22', 's27', 's28', 's32', 's33', 's34']
N, TW, TH = 6, 108, 192

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, '..', 'public', 'plates')
out = os.path.join(here, '..', 'public', 'thumbs')
os.makedirs(out, exist_ok=True)

durs = {}
for p in PLATES:
    f = os.path.join(src, p + '.mp4')
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                             capture_output=True, text=True).stdout)
    durs[p] = round(d, 3)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-vf', f'fps={N / d:.5f},scale={TW}:{TH},tile={N}x1',
                    '-frames:v', '1', '-q:v', '4', os.path.join(out, p + '_strip.jpg')], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{d / 2:.3f}', '-i', f, '-frames:v', '1', '-vf', 'scale=360:640',
                    '-q:v', '3', os.path.join(out, p + '.jpg')], check=True)
json.dump(durs, open(os.path.join(out, 'clips.json'), 'w'), indent=1)
print(len(durs), 'plates ->', os.path.relpath(out))
