#!/usr/bin/env python3
"""Make a new FD carousel campaign folder from the kit.

  python3 formula-dynamics/17-carousel-kit/new_campaign.py formula-dynamics/31-spring-sale \\
      --code FD-SPRING-30 --title "Spring service sale" --start 2027-03-01 --end 2027-03-06

Copies template/ and the kit's tools/ into the new folder, writes campaign.json (five daily posts at 9, 11, 1, 4 and
7 Pacific unless --slots says otherwise) and fills the brief's header. Refuses to touch a folder that already exists.
Standard library only, so the system Python runs it. Everything after this needs uv (see the README)."""
import argparse, datetime, json, pathlib, shutil, sys

KIT = pathlib.Path(__file__).resolve().parent
DEFAULT_SLOTS = [
    {"id": "1_products", "role": "Product spotlight", "time": "9 AM"},
    {"id": "2_sale", "role": "Sale guide", "time": "11 AM"},
    {"id": "3_cars", "role": "Car with product", "time": "1 PM"},
    {"id": "4_education", "role": "Education", "time": "4 PM"},
    {"id": "5_reminder", "role": "Sale reminder", "time": "7 PM"},
]
NEVER = ["horsepower", "hp", "whp", "bhp", "torque", "faster"]


def parse_slots(spec):
    """--slots "1_products=Product spotlight@9 AM,2_sale=Sale guide@11 AM" """
    out = []
    for part in filter(None, (x.strip() for x in spec.split(","))):
        sid, rest = part.split("=", 1)
        role, time = (rest.split("@", 1) + [""])[:2]
        out.append({"id": sid.strip(), "role": role.strip(), "time": time.strip()})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest", help="new campaign folder, e.g. formula-dynamics/31-spring-sale")
    ap.add_argument("--code", required=True, help="short campaign code, e.g. FD-SPRING-30 (used in file names)")
    ap.add_argument("--title", required=True, help="campaign title, e.g. 'Spring service sale'")
    ap.add_argument("--start", required=True, help="first post date, YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="last post date, YYYY-MM-DD")
    ap.add_argument("--slides", type=int, default=3, help="slides per carousel (default 3)")
    ap.add_argument("--slots", default="", help="posts per day as id=role@time, comma separated (default: the five FD slots)")
    ap.add_argument("--never", default="", help="extra words the checker must block, comma separated (a sale code, say)")
    ap.add_argument("--delivery", default="", help="delivery folder; one * allowed for the account part of a Drive path")
    a = ap.parse_args()

    dest = pathlib.Path(a.dest).resolve()
    if dest.exists():
        sys.exit(f"{dest} already exists. Pick a new folder; the kit never writes over a campaign.")
    s, e = datetime.date.fromisoformat(a.start), datetime.date.fromisoformat(a.end)
    if e < s:
        sys.exit("--end is before --start")
    slots = parse_slots(a.slots) if a.slots else DEFAULT_SLOTS
    days = (e - s).days + 1
    first = s.strftime("%b %-d")
    last = e.strftime("%b %-d") if (s.year, s.month) != (e.year, e.month) else e.strftime("%-d")
    span = first if s == e else f"{first} to {last}"     # a one-day run reads "Dec 10", not "Dec 10 to 10"

    shutil.copytree(KIT / "template", dest, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    shutil.copytree(KIT / "tools", dest / "tools", ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))

    c = {
        "code": a.code, "title": a.title, "start": a.start, "end": a.end, "slides": a.slides,
        "slots": slots,
        "plan": {(s + datetime.timedelta(days=i)).isoformat(): ["" for _ in slots] for i in range(days)},
        "notes": {},
        "never_print": NEVER + [w.strip() for w in a.never.split(",") if w.strip()],
        "delivery_dir": a.delivery,
        "drive_link": "",
        "store_json": "ref/store/*.json",
        "date_label": span,
        "price_note": "Every price matches the formuladynamics.com listing on the day it was built.",
        "open_notes": [],
        "page": {
            "title": f"FD {a.title} carousels",
            "h1": f"{a.title} on the feed: {{carousels}}, {span}",
            "lede": "{carousels} over {days}. Every price on a slide matches the saved formuladynamics.com listing "
                    "named in the ledger.",
            "hot_figure": ["", ""],
            "warning": "",
        },
    }
    (dest / "campaign.json").write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")

    table = ["| slot folder | role | posted (Pacific) |", "|---|---|---|"]
    table += [f"| `{x['id']}` | {x['role']} | {x['time']} |" for x in slots]
    b = (dest / "BRIEF.md").read_text()
    for k, v in {"{{CODE}}": a.code, "{{TITLE}}": a.title, "{{START}}": a.start, "{{END}}": a.end,
                 "{{COUNT}}": str(days * len(slots)), "{{SLIDES}}": str(a.slides),
                 "{{SLOT_TABLE}}": "\n".join(table)}.items():
        b = b.replace(k, v)
    (dest / "BRIEF.md").write_text(b)

    print(f"Made {dest}")
    print(f"  {days} days x {len(slots)} posts = {days * len(slots)} carousels, {a.slides} slides each")
    print("  Next: fill the [[...]] parts of BRIEF.md and the plan in campaign.json, save the store listings in")
    print("  ref/store/, then follow 'Running it' in 17-carousel-kit/README.md.")


if __name__ == "__main__":
    main()
