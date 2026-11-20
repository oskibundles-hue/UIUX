#!/usr/bin/env python3
"""Writes PROGRESS.md (75-row checklist) from ledger.csv. Run after each carousel: build_meta.py DELIVERY_DIR"""
import csv, sys, pathlib, datetime
CAL = {  # date: (spotlight, sale guide, car, education, reminder) from the Codex proof book
 "2026-11-20":("ECU tuning","Public launch","Ferrari F8","Pedal feel","Bookmark"),
 "2026-11-21":("FD brake lines","Wheel work","Ferrari 812 GTS","Carbon styling","Pad match"),
 "2026-11-22":("Larini exhaust","Exhaust budget","BMW Project M2","Air filter care","Garage handoff"),
 "2026-11-23":("FD wheel spacers","Brake project","Maserati Ghibli","Wheel position","Braided lines"),
 "2026-11-24":("Oil change kit","Service sheet","Maserati MC20","Fitment","Two cars"),
 "2026-11-25":("KW coilovers","Throttle response","Lamborghini Huracan Tecnica","Exhaust valves","Holiday travel"),
 "2026-11-26":("FD brake pads","Thanksgiving","Ferrari SF90","Brake rotors","Used car history"),
 "2026-11-27":("Service kit","Black Friday","Maserati GranTurismo","Suspension language","Friday night"),
 "2026-11-28":("Wheels","Shop small","Ferrari F8","Service scope","Spacer pairing"),
 "2026-11-29":("Drive-by-wire module","Ferrari example","Maserati 4200","Throttle response","Exhaust gift"),
 "2026-11-30":("BMC air filter","Cyber Monday","Ferrari F430","Shop evaluation","Monday receipt"),
 "2026-12-01":("Big brake kit","Suspension","Maserati Ghibli","Wheel clearance","Mixed cart"),
 "2026-12-02":("Cabin air filter","Filter shopping","Ferrari SF90 Stradale","Transmission identification","Carbon question"),
 "2026-12-03":("Muffler valve control kit","Parts quote","Maserati GranTurismo","Brake-kit contents","Open question"),
 "2026-12-04":("Morimoto LED tail lights","Two jobs one car","Ferrari F8","Sale arithmetic","Closing post"),
}
SLOTS = ["1_products","2_sale","3_cars","4_education","5_reminder"]
NAMES = ["Product spotlight","Sale guide","Car with product","Education","Sale reminder"]
out = pathlib.Path(sys.argv[1])
done = {}
with open(out/"ledger"/"FD-BFCM-75 source and fitment ledger.csv") as f:
    for r in csv.DictReader(f): done[(r["date"], r["slot"])] = r
n = len(done)
L = [f"# FD-BFCM-75 progress", "",
     f"Updated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} Pacific. **{n} of 75 carousels done, {3*n} of 225 slides exported.** {75-n} carousels to go.", "",
     "Planned topics are Codex's proof-book calendar; each done row names the angle actually built. Exports are in `exports/<date>/<slot>/01-03.jpg + Caption.txt`.", "",
     "| | Date | Slot | Planned topic | Built angle |", "|---|---|---|---|---|"]
for d, topics in CAL.items():
    for s, nm, t in zip(SLOTS, NAMES, topics):
        r = done.get((d, s))
        L.append(f"| {'✅' if r else '☐'} | {d} | {nm} | {t} | {r['concept'] if r else ''} |")
L += ["", "## Open notes for the lead", "", "- The public sale emails were not found in Gmail, Drive or Dropbox. Discounts follow the Codex source-of-truth notes, and every price on a slide is checked against the live formuladynamics.com listing on the day it is built.", "- The F8 tune saving of $859.80 is Stage 1 (stock exhaust) only; Stage 2 saves $899.80. Codex's day-1 caption did not say which stage.", ""]
L += ["", "## Still to build after the 75", "", "- ☐ Numbered contact sheet", "- ☐ Visual gallery HTML", "- ☐ Boss-review PDF", ""]
(out/"PROGRESS.md").write_text("\n".join(L))
print(f"{n}/75")
