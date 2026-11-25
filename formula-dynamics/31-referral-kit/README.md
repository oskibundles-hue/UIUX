# Formula Dynamics referral kit

Nate (FD) offered Omarie commission on local customers he sends in for service or parts.
This kit makes every referral traceable to Omarie without a booking system.

## How a referral is credited

FD has no booking system. The site's Contact page is its booking form, and it has a free-text
message box. So:

1. Omarie sends or hands over a card (or a script from `SCRIPTS.md`).
2. The QR opens `formuladynamicsperformance.com/contact?ref=omarie`.
3. The customer puts **OMARIE** in the message box, or says it when they call.
4. The shop notes the code on the work order (Nate to confirm, see placeholders).
5. Omarie logs it in the tracker; commission works itself out.

The `?ref=omarie` tag also shows in FD's site analytics if they read them, but the code in
the message is what counts. Nothing depends on the shop changing their site.

## Files (renders/)

| File | What it is |
|---|---|
| `referral-card_9x16.png` | Phone card, 2160x3840. Ready to text now (no offer line). |
| `referral-card_9x16_offer-draft.png` | Same card, showing where an offer line would sit. Not for sending. |
| `referral-card_9x16_animated.mp4` | 7 s animated phone card, 1080x1920, ends on the still. |
| `referral-card_print_3.5x2.png` | Business card, 3.5x2 in at 600 dpi with 1/8 in bleed (2250x1350). |
| `FD-referral-tracker.xlsx` | Tracker: SUMMARY, LOG (200 rows), SETTINGS (placeholders). |
| `animation-contact-sheet.png` | Nine frames of the animation, for review. |

## Placeholders (Nate decides)

All live in one place each, so a sign-off is a one-line change and a re-run:

- Code name `OMARIE`: `CODE` in `build_referral_kit.py` and `build_tracker.py`.
- Offer for the referred customer: `OFFER` in `build_referral_kit.py` (None = no line).
- Commission % on service and on parts, before/after tax, payout timing, how the shop records
  the code: yellow cells on the tracker's SETTINGS tab.

## Rebuild

```bash
uv run --no-project --with pillow --with "qrcode[pil]" python build_referral_kit.py
uv run --no-project --with openpyxl python build_tracker.py
```

## Checked (2026-11-24)

- QR decodes to the contact link on all three stills and the video's last frame, at full
  size and at 35 % (8 of 8), and the link returns 200.
- Tracker formulas tested with sample rows: rates follow Service/Parts, a row with no type
  stays blank, totals and "still owed" are right. Rates ship blank, so no commission shows
  until Nate's numbers go in (tested blank and at 12 %).
- Reviewer pass: print card stripe now runs off the bottom edge (bleed), all print text is
  60 px or more (about 7 pt) and inside the 150 px safe line (measured 150 to 2086 x, 150 to
  1189 y). Phone card, video, copy passed first time.
