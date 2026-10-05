import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {evolvePath} from '@remotion/paths';
import {C, F, clamp, lin, rnd} from './theme';
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
  const txt = 'SUPERCAR EXPERIENCE ★ F1 WEEKEND ★ LAS VEGAS ★ ';
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
        <text fontFamily="Archivo Black" fontSize={27} letterSpacing={3} fill={C.chalk} transform={`rotate(${-90 + rot * 0.4} 300 300)`}>
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

// ---------------- editor window chrome ----------------
export const EditorChrome: React.FC<{children: React.ReactNode; comp: string; viewerH?: number; showTimeline?: boolean; playhead?: number}> = ({children, comp, viewerH = 1100, showTimeline = true, playhead = 0}) => {
  return (
    <AbsoluteFill style={{background: '#0f0f11', fontFamily: F.mono, color: '#b9b7b0'}}>
      {/* menu bar */}
      <div style={{height: 64, display: 'flex', alignItems: 'center', gap: 26, padding: '0 28px', borderBottom: `1px solid ${C.rule}`, fontSize: 20, marginTop: 150}}>
        <span style={{color: C.yellow}}>●</span>
        {['File', 'Edit', 'Comp', 'Layer', 'Window'].map((m) => (
          <span key={m}>{m}</span>
        ))}
      </div>
      {/* tabs */}
      <div style={{height: 52, display: 'flex', alignItems: 'flex-end', gap: 4, padding: '0 20px', background: '#131315'}}>
        <div style={{background: C.panel2, padding: '12px 22px', fontSize: 19, color: C.chalk, borderTop: `2px solid ${C.yellow}`}}>{comp}</div>
        <div style={{padding: '12px 22px', fontSize: 19}}>Render Queue</div>
      </div>
      {/* viewer */}
      <div style={{position: 'relative', height: viewerH, margin: '0 20px', background: '#08080a', overflow: 'hidden', border: `1px solid ${C.rule}`}}>{children}</div>
      {showTimeline && <MiniTimeline playhead={playhead} />}
    </AbsoluteFill>
  );
};

const LAYERS = [
  ['Badge_ring', C.yellow],
  ['Checker_band', C.chalk],
  ['Text_ring', C.blue],
  ['Monogram', C.red],
  ['Ribbon', C.magenta],
  ['Rays', '#7BD389'],
  ['Footage_STO', '#9a8cff'],
] as const;

export const MiniTimeline: React.FC<{playhead: number; grow?: number}> = ({playhead, grow = 1}) => (
  <div style={{margin: '18px 20px 0', background: C.panel, border: `1px solid ${C.rule}`, padding: '14px 0', fontSize: 18}}>
    <div style={{display: 'flex', padding: '0 18px 10px', color: C.yellow, fontSize: 22}}>0:00:{String(Math.floor(playhead * 24)).padStart(2, '0')}:00</div>
    {LAYERS.slice(0, 5).map(([n, c], i) => (
      <div key={n} style={{display: 'flex', alignItems: 'center', height: 34}}>
        <div style={{width: 250, padding: '0 18px', color: '#9a988f', overflow: 'hidden', whiteSpace: 'nowrap'}}>{n}</div>
        <div style={{flex: 1, position: 'relative', height: 18, marginRight: 18}}>
          <div style={{position: 'absolute', left: `${i * 6}%`, width: `${(90 - i * 6) * grow}%`, top: 0, bottom: 0, background: c, opacity: 0.85}} />
        </div>
      </div>
    ))}
    <div style={{position: 'absolute'}} />
  </div>
);

// full-screen layer stack (shot 13)
export const LayerStack: React.FC = () => {
  const f = useCurrentFrame();
  const ph = lin(f, 0, 30, 0.05, 0.85, (t) => t);
  return (
    <AbsoluteFill style={{background: '#0f0f11', fontFamily: F.mono, paddingTop: 200}}>
      <div style={{display: 'flex', padding: '0 30px 18px', color: C.yellow, fontSize: 34}}>0:00:{String(Math.floor(ph * 90)).padStart(2, '0')}:12</div>
      <div style={{position: 'relative'}}>
        {LAYERS.map(([n, c], i) => {
          const p = lin(f, i * 2.5, i * 2.5 + 10);
          return (
            <div key={n} style={{display: 'flex', alignItems: 'center', height: 110, borderBottom: `1px solid ${C.rule}`, opacity: p, transform: `translateY(${(1 - p) * 60}px)`}}>
              <div style={{width: 330, padding: '0 30px', fontSize: 28, color: '#cfcdc5', display: 'flex', gap: 16, alignItems: 'center'}}>
                <div style={{width: 18, height: 18, background: c}} />
                {n}
              </div>
              <div style={{flex: 1, position: 'relative', height: 50, marginRight: 30}}>
                <div style={{position: 'absolute', left: `${(i * 7) % 30}%`, width: `${(70 - (i * 5) % 30) * p}%`, top: 0, bottom: 0, background: c, borderRadius: 4}} />
              </div>
            </div>
          );
        })}
        <div style={{position: 'absolute', top: -20, bottom: 0, left: `calc(330px + ${ph * 100 * 0.62}%)`, width: 3, background: C.yellow, boxShadow: '0 0 12px rgba(242,197,0,0.8)'}} />
      </div>
    </AbsoluteFill>
  );
};

// keyframe streak timeline (shot 19)
export const KeyframeStreak: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const zoom = interpolate(f, [0, dur], [1, 1.5], clamp);
  const pan = f * 26;
  const tracks = [C.yellow, C.chalk, C.blue, C.red, C.magenta, '#7BD389', '#9a8cff', C.yellow, C.chalk, C.red];
  return (
    <AbsoluteFill style={{background: '#0f0f11', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom}) rotate(-4deg)`, top: 200}}>
        {tracks.map((c, i) => (
          <div key={i} style={{position: 'absolute', left: -200, right: -200, top: 120 + i * 150, height: 54}}>
            <div style={{position: 'absolute', inset: 0, background: c, opacity: 0.22, borderRadius: 6}} />
            {Array.from({length: 26}).map((_, k) => {
              const x = ((k * 190 + rnd(i * 31 + k) * 120 - pan * (0.7 + (i % 3) * 0.25)) % 5000 + 5000) % 5000 - 300;
              const streak = Math.min(220, 26 * (0.7 + (i % 3) * 0.25) * 4);
              return (
                <div key={k} style={{position: 'absolute', left: x, top: 10}}>
                  <div style={{position: 'absolute', left: 30, top: 14, width: streak, height: 6, background: `linear-gradient(90deg, ${c}, transparent)`, opacity: 0.6}} />
                  <div style={{width: 34, height: 34, background: c, transform: 'rotate(45deg)', boxShadow: `0 0 14px ${c}`}} />
                </div>
              );
            })}
          </div>
        ))}
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 0, bottom: 0, left: 520, width: 4, background: C.yellow, boxShadow: '0 0 20px rgba(242,197,0,0.9)'}} />
    </AbsoluteFill>
  );
};

// project panel file cascade (shot 17)
const FILES = [
  ['▾', '01_REFERENCES', 0],
  ['', 'f1_weekend_brief.txt', 1],
  ['▾', '02_FOOTAGE', 0],
  ['', 'GT3RS_white.mov', 1],
  ['', '750S_Spider.mov', 1],
  ['', 'Huracan_STO_strip.mp4', 1],
  ['', 'Sphere_night.mov', 1],
  ['▾', '03_ASSETS', 0],
  ['', 'SE_race_badge.svg', 1],
  ['', 'vegas_route.json', 1],
  ['', 'REV_sprite.png', 1],
  ['▸', '04_RENDERS', 0],
] as const;

export const ProjectPanel: React.FC = () => {
  const f = useCurrentFrame();
  const whip = interpolate(f, [0, 7], [900, 0], {...clamp, easing: (t) => 1 - (1 - t) ** 3});
  const blur = interpolate(f, [0, 7], [40, 0], clamp);
  return (
    <AbsoluteFill style={{background: '#0f0f11', transform: `translateX(${whip}px)`, filter: `blur(${blur}px)`}}>
      <div style={{marginTop: 220, marginLeft: 50, marginRight: 50, background: C.panel, border: `1px solid ${C.rule}`, fontFamily: F.mono}}>
        <div style={{padding: '18px 24px', borderBottom: `1px solid ${C.rule}`, color: C.chalk, fontSize: 26}}>Project</div>
        <div style={{padding: '14px 24px', borderBottom: `1px solid ${C.rule}`, display: 'flex', gap: 12, alignItems: 'center'}}>
          <div style={{flex: 1, height: 44, background: '#0c0c0e', borderRadius: 6, color: C.mute, fontSize: 22, display: 'flex', alignItems: 'center', padding: '0 14px'}}>⌕ search</div>
        </div>
        {FILES.map(([icon, name, ind], i) => {
          const p = lin(f, 5 + i * 1.3, 11 + i * 1.3);
          const isFolder = !ind;
          return (
            <div key={name} style={{display: 'flex', alignItems: 'center', gap: 14, height: 66, padding: `0 24px 0 ${24 + ind * 44}px`, fontSize: 26, color: isFolder ? C.chalk : '#bdbbb4', opacity: p, transform: `translateX(${(1 - p) * 40}px)`}}>
              <span style={{width: 18, color: C.mute}}>{icon}</span>
              <div style={{width: 26, height: 20, background: isFolder ? C.yellow : name.endsWith('.svg') || name.endsWith('.png') ? C.red : name.endsWith('.json') || name.endsWith('.txt') ? C.mute : C.blue, borderRadius: 3}} />
              <span style={{flex: 1}}>{name}</span>
              <div style={{width: 18, height: 18, borderRadius: 3, background: '#4ad66d'}} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// asset board (shot 18)
export const AssetBoard: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tile = (i: number) => spring({frame: f - i * 3, fps, config: {damping: 11, stiffness: 200}});
  const route = evolvePath(lin(f, 10, 34), 'M 20 200 C 90 40, 170 260, 250 110 S 330 30, 380 90');
  const T: React.CSSProperties = {background: C.panel, border: `1px solid ${C.rule}`, borderRadius: 18, position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center'};
  const lbl = (t: string) => <div style={{position: 'absolute', left: 18, bottom: 14, fontFamily: F.mono, fontSize: 20, color: C.mute}}>{t}</div>;
  return (
    <AbsoluteFill style={{background: '#0f0f11', backgroundImage: 'radial-gradient(rgba(255,255,255,0.06) 1.5px, transparent 1.5px)', backgroundSize: '36px 36px', padding: '230px 44px 140px', display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr 1fr', gap: 26}}>
      <div style={{...T, transform: `scale(${tile(0)})`}}>
        <svg width="380" height="380" viewBox="-190 -190 380 380">
          {Array.from({length: 20}).map((_, i) => (
            <path key={i} d="M 0 0 L -14 -190 L 14 -190 Z" fill={i % 2 ? C.yellow : '#2a2a2e'} transform={`rotate(${i * 18 + f * 3})`} />
          ))}
          <circle r="54" fill={C.asphalt} stroke={C.yellow} strokeWidth="8" />
        </svg>
        {lbl('sunburst.ae')}
      </div>
      <div style={{...T, transform: `scale(${tile(1)})`, padding: 22, flexDirection: 'column'}}>
        <div style={{width: '100%', height: '78%', borderRadius: 10, overflow: 'hidden', border: `4px solid ${C.chalk}`}}>
          <Still src="gt3_side" />
        </div>
        <div style={{fontFamily: F.display, fontSize: 30, color: C.chalk, marginTop: 12, alignSelf: 'flex-start'}}>911 GT3 RS</div>
      </div>
      <div style={{...T, transform: `scale(${tile(2)})`}}>
        <svg width="200" height="260" viewBox="0 0 100 130" style={{transform: `translateY(${Math.sin(f * 0.25) * 10}px)`}}>
          <path d="M50 125 C 50 125 8 72 8 46 A 42 42 0 1 1 92 46 C 92 72 50 125 50 125 Z" fill={C.red} stroke={C.asphalt} strokeWidth="5" />
          <circle cx="50" cy="46" r="17" fill={C.chalk} />
        </svg>
        {lbl('pin.svg')}
      </div>
      <div style={{...T, transform: `scale(${tile(3)})`}}>
        <svg width="400" height="260" viewBox="0 0 400 260">
          <path d="M 20 200 C 90 40, 170 260, 250 110 S 330 30, 380 90" stroke="#333" strokeWidth="14" fill="none" strokeLinecap="round" />
          <path d="M 20 200 C 90 40, 170 260, 250 110 S 330 30, 380 90" stroke={C.yellow} strokeWidth="14" fill="none" strokeLinecap="round" strokeDasharray={route.strokeDasharray} strokeDashoffset={route.strokeDashoffset} />
        </svg>
        {lbl('route.path')}
      </div>
      <div style={{...T, transform: `scale(${tile(4)})`}}>
        <svg width="320" height="240" viewBox="-160 -170 320 240">
          <path d="M -130 0 A 130 130 0 0 1 130 0" stroke="#333" strokeWidth="22" fill="none" />
          <path d="M -130 0 A 130 130 0 0 1 130 0" stroke={C.yellow} strokeWidth="22" fill="none" strokeDasharray="410" strokeDashoffset={410 * (1 - lin(f, 8, 34) * 0.92)} />
          <line x1="0" y1="0" x2={-110 * Math.cos(lin(f, 8, 34) * Math.PI * 0.92)} y2={-110 * Math.sin(lin(f, 8, 34) * Math.PI * 0.92)} stroke={C.chalk} strokeWidth="8" strokeLinecap="round" />
          <circle r="14" fill={C.chalk} />
        </svg>
        {lbl('gauge.ae')}
      </div>
      <div style={{...T, transform: `scale(${tile(5)})`}}>
        <svg width="260" height="200" viewBox="0 0 260 200">
          {Array.from({length: 6}).flatMap((_, x) =>
            Array.from({length: 4}).map((__, y) => {
              const wave = Math.sin(f * 0.3 + x * 0.7) * 10;
              return <rect key={x + '-' + y} x={20 + x * 36} y={20 + y * 36 + wave} width="36" height="36" fill={(x + y) % 2 ? C.asphalt : C.chalk} />;
            }),
          )}
        </svg>
        {lbl('flag.ae')}
      </div>
    </AbsoluteFill>
  );
};
