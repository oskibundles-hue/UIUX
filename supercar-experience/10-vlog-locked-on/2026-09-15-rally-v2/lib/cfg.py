"""cfg.py: config.json with this machine's paths.

`paths` in config.json are this build's defaults. A git-ignored `config.local.json` next to it can override any of
them per machine (the Mac setup writes one), and `$VARS`, `~` and paths relative to the build folder are expanded.
ffmpeg is taken from $FFMPEG, then the configured path if it exists, then the one on PATH.
`paths.work` (optional) is where the build cache lives; `.work` in the build folder is made a link to it, because
story.html loads its data from `.work/` by relative path. An existing real `.work` folder is left as it is.
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _expand(p):
    p = os.path.expanduser(os.path.expandvars(p))
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(ROOT, p))


def _link_work(work):
    if not work or os.path.normpath(work) == os.path.join(ROOT, '.work'):
        return
    link = os.path.join(ROOT, '.work')
    os.makedirs(work, exist_ok=True)
    if os.path.islink(link) and os.path.realpath(link) != os.path.realpath(work):
        os.remove(link)
    if not os.path.lexists(link):
        os.symlink(work, link)


def load_config():
    c = json.load(open(os.path.join(ROOT, 'config.json')))
    local = os.path.join(ROOT, 'config.local.json')
    if os.path.exists(local):
        c['paths'].update(json.load(open(local)).get('paths', {}))
    for k, v in list(c['paths'].items()):
        if k != 'sfx' and not k.startswith('_'):  # sfx stays relative to ROOT, the way the build joins it
            c['paths'][k] = _expand(v)
    _link_work(c['paths'].get('work'))
    ff = os.environ.get('FFMPEG') or c['paths'].get('ffmpeg')
    if not ff or not os.path.exists(ff):
        ff = shutil.which('ffmpeg') or 'ffmpeg'
    c['paths']['ffmpeg'] = ff
    return c
