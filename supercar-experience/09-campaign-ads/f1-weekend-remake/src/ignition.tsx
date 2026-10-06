import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {noise2D} from '@remotion/noise';
import {C, F, lin} from './theme';
import {Flash, Plate} from './core';
import {Badge} from './editor';
import {REV_ENV} from './rev_env';

// Shot 30 "Ignition" (replaced the yellow RACE WEEKEND poster, 2026-10-05). The GT3 RS start-up carries the shot on
// its own engine sound; the graphics borrow the race-weekend Night grammar (black scrim band, flat chequer band,
// lock-on gate, sector strip) in this ad's yellow/asphalt palette. Text stays inside the 4:5 band (y 285-1635).
const FIRE = 36; // the engine fires on this frame (src 3.20 s); the 30 s cut's music drop lands here too
const LAUNCH = 60; // cut to the car launching down the tunnel (src 8.592 s)
const SCENE = 84; // the clip's own cut to the tracking shot (src 9.384 s)
const PUSH: [number, number] = [1.0, 1.04];

type Box = [number, number, number, number];
// where the car sits in the plate (measured on frames 64, 78, 90, 108), before the push
const GATE: [number, Box][] = [
  [LAUNCH, [70, 620, 1010, 1150]],
  [SCENE - 1, [140, 665, 940, 1115]],
  [SCENE, [140, 800, 960, 1215]],
  [120, [140, 815, 955, 1215]],
];

const gateAt = (f: number, dur: number): Box => {
  let k = 0;
  while (k < GATE.length - 2 && f >= GATE[k + 1][0]) k++;
  const [fa, a] = GATE[k];
  const [fb, b] = GATE[k + 1];
  const t = Math.max(0, Math.min(1, (f - fa) / Math.max(1, fb - fa)));
  const sc = PUSH[0] + (PUSH[1] - PUSH[0]) * (f / dur);
  return a.map((v, i) => {
    const raw = v + (b[i] - v) * t;
    const c = i % 2 ? 960 : 540;
    return c + (raw - c) * sc;
  }) as Box;
};

const Typed: React.FC<{text: string; at: number; cps?: number; style: React.CSSProperties}> = ({text, at, cps = 2, style}) => {
  const f = useCurrentFrame();
  const n = Math.max(0, Math.min(text.length, Math.floor((f - at) * cps)));
  return <span style={{whiteSpace: 'pre', ...style}}>{text.slice(0, n)}</span>;
};

const Chequer: React.FC<{y: number; at: number; h?: number}> = ({y, at, h = 28}) => {
  const f = useCurrentFrame();
  const w = lin(f, at, at + 8) * 1080;
  const sq = h / 2;
  return (
    <div style={{position: 'absolute', left: 0, top: y, width: w, height: h, overflow: 'hidden'}}>
      <svg width={1080} height={h}>
        {Array.from({length: Math.ceil(1080 / sq) * 2}).map((_, i) => {
          const col = Math.floor(i / 2), row = i % 2;
          return <rect key={i} x={col * sq} y={row * sq} width={sq} height={sq} fill={(col + row) % 2 ? C.chalk : C.asphalt} />;
        })}
      </svg>
    </div>
  );
};

// lock-on gate: four corner brackets close onto the car with an overshoot, re-lock when the clip cuts
const Gate: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < LAUNCH + 2) return null;
  const relock = f >= SCENE;
  const sp = spring({frame: f - (relock ? SCENE : LAUNCH + 2), fps, config: {damping: 11, stiffness: 240}});
  const open = (1 - sp) * (relock ? 60 : 140);
  const [x0, y0, x1, y1] = gateAt(f, dur);
  const arm = 74, th = 7;
  const corners = [
    [x0 - open, y0 - open, 1, 1],
    [x1 + open, y0 - open, -1, 1],
    [x0 - open, y1 + open, 1, -1],
    [x1 + open, y1 + open, -1, -1],
  ];
  const lab = lin(f, LAUNCH + 6, LAUNCH + 12);
  return (
    <>
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, opacity: Math.min(1, sp * 1.6)}}>
        {corners.map(([x, y, sx, sy], i) => (
          <path key={i} d={`M ${x} ${y + sy * arm} L ${x} ${y} L ${x + sx * arm} ${y}`} stroke={C.yellow} strokeWidth={th} fill="none" strokeLinecap="square" />
        ))}
        {/* centre tick */}
        <path d={`M ${(x0 + x1) / 2 - 18} ${(y0 + y1) / 2} h 36 M ${(x0 + x1) / 2} ${(y0 + y1) / 2 - 18} v 36`} stroke={C.yellow} strokeWidth={3} opacity={0.6 * sp} />
      </svg>
      {/* LOCK tag on the top-right corner */}
      <div style={{position: 'absolute', left: x1 - 118, top: y0 - 50, background: C.yellow, padding: '4px 12px', fontFamily: F.mono, fontWeight: 500, fontSize: 24, letterSpacing: 3, color: C.asphalt, opacity: sp > 0.8 ? 1 : 0}}>
        LOCK
      </div>
      {/* car label: only on this car's own shot, held well over 1 s */}
      <div style={{position: 'absolute', left: x0, top: y0 - 104, opacity: lab, display: 'flex', flexDirection: 'column', gap: 6}}>
        <div style={{background: C.asphalt, padding: '6px 14px', alignSelf: 'flex-start'}}>
          <Typed text="PORSCHE 911 GT3 RS" at={LAUNCH + 6} cps={3} style={{fontFamily: F.mono, fontWeight: 500, fontSize: 30, letterSpacing: 2, color: C.chalk}} />
        </div>
        <div style={{padding: '0 14px'}}>
          <Typed text="LAS VEGAS FLEET · AVAILABLE" at={LAUNCH + 12} cps={3} style={{fontFamily: F.mono, fontSize: 24, letterSpacing: 2, color: C.yellow, textShadow: '0 2px 10px rgba(0,0,0,0.9)'}} />
        </div>
      </div>
    </>
  );
};

const SECTORS = ['S1 THU', 'S2 FRI', 'S3 SAT', 'RACE NIGHT'];
const SectorStrip: React.FC<{y: number}> = ({y}) => {
  const f = useCurrentFrame();
  if (f < LAUNCH + 2) return null;
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: y, display: 'flex', gap: 8, opacity: lin(f, LAUNCH + 2, LAUNCH + 6)}}>
      {SECTORS.map((s, i) => {
        const at = LAUNCH + 4 + i * 5;
        const on = f >= at;
        const last = i === SECTORS.length - 1;
        const flash = on ? Math.max(0, 1 - (f - at) / 5) : 0;
        return (
          <div key={s} style={{flex: last ? 1.5 : 1, height: 54, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `2px solid ${on ? 'transparent' : 'rgba(245,243,238,0.45)'}`, background: on ? (last ? C.red : C.yellow) : 'rgba(11,11,12,0.55)', boxShadow: flash ? `0 0 ${30 * flash}px ${last ? C.red : C.yellow}` : 'none'}}>
            <span style={{fontFamily: F.mono, fontWeight: 500, fontSize: 26, letterSpacing: 2, color: on ? (last ? C.chalk : C.asphalt) : 'rgba(245,243,238,0.7)'}}>{s}</span>
          </div>
        );
      })}
    </div>
  );
};

// rev meter driven by the clip's own engine loudness (src/rev_env.ts): idles until the engine fires. No rpm or hp
// numbers anywhere: SE is a client and ads carry no performance figure we can't back up (deliver-to-dropbox rule)
const RevMeter: React.FC<{y: number}> = ({y}) => {
  const f = useCurrentFrame();
  const N = 28, RED = 23;
  const env = REV_ENV[Math.min(REV_ENV.length - 1, Math.max(0, f))] ?? 0;
  const idle = 0.1 + 0.03 * noise2D('idle', f * 0.3, 0);
  const v = f < FIRE - 2 ? idle : Math.max(idle, lin(env, 0.45, 1, 0.25, 1, (t) => t));
  const lit = Math.round(v * N);
  return (
    <div style={{position: 'absolute', left: 60, top: y, width: 960, opacity: lin(f, 2, 8)}}>
      <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: F.pixel, fontSize: 22, color: C.chalk, marginBottom: 10, textShadow: '0 2px 8px rgba(0,0,0,0.9)'}}>
        <span>ENGINE</span>
        <span style={{color: lit >= RED ? C.red : C.yellow}}>{f < FIRE ? 'IDLE' : lit >= RED ? 'REDLINE' : 'REVVING'}</span>
      </div>
      <div style={{display: 'flex', gap: 4}}>
        {Array.from({length: N}).map((_, i) => (
          <div key={i} style={{flex: 1, height: 26, background: i < lit ? (i >= RED ? C.red : i >= RED - 6 ? C.yellow : C.chalk) : 'rgba(245,243,238,0.14)'}} />
        ))}
      </div>
      <div style={{display: 'flex', justifyContent: 'space-between', marginTop: 6, fontFamily: F.pixel, fontSize: 18, color: C.mute}}>
        <span>IDLE</span><span>REDLINE</span>
      </div>
    </div>
  );
};

export const Ignition: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  // engine-start jolt
  const j = f >= FIRE && f < FIRE + 14 ? (1 - (f - FIRE) / 14) * 16 : 0;
  // HUD tags over the start button and the dial
  const hud = f < FIRE ? lin(f, 2, 6) * (1 - lin(f, FIRE - 3, FIRE)) : 0;
  // RACE WEEKEND: two-line slam on the engine start, one line once the car launches
  const big = f >= FIRE && f < LAUNCH;
  const slam = spring({frame: f - FIRE, fps, config: {damping: 9, stiffness: 300}});
  const sh = big ? Math.max(0, 1 - (f - FIRE) / 12) * 20 : 0;
  const band = lin(f, FIRE, FIRE + 4);
  const small = lin(f, LAUNCH, LAUNCH + 6);
  const stamp = spring({frame: f - 88, fps, config: {damping: 10, stiffness: 260}});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{transform: `translate(${noise2D('jx', f * 0.9, 0) * j}px, ${noise2D('jy', f * 0.9, 1) * j}px)`}}>
        <Plate id={30} len={dur} push={PUSH} grade="night" />
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(11,11,12,0.7) 0%, rgba(11,11,12,0) 34%, rgba(11,11,12,0) 62%, rgba(11,11,12,0.75) 100%)'}} />

      {/* HUD: ignition, then the drive mode */}
      {hud > 0 && (
        <div style={{position: 'absolute', left: 60, top: 300, display: 'flex', flexDirection: 'column', gap: 12, opacity: hud}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 14, background: 'rgba(11,11,12,0.75)', padding: '10px 18px', alignSelf: 'flex-start'}}>
            <div style={{width: 16, height: 16, borderRadius: 8, background: C.red, opacity: Math.floor(f / 5) % 2 ? 1 : 0.3}} />
            <Typed text="IGNITION" at={3} style={{fontFamily: F.mono, fontWeight: 500, fontSize: 32, letterSpacing: 5, color: C.chalk}} />
          </div>
          {f >= 15 && (
            <div style={{background: C.yellow, padding: '10px 18px', alignSelf: 'flex-start'}}>
              <Typed text="MODE · SPORT" at={15} style={{fontFamily: F.mono, fontWeight: 500, fontSize: 32, letterSpacing: 5, color: C.asphalt}} />
            </div>
          )}
        </div>
      )}

      {/* title: black scrim band + flat chequer band */}
      {big && (
        <>
          <div style={{position: 'absolute', left: 0, top: 296, width: 1080 * band, height: 352, background: 'rgba(11,11,12,0.9)'}} />
          <div style={{position: 'absolute', left: 60, top: 334, fontFamily: F.display, fontSize: 150, lineHeight: 0.92, letterSpacing: -4,
                       transform: `translate(${noise2D('ta', f, 0) * sh}px, ${noise2D('tb', f, 0) * sh}px) scale(${1.5 - slam * 0.5})`, transformOrigin: '40% 50%', opacity: Math.min(1, slam * 2)}}>
            <div style={{color: C.chalk}}>RACE</div>
            <div style={{color: C.yellow}}>WEEKEND</div>
          </div>
          <Chequer y={648} at={FIRE + 2} />
        </>
      )}
      {f >= LAUNCH && (
        <>
          <div style={{position: 'absolute', left: 0, top: 296, width: 1080, height: 124, background: 'rgba(11,11,12,0.9)', transform: `translateY(${(1 - small) * -16}px)`}} />
          <div style={{position: 'absolute', left: 60, top: 306, fontFamily: F.display, fontSize: 92, letterSpacing: -2, whiteSpace: 'nowrap', transform: `translateY(${(1 - small) * -16}px)`}}>
            <span style={{color: C.chalk}}>RACE </span>
            <span style={{color: C.yellow}}>WEEKEND</span>
          </div>
          <Chequer y={420} at={LAUNCH} h={20} />
        </>
      )}
      <SectorStrip y={462} />
      <Gate dur={dur} />

      {/* rental line */}
      <div style={{position: 'absolute', left: 60, top: 1296, width: 680, opacity: lin(f, 70, 80), transform: `translateY(${(1 - lin(f, 70, 80)) * 24}px)`}}>
        <div style={{fontFamily: F.display, fontSize: 52, lineHeight: 1.02, color: C.chalk, textShadow: '0 3px 18px rgba(0,0,0,0.85)'}}>BOOK IT FOR THE WEEKEND</div>
        <div style={{fontFamily: F.mono, fontWeight: 500, fontSize: 26, letterSpacing: 3, color: C.yellow, marginTop: 12, textShadow: '0 2px 10px rgba(0,0,0,0.9)'}}>PICK UP IN LAS VEGAS</div>
      </div>
      <RevMeter y={1520} />

      {/* the pass stamps */}
      {f >= 88 && (
        <div style={{position: 'absolute', left: 792, top: 1262, transform: `scale(${2.2 - stamp * 1.2}) rotate(${-12 + stamp * 4}deg)`, opacity: Math.min(1, stamp * 2)}}>
          <Badge at={0} size={220} full />
        </div>
      )}
      <Flash at={FIRE} peak={0.45} len={5} />
    </AbsoluteFill>
  );
};
