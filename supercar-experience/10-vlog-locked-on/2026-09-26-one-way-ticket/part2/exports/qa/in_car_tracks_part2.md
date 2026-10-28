# In-car tracks heard in 2026-09-26 One-way ticket Part 2 v2 - SE LOCKED-ON vlog

For Omarie to check before posting (commercial tracks can get a business-page post muted). Episode timecodes are
m:ss.ss in the v2 cut. Source: Shazam on the exact clip span of every music bed segment, cabin dialog piece and NO MUSIC substitute span
(data/shazam_spans.json), cross-checked with the full-clip scan (one 10 s window every 30 s, ../in_car_tracks.json).
"check" = at most one nearby clip-scan window (within 15 s) agrees with the direct match.

| # | Title | Artist | Episode in -> out | Clip (s) | Where | Confidence |
|---|---|---|---|---|---|---|
| 1 | Say It Was | Lil Uzi Vert | 0:00.00 -> 0:08.30 | 0122 96.0-104.3 | bed (music) | direct match on the exact span + 2 nearby clip-scan window(s) |
| 2 | Quebec | Drake | 0:17.32 -> 0:23.14 | 0107 14.62-20.44 | under the voice | direct match on the exact span + 1 nearby clip-scan window(s); **check: clip scan: 1 window(s); under the voice** |
| 3 | Sweater Weather | The Neighbourhood | 0:37.40 -> 0:45.70 | 0113 121.0-129.3 | bed (music) | direct match on the exact span + 2 nearby clip-scan window(s) |
| 4 | Maverick Intro | Lil Uzi Vert | 2:18.55 -> 2:31.75 | 0122 447.0-460.2 | bed (music) | direct match on the exact span + 3 nearby clip-scan window(s) |

Dialog pieces from the cabin clips with no song recognised on their exact span (30): 0116 at 0:02.00, 0105 at 0:08.60, 0106 at 0:14.20, 0111 at 0:25.85, 0111 at 0:27.60, 0112 at 0:30.10, 0112 at 0:33.05, 0114 at 0:45.10, 0114 at 0:49.30, 0114 at 0:52.87, 0114 at 0:55.65, 0115 at 0:58.45, 0116 at 1:03.90, 0116 at 1:06.45, 0116 at 1:11.95, 0116 at 1:16.82, 0117 at 1:27.20, 0117 at 1:28.90, 0117 at 1:31.25, 0119 at 1:33.85, 0119 at 1:41.95, 0121 at 1:48.55, 0121 at 1:52.21, 0118 at 2:08.25, 0118 at 2:10.45, 0118 at 2:15.35, 0123 at 2:30.70, 0123 at 2:32.75, 0123 at 2:36.00, 0123 at 2:41.95. A stereo may still be faintly audible under the voice there.

**NO MUSIC version:** the music bed segments (0:00.00, 0:37.40, 2:18.55) are swapped for road/exhaust nat from clip 0121 (0121 160.0-168.3, 0121 210.0-218.3, 0121 230.0-243.2; Shazam on each whole span and in 10 s windows every 5 s: no song recognised, data/shazam_spans.json).
The dialog pieces keep their own cabin audio in both versions, so every song listed above as "under the voice" (Quebec at 0:17.32)
also plays in the NO MUSIC version, as does any faint stereo under his voice in the pieces listed above.
