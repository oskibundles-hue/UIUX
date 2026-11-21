#!/usr/bin/env python3
"""Merge ledger/rows/*.csv into one ledger and write PROGRESS.md: progress.py [--to DIR]
The merged ledger "<code> source and fitment ledger.csv" goes to ledger/ here and to <delivery>/ledger/.
PROGRESS.md (in the delivery folder) lists every planned post, ticked when its export exists."""
import sys, csv, argparse, datetime, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C

ap = argparse.ArgumentParser(); ap.add_argument("--to"); a = ap.parse_args()
c = C.load(); DEL = C.delivery_dir(c, a.to)
rows = []
for fp in sorted((C.HERE / "ledger" / "rows").glob("*.csv")):
    with open(fp, newline="") as f:
        rows += list(csv.DictReader(f))
rows.sort(key=lambda r: (r["date"], r["slot"]))
fields = list(dict.fromkeys(C.LEDGER_FIELDS + [k for r in rows for k in r]))
for dest in (C.HERE / "ledger" / C.ledger_name(c), DEL / "ledger" / C.ledger_name(c)):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def days():
    d, end = datetime.date.fromisoformat(c["start"]), datetime.date.fromisoformat(c["end"])
    while d <= end:
        yield d.isoformat(); d += datetime.timedelta(days=1)

byk = {(r["date"], r["slot"]): r for r in rows}
plan = [(d, s) for d in days() for s in c["slots"]
        if not c["plan"] or (d in c["plan"] and c["plan"][d][c["slots"].index(s)] != "-")]
done = [(d, s) for d, s in plan if (DEL / "exports" / d / s["id"] / "01.jpg").exists()]
slides = sum(len(list((DEL / "exports" / d / s["id"]).glob("[0-9][0-9].jpg"))) for d, s in done)
n, N = len(done), len(plan)
L = [f"# {c['code']} progress", "",
     f"Updated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} (Pacific). **{n} of {N} carousels done, {slides} slides exported.** {N - n} to go.", "",
     "Exports are in `exports/<date>/<slot>/01.jpg ... + Caption.txt`. Planned topics come from campaign.json; a done row names the angle built.", "",
     "| | Date | Post | Planned topic | Built angle |", "|---|---|---|---|---|"]
for d, s in plan:
    i = c["slots"].index(s)
    topic = c["plan"].get(d, [""] * len(c["slots"]))[i] if c["plan"] else ""
    r = byk.get((d, s["id"]), {})
    ok = (d, s) in done
    L.append(f"| {'✅' if ok else '☐'} | {d} | {s['role']} · {s.get('time', '')} | {topic} | {r.get('concept', '') if ok else ''} |")
if c.get("open_notes"):
    L += ["", "## Open notes", ""] + [f"- {x}" for x in c["open_notes"]]
(DEL / "PROGRESS.md").parent.mkdir(parents=True, exist_ok=True)
(DEL / "PROGRESS.md").write_text("\n".join(L) + "\n")
print(f"{n}/{N} carousels, {slides} slides; ledger {len(rows)} rows")
