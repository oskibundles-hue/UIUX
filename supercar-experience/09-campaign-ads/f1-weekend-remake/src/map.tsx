import React from 'react';
import {AbsoluteFill, Img, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, F, inOut, lin, rnd} from './theme';
import {Still} from './core';
import MAP from '../public/map/data.json';

// Las Vegas at night, built by tools/vegas_map.py from OpenStreetMap (roads, water, buildings) and
// AWS terrain tiles. The ground is one CSS 3D plane; anything with height (towers, the Sphere, beams,
// pins) is drawn flat on top through project(), the same maths as the plane's CSS transform.

type Cam = {t: number; r: number; s: number; u0: number; v0: number; cx: number; cy: number; P: number};
type Pt = [number, number, number];

const RAD = Math.PI / 180;
const PXM = 1 / MAP.m_per_px; // map px per metre
const EX = 6; // tower heights x6 so the Strip reads at valley scale
const NIGHT = '#05070B';
const HUD = 'rgba(170, 200, 255, 0.75)';

// t: tilt (deg), r: turn (deg, -90 = east up), s: zoom, (u0, v0): map px at the screen point (cx, cy), P: perspective
export const project = (c: Cam, u: number, v: number, h = 0): Pt => {
  const t = c.t * RAD;
  const r = c.r * RAD;
  const du = u - c.u0;
  const dv = v - c.v0;
  const x1 = c.s * (du * Math.cos(r) - dv * Math.sin(r));
  const y1 = c.s * (du * Math.sin(r) + dv * Math.cos(r));
  const z1 = c.s * h;
  const Y = y1 * Math.cos(t) - z1 * Math.sin(t);
  const Z = y1 * Math.sin(t) + z1 * Math.cos(t);
  const w = 1 - Z / c.P;
  return [c.cx + x1 / w, c.cy + Y / w, w];
};

const mix = (a: Cam, b: Cam, k: number): Cam => {
  const o = {...a};
  (Object.keys(a) as (keyof Cam)[]).forEach((key) => (o[key] = a[key] + (b[key] - a[key]) * k));
  return o;
};

const PHOTO: Record<string, string> = {
  PICKUP: 'stop_pickup',
  'RED ROCK': 'stop_desert',
  'THE STRIP': 'stop_skyline',
  'THE SPHERE': 'stop_sphere',
  'LAKE MEAD': 'stop_lakemead',
};
export const STOPS = MAP.stops.map((s) => ({...s, img: PHOTO[s.name]}));
const stop = (n: string) => STOPS.find((s) => s.name === n)!;
const STRIP = stop('THE STRIP');
const SPHERE = stop('THE SPHERE');

// the driven route (real roads, shortest path between the stops)
const ROUTE = MAP.route as [number, number][];
const CUM = ROUTE.map((_, i) => 0);
ROUTE.forEach((p, i) => (CUM[i] = i ? CUM[i - 1] + Math.hypot(p[0] - ROUTE[i - 1][0], p[1] - ROUTE[i - 1][1]) : 0));
const LEN = CUM[CUM.length - 1];
const ROUTE_D = 'M ' + ROUTE.map((p) => `${p[0]} ${p[1]}`).join(' L ');
const along = (d: number): [number, number] => {
  const i = Math.max(1, CUM.findIndex((c) => c >= d));
  const k = (d - CUM[i - 1]) / (CUM[i] - CUM[i - 1] || 1);
  return [ROUTE[i - 1][0] + (ROUTE[i][0] - ROUTE[i - 1][0]) * k, ROUTE[i - 1][1] + (ROUTE[i][1] - ROUTE[i - 1][1]) * k];
};

// towers with a real height tag (>= 45 m), heights exaggerated
type Tower = {name: string; h: number; pts: number[][]};
const TOWERS = (MAP.towers as Tower[]).map((t) => {
  const cu = t.pts.reduce((a, p) => a + p[0], 0) / t.pts.length;
  const cv = t.pts.reduce((a, p) => a + p[1], 0) / t.pts.length;
  return {...t, cu, cv, hp: t.h * PXM * EX, d: Math.hypot(cu - STRIP.u, cv - STRIP.v)};
});
const LIGHT = [-0.8, 0.6]; // from the west-south-west, the side the camera sits on

// ---------------------------------------------------------------- the ground plane
const Plane: React.FC<{cam: Cam; reveal: number; children?: React.ReactNode}> = ({cam, reveal, children}) => {
  const {t, r, s, u0, v0, cx, cy, P} = cam;
  const R = reveal * 2800;
  const lights = (ox: number, oy: number) =>
    `radial-gradient(circle at ${STRIP.u - ox}px ${STRIP.v - oy}px, #000 ${R}px, transparent ${R + 380}px)`;
  const [a0, b0, a1, b1] = MAP.city;
  const grid = 5000 * PXM; // 5 km
  return (
    <AbsoluteFill style={{perspective: P, perspectiveOrigin: `${cx}px ${cy}px`, overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: MAP.w,
          height: MAP.h,
          transformOrigin: '0 0',
          transform: `translate(${cx}px, ${cy}px) rotateX(${t}deg) rotateZ(${r}deg) scale(${s}) translate(${-u0}px, ${-v0}px)`,
          WebkitMaskImage: 'radial-gradient(ellipse 50% 50% at 50% 50%, #000 80%, transparent 100%)',
        }}
      >
        <Img src={staticFile('map/base.jpg')} style={{position: 'absolute', left: 0, top: 0, width: MAP.w, height: MAP.h}} />
        <Img src={staticFile('map/lit.jpg')} style={{position: 'absolute', left: 0, top: 0, width: MAP.w, height: MAP.h, WebkitMaskImage: lights(0, 0)}} />
        <div style={{position: 'absolute', left: a0, top: b0, width: a1 - a0, height: b1 - b0, WebkitMaskImage: 'radial-gradient(ellipse 50% 50% at 50% 50%, #000 60%, transparent 100%)'}}>
          <Img src={staticFile('map/city_hd.jpg')} style={{width: '100%', height: '100%', WebkitMaskImage: lights(a0, b0)}} />
        </div>
        <svg width={MAP.w} height={MAP.h} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
          <defs>
            <filter id="mapglow" x="-10%" y="-10%" width="120%" height="120%">
              <feGaussianBlur stdDeviation={7} />
            </filter>
          </defs>
          <g stroke="rgba(150, 190, 255, 0.09)" strokeWidth={1.5}>
            {Array.from({length: Math.ceil(MAP.w / grid)}).map((_, i) => (
              <line key={`x${i}`} x1={i * grid} y1={0} x2={i * grid} y2={MAP.h} />
            ))}
            {Array.from({length: Math.ceil(MAP.h / grid)}).map((_, i) => (
              <line key={`y${i}`} x1={0} y1={i * grid} x2={MAP.w} y2={i * grid} />
            ))}
          </g>
          {reveal > 0 && reveal < 1 && (
            <circle cx={STRIP.u} cy={STRIP.v} r={R + 190} fill="none" stroke="rgba(160, 210, 255, 0.55)" strokeWidth={10} opacity={1 - reveal} />
          )}
          {children}
        </svg>
      </div>
    </AbsoluteFill>
  );
};

const RouteLine: React.FC<{p: number}> = ({p}) => {
  if (p <= 0) return null;
  const d = p * LEN;
  const [hx, hy] = along(d);
  const dash = {strokeDasharray: `${d} ${LEN + 10}`, fill: 'none', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <g>
      <path d={ROUTE_D} stroke={C.red} strokeOpacity={0.6} strokeWidth={22} filter="url(#mapglow)" {...dash} />
      <path d={ROUTE_D} stroke={C.red} strokeWidth={7} {...dash} />
      <path d={ROUTE_D} stroke="#FFD6D2" strokeWidth={2} {...dash} />
      {p < 1 && (
        <>
          <circle cx={hx} cy={hy} r={26} fill="#FFFFFF" opacity={0.5} filter="url(#mapglow)" />
          <circle cx={hx} cy={hy} r={8} fill="#FFFFFF" />
        </>
      )}
    </g>
  );
};

const GroundRing: React.FC<{u: number; v: number; at: number}> = ({u, v, at}) => {
  const f = useCurrentFrame();
  if (f < at) return null;
  const k = ((f - at) % 36) / 36;
  return (
    <g>
      <circle cx={u} cy={v} r={10 + k * 60} fill="none" stroke={C.red} strokeWidth={4} opacity={(1 - k) * 0.9} />
      <circle cx={u} cy={v} r={9} fill={C.red} opacity={0.9} />
      <circle cx={u} cy={v} r={22} fill={C.red} opacity={0.35} filter="url(#mapglow)" />
    </g>
  );
};

// ---------------------------------------------------------------- things with height
// night glass: dark walls, a warm uplight at the base, lit floor lines and bright edges
const wallFill = (k: number) => `rgb(${Math.round(18 + 52 * k)}, ${Math.round(20 + 44 * k)}, ${Math.round(28 + 34 * k)})`;
const FLOORS = 9;
const poly = (pts: Pt[]) => pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');

const Skyline: React.FC<{cam: Cam; grow: (d: number, i: number) => number; sphere: number}> = ({cam, grow, sphere}) => {
  const f = useCurrentFrame();
  const items: {depth: number; el: React.ReactNode}[] = [];
  TOWERS.forEach((t, i) => {
    const g = grow(t.d, i);
    if (g <= 0) return;
    const n = t.pts.length;
    const base = t.pts.map(([u, v]) => project(cam, u, v, 0));
    const top = t.pts.map(([u, v]) => project(cam, u, v, t.hp * g));
    const walls = t.pts
      .map(([u, v], k) => {
        const k2 = (k + 1) % n;
        const [u2, v2] = t.pts[k2];
        let nx = v2 - v;
        let ny = -(u2 - u);
        if (nx * ((u + u2) / 2 - t.cu) + ny * ((v + v2) / 2 - t.cv) < 0) {
          nx = -nx;
          ny = -ny;
        }
        const lit = 0.25 + 0.75 * Math.max(0, (nx * LIGHT[0] + ny * LIGHT[1]) / (Math.hypot(nx, ny) || 1));
        return {pts: [base[k], base[k2], top[k2], top[k]], lit, depth: (base[k][2] + base[k2][2]) / 2};
      })
      .sort((a, b) => b.depth - a.depth);
    const lerp = (p: Pt, q: Pt, k: number) => [p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k];
    const tall = t.h >= 150 && g >= 1;
    const [rx, ry] = project(cam, t.cu, t.cv, t.hp * g);
    items.push({
      depth: project(cam, t.cu, t.cv, 0)[2],
      el: (
        <g key={`t${i}`}>
          {walls.map((w, k) => {
            const [b0, b1, t1, t0] = w.pts;
            return (
              <g key={k}>
                <polygon points={poly(w.pts)} fill={wallFill(w.lit)} />
                <polygon points={poly(w.pts)} fill="url(#uplight)" />
                {Array.from({length: FLOORS - 1}).map((_, j) => {
                  const q = (j + 1) / FLOORS;
                  const [x0, y0] = lerp(b0, t0, q);
                  const [x1, y1] = lerp(b1, t1, q);
                  return <line key={j} x1={x0} y1={y0} x2={x1} y2={y1} stroke="#FFD9A0" strokeOpacity={0.18 + 0.32 * w.lit * (0.6 + 0.4 * rnd(i * 31 + j))} strokeWidth={0.9} />;
                })}
                <line x1={b0[0]} y1={b0[1]} x2={t0[0]} y2={t0[1]} stroke="#FFE6C0" strokeOpacity={0.35 + 0.4 * w.lit} strokeWidth={0.9} />
              </g>
            );
          })}
          <polygon points={poly(top)} fill="#2A2C34" stroke="#FFF1DA" strokeWidth={1.3} />
          {tall && <circle cx={rx} cy={ry} r={2.2} fill="#FF3B30" opacity={(f + i * 7) % 30 < 8 ? 1 : 0.25} />}
        </g>
      ),
    });
  });
  if (sphere > 0) {
    const R = 15 * sphere;
    const [x, y, w] = project(cam, SPHERE.u, SPHERE.v, R * 0.8);
    const rs = (R * cam.s) / w;
    items.push({
      depth: w,
      el: (
        <g key="sphere">
          <circle cx={x} cy={y} r={rs * 2.6} fill="url(#sphereGlow)" />
          <circle cx={x} cy={y} r={rs} fill="url(#sphereFill)" />
          <circle cx={x} cy={y} r={rs} fill="none" stroke="rgba(200, 230, 255, 0.7)" strokeWidth={1.2} />
        </g>
      ),
    });
  }
  items.sort((a, b) => b.depth - a.depth);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0}}>
      <defs>
        <linearGradient id="uplight" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0" stopColor="#FFB45C" stopOpacity={0.75} />
          <stop offset="0.35" stopColor="#FFB45C" stopOpacity={0.18} />
          <stop offset="1" stopColor="#FFB45C" stopOpacity={0} />
        </linearGradient>
        <radialGradient id="sphereFill" cx="0.5" cy="0.5" r="0.5" fx="0.34" fy="0.3">
          <stop offset="0" stopColor="#FFFFFF" />
          <stop offset="0.16" stopColor="#9FDBFF" />
          <stop offset="0.45" stopColor="#3D7BFF" />
          <stop offset="0.8" stopColor="#24237A" />
          <stop offset="1" stopColor="#100F33" />
        </radialGradient>
        <radialGradient id="sphereGlow">
          <stop offset="0.3" stopColor="#3D7BFF" stopOpacity={0.55} />
          <stop offset="1" stopColor="#3D7BFF" stopOpacity={0} />
        </radialGradient>
      </defs>
      {items.map((it) => it.el)}
    </svg>
  );
};

// a stop's beam and name tag (shot 24)
const TAG: Record<string, [number, number]> = {
  PICKUP: [-1, -64],
  'RED ROCK': [1, -40],
  'THE STRIP': [1, 56],
  'THE SPHERE': [1, -74],
  'LAKE MEAD': [1, -40],
};
const Beacon: React.FC<{cam: Cam; s: (typeof STOPS)[number]; at: number}> = ({cam, s, at}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < at) return null;
  const sp = spring({frame: f - at, fps, config: {damping: 12, stiffness: 210}});
  const [x, y] = project(cam, s.u, s.v, 0);
  const [bx, by] = project(cam, s.u, s.v, 70 * sp);
  const [side, dy] = TAG[s.name];
  const lx = x + side * 70;
  const ly = y + dy;
  return (
    <>
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        <line x1={x} y1={y} x2={bx} y2={by} stroke="#FFFFFF" strokeWidth={3} opacity={0.85} />
        <polyline points={`${x},${y} ${x + side * 30},${ly} ${lx},${ly}`} fill="none" stroke="rgba(245, 243, 238, 0.7)" strokeWidth={2} opacity={sp} />
        <circle cx={x} cy={y} r={6} fill="#FFFFFF" />
      </svg>
      <div
        style={{
          position: 'absolute',
          left: lx,
          top: ly,
          transform: `translate(${side < 0 ? '-100%' : '0'}, -50%) scale(${sp})`,
          transformOrigin: side < 0 ? '100% 50%' : '0 50%',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '8px 14px',
          background: 'rgba(8, 10, 14, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.18)',
          borderRadius: 6,
          fontFamily: F.mono,
          fontWeight: 500,
          fontSize: 22,
          letterSpacing: 2,
          color: C.chalk,
          whiteSpace: 'nowrap',
        }}
      >
        <div style={{width: 9, height: 9, background: C.red, boxShadow: `0 0 10px ${C.red}`}} />
        {s.name}
      </div>
    </>
  );
};

// a map pin that drops onto a stop (shot 26); returns its head position for leader lines
const pinHead = (cam: Cam, s: {u: number; v: number}): [number, number] => {
  const [x, y] = project(cam, s.u, s.v, 0);
  return [x, y - 62];
};
const Pin: React.FC<{cam: Cam; s: {u: number; v: number}; at: number}> = ({cam, s, at}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < at) return null;
  const sp = spring({frame: f - at, fps, config: {damping: 8, stiffness: 160}});
  const [x, y] = project(cam, s.u, s.v, 0);
  const drop = (1 - sp) * 260;
  const k = ((f - at) % 30) / 30;
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
      <ellipse cx={x} cy={y} rx={8 + k * 34} ry={(8 + k * 34) * 0.45} fill="none" stroke={C.red} strokeWidth={3} opacity={(1 - k) * Math.min(1, sp)} />
      <line x1={x} y1={y} x2={x} y2={y - 62 - drop} stroke="#FFFFFF" strokeWidth={3} opacity={0.8 * Math.min(1, sp)} />
      <circle cx={x} cy={y - 62 - drop} r={26} fill={C.red} opacity={0.35} />
      <circle cx={x} cy={y - 62 - drop} r={15} fill={C.red} stroke={C.chalk} strokeWidth={4} />
      <circle cx={x} cy={y - 62 - drop} r={5} fill={C.chalk} />
    </svg>
  );
};

// ---------------------------------------------------------------- screen furniture
const Atmosphere: React.FC = () => (
  <>
    <AbsoluteFill style={{background: `linear-gradient(180deg, ${NIGHT} 0%, rgba(5, 7, 11, 0.9) 16%, rgba(5, 7, 11, 0) 36%)`}} />
    <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(5, 7, 11, 0.75) 0%, rgba(5, 7, 11, 0) 20%)'}} />
  </>
);

const lonlat = (u: number, v: number) => {
  const [lon0, , lon1, lat1] = MAP.bbox;
  const k = MAP.w / (lon1 - lon0);
  const m = Math.log(Math.tan(Math.PI / 4 + (lat1 * RAD) / 2)) - v / ((k * 180) / Math.PI);
  return [lon0 + u / k, (2 * Math.atan(Math.exp(m)) - Math.PI / 2) / RAD];
};

const Hud: React.FC<{cam: Cam; bottom?: number; compact?: boolean}> = ({cam, bottom = 150, compact}) => {
  const [lon, lat] = lonlat(cam.u0, cam.v0);
  const hdg = Math.round((((-cam.r % 360) + 360) % 360));
  const km = (cam.s * 1000 * PXM) / 1; // screen px per km at the centre
  const bar = km * 5 > 360 ? 2 : 5;
  const mono: React.CSSProperties = {fontFamily: F.mono, fontSize: 20, letterSpacing: 2, color: HUD};
  const corner = (x: number, y: number, sx: number, sy: number) => (
    <path d={`M ${x} ${y + sy * 44} L ${x} ${y} L ${x + sx * 44} ${y}`} fill="none" stroke={HUD} strokeWidth={2.5} />
  );
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute'}}>
        {corner(36, 36, 1, 1)}
        {corner(1044, 36, -1, 1)}
        {corner(36, 1884, 1, -1)}
        {corner(1044, 1884, -1, -1)}
        <g transform={`translate(976 ${1920 - bottom - 46})`}>
          <circle r={38} fill="rgba(5, 7, 11, 0.6)" stroke={HUD} strokeWidth={2} />
          <g transform={`rotate(${cam.r})`}>
            <path d="M 0 -30 L 9 0 L -9 0 Z" fill={C.red} />
            <path d="M 0 30 L 9 0 L -9 0 Z" fill={HUD} />
            <text y={-42} textAnchor="middle" fontFamily={F.mono} fontSize={18} fill={C.chalk} transform={`rotate(${-cam.r} 0 -50)`}>N</text>
          </g>
        </g>
      </svg>
      {!compact && <div style={{position: 'absolute', left: 56, bottom, display: 'flex', flexDirection: 'column', gap: 6, ...mono}}>
        <div style={{color: C.chalk}}>LAS VEGAS VALLEY · NV</div>
        <div>
          {lat.toFixed(4)}° N {(-lon).toFixed(4)}° W
        </div>
        <div>
          HDG {String(hdg).padStart(3, '0')}° · PITCH {Math.round(cam.t)}°
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 12, marginTop: 6}}>
          <div style={{width: km * bar, height: 8, borderLeft: `2px solid ${HUD}`, borderRight: `2px solid ${HUD}`, borderBottom: `2px solid ${HUD}`}} />
          <span>{bar} KM</span>
        </div>
      </div>}
      <div style={{position: 'absolute', right: 56, bottom: 64, fontFamily: F.mono, fontSize: 17, letterSpacing: 1, color: 'rgba(245, 243, 238, 0.6)'}}>
        {MAP.credit}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- shot 24: the map builds
const CAM_A: Cam = {t: 0, r: -90, s: 0.55, u0: 1620, v0: 990, cx: 540, cy: 990, P: 1900};
const CAM_B: Cam = {t: 56, r: -98, s: 1.1, u0: 1475, v0: 1090, cx: 540, cy: 1150, P: 1900};

export const MapBuild: React.FC = () => {
  const f = useCurrentFrame();
  const cam = mix(CAM_A, CAM_B, lin(f, 4, 66, 0, 1, inOut));
  cam.s *= 0.93 + 0.07 * lin(f, 0, 16);
  const reveal = lin(f, 2, 22, 0, 1, inOut);
  return (
    <AbsoluteFill style={{background: NIGHT}}>
      <AbsoluteFill style={{opacity: lin(f, 0, 6)}}>
        <Plane cam={cam} reveal={reveal}>
          {STOPS.map((s, i) => (
            <GroundRing key={i} u={s.u} v={s.v} at={14 + 3 * i} />
          ))}
          <RouteLine p={lin(f, 28, 58, 0, 1, inOut)} />
        </Plane>
        <Skyline cam={cam} grow={(d, i) => lin(f, 18 + d / 25 + rnd(i) * 4, 30 + d / 25 + rnd(i) * 4)} sphere={spring({frame: f - 36, fps: 30, config: {damping: 10, stiffness: 150}})} />
        {STOPS.map((s, i) => (
          <Beacon key={i} cam={cam} s={s} at={14 + 3 * i} />
        ))}
      </AbsoluteFill>
      <Atmosphere />
      <Hud cam={cam} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- shot 26: route, pins, photo cards, click
const CAM_C: Cam = {t: 46, r: -84, s: 0.56, u0: 1580, v0: 1060, cx: 540, cy: 1060, P: 2200};
const CAM_D: Cam = {t: 50, r: -94, s: 0.6, u0: 1560, v0: 1070, cx: 540, cy: 1060, P: 2200};

// where each stop's photo card sits (screen px), in pin order
const CARDS: {x: number; y: number; r: number}[] = [
  {x: 60, y: 820, r: -3},
  {x: 60, y: 1420, r: 3},
  {x: 770, y: 1290, r: -2},
  {x: 770, y: 900, r: 3},
  {x: 770, y: 560, r: -3},
];
const CW = 250;

export const MapFull: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cam = mix(CAM_C, CAM_D, lin(f, 0, dur, 0, 1, inOut));
  const title = lin(f, 0, 12);
  const [px, py] = pinHead(cam, STOPS[0]);
  const cx = lin(f, 40, 62, 300, px, inOut);
  const cy = lin(f, 40, 62, 1700, py, inOut);
  const click = f - 62;
  return (
    <AbsoluteFill style={{background: NIGHT}}>
      <Plane cam={cam} reveal={1}>
        <RouteLine p={1} />
      </Plane>
      <Skyline cam={cam} grow={() => 1} sphere={1} />
      <Atmosphere />
      {STOPS.map((s, i) => (
        <Pin key={i} cam={cam} s={s} at={6 + 5 * i} />
      ))}
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0}}>
        {STOPS.map((s, i) => {
          const at = 20 + 5 * i;
          const k = lin(f, at + 4, at + 14);
          if (k <= 0) return null;
          const [hx, hy] = pinHead(cam, s);
          const c = CARDS[i];
          const ax = c.x < 540 ? c.x + CW : c.x;
          const ay = c.y + 100;
          return <line key={i} x1={hx} y1={hy} x2={hx + (ax - hx) * k} y2={hy + (ay - hy) * k} stroke="rgba(245, 243, 238, 0.75)" strokeWidth={2} strokeDasharray="6 6" />;
        })}
      </svg>
      {STOPS.map((s, i) => {
        const sp = spring({frame: f - (20 + i * 5), fps, config: {damping: 11, stiffness: 190}});
        const c = CARDS[i];
        return (
          <div key={i} style={{position: 'absolute', left: c.x, top: c.y, width: CW, transform: `rotate(${c.r}deg) scale(${sp})`, background: C.chalk, padding: 9, paddingBottom: 12, boxShadow: '0 18px 40px rgba(0,0,0,0.6)'}}>
            <div style={{height: 160, overflow: 'hidden'}}>
              <Still src={s.img} />
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 8, marginTop: 9, fontFamily: F.ui, fontWeight: 800, fontSize: 20, color: C.asphalt}}>
              <div style={{width: 9, height: 9, borderRadius: 5, background: C.red}} />
              {s.name}
            </div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 64, top: 210, opacity: title, transform: `translateY(${(1 - title) * 30}px)`}}>
        <div style={{display: 'flex', gap: 14, alignItems: 'center'}}>
          <Img src={staticFile('brand/mono.svg')} style={{height: 40}} />
          <div style={{fontFamily: F.ui, fontWeight: 800, fontSize: 24, letterSpacing: 4, color: C.yellow}}>LAS VEGAS · F1 WEEKEND</div>
        </div>
        <div style={{fontFamily: F.display, fontSize: 92, lineHeight: 0.95, color: C.chalk, marginTop: 10}}>
          RACE WEEKEND
          <br />
          ROUTE
        </div>
        <div style={{display: 'flex', gap: 12, marginTop: 18}}>
          {['5 STOPS', '1 ROUTE'].map((t, i) => (
            <div key={t} style={{fontFamily: F.ui, fontWeight: 800, fontSize: 22, padding: '8px 18px', borderRadius: 30, background: [C.yellow, C.red][i], color: i === 1 ? C.chalk : C.asphalt, opacity: lin(f, 6 + i * 3, 12 + i * 3)}}>
              {t}
            </div>
          ))}
        </div>
      </div>
      <Hud cam={cam} compact />
      {f > 38 && (
        <div style={{position: 'absolute', left: cx, top: cy}}>
          {click > 0 && click < 18 && (
            <div style={{position: 'absolute', left: -60 * (click / 18) - 4, top: -60 * (click / 18) - 4, width: 120 * (click / 18) + 8, height: 120 * (click / 18) + 8, borderRadius: '50%', border: `4px solid ${C.yellow}`, opacity: 1 - click / 18}} />
          )}
          <svg width="56" height="70" viewBox="0 0 20 25" style={{transform: `scale(${click > 0 && click < 4 ? 0.85 : 1})`}}>
            <path d="M1 1 L1 19 L6 14.5 L9.5 22.5 L12.5 21 L9 13.5 L15.5 13.5 Z" fill="#fff" stroke="#000" strokeWidth="1.4" strokeLinejoin="round" />
          </svg>
        </div>
      )}
    </AbsoluteFill>
  );
};
