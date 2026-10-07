import {Easing, interpolate} from 'remotion';
import '@fontsource/archivo-black/400.css';
import '@fontsource/archivo/400.css';
import '@fontsource/archivo/500.css';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/700.css';
import '@fontsource/archivo/800.css';
import '@fontsource/silkscreen/400.css';
import '@fontsource/silkscreen/700.css';
import '@fontsource/dm-mono/400.css';
import '@fontsource/dm-mono/500.css';

export const FPS = 30;
export const W = 1080;
export const H = 1920;

export const C = {
  asphalt: '#0B0B0C',
  panel: '#151517',
  panel2: '#1E1E21',
  rule: '#2C2C30',
  yellow: '#F2C500',
  yellowDeep: '#C99A00',
  red: '#FF3B30',
  chalk: '#F5F3EE',
  paper: '#F7F6F2',
  mute: '#8E8C86',
  sand: '#E9C58A',
  sandDark: '#B98E52',
  rock: '#C2603A',
  lake: '#2FB3A8',
  teal: '#1F8C84',
  magenta: '#FF3DA8',
  blue: '#3D7BFF',
};

export const F = {
  display: '"Archivo Black", "Archivo", sans-serif',
  ui: 'Archivo, sans-serif',
  pixel: 'Silkscreen, monospace',
  mono: '"DM Mono", monospace',
};

export const s2f = (s: number) => Math.round(s * FPS);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const outExpo = Easing.bezier(0.16, 1, 0.3, 1);
export const inOut = Easing.bezier(0.65, 0, 0.35, 1);
export const lin = (f: number, a: number, b: number, from = 0, to = 1, ease = outExpo) =>
  interpolate(f, [a, b], [from, to], {...clamp, easing: ease});

// deterministic random
export const rnd = (i: number) => {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
