import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, F, clamp, inOut, lin, rnd} from './theme';
import {Still} from './core';

// ---------------- SE race badge, built in stages ----------------
const gearPath = (cx: number, cy: number, r1: number, r2: number, teeth: number) => {
  let d = '';
  for (let i = 0; i < teeth * 2; i++) {
    const r = i % 2 ? r2 : r1;
    const a = (i / (teeth * 2)) * Math.PI * 2;
    d += (i ? 'L' : 'M') + (cx + Math.cos(a) * r).toFixed(1) + ' ' + (cy + Math.sin(a) * r).toFixed(1) + ' ';
  }
  return d + 'Z';
};

export const Badge: React.FC<{at: number; size?: number; full?: boolean}> = ({at, size = 600, full}) => {
  const f = useCurrentFrame() - at + (full ? 200 : 0);
  const {fps} = useVideoConfig();
  const s = (d: number, k = 180, dmp = 12) => spring({frame: f - d, fps, config: {damping: dmp, stiffness: k}});
  const ring = lin(f, 0, 14);
  const gear = s(8);
  const disc = s(14);
  const check = lin(f, 20, 34);
  const textN = Math.floor(lin(f, 24, 52, 0, 1) * 60);
  const mono = s(38, 220, 9);
  const ribbon = lin(f, 46, 58);
  const rays = lin(f, 28, 40);
  const txt = 'RACE WEEKEND PASS ★ THU · FRI · SAT ★ ';
  const rot = f * 0.6;
  const checks = [];
  const N = 48;
  for (let i = 0; i < N; i++) {
    if (i / N > check) break;
    const a0 = (i / N) * Math.PI * 2, a1 = ((i + 1) / N) * Math.PI * 2;
    const r0 = 196, r1 = 214;
    const p = (r: number, a: number) => `${300 + Math.cos(a) * r} ${300 + Math.sin(a) * r}`;
    checks.push(<path key={i} d={`M ${p(r0, a0)} L ${p(r1, a0)} L ${p(r1, a1)} L ${p(r0, a1)} Z`} fill={i % 2 ? C.chalk : C.asphalt} />);
  }
  return (
    <div style={{width: size, height: size, position: 'relative'}}>
      <svg viewBox="0 0 600 600" width={size} height={size} style={{overflow: 'visible'}}>
        <defs>
          <path id="tring" d="M 300 300 m -168 0 a 168 168 0 1 1 336 0 a 168 168 0 1 1 -336 0" />
        </defs>
        {/* rays */}
        <g opacity={rays} transform={`rotate(${rot * 0.5} 300 300)`}>
          {Array.from({length: 24}).map((_, i) => {
            const a = (i / 24) * 360;
            return <path key={i} d="M 300 300 L 292 0 L 308 0 Z" fill={C.yellow} opacity={0.18} transform={`rotate(${a} 300 300) scale(${1})`} style={{transformOrigin: '300px 300px'}} />;
          })}
        </g>
        {/* pixel particle ring */}
        <g opacity={ring * (1 - lin(f, 20, 40) * 0.6)}>
          {Array.from({length: 64}).map((_, i) => {
            const a = (i / 64) * Math.PI * 2 + f * 0.03;
            const r = 290 + Math.sin(i * 1.7 + f * 0.3) * 10;
            const sz = 8 + (i % 3) * 4;
            return <rect key={i} x={300 + Math.cos(a) * r - sz / 2} y={300 + Math.sin(a) * r - sz / 2} width={sz} height={sz} fill={i % 4 ? C.yellow : '#fff7c2'} style={{filter: 'drop-shadow(0 0 8px rgba(242,197,0,0.9))'}} />;
          })}
        </g>
        <g transform={`translate(300 300) scale(${gear}) rotate(${(1 - gear) * -60}) translate(-300 -300)`}>
          <path d={gearPath(300, 300, 262, 238, 28)} fill={C.yellow} stroke={C.asphalt} strokeWidth={6} />
        </g>
        <circle cx={300} cy={300} r={226 * disc} fill={C.asphalt} />
        {checks}
        <circle cx={300} cy={300} r={196 * disc} fill={C.asphalt} />
        <text fontFamily="Archivo Black" fontSize={27} letterSpacing={9} fill={C.chalk} transform={`rotate(${-90 + rot * 0.4} 300 300)`}>
          <textPath href="#tring">{txt.slice(0, textN)}</textPath>
        </text>
        <circle cx={300} cy={300} r={128 * disc} fill={C.yellow} />
      </svg>
      <Img
        src={staticFile('brand/mono.svg')}
        style={{position: 'absolute', left: '50%', top: '50%', width: size * 0.26, transform: `translate(-50%,-55%) scale(${mono})`, filter: 'invert(1)'}}
      />
      {/* ribbon */}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: size * 0.76,
          transform: `translateX(-50%) scaleX(${ribbon})`,
          background: C.red,
          color: C.chalk,
          fontFamily: F.display,
          fontSize: size * 0.06,
          padding: `${size * 0.012}px ${size * 0.05}px`,
          whiteSpace: 'nowrap',
          boxShadow: '0 8px 0 #8e1b14',
          clipPath: 'polygon(0 0,100% 0,96% 50%,100% 100%,0 100%,4% 50%)',
        }}
      >
        RACE WEEKEND
      </div>
    </div>
  );
};

// ---------------- SE Concierge booking window chrome ----------------
export const EditorChrome: React.FC<{children: React.ReactNode; comp: string; viewerH?: number; showTimeline?: boolean; playhead?: number}> = ({children, comp, viewerH = 1100, showTimeline = true, playhead = 0}) => {
  return (
    <AbsoluteFill style={{background: '#0f0f11', fontFamily: F.mono, color: '#b9b7b0'}}>
      {/* menu bar */}
      <div style={{height: 64, display: 'flex', alignItems: 'center', gap: 26, padding: '0 28px', borderBottom: `1px solid ${C.rule}`, fontSize: 20, marginTop: 150}}>
        <span style={{color: C.yellow}}>●</span>
        <span style={{color: C.chalk}}>SE Concierge</span>
        {['Fleet', 'Dates', 'Route', 'Pickup'].map((m) => (
          <span key={m}>{m}</span>
        ))}
      </div>
      {/* tabs */}
      <div style={{height: 52, display: 'flex', alignItems: 'flex-end', gap: 4, padding: '0 20px', background: '#131315'}}>
        <div style={{background: C.panel2, padding: '12px 22px', fontSize: 19, color: C.chalk, borderTop: `2px solid ${C.yellow}`}}>{comp}</div>
        <div style={{padding: '12px 22px', fontSize: 19}}>Confirmation</div>
      </div>
      {/* viewer */}
      <div style={{position: 'relative', height: viewerH, margin: '0 20px', background: '#08080a', overflow: 'hidden', border: `1px solid ${C.rule}`}}>{children}</div>
      {showTimeline && <MiniTimeline playhead={playhead} />}
    </AbsoluteFill>
  );
};

// race-weekend day bars: each day owns a third of the track, like a booking calendar
const DAYS = [
  ['THU', 'NOV 19', C.yellow],
  ['FRI', 'NOV 20', C.chalk],
  ['SAT · RACE NIGHT', 'NOV 21', C.red],
] as const;
const dayAt = (ph: number) => DAYS[Math.min(2, Math.floor(ph * 3))];

export const MiniTimeline: React.FC<{playhead: number; grow?: number}> = ({playhead, grow = 1}) => {
  const [d, date] = dayAt(playhead);
  return (
    <div style={{margin: '18px 20px 0', background: C.panel, border: `1px solid ${C.rule}`, padding: '14px 0', fontSize: 18}}>
      <div style={{display: 'flex', padding: '0 18px 10px', color: C.yellow, fontSize: 22}}>{date} · {d.split(' ')[0]}</div>
      {DAYS.map(([n, , c], i) => (
        <div key={n} style={{display: 'flex', alignItems: 'center', height: 34}}>
          <div style={{width: 250, padding: '0 18px', color: '#9a988f', overflow: 'hidden', whiteSpace: 'nowrap'}}>{n}</div>
          <div style={{flex: 1, position: 'relative', height: 18, marginRight: 18}}>
            <div style={{position: 'absolute', left: `${i * 33.3}%`, width: `${33.3 * grow}%`, top: 0, bottom: 0, background: c, opacity: 0.85}} />
          </div>
        </div>
      ))}
    </div>
  );
};

// shots 13 and 19 (the day tracks and the scrubbing edit) live in timeline.tsx

// fleet list cascade (shot 17). Only cars on supercarexp.vip's Las Vegas page (checked 2026-10-05); never the SF90.
const FLEET = [
  ['▾', 'EXOTIC · LAS VEGAS', 0],
  ['', 'PORSCHE 911 GT3 RS', 1],
  ['', 'LAMBORGHINI HURACÁN STO', 1],
  ['', 'MCLAREN 750S SPIDER', 1],
  ['', 'MERCEDES-AMG GT BLACK SERIES', 1],
  ['', 'FERRARI F8 TRIBUTO', 1],
  ['', 'LAMBORGHINI HURACÁN EVO SPYDER', 1],
  ['▸', 'LUXURY · LAS VEGAS', 0],
] as const;

export const FleetPanel: React.FC = () => {
  const f = useCurrentFrame();
  const whip = interpolate(f, [0, 7], [900, 0], {...clamp, easing: (t) => 1 - (1 - t) ** 3});
  const blur = interpolate(f, [0, 7], [40, 0], clamp);
  return (
    <AbsoluteFill style={{background: '#0f0f11', transform: `translateX(${whip}px)`, filter: `blur(${blur}px)`}}>
      <div style={{marginTop: 220, marginLeft: 50, marginRight: 50, background: C.panel, border: `1px solid ${C.rule}`, fontFamily: F.mono}}>
        <div style={{padding: '18px 24px', borderBottom: `1px solid ${C.rule}`, color: C.chalk, fontSize: 26}}>Fleet</div>
        <div style={{padding: '14px 24px', borderBottom: `1px solid ${C.rule}`, display: 'flex', gap: 12, alignItems: 'center'}}>
          <div style={{flex: 1, height: 44, background: '#0c0c0e', borderRadius: 6, color: C.mute, fontSize: 22, display: 'flex', alignItems: 'center', padding: '0 14px'}}>⌕ race weekend · NOV 19–21</div>
        </div>
        {FLEET.map(([icon, name, ind], i) => {
          const p = lin(f, 5 + i * 1.3, 11 + i * 1.3);
          const tick = lin(f, 8 + i * 1.3, 12 + i * 1.3);
          const isGroup = !ind;
          return (
            <div key={name} style={{display: 'flex', alignItems: 'center', gap: 14, height: 66, padding: `0 24px 0 ${24 + ind * 44}px`, fontSize: isGroup ? 24 : 23, color: isGroup ? C.chalk : '#bdbbb4', opacity: p, transform: `translateX(${(1 - p) * 40}px)`}}>
              <span style={{width: 18, color: C.mute}}>{icon}</span>
              <div style={{width: isGroup ? 26 : 12, height: isGroup ? 20 : 12, background: isGroup ? C.yellow : C.blue, borderRadius: isGroup ? 3 : 6}} />
              <span style={{flex: 1, whiteSpace: 'nowrap'}}>{name}</span>
              {!isGroup && (
                <div style={{display: 'flex', alignItems: 'center', gap: 8, fontSize: 17, letterSpacing: 1, color: '#4ad66d', opacity: tick, transform: `scale(${0.6 + tick * 0.4})`}}>
                  <span style={{fontSize: 20}}>✓</span>AVAILABLE
                </div>
              )}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// booking kit (shot 18): sunburst, car card, key fob, pickup pin, license card, chequered tile
// one photo tile: slow push, a light sweep across the glass, a label chip
const PhotoTile: React.FC<{src: string; i: number; label: string; pos?: string; ripple?: boolean; children?: React.ReactNode}> = ({src, i, label, pos = '50% 50%', ripple, children}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f - i * 3, fps, config: {damping: 13, stiffness: 190}});
  const sweep = lin(f, 8 + i * 3, 30 + i * 3, -60, 160);
  const fid = `ripple${i}`;
  return (
    <div style={{position: 'relative', overflow: 'hidden', borderRadius: 18, border: `1px solid ${C.rule}`, background: C.panel, transform: `scale(${0.85 + sp * 0.15})`, opacity: Math.min(1, sp * 1.6), boxShadow: '0 18px 40px rgba(0,0,0,0.55)'}}>
      {ripple && (
        <svg width="0" height="0" style={{position: 'absolute'}}>
          <filter id={fid}>
            <feTurbulence type="fractalNoise" baseFrequency="0.008 0.014" numOctaves={2} seed={3} result="n" />
            <feOffset in="n" dx={-f * 3} dy={0} result="m" />
            <feDisplacementMap in="SourceGraphic" in2="m" scale={22} xChannelSelector="R" yChannelSelector="G" />
          </filter>
        </svg>
      )}
      <Img src={staticFile(src)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, transform: `scale(${1.06 + lin(f, 0, 90) * 0.06})`, filter: ripple ? `url(#${fid})` : undefined}} />
      <div style={{position: 'absolute', inset: 0, background: `linear-gradient(115deg, rgba(255,255,255,0) ${sweep - 18}%, rgba(255,255,255,0.16) ${sweep}%, rgba(255,255,255,0) ${sweep + 18}%)`}} />
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(0,0,0,0) 62%, rgba(0,0,0,0.6))'}} />
      {children}
      <div style={{position: 'absolute', left: 18, bottom: 16, display: 'flex', alignItems: 'center', gap: 10, fontFamily: F.mono, fontSize: 21, letterSpacing: 2, color: C.chalk}}>
        <div style={{width: 9, height: 9, borderRadius: 5, background: C.red, boxShadow: `0 0 10px ${C.red}`}} />
        {label}
      </div>
    </div>
  );
};

export const AssetBoard: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ok = spring({frame: f - 22, fps, config: {damping: 9, stiffness: 260}});
  const pin = spring({frame: f - 14, fps, config: {damping: 8, stiffness: 170}});
  const pulse = (f % 24) / 24;
  return (
    <AbsoluteFill style={{background: '#0f0f11', backgroundImage: 'radial-gradient(rgba(255,255,255,0.05) 1.5px, transparent 1.5px)', backgroundSize: '36px 36px', padding: '230px 44px 140px', display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr 1fr', gap: 26}}>
      <PhotoTile src="tiles/pass.png" i={0} label="RACE PASS" pos="40% 60%" />
      <PhotoTile src="stills/gt3_side.jpg" i={1} label="911 GT3 RS" />
      <PhotoTile src="tiles/fob.png" i={2} label="KEY FOB" pos="45% 45%" />
      {/* pickup: a crop of the real map with a live pin */}
      <PhotoTile src="map/pickup_tile.jpg" i={3} label="PICKUP">
        <div style={{position: 'absolute', left: '50%', top: '50%', width: 0, height: 0}}>
          <div style={{position: 'absolute', left: -60 - pulse * 40, top: -60 - pulse * 40, width: 120 + pulse * 80, height: 120 + pulse * 80, borderRadius: '50%', border: `3px solid ${C.red}`, opacity: (1 - pulse) * pin}} />
          <div style={{position: 'absolute', left: -14, top: -14, width: 28, height: 28, borderRadius: '50%', background: C.red, border: `5px solid ${C.chalk}`, boxShadow: `0 0 24px ${C.red}`, transform: `scale(${pin})`}} />
        </div>
      </PhotoTile>
      <PhotoTile src="tiles/licence.png" i={4} label="LICENSE" pos="60% 45%">
        {f >= 22 && (
          <div style={{position: 'absolute', right: 22, top: 30, transform: `scale(${2 - ok}) rotate(-10deg)`, opacity: Math.min(1, ok * 2), border: '5px solid #2fa84f', background: 'rgba(10,30,16,0.55)', color: '#41d36a', fontFamily: F.display, fontSize: 30, padding: '4px 14px', borderRadius: 10, letterSpacing: 1}}>✓ VERIFIED</div>
        )}
      </PhotoTile>
      <PhotoTile src="tiles/flag.png" i={5} label="RACE NIGHT" pos="55% 50%" ripple />
    </AbsoluteFill>
  );
};
