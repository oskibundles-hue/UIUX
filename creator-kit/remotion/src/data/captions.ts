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
