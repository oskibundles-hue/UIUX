from PIL import Image, ImageDraw, ImageFont
F = '/home/user/UIUX-se-vlog/supercar-experience/07-fonts/'
beb = lambda s: ImageFont.truetype(F + 'BebasNeue-Regular.ttf', s)
mic = lambda s: ImageFont.truetype(F + 'Michroma-Regular.ttf', s)
sans = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', s)
ORG, W, M, G, TW = (255, 79, 22), 1080, 18, 18, 336
TH, CAP = round(TW * 16 / 9), 92
def board(title, sub, tiles, notes, out):
    rows = (len(tiles) + (1 if notes else 0) + 2) // 3
    H = 190 + rows * (TH + CAP + G) + 20
    im = Image.new('RGB', (W, H), (8, 8, 10)); d = ImageDraw.Draw(im)
    d.rectangle([M, 40, M + 120, 46], fill=ORG); d.rectangle([M + 120, 40, M + 154, 46], fill=(255, 255, 255))
    d.text((M, 58), title, font=beb(84), fill=(255, 255, 255))
    d.text((M, 150), sub, font=mic(15), fill=(200, 200, 205))
    for i, (f, a, b) in enumerate(tiles):
        r, c = divmod(i, 3); x, y = M + c * (TW + G), 190 + r * (TH + CAP + G)
        im.paste(Image.open('out/' + f + '.png').convert('RGB').resize((TW, TH), Image.LANCZOS), (x, y))
        d.text((x, y + TH + 12), a, font=beb(34), fill=ORG)
        d.text((x, y + TH + 52), b, font=sans(19), fill=(235, 235, 238))
    if notes:
        i = len(tiles); r, c = divmod(i, 3); x, y = M + c * (TW + G), 190 + r * (TH + CAP + G)
        w = W - M - x; d.rectangle([x, y, x + w, y + TH], fill=(24, 24, 28)); d.rectangle([x, y, x + w, y + 6], fill=ORG)
        d.text((x + 24, y + 30), 'MOCKUP NOTES', font=beb(44), fill=(255, 255, 255)); yy = y + 96
        for n in notes:
            words, line = n.split(), ''
            for wd in words:
                if d.textlength(line + ' ' + wd, font=sans(21)) > w - 70: d.text((x + 44, yy), line.strip(), font=sans(21), fill=(225, 225, 230)); yy += 30; line = ''
                line += ' ' + wd
            d.rectangle([x + 24, yy + 10, x + 32, yy + 18], fill=ORG) if False else None
            d.text((x + 44, yy), line.strip(), font=sans(21), fill=(225, 225, 230)); yy += 46
    im.save(out, quality=88); print(out, im.size)
board('ONE-WAY TICKET · PART 1', 'SE VLOG MOCKUP · SEP 26 2026 · RALLY V2 + DARK-GLASS HUD · ABOUT 2:45', [
 ('p1-01', '0:00 · HOOK', '13:30 · open top in the mountains (0096)'),
 ('p1-02', '0:02 · CH 01 WHEELS UP', '04:58 · the airport before dawn (0076)'),
 ('p1-03', '0:12 · NAME LOCK', '05:31 · at the gate (0080)'),
 ('p1-04', '0:30 · CLOCK STAMP', '09:00 · in the air (0082)'),
 ('p1-05', '0:45 · CH 02 THE PICKUP', '10:14 · at the shop (0087)'),
 ('p1-06', '1:10 · CH 03 HIT THE ROAD', '12:17 · into the trees (0095)'),
 ('p1-07', '1:25 · HUD-1 STRIP', '13:28 · into the mountains (0096)'),
 ('p1-08', '2:05 · HUD-1 STRIP', '15:42 · open road (0099)'),
 ('p1-09', '2:40 · TEASE', '16:48 · fuel stop, Part 2 next (0102)')], None, 'storyboard-part1.jpg')
board('ONE-WAY TICKET · PART 2', 'SE VLOG MOCKUP · SEP 26–27 2026 · RALLY V2 + DARK-GLASS HUD · ABOUT 2:45', [
 ('p2-01', '0:00 · HOOK', '06:26 · sunrise at the wheel (0116)'),
 ('p2-02', '0:02 · CH 01 NIGHT SHIFT', '19:53 · dinner stop (0107)'),
 ('p2-03', '0:15 · PLACE TAG', '19:55 · In-N-Out (0107)'),
 ('p2-04', '0:40 · CLOCK STAMP', '01:29 · still going (0114)'),
 ('p2-05', '1:00 · CH 02 FIRST LIGHT', '07:11 · morning in the desert (0117)'),
 ('p2-06', '1:20 · LOCK-ON', '07:26 · gas stop, doors up (0119)'),
 ('p2-07', '1:45 · CH 03 HOME STRETCH', '07:35 · rear-deck cam (0121)'),
 ('p2-08', '2:05 · HUD-2 STRIP', '09:04 · into Las Vegas (0122)'),
 ('p2-09', '2:25 · ARRIVED', '09:10 · SE Las Vegas (0123)'),
 ('p2-10', '2:40 · END CARD', 'the approved rally end card')], [
 'Each part runs about 2:45, over your 2:00 minimum.',
 'HEADING and SIDE G are placeholders here; the full build reads them from the footage.',
 'Captions come from the transcript in the full build, so none are shown.',
 'To confirm: the McLaren model, the pickup city and the title.',
 'Dark glass + SE orange throughout, to match your HUD pick. The rally standard is gold: one switch.'], 'storyboard-part2.jpg')
