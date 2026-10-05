import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {noise2D} from '@remotion/noise';
import {C, F, clamp, lin, rnd} from './theme';

// ---------- footage plate with camera move + grade ----------
export const Plate: React.FC<{
  id: number;
  push?: [number, number]; // scale from→to across the shot
  drift?: [number, number]; // x px from→to
  grade?: 'none' | 'night' | 'hot' | 'cool';
  dim?: number;
  shake?: number;
  len: number;
}> = ({id, push = [1.04, 1.1], drift = [0, 0], grade = 'none', dim = 0, shake = 0, len}) => {
  const f = useCurrentFrame();
  const p = f / Math.max(1, len);
  const sc = interpolate(p, [0, 1], push);
  const dx = interpolate(p, [0, 1], drift);
  const sx = shake ? noise2D('sx', f * 0.25, 0) * shake : 0;
  const sy = shake ? noise2D('sy', f * 0.25, 1) * shake : 0;
  const filter =
    grade === 'hot'
      ? 'saturate(1.6) contrast(1.15) sepia(0.35) hue-rotate(-12deg) brightness(1.05)'
      : grade === 'night'
        ? 'saturate(1.15) contrast(1.08)'
        : grade === 'cool'
          ? 'saturate(0.9) hue-rotate(8deg) contrast(1.05)'
          : 'contrast(1.04)';
  return (
    <AbsoluteFill style={{background: C.asphalt, overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${dx + sx}px, ${sy}px) scale(${sc})`}}>
        <OffthreadVideo src={staticFile(`plates/s${String(id).padStart(2, '0')}.mp4`)} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter}} />
      </AbsoluteFill>
      {grade === 'hot' && <AbsoluteFill style={{background: 'radial-gradient(circle at 40% 45%, rgba(255,140,30,0.35), rgba(120,20,0,0.35))', mixBlendMode: 'overlay'}} />}
      {dim > 0 && <AbsoluteFill style={{background: `rgba(11,11,12,${dim})`}} />}
    </AbsoluteFill>
  );
};

export const Still: React.FC<{src: string; style?: React.CSSProperties}> = ({src, style}) => (
  <Img src={staticFile(`stills/${src}.jpg`)} style={{width: '100%', height: '100%', objectFit: 'cover', ...style}} />
);

// ---------- film grain + vignette ----------
export const Finish: React.FC<{vignette?: boolean}> = ({vignette = true}) => {
  const f = useCurrentFrame();
  return (
    <>
      {vignette && <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0) 52%, rgba(0,0,0,0.55) 100%)'}} />}
      <AbsoluteFill style={{opacity: 0.07, mixBlendMode: 'overlay'}}>
        <svg width="100%" height="100%">
          <filter id="gr">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 30} />
          </filter>
          <rect width="100%" height="100%" filter="url(#gr)" />
        </svg>
      </AbsoluteFill>
    </>
  );
};

// ---------- persistent handle bug (top right) ----------
export const HandleBug: React.FC<{dark?: boolean; opacity?: number}> = ({dark, opacity = 1}) => (
  <div style={{position: 'absolute', top: 92, right: 56, display: 'flex', alignItems: 'center', gap: 14, opacity}}>
    <Img src={staticFile('brand/mono.svg')} style={{height: 30, filter: dark ? 'invert(1)' : 'none'}} />
    <div style={{fontFamily: F.ui, fontWeight: 700, fontSize: 22, letterSpacing: 1.5, color: dark ? C.asphalt : C.chalk}}>@SUPERCAR_EXPERIENCE_</div>
  </div>
);

// ---------- phone message bubble ----------
export const TextBubble: React.FC<{at: number; text: string; y?: number; typingFrom?: number}> = ({at, text, y = 640, typingFrom}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f - at, fps, config: {damping: 13, stiffness: 190}});
  const typing = typingFrom !== undefined && f >= typingFrom && f < at;
  return (
    <div style={{position: 'absolute', left: 64, top: y, width: 760}}>
      <div style={{fontFamily: F.ui, fontSize: 24, color: 'rgba(245,243,238,0.75)', textAlign: 'center', marginBottom: 16, opacity: lin(f, (typingFrom ?? at) - 4, (typingFrom ?? at) + 4)}}>
        <b style={{color: C.chalk}}>Today</b> 9:41 PM
      </div>
      {typing && (
        <div style={{display: 'inline-flex', gap: 10, padding: '26px 30px', background: 'rgba(235,235,240,0.92)', borderRadius: 36, borderBottomLeftRadius: 10}}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{width: 15, height: 15, borderRadius: 8, background: '#7a7a80', opacity: 0.35 + 0.65 * Math.max(0, Math.sin(f * 0.5 - i))}} />
          ))}
        </div>
      )}
      {f >= at && (
        <div
          style={{
            display: 'inline-block',
            padding: '26px 34px',
            background: 'rgba(240,240,244,0.96)',
            color: '#111',
            borderRadius: 38,
            borderBottomLeftRadius: 10,
            fontFamily: F.ui,
            fontWeight: 500,
            fontSize: 40,
            lineHeight: 1.25,
            maxWidth: 720,
            transformOrigin: '0% 100%',
            transform: `scale(${0.5 + sp * 0.5})`,
            opacity: Math.min(1, sp * 1.6),
            boxShadow: '0 16px 50px rgba(0,0,0,0.35)',
          }}
        >
          {text}
        </div>
      )}
      {f >= at && <div style={{fontFamily: F.ui, fontSize: 22, color: 'rgba(245,243,238,0.7)', marginTop: 10, marginLeft: 14, opacity: lin(f, at + 6, at + 14)}}>Client</div>}
    </div>
  );
};

// ---------- concierge prompt bar (typewriter) ----------
export const PromptBar: React.FC<{text: string; typeAt: number; cps?: number; sendAt?: number; y?: number}> = ({text, typeAt, cps = 1.25, sendAt, y = 1560}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const inn = spring({frame: f - (typeAt - 8), fps, config: {damping: 16, stiffness: 160}});
  const n = Math.max(0, Math.min(text.length, Math.floor((f - typeAt) * cps)));
  const done = n >= text.length;
  const sent = sendAt !== undefined && f >= sendAt;
  const glow = sent ? interpolate(f - sendAt!, [0, 6, 22], [0, 1, 0.35], clamp) : done ? 0.3 + 0.2 * Math.sin(f * 0.4) : 0;
  return (
    <div
      style={{
        position: 'absolute',
        left: 48,
        right: 48,
        top: y,
        transform: `translateY(${(1 - inn) * 140}px)`,
        opacity: inn,
        background: 'rgba(22,22,24,0.82)',
        border: '1.5px solid rgba(255,255,255,0.14)',
        borderRadius: 34,
        padding: '26px 30px 22px',
        backdropFilter: 'blur(18px)',
        boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
      }}
    >
      <div style={{fontFamily: F.ui, fontSize: 34, lineHeight: 1.3, color: C.chalk, minHeight: 88}}>
        {text.slice(0, n)}
        {!sent && <span style={{opacity: Math.floor(f / 8) % 2 ? 1 : 0, color: C.yellow}}>|</span>}
      </div>
      <div style={{display: 'flex', alignItems: 'center', gap: 22, marginTop: 10}}>
        <div style={{fontFamily: F.ui, fontSize: 40, color: C.mute, lineHeight: 1}}>+</div>
        <div style={{flex: 1}} />
        <div style={{fontFamily: F.ui, fontSize: 22, color: C.mute}}>SE Concierge</div>
        <svg width="26" height="30" viewBox="0 0 24 28"><rect x="7" y="1" width="10" height="17" rx="5" fill="none" stroke={C.mute} strokeWidth="2.4" /><path d="M3 13a9 9 0 0 0 18 0M12 22v5" stroke={C.mute} strokeWidth="2.4" fill="none" strokeLinecap="round" /></svg>
        <div
          style={{
            width: 62,
            height: 62,
            borderRadius: 31,
            background: done ? C.yellow : '#3a3a3e',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 0 ${10 + glow * 60}px ${glow * 18}px rgba(242,197,0,${glow * 0.6})`,
            transform: `scale(${sent ? 1 + 0.18 * Math.max(0, 1 - (f - sendAt!) / 8) : 1})`,
          }}
        >
          <svg width="28" height="28" viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7" stroke={done ? C.asphalt : '#888'} strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </div>
      </div>
    </div>
  );
};

// ---------- white status card (agent working) ----------
export const StatusCard: React.FC<{lines: [string, string?]; chip?: string; dur: number}> = ({lines, chip, dur}) => {
  const f = useCurrentFrame();
  const spin = lin(f, 0, 14);
  const t1 = lin(f, 3, 16);
  const t2 = lin(f, 9, 22);
  const out = lin(f, dur - 6, dur);
  const shimmer = (f * 18) % 1400;
  return (
    <AbsoluteFill style={{background: C.paper, justifyContent: 'center', padding: '0 90px', opacity: 1 - out * 0.0}}>
      <div style={{display: 'flex', gap: 28, alignItems: 'flex-start', transform: `translateY(${-out * 30}px)`, opacity: 1 - out}}>
        <Img src={staticFile('brand/mono.svg')} style={{width: 64, marginTop: 6, filter: 'invert(1)', transform: `rotate(${(1 - spin) * -180}deg) scale(${0.4 + spin * 0.6})`, opacity: spin}} />
        <div style={{fontFamily: F.ui, fontSize: 50, lineHeight: 1.18, letterSpacing: -0.5}}>
          <div style={{color: '#151515', fontWeight: 600, opacity: t1, filter: `blur(${(1 - t1) * 10}px)`}}>{lines[0]}</div>
          {lines[1] && <div style={{color: '#55534e', opacity: t2, filter: `blur(${(1 - t2) * 10}px)`}}>{lines[1]}</div>}
          {chip && (
            <div style={{display: 'flex', alignItems: 'center', gap: 16, marginTop: 26, opacity: lin(f, 8, 18), transform: `translateX(${(1 - lin(f, 8, 22)) * -30}px)`}}>
              <div style={{width: 44, height: 44, borderRadius: 11, background: C.yellow, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <Img src={staticFile('brand/mono.svg')} style={{width: 26, filter: 'invert(1)'}} />
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 500,
                  backgroundImage: `linear-gradient(90deg, #6b6963 0px, #6b6963 ${shimmer - 200}px, ${C.yellowDeep} ${shimmer}px, #6b6963 ${shimmer + 200}px)`,
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
                }}
              >
                {chip}
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- floating caption words ----------
export const FloatWords: React.FC<{words: {t: string; at: number; x: number; y: number; size?: number; rot?: number}[]; out?: number}> = ({words, out}) => {
  const f = useCurrentFrame();
  return (
    <>
      {words.map((w, i) => {
        const p = lin(f, w.at, w.at + 8);
        const o = out !== undefined ? 1 - lin(f, out, out + 6) : 1;
        if (f < w.at) return null;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: w.x,
              top: w.y - (f - w.at) * 0.4,
              fontFamily: F.ui,
              fontWeight: 700,
              fontSize: w.size ?? 58,
              color: C.chalk,
              textShadow: '0 4px 24px rgba(0,0,0,0.6)',
              transform: `rotate(${w.rot ?? 0}deg) scale(${0.6 + p * 0.4})`,
              opacity: p * o,
              filter: `blur(${(1 - p) * 8}px)`,
              whiteSpace: 'nowrap',
            }}
          >
            {w.t}
          </div>
        );
      })}
    </>
  );
};

// ---------- flash / whip helpers ----------
export const Flash: React.FC<{at: number; color?: string; peak?: number; len?: number}> = ({at, color = '#fff', peak = 0.9, len = 6}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [at - 1, at, at + len], [0, peak, 0], clamp);
  if (o <= 0) return null;
  return <AbsoluteFill style={{background: color, opacity: o}} />;
};

// cheap bokeh / dust particles (procedural)
export const Bokeh: React.FC<{n?: number; color?: string; speed?: number; seed?: number}> = ({n = 22, color = 'rgba(255,220,140,', speed = 1, seed = 0}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {Array.from({length: n}).map((_, i) => {
        const r = 20 + rnd(i + seed) * 90;
        const x = rnd(i * 3 + seed) * 1180 - 50 + Math.sin(f * 0.02 + i) * 30 * speed;
        const y = ((rnd(i * 7 + seed) * 2100 - f * (0.6 + rnd(i) * 1.4) * speed) % 2100 + 2100) % 2100 - 90;
        return <div key={i} style={{position: 'absolute', left: x, top: y, width: r, height: r, borderRadius: r, background: `${color}${0.08 + rnd(i * 11) * 0.18})`, filter: `blur(${4 + rnd(i * 5) * 10}px)`}} />;
      })}
    </AbsoluteFill>
  );
};
