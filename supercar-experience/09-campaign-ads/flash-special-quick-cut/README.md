# Flash special story, quick cut (Lamborghini Huracán STO)

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
