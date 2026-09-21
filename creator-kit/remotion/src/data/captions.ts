/**
 * Word-level caption timing.
 *
 * You write phrases with a start and end in seconds; `toWords` splits each
 * phrase into words and distributes the time by word length, which tracks
 * real speech far better than dividing the phrase evenly (long words take
 * longer to say). Good enough to look hand-timed without a transcription
 * service in the loop.
 *
 * If you do have word-level timings from a transcription tool, skip `toWords`
 * and pass the words straight through.
 */

export type Phrase = { text: string; start: number; end: number };
export type Word = { text: string; start: number; end: number };

export const toWords = (phrases: Phrase[]): Word[] => {
  const out: Word[] = [];
  for (const p of phrases) {
    const words = p.text.split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    // Weight by length, with a floor so short words still get a readable beat.
    const weights = words.map((w) => Math.max(2.5, w.length));
    const total = weights.reduce((a, b) => a + b, 0);
    const span = p.end - p.start;
    let t = p.start;
    words.forEach((w, i) => {
      const d = (weights[i] / total) * span;
      out.push({ text: w, start: t, end: t + d });
      t += d;
    });
  }
  return out;
};

/** Group words into on-screen lines of at most `max` words. */
export const toLines = (words: Word[], max = 3): Word[][] => {
  const lines: Word[][] = [];
  for (let i = 0; i < words.length; i += max) lines.push(words.slice(i, i + max));
  return lines;
};

/**
 * Face-aware caption placement (story/caption_faces.py): a per-segment vertical override, in seconds and a
 * fraction of frame height. story/caption_faces.py samples frames across each caption line's span with the same
 * YuNet detector bridges.py uses for T2, and writes one entry here only for a line whose default position
 * (theme.captionCentreY) overlaps a detected face -- most often handheld/chest-mounted footage where the face
 * sits low in frame, the same place captions default to. `y` is always inside theme.safe (caption_faces.py's
 * ALT_Y is computed from theme.safe.top with its own band-height margin); captionYAt clamps again here as a
 * second, defensive check, in case a hand-written position prop is fed in some other way.
 */
export type CaptionPosition = { start: number; end: number; y: number };

/** The caption centre-Y to use at time `t`: an override active at `t`, clamped inside theme.safe, else the
 * theme default. Overrides never stack; the first one whose [start, end) contains `t` wins. */
export const captionYAt = (
  t: number,
  positions: CaptionPosition[] | undefined,
  defaultY: number,
  safeTop: number,
  safeBottom: number
): number => {
  const hit = (positions ?? []).find((p) => t >= p.start && t < p.end);
  if (!hit) return defaultY;
  return Math.min(Math.max(hit.y, safeTop), 1 - safeBottom);
};
