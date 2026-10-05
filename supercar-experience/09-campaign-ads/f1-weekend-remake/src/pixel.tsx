import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {noise3D} from '@remotion/noise';
import {C, F, lin, rnd} from './theme';

// REV — original pixel mascot: a tiny supercar seen head-on, headlights for eyes.
const PAL: Record<string, string> = {
  k: '#141414',
  y: C.yellow,
  d: C.yellowDeep,
  w: '#BFE6FF',
  e: '#FFFFFF',
  p: '#141414',
  r: C.red,
  g: '#3A3A3A',
  o: '#FF8A1F',
  O: '#FFD23F',
  R: '#E2341D',
  s: '#FFF3C4',
};

const REV_OPEN = [
  '...kkkkkkkkkk...',
  '..kyyyyyyyyyyk..',
  '.kyywwwwwwwwyyk.',
  '.kywwwwwwwwwwyk.',
  'kyyyyyyyyyyyyyyk',
  'kyeeeyyyyyyeeeyk',
  'kyeppyyyyyyppeyk',
  'kyeeeyyyyyyeeeyk',
  'kyyyyykkkkyyyyyk',
  'kdyyyyykkyyyyydk',
  '.kkddddddddddkk.',
  '.kgk.kkkkkk.kgk.',
  '.kkk........kkk.',
];
const REV_BLINK = REV_OPEN.map((r, i) => (i === 5 || i === 7 ? r.replace(/e/g, 'y') : i === 6 ? r.replace(/[ep]/g, 'k') : r));

// side-view coupe silhouette
const COUPE = [
  '................',
  '................',
  '................',
  '.....kkkkkk.....',
  '...kkywwwwykk...',
  '.kkyywwwwwwyyk..',
  'kyyyyyyyyyyyyykk',
  'kyyyyyyyyyyyyyyk',
  'kdkkdyyyyyykkddk',
  '.kgk.kkkkkkkgk..',
  '..k...........k.',
  '................',
  '................',
];
// low wedge / open spider
const WEDGE = [
  '................',
  '................',
  '..............k.',
  '............kkk.',
  '..........kkyyk.',
  '........kkyyyyk.',
  '......kkyyyyyyk.',
  '....kkyyyyyyyyk.',
  '..kkyyyyyyyyyyk.',
  'kkyyyyyyyyyyyyk.',
  'kdkkddddddkkddk.',
  '.kgk......kgk...',
  '................',
];

export const Sprite: React.FC<{grid: string[]; px: number; mix?: {grid: string[]; t: number; seed?: number}}> = ({grid, px, mix}) => {
  const rows = grid.length;
  const cols = grid[0].length;
  const rects: React.ReactNode[] = [];
  for (let y = 0; y < rows; y++)
    for (let x = 0; x < cols; x++) {
      let ch = grid[y][x];
      if (mix) {
        const th = rnd(x * 31 + y * 17 + (mix.seed ?? 0));
        if (th < mix.t) ch = mix.grid[y]?.[x] ?? '.';
      }
      if (ch === '.') continue;
      rects.push(<rect key={x + '-' + y} x={x * px} y={y * px} width={px + 0.5} height={px + 0.5} fill={PAL[ch] ?? ch} />);
    }
  return (
    <svg width={cols * px} height={rows * px} shapeRendering="crispEdges" style={{overflow: 'visible', filter: 'drop-shadow(0 10px 18px rgba(0,0,0,0.45))'}}>
      {rects}
    </svg>
  );
};

// REV with pop-in, idle bob, blink, optional morph target
export const Rev: React.FC<{at: number; x: number; y: number; px?: number; morph?: {to: 'coupe' | 'wedge' | 'rev'; from?: 'coupe' | 'wedge' | 'rev'; at: number}[]; exitAt?: number; hop?: boolean}> = ({
  at,
  x,
  y,
  px = 14,
  morph = [],
  exitAt,
  hop,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < at) return null;
  const sp = spring({frame: f - at, fps, config: {damping: 9, stiffness: 200}});
  const squash = 1 + (1 - sp) * 0.35 * Math.sin((f - at) * 0.9);
  const bob = hop ? -Math.abs(Math.sin((f - at) * 0.22)) * 46 : Math.sin((f - at) * 0.16) * 8;
  const blink = (f - at) % 70 > 64;
  const grids = {rev: blink ? REV_BLINK : REV_OPEN, coupe: COUPE, wedge: WEDGE};
  let grid = grids.rev;
  let mix: {grid: string[]; t: number; seed: number} | undefined;
  for (const m of morph) {
    if (f >= m.at) {
      const t = lin(f, m.at, m.at + 9, 0, 1);
      const fromG = grids[m.from ?? 'rev'];
      grid = fromG;
      mix = {grid: grids[m.to], t, seed: m.at};
      if (t >= 1) {
        grid = grids[m.to];
        mix = undefined;
      }
    }
  }
  const out = exitAt !== undefined ? lin(f, exitAt, exitAt + 8) : 0;
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y + bob,
        transformOrigin: '50% 100%',
        transform: `scale(${sp * (1 - out) * squash}, ${(sp * (1 - out)) / squash})`,
      }}
    >
      <Sprite grid={grid} px={px} mix={mix} />
    </div>
  );
};

// procedural pixel fire
export const PixelFire: React.FC<{at: number; x: number; y: number; cols?: number; rows?: number; px?: number; burst?: number}> = ({at, x, y, cols = 18, rows = 22, px = 16, burst}) => {
  const f = useCurrentFrame();
  if (f < at) return null;
  const grow = lin(f, at, at + 6);
  const boom = burst !== undefined ? lin(f, burst, burst + 10) : 0;
  const fade = burst !== undefined ? 1 - lin(f, burst + 6, burst + 20) : 1;
  const rects: React.ReactNode[] = [];
  for (let yy = 0; yy < rows; yy++)
    for (let xx = 0; xx < cols; xx++) {
      const cx = (xx + 0.5 - cols / 2) / (cols / 2);
      const h = 1 - yy / rows; // 0 bottom .. 1 top
      const n = noise3D('fire', xx * 0.25, yy * 0.2 + f * 0.4, f * 0.05);
      const half = 0.95 - h * 0.8 + n * 0.18;
      const base = 1 - Math.abs(cx) / Math.max(0.05, half);
      const heat = base * 1.25 - h * 0.35 + n * 0.35;
      const v = heat * grow * fade;
      if (v < 0.25) continue;
      const col = v > 1.05 ? PAL.s : v > 0.8 ? PAL.O : v > 0.5 ? PAL.o : PAL.R;
      rects.push(<rect key={xx + '-' + yy} x={xx * px} y={yy * px} width={px} height={px} fill={col} />);
    }
  return (
    <svg
      width={cols * px}
      height={rows * px}
      shapeRendering="crispEdges"
      style={{position: 'absolute', left: x - (cols * px) / 2, top: y - rows * px, overflow: 'visible', transform: `scale(${1 + boom * 1.2})`, transformOrigin: '50% 100%', filter: `drop-shadow(0 0 ${30 + boom * 60}px rgba(255,140,30,0.9))`}}
    >
      {rects}
    </svg>
  );
};

// pixel sparks / embers flying out
export const Sparks: React.FC<{at: number; x: number; y: number; n?: number; spread?: number}> = ({at, x, y, n = 40, spread = 900}) => {
  const f = useCurrentFrame();
  if (f < at) return null;
  const t = f - at;
  return (
    <>
      {Array.from({length: n}).map((_, i) => {
        const a = rnd(i) * Math.PI * 2;
        const v = 0.3 + rnd(i * 3) * 1;
        const life = 18 + rnd(i * 5) * 28;
        if (t > life) return null;
        const d = (t / life) ** 0.6 * spread * v * 0.5;
        const sz = 6 + Math.round(rnd(i * 7) * 3) * 4;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x + Math.cos(a) * d,
              top: y + Math.sin(a) * d - t * 2 + (t * t) * 0.05,
              width: sz,
              height: sz,
              background: i % 3 ? PAL.O : PAL.s,
              opacity: 1 - t / life,
              boxShadow: '0 0 12px rgba(255,170,40,0.9)',
            }}
          />
        );
      })}
    </>
  );
};

// pixel-font code that types on
export const PixelCode: React.FC<{lines: string[]; at: number; x: number; y: number; cps?: number}> = ({lines, at, x, y, cps = 1.4}) => {
  const f = useCurrentFrame();
  let budget = Math.max(0, (f - at) * cps);
  return (
    <div style={{position: 'absolute', left: x, top: y, fontFamily: F.pixel, fontWeight: 700, fontSize: 64, lineHeight: 1.15, color: C.yellow, textShadow: '0 0 18px rgba(242,197,0,0.7), 4px 4px 0 #6a4b00'}}>
      {lines.map((l, i) => {
        const n = Math.min(l.length, Math.floor(budget));
        budget -= l.length;
        return <div key={i}>{l.slice(0, Math.max(0, n))}{n > 0 && n < l.length && <span style={{color: C.chalk}}>█</span>}</div>;
      })}
    </div>
  );
};
