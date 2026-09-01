# Services & Partners — exact wording

Use this wording verbatim so it stays consistent across video, captions, and
site copy.

## Services

Formula Dynamics offers **upgrades and service**. Both are core to the business.

### Upgrades

| Service | On-screen | Descriptor |
|---|---|---|
| Body kits | BODY KITS | Aero, carbon fibre, widebody, full conversions. |
| Exhaust | EXHAUST | Valvetronic, catback, downpipes, titanium systems. |
| Wheels | WHEELS | Forged, monoblock and multi-piece fitment. |
| Tuning | TUNING | ECU / TCU calibration, custom maps, dyno-verified gains. |
| Suspension | SUSPENSION | Coilovers, lowering springs, air, lift kits. |
| PPF | PPF | Paint protection film. Full front, track pack, full body. |
| Ceramic coating | CERAMIC COATING | Multi-year paint, wheel and glass protection. |
| Paint correction | PAINT CORRECTION | Multi-stage machine polish and gloss restoration. |
| Detailing | DETAILING | Interior and exterior maintenance detailing. |

**"PPF"** — spell it out on first use in a caption: *paint protection film
(PPF)*. On screen, the abbreviation alone is fine.

### Service

| Service | On-screen | Descriptor |
|---|---|---|
| Service | SERVICE | Scheduled maintenance, fluids, brakes, diagnostics. |

Don't let service disappear behind the upgrade content. It's what turns a
one-time customer into a long-term one, and it's a differentiator against shops
that only bolt on parts.

### Current video focus

Body kits · exhaust · wheels · tuning.
Ready-made strip: `../03-overlays/service-badges/badge-strip_lead-services_dark.png`

---

## Select partners

| Partner | Category | Lower third |
|---|---|---|
| **NV Forged** | Forged wheels | `lt_9x16_partner_nv-forged.png` |
| **IPE** | Titanium / valvetronic exhaust | `lt_9x16_partner_ipe.png` |
| **RIFT** | Exhaust, blow-off valves, performance hardware | `lt_9x16_partner_rift.png` |
| **Luring** | Lowering springs / suspension | `lt_9x16_partner_luring.png` |

### Before publishing partner content — check these

The kit sets partner names as **text only**. Two things to confirm:

1. **Exact legal styling** of each name (capitalisation, spacing, "Inc."/"Ltd").
   "IPE" is also written "iPE Exhaust" by the manufacturer — confirm which they
   prefer.
2. **"Luring"** — supplied as *luring springs*. Confirm the correct spelling and
   whether this is the springs brand or a separate exhaust/BOV line.

To change any of these, edit `PARTNERS` in `99-toolkit/fd_brand.py` and re-run
`build_all.py`. Every partner lower third regenerates.

### Partner logos

Partner logos are **their** intellectual property and are deliberately not
generated here. Request official assets from each partner, then drop them into
`../03-overlays/partner-logos/`.

Most brands publish a media/press kit. Using an official file also avoids the
low-resolution, screenshot-off-a-website look.

Check each partner's brand guidelines before putting their mark next to yours —
some require minimum clear space or prohibit co-locking entirely.
