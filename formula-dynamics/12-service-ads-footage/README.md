# Service ads cut from real footage

The R1–R8 reels in `11-service-reels/` are pure motion graphics — they were
built because there was no service footage to cut against. These are the other
thing: **the shop's own video with the graphic system burned onto it.** Same
brand kit, same overlay set, real cars.

Use these for the specials. A motion-graphic reel explains an offer; footage of
the actual car on the actual lift proves the shop can do the work.

---

## How one gets made

Three steps, and only the first needs judgement.

**1. Pick the shots and cut a montage.** `build_edit.py` takes one source clip,
so a multi-shot ad is assembled first with ffmpeg. Segments are listed in a
plain text file — source, start, duration — and cut to 1080×1920 / 30 fps:

```bash
while read src st du; do
  ffmpeg -nostdin -y -ss $st -i $src.mp4 -t $du \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
    -c:v libx264 -crf 18 -c:a aac seg$i.mp4
done < segs.txt
```

`-nostdin` matters: without it ffmpeg swallows the loop's input and the rest of
the shot list silently disappears.

**2. Burn the overlays on.**

```bash
python3 ../99-toolkit/build_edit.py montage.mp4 -t service \
  --title-text 'ANNUAL SERVICE|$3,999' --title-scrim \
  --title-block 'ANNUAL SERVICE PACKAGE|$3,999 PER YEAR' \
  --ticker 'OIL INCLUDED|PADS NOT INCLUDED|10% OFF UPGRADES' \
  --spec '2 OIL SERVICES' --spec '1 BRAKE SERVICE' \
  --spec '2 DIAGNOSTICS' --spec 'ANY SUSPENSION' \
  --none badge -o out.mp4
```

**3. Run it again with `--motion`** for the sound-designed version. That is a
separate deliverable, not a replacement — the plain cut still ships.

Always `--dry-run` first. It prints the cue sheet without rendering, and the
cue sheet is where the problems are visible.

---

## What the first one taught us

**Chips need room to be read.** The spec window is a fixed slice of the clip,
so six chips landed at 0.42 s each — unreadable. Four is the working maximum on
a 19-second cut, and even then they are glanceable, not readable.

**Put the fine print in the ticker, not a chip.** "Oil included / pads not
included" has to be legible or it is not a disclosure. In a chip it gets 0.7 s;
in the ticker it holds for eight seconds. The ticker is where conditions belong.

**Drop the badge when specs are running.** The service badge and the spec chips
occupy the same band, and the first render stacked "1 BRAKE SERVICE" on top of
"SERVICE" — both illegible. `--none badge` fixes it, and the badge was
redundant against the title block anyway.

**Check the CTA name.** `--cta` takes the slug only — `we-service-what-we-build`
— because the group comes from the template. Passing `trust_we-service-what-we-build`
silently drops the CTA and produces an ad with no ask. Nothing errors; the layer
just is not in the cue sheet. Read the dry run.

---

## Built

### Annual Service Package — $3,999

`FD-Annual-Service-3999.mp4` · 19.0 s · 1080×1920

Cut from the Aston Martin brake job and the black car on the lift. Four shots:

| | Shot | From |
|---|---|---|
| 1 | Hero car, lit tail bar, in the shop | lift @ 2.0 s |
| 2 | Rotor exposed, gloved hands on the caliper | brakes @ 9.0 s |
| 3 | Wide shop, tech working, car on the lift | brakes @ 29.5 s |
| 4 | Back to the hero car — CTA and end card land here | lift @ 41.0 s |

It opens on the car rather than on the work, because the buyer for a $3,999
annual package owns a car like that one. The work is the proof in the middle,
and it returns to the car for the ask.

---

## Which footage suits which special

The tooling is not the constraint any more — footage is.

| Special | Footage that would cut it | Have it? |
|---|---|---|
| Annual service $3,999 | Lift, brake job, shop wide | **Yes — built** |
| Free tune with a RYFT or Opus exhaust | Exhaust work, car on dyno, RYFT product | Partly — "teal brakes and ryft wheels" is RYFT-branded but is wheels, not exhaust |
| Windshield PPF 899 + free headlights | Film going onto glass, squeegee, headlight | **No** |
| Full car PPF + ceramic coating | Roma PPF footage — the shop's own note says "Using Roma Video, PPF focused video" | Roma source exists on the ad branch |

The exhaust special is the one that wants the partner URL graphic from
`11-service-reels/partner.js` — `ryft.co` typed on while a RYFT part is on
screen. It needs exhaust footage first; a URL bar over a wheel shot is a claim
about the wrong product.
