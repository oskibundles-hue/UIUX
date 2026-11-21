"""Shared loader for an FD carousel campaign folder (the folder that holds campaign.json).

Every tool in tools/ imports this, so a campaign is described in one place:
  campaign.json  code, titles, dates, slots (id, role, time), plan, notes, delivery folder, Drive link, rules.
Carousels live in source/<YYYY-MM-DD>/<slot id>/slide-01.html ... slide-NN.html + Caption.txt.
"""
import glob, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent.parent          # the campaign folder
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load():
    f = HERE / "campaign.json"
    if not f.exists():
        sys.exit(f"No campaign.json in {HERE}. Make a campaign with 17-carousel-kit/new_campaign.py, or run the tool "
                 "from inside a campaign's tools/ folder.")
    c = json.loads(f.read_text())
    c.setdefault("slides", 3)
    c.setdefault("notes", {})
    c.setdefault("plan", {})
    c.setdefault("never_print", [])
    c.setdefault("drive_link", "")
    return c


def delivery_dir(c, override=None):
    """Where finished files go (a Drive or Dropbox folder). --to on any tool overrides campaign.json.
    One * is allowed, for the part of the path that names an account, so no address is written into the repo:
    "~/Library/CloudStorage/GoogleDrive-*/My Drive/..." finds the signed-in Drive. The folders after it are made."""
    d = os.path.expanduser(override or c.get("delivery_dir") or str(HERE / "out" / "delivery"))
    if "*" in d:
        parts = pathlib.Path(d).parts
        k = next(i for i, x in enumerate(parts) if "*" in x)
        hits = sorted(glob.glob(str(pathlib.Path(*parts[:k + 1]))))
        if len(hits) != 1:
            sys.exit(f"delivery_dir: {pathlib.Path(*parts[:k + 1])} matches {len(hits)} folders, needs exactly 1: {hits}")
        d = str(pathlib.Path(hits[0], *parts[k + 1:]))
    return pathlib.Path(d)


def slot_ids(c):
    return [s["id"] for s in c["slots"]]


def slides_of(carousel_dir):
    """slide-01.html, slide-02.html ... in order. A carousel may have 1 to 20 slides."""
    return sorted(pathlib.Path(carousel_dir).glob("slide-[0-9][0-9].html"))


def carousels(c, dates=None):
    """Every built carousel folder in source/, in date then slot order."""
    out = []
    ids = slot_ids(c)
    for day in sorted(p for p in (HERE / "source").iterdir() if p.is_dir() and DATE_DIR.match(p.name)):
        if dates and day.name not in dates:
            continue
        for sid in ids:
            p = day / sid
            if p.is_dir() and slides_of(p):
                out.append(p)
    return out


def ledger_name(c):
    return f"{c['code']} source and fitment ledger.csv"


LEDGER_FIELDS = ["date", "slot", "post_type", "concept", "angle", "visual_sequence", "photos", "photo_originals",
                 "vehicle_verified", "parts_or_products_named", "part_verification", "prices_shown", "price_source",
                 "discount_source", "plate_blur", "notes"]


def pl(n, word):
    """pl(1, "carousel") -> "1 carousel", pl(3, "day") -> "3 days"."""
    return f"{n} {word}{'' if n == 1 else 's'}"


def sync_editable(DEL):
    """Copy everything needed to re-render the campaign into <delivery>/editable source/."""
    import subprocess
    dest = pathlib.Path(DEL) / "editable source"
    dest.mkdir(parents=True, exist_ok=True)
    have = [p for p in ("source", "assets", "tools", "ledger", "ref", "campaign.json", "BRIEF.md") if (HERE / p).exists()]
    subprocess.run(["rsync", "-a", "--exclude", ".DS_Store", "--exclude", "__pycache__", "--exclude", ".keep"]
                   + have + [str(dest) + "/"],
                   cwd=HERE, check=True)
