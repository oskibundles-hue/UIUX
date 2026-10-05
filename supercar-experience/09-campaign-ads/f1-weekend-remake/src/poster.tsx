import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, F, clamp, lin, rnd} from './theme';
import {Still} from './core';
import {Badge} from './editor';

// custom frame shape: notched corners + tab
const FRAME = 'polygon(0 6%, 6% 0, 40% 0, 44% 3%, 94% 3%, 100% 9%, 100% 94%, 94% 100%, 8% 100%, 0 92%)';

// glow ring reveal (shot 29)
export const GlowReveal: React.FC = () => {
  const f = useCurrentFrame();
  const ring = lin(f, 0, 16);
  const open = lin(f, 10, 30);
  return (
    <AbsoluteFill style={{background: C.asphalt, alignItems: 'center', justifyContent: 'center'}}>
      {/* frame outline draws */}
      <div style={{position: 'absolute', width: 920, height: 1180, border: `3px solid rgba(245,243,238,${0.25 + 0.5 * ring})`, clipPath: FRAME, opacity: ring}} />
      <div style={{position: 'absolute', width: 920, height: 1180, clipPath: FRAME, overflow: 'hidden'}}>
        <div style={{position: 'absolute', inset: 0, clipPath: `circle(${open * 75}% at 50% 50%)`}}>
          <Still src="gt3_garage" style={{transform: `scale(${1.25 - open * 0.15})`}} />
        </div>
      </div>
      {/* pixel glow ring */}
      <svg width="1080" height="1920" style={{position: 'absolute', left: 0, top: 0}}>
        {Array.from({length: 72}).map((_, i) => {
          const a = (i / 72) * Math.PI * 2 + f * 0.05;
          const r = 60 + open * 640 + Math.sin(i * 2.1 + f * 0.4) * 14;
          const sz = 10 + (i % 3) * 5;
          return <rect key={i} x={540 + Math.cos(a) * r} y={960 + Math.sin(a) * r} width={sz} height={sz} fill={i % 3 ? C.yellow : '#fff6bf'} opacity={ring * (1 - lin(f, 26, 38))} style={{filter: 'drop-shadow(0 0 10px rgba(242,197,0,1))'}} />;
        })}
      </svg>
      <AbsoluteFill style={{background: 'radial-gradient(circle, rgba(242,197,0,0.35), rgba(0,0,0,0) 40%)', opacity: interpolate(f, [0, 8, 30], [0, 1, 0], clamp)}} />
    </AbsoluteFill>
  );
};

// big type-on poster (shot 30)
export const Poster: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = ['THE', 'GT3 RS'];
  let budget = Math.floor(lin(f, 2, 22, 0, 9, (t) => t));
  const caret = Math.floor(f / 6) % 2;
  const body = lin(f, 22, 34);
  const tags = ['518 HP', '9,000 RPM', 'TRACK-BRED', 'F1 WEEKEND'];
  const thumbs = ['gt3_crest', 'gt3_front', 'gt3_tunnel'];
  const stamp = spring({frame: f - 78, fps, config: {damping: 10, stiffness: 260}});
  return (
    <AbsoluteFill style={{background: C.yellow}}>
      {/* rays */}
      <svg width="1080" height="1920" style={{position: 'absolute', opacity: 0.25}}>
        {Array.from({length: 28}).map((_, i) => (
          <path key={i} d="M 760 760 L 740 -1300 L 780 -1300 Z" fill={C.yellowDeep} transform={`rotate(${i * 12.85 + f * 0.25} 760 760)`} />
        ))}
      </svg>
      {/* photo in custom frame */}
      <div style={{position: 'absolute', left: 50, top: 590, width: 980, height: 660, clipPath: FRAME, background: C.asphalt, padding: 10}}>
        <div style={{width: '100%', height: '100%', clipPath: FRAME, overflow: 'hidden'}}>
          <Still src="gt3_garage" style={{transform: `scale(${1.1 + f * 0.0015})`}} />
        </div>
      </div>
      {/* pin label on photo */}
      <div style={{position: 'absolute', left: 560, top: 1170, display: 'flex', alignItems: 'center', gap: 10, background: C.asphalt, padding: '12px 22px 12px 14px', borderRadius: 40, opacity: lin(f, 30, 38), transform: `scale(${lin(f, 30, 40, 0.6, 1)})`}}>
        <div style={{width: 28, height: 28, borderRadius: 14, background: C.red, border: `4px solid ${C.chalk}`}} />
        <div style={{fontFamily: F.ui, fontWeight: 800, fontSize: 24, color: C.chalk}}>AVAILABLE · LAS VEGAS</div>
      </div>
      {/* big type */}
      <div style={{position: 'absolute', left: 50, top: 230, fontFamily: F.display, fontSize: 176, lineHeight: 0.86, color: C.asphalt, letterSpacing: -4}}>
        {words.map((w, i) => {
          const n = Math.max(0, Math.min(w.length, budget));
          budget -= w.length;
          return (
            <div key={i} style={{height: 156, whiteSpace: 'pre'}}>
              <span style={{background: n > 0 ? C.yellow : 'transparent', paddingRight: 10}}>{w.slice(0, n)}</span>
              {n > 0 && n < w.length && caret ? <span style={{display: 'inline-block', width: 12, height: 140, background: C.asphalt, verticalAlign: 'top'}} /> : null}
            </div>
          );
        })}
      </div>
      {/* body copy */}
      <div style={{position: 'absolute', left: 56, top: 1300, width: 960, opacity: body, transform: `translateY(${(1 - body) * 30}px)`}}>
        <div style={{fontFamily: F.ui, fontWeight: 600, fontSize: 38, lineHeight: 1.3, color: C.asphalt}}>The track car you can book for race weekend. Pick it up in Las Vegas and drive the route yourself.</div>
        <div style={{display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 26}}>
          {tags.map((t, i) => {
            const sp = spring({frame: f - (34 + i * 4), fps, config: {damping: 10, stiffness: 220}});
            return (
              <div key={t} style={{fontFamily: F.ui, fontWeight: 800, fontSize: 24, padding: '10px 20px', borderRadius: 30, background: [C.asphalt, C.red, C.chalk, C.asphalt][i], color: i === 2 ? C.asphalt : C.chalk, transform: `scale(${sp})`}}>
                {t}
              </div>
            );
          })}
        </div>
      </div>
      {/* thumbnails */}
      <div style={{position: 'absolute', left: 56, top: 1600, display: 'flex', gap: 20}}>
        {thumbs.map((t, i) => {
          const sp = spring({frame: f - (52 + i * 6), fps, config: {damping: 11, stiffness: 200}});
          return (
            <div key={t} style={{width: 210, height: 210, border: `6px solid ${C.asphalt}`, background: C.asphalt, transform: `scale(${sp}) rotate(${(i - 1) * 3}deg)`, overflow: 'hidden'}}>
              <Still src={t} />
            </div>
          );
        })}
      </div>
      {/* badge stamp */}
      {f >= 78 && (
        <div style={{position: 'absolute', left: 760, top: 1560, transform: `scale(${2.2 - stamp * 1.2}) rotate(${-12 + stamp * 4}deg)`, opacity: Math.min(1, stamp * 2)}}>
          <Badge at={0} size={280} full />
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------------- title lockup (shot 1) ----------------
export const TitleLockup: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const l1 = lin(f, 0, 12);
  const big = spring({frame: f - 6, fps, config: {damping: 14, stiffness: 140}});
  const pill = spring({frame: f - 16, fps, config: {damping: 12, stiffness: 200}});
  const streak = interpolate(f, [2, 26], [-600, 1700], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div style={{position: 'absolute', top: 680, display: 'flex', alignItems: 'center', gap: 24, opacity: l1, filter: `blur(${(1 - l1) * 12}px)`}}>
        <Img src={staticFile('brand/logo.svg')} style={{height: 64}} />
        <div style={{fontFamily: F.ui, fontWeight: 400, fontSize: 40, color: C.chalk}}>×</div>
        <div style={{fontFamily: F.pixel, fontWeight: 700, fontSize: 38, color: C.yellow}}>REV</div>
      </div>
      <div
        style={{
          position: 'absolute',
          top: 790,
          fontFamily: F.display,
          fontSize: 140,
          letterSpacing: -4,
          lineHeight: 1,
          backgroundImage: 'linear-gradient(180deg, #ffffff 0%, #f5f3ee 45%, #b9b5aa 52%, #ffffff 100%)',
          WebkitBackgroundClip: 'text',
          color: 'transparent',
          transform: `scale(${0.8 + big * 0.2})`,
          opacity: big,
          filter: 'drop-shadow(0 12px 40px rgba(0,0,0,0.6))',
          whiteSpace: 'nowrap',
        }}
      >
        F1 WEEKEND
      </div>
      <div style={{position: 'absolute', top: 1010, transform: `scale(${pill})`, background: C.yellow, color: C.asphalt, fontFamily: F.ui, fontWeight: 800, fontSize: 40, padding: '12px 34px', borderRadius: 14}}>for Las Vegas</div>
      {/* light streak */}
      <div style={{position: 'absolute', top: 760, left: streak, width: 420, height: 260, background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.75), rgba(255,255,255,0))', mixBlendMode: 'overlay', transform: 'skewX(-24deg)'}} />
      <div style={{position: 'absolute', top: 1110, left: 140, right: 140, height: 3, background: `linear-gradient(90deg, transparent, ${C.yellow}, transparent)`, transform: `scaleX(${lin(f, 10, 30)})`}} />
    </AbsoluteFill>
  );
};

// ---------------- end card (shot 35) ----------------
export const EndCard: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const logo = spring({frame: f, fps, config: {damping: 14, stiffness: 120}});
  const shine = interpolate(f, [14, 44], [-30, 130], clamp);
  const out = lin(f, dur - 22, dur);
  return (
    <AbsoluteFill style={{background: C.asphalt, alignItems: 'center', justifyContent: 'center', opacity: 1 - out}}>
      <div style={{position: 'relative', transform: `scale(${0.85 + logo * 0.15})`, opacity: logo}}>
        <Img src={staticFile('brand/logo.svg')} style={{width: 800, display: 'block'}} />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `linear-gradient(100deg, transparent ${shine - 12}%, ${C.yellow} ${shine}%, transparent ${shine + 12}%)`,
            WebkitMaskImage: `url(${staticFile('brand/logo.svg')})`,
            WebkitMaskSize: '100% 100%',
            maskImage: `url(${staticFile('brand/logo.svg')})`,
            maskSize: '100% 100%',
          }}
        />
      </div>
      <div style={{marginTop: 70, fontFamily: F.ui, fontWeight: 700, fontSize: 44, letterSpacing: 2, color: C.chalk, opacity: lin(f, 10, 22)}}>@supercar_experience_</div>
      <div style={{marginTop: 60, textAlign: 'center', opacity: lin(f, 16, 28)}}>
        <div style={{fontFamily: F.display, fontSize: 64, color: C.yellow}}>TEXT OR DM TO BOOK</div>
        <div style={{fontFamily: F.display, fontSize: 52, color: C.chalk, marginTop: 6}}>(725) 425-3583</div>
        <div style={{fontFamily: F.ui, fontWeight: 700, fontSize: 36, color: C.chalk, marginTop: 14, letterSpacing: 3}}>SUPERCAREXP.VIP</div>
        <div style={{fontFamily: F.ui, fontWeight: 500, fontSize: 24, color: C.mute, marginTop: 26, letterSpacing: 3}}>21+ · VALID DRIVER'S LICENSE · INSURANCE</div>
      </div>
    </AbsoluteFill>
  );
};
