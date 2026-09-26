# Flash special story, quick cut (Lamborghini Huracán STO)

**Approved 2026-09-26 as the go-to treatment for quick promo story ads** (`quick-promo` in
`../HOUSE-STYLE.md`). Start the next promo story from `story2.html`.

A 15 s 9:16 Instagram/Facebook story for a two-hour flash special today, 11 AM to 1 PM. Cut fast so it
could go out when the window opened. The polished version is built next to it in `../flash-special-story/`.

## On screen, and where each line comes from

| Line | Source |
|---|---|
| SUPERCAR EXPERIENCE · 2-HOUR FLASH SPECIAL | Omarie's brief ("two hour flash special") |
| 2023 · EXOTIC · LAMBORGHINI · HURACAN STO | `01-brand-core/brand-tokens.json` (site listing: "2023 - Exotic") |
| TODAY ONLY · 11AM–1PM · ENDS AT 1PM | Omarie's brief ("till 1 o'clock", two hours) |
| TO DRIVE IT, YOU NEED · VALID DRIVER'S LICENSE · AGE 21+ · INSURANCE | Omarie's brief |
| FLASH SPECIAL ENDS 1PM · CALL OR DM TO BOOK · (888) 678-6079 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ | brand tokens |

No discount figure is shown because none was given. Add one only from a named source.
Copy passed SlopMonster at 5/5.

## Footage and sound

`SCE_Lamborghini-Huracan-STO_green_no-branding.mp4` from Dropbox `Supercar Experience/01 Car Footage/`.
The clip's own audio is not used because we don't know where it came from. The sound bed (kick, sub, whooshes on the cuts, impacts on the slams)
was synthesised for this cut. Swap in IG music if wanted.

## Re-render

    ./build.sh <source clip> <sfx.wav> [path/to/ffmpeg]

`story.html` is the motion layer: `window.renderAt(t)` sets every element for time t, and `render.js` screenshots it frame by
frame with a transparent background. Change the end time by editing the `11AM–1PM` / `1PM` strings in `story.html`.

## GT3 RS and Black Series variants (`story2.html`)

The same motion layer with the offer card swapped for a price card. Pick the car with the URL hash:
`story2.html#gt3rs` or `story2.html#bs` (config block at the top of the file).

| Car | Offer on screen | Footage |
|---|---|---|
| Porsche 911 GT3 RS (2025 · EXOTIC) | TODAY ONLY · ENDS 1PM · 5 HOURS · $1,200 · OUT THE DOOR | `SCE_Porsche-911-GT3RS_white-red-livery_no-branding.mov` |
| Mercedes-AMG GT Black Series (2021 · EXOTIC) | TODAY ONLY · ENDS 1PM · 5 HOURS · $800 · OUT THE DOOR | `SCE_Mercedes-AMG-GT-Black-Series_no-branding.mov` |

Prices, hours and "out the door" are Omarie's figures from 26 Sept 2026. Years and class come from brand tokens.
The hook reads TODAY ONLY / FLASH SPECIAL rather than 2-HOUR, so it does not clash with the 5-hour rental.

    python3 plate.py <ffmpeg> gt3rs <source clip>      # or: bs
    PAGE="story2.html#gt3rs" node render.js seq .work/seq_gt3rs 24
    # then the same overlay/encode step as build.sh, with plate_gt3rs.mp4 and .work/seq_gt3rs

## Delivered to Dropbox

`Supercar Experience/04 Flash Special Stories (2026-09-26)/`, one numbered folder per car plus `00 README.md`.
Sizes were checked against the local renders.

The Dropbox connector can't upload video, but a cloud session can go through a **file request**:
`create_file_request` on the target folder, then Playwright on `dropbox.com/request/<id>`
("Add files" → "Files from computer" → name + email → Upload). Dropbox puts the uploader's name in
front of each filename, so move the files into place afterwards. Chromium needs the proxy CA in its NSS store first
(`certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n ccr-agent-proxy -i /root/.ccr/agent-proxy-ca.crt`,
from `libnss3-tools`). Don't use `--ignore-certificate-errors`.
