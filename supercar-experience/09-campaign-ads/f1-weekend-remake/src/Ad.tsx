import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {noise2D} from '@remotion/noise';
import {C, F, clamp, lin, s2f} from './theme';
import {Bokeh, Finish, Flash, FloatWords, HandleBug, Plate, PromptBar, StatusCard, TextBubble} from './core';
import {Driver, PixelCode, PixelFire, Sparks} from './pixel';
import {AssetBoard, Badge, EditorChrome, FleetPanel} from './editor';
import {DayTimeline, ScrubTimeline} from './timeline';
import {MapBuild, MapFull} from './map';
import {EndCard, GlowReveal, TitleLockup} from './poster';
import {Ignition} from './ignition';
import cut30 from './cut30.json';

// shot timings (seconds) matched 1:1 to the Higgsfield reel
export const T: [number, number][] = [
  [0, 2.3], [2.3, 4.0], [4.0, 8.0], [8.0, 11.6], [11.6, 12.7], [12.7, 15.0], [15.0, 16.7], [16.7, 17.6], [17.6, 19.0], [19.0, 22.0],
  [22.0, 23.3], [23.3, 26.0], [26.0, 27.0], [27.0, 28.3], [28.3, 31.0], [31.0, 32.4], [32.4, 33.2], [33.2, 34.5], [34.5, 37.0], [37.0, 40.0],
  [40.0, 41.2], [41.2, 42.0], [42.0, 43.2], [43.2, 45.4], [45.4, 46.7], [46.7, 49.6], [49.6, 50.8], [50.8, 55.0], [55.0, 56.3], [56.3, 60.0],
  [60.0, 63.5], [63.5, 64.5], [64.5, 68.0], [68.0, 72.5], [72.5, 76.5],
];
export const TOTAL = s2f(76.5);

// ---------- small shot-specific pieces ----------
const Slam: React.FC<{text: string; at: number}> = ({text, at}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < at) return null;
  const sp = spring({frame: f - at, fps, config: {damping: 9, stiffness: 300}});
  const sh = Math.max(0, 1 - (f - at) / 14) * 26;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div
        style={{
          fontFamily: F.display,
          fontSize: 190,
          color: C.yellow,
          letterSpacing: -6,
          transform: `translate(${noise2D('a', f, 0) * sh}px, ${noise2D('b', f, 0) * sh}px) scale(${2.0 - sp * 1.0}) rotate(-6deg)`,
          opacity: Math.min(1, sp * 2),
          textShadow: '10px 10px 0 #0b0b0c, 0 0 60px rgba(242,197,0,0.5)',
          WebkitTextStroke: '6px #0b0b0c',
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

const Stack: React.FC<{items: {t: string; at: number}[]; x: number; y: number}> = ({items, x, y}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{position: 'absolute', left: x, top: y, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4}}>
      {items.map((it, i) => {
        if (f < it.at) return null;
        const sp = spring({frame: f - it.at, fps, config: {damping: 10, stiffness: 260}});
        return (
          <div key={i} style={{fontFamily: F.ui, fontWeight: 800, fontSize: 64, color: C.chalk, textShadow: '0 4px 24px rgba(0,0,0,0.7)', transform: `scale(${sp})`, transformOrigin: '100% 50%'}}>
            {it.t}
          </div>
        );
      })}
    </div>
  );
};

const SpeechBubble: React.FC<{at: number; x: number; y: number}> = ({at, x, y}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < at) return null;
  const sp = spring({frame: f - at, fps, config: {damping: 10, stiffness: 220}});
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `scale(${sp})`, transformOrigin: '0% 100%', background: C.chalk, border: `6px solid ${C.asphalt}`, borderRadius: 28, padding: '22px 30px', boxShadow: '8px 8px 0 #0b0b0c'}}>
      <div style={{fontFamily: F.display, fontSize: 52, color: C.asphalt}}>HI, I'M REV!</div>
      <div style={{fontFamily: F.ui, fontWeight: 600, fontSize: 30, color: '#3a3a3a', marginTop: 4}}>Ask me about the fleet.</div>
      <div style={{position: 'absolute', left: 40, bottom: -36, width: 0, height: 0, borderLeft: '22px solid transparent', borderRight: '22px solid transparent', borderTop: `36px solid ${C.asphalt}`}} />
    </div>
  );
};

// shot 12: badge builds full screen, then camera pulls back to the editor
const BadgeBuild: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [34, 60], [1, 0], {...clamp, easing: (t) => 1 - (1 - t) ** 3});
  const scale = 1 + z * 0.9;
  return (
    <AbsoluteFill style={{transform: `scale(${scale})`, transformOrigin: '50% 37%'}}>
      <EditorChrome comp="Race_Weekend_Pass" viewerH={1100} playhead={lin(f, 0, dur)}>
        <div style={{position: 'absolute', inset: 0, opacity: lin(f, 30, 50)}}>
          <Plate id={12} len={dur} push={[1.05, 1.1]} dim={0.35} />
        </div>
        <div style={{position: 'absolute', left: '50%', top: '50%', transform: `translate(-50%,-50%) scale(${1 - lin(f, 40, 70) * 0.45}) translate(${lin(f, 40, 70) * -300}px, ${lin(f, 40, 70) * -260}px)`}}>
          <Badge at={0} size={640} />
        </div>
      </EditorChrome>
    </AbsoluteFill>
  );
};

const CtaLine: React.FC<{at: number}> = ({at}) => {
  const f = useCurrentFrame();
  const o = lin(f, at, at + 14);
  return (
    <div style={{position: 'absolute', top: 1040, left: 0, right: 0, textAlign: 'center', opacity: o, filter: `blur(${(1 - o) * 6}px)`}}>
      <div style={{fontFamily: F.ui, fontWeight: 800, fontSize: 30, letterSpacing: 3, color: C.chalk, textShadow: '0 2px 16px rgba(0,0,0,0.8)'}}>TEXT OR DM TO BOOK · (725) 425-3583</div>
      <div style={{fontFamily: F.ui, fontWeight: 700, fontSize: 26, letterSpacing: 5, color: C.yellow, marginTop: 8, textShadow: '0 2px 16px rgba(0,0,0,0.8)'}}>SUPERCAREXP.VIP</div>
    </div>
  );
};

// ---------- sound design ----------
// Music + every SFX is one mixed file made by the SFX engine (npm run sfx): it reads sfx/events.json
// (what happens on screen, frame-exact), picks the sound, places its hit on the frame and sets its level
// over the music. The cue sheet with the reason for every sound and every skip is sfx/cuesheet.md.

// one shot's picture and graphics for L frames; `short` = the 30 s cut's tighter timings
const shot = (n: number, L: number, short: boolean): React.ReactNode => {
  switch (n) {
    case 1:
      return (
        <>
          <Plate id={1} len={L} push={[1.18, 1.06]} dim={0.45} grade="night" />
          <Bokeh n={18} speed={2} />
          <TitleLockup />
        </>
      );
    case 2:
      return (
        <>
          <Plate id={2} len={L} push={[1.0, 1.16]} grade="night" />
        </>
      );
    case 3:
      return (
        <>
          <Plate id={3} len={L} push={[1.08, 1.0]} drift={[-30, 30]} grade="night" />
        </>
      );
    case 4:
      return (
        <>
          <Plate id={4} len={L} push={[1.05, 1.12]} />
          <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.45), rgba(0,0,0,0) 50%)'}} />
          <TextBubble at={14} typingFrom={2} text="Need a supercar for F1 weekend. ASAP." y={560} />
        </>
      );
    case 5:
      return (
        <>
          <Plate id={5} len={L} push={[1.1, 1.2]} grade="night" />
        </>
      );
    case 6:
      return (
        <>
          <Plate id={6} len={L} push={[1.04, 1.08]} dim={0.1} />
          <Driver at={4} x={60} y={554} px={14} poses={[{at: 10, pose: 'wave'}, {at: 30, pose: 'idle'}]} />
          <FloatWords words={[{t: 'What', at: short ? 6 : 22, x: 640, y: 640, rot: -4}, {t: 'is it', at: short ? 11 : 28, x: 600, y: 720, rot: 3}, {t: 'this time?', at: short ? 16 : 34, x: 560, y: 800, rot: -2}]} />
        </>
      );
    case 7:
      return (
        <>
          <Plate id={7} len={L} push={[1.04, 1.08]} dim={0.1} />
          <Driver at={-20} x={60} y={554} px={14} pose="think" think={[{car: 'evo', at: 2}, {car: 'm750', at: 26}]} />
          <FloatWords words={[{t: 'Coupe?', at: 4, x: 640, y: 660, rot: -3}]} out={24} />
          <FloatWords words={[{t: 'Spyder?', at: 28, x: 640, y: 660, rot: 3}]} />
        </>
      );
    case 8:
      return (
        <>
          <Plate id={8} len={L} push={[1.06, 1.14]} grade="hot" shake={8} />
          <PixelFire at={0} x={460} y={1160} burst={12} />
          <Sparks at={12} x={460} y={980} n={60} spread={1400} />
          <FloatWords words={[{t: 'Launch?', at: 2, x: 640, y: 600, rot: -5}]} />
          <Flash at={12} color="#FFB040" peak={0.7} len={8} />
        </>
      );
    case 9:
      return (
        <>
          <Plate id={9} len={L} push={[1.04, 1.1]} dim={0.2} />
          <Sparks at={0} x={300} y={1300} n={30} spread={700} />
          <PixelCode lines={['rpm * 9000', 'launch(3.0)']} at={2} x={70} y={700} cps={1.5} />
          <FloatWords words={[{t: 'Specs?', at: 20, x: 700, y: 560, rot: 4}]} />
        </>
      );
    case 10:
      return (
        <>
          <Plate id={10} len={L} push={[1.03, 1.1]} dim={0.15} />
          <Driver at={0} x={60} y={514} px={14} poses={[{at: 4, pose: 'think'}, {at: short ? 16 : 20, pose: 'thumb'}]} />
          <Stack x={560} y={560} items={[{t: 'Wait', at: 4}, {t: 'No', at: short ? 10 : 12}, {t: 'Let me book it', at: short ? 16 : 20}]} />
          {!short && <PromptBar text="I need a car for F1 weekend. Fast. No mistakes." typeAt={30} cps={1.6} sendAt={82} />}
        </>
      );
    case 11:
      return (
        <>
          <StatusCard lines={['Booking request received.', 'Checking the fleet for race weekend.']} dur={L} />
        </>
      );
    case 12:
      return (
        <>
          <BadgeBuild dur={L} />
        </>
      );
    case 13:
      return (
        <>
          <DayTimeline />
        </>
      );
    case 14:
      return (
        <>
          <EditorChrome comp="Race_Weekend_Pass" viewerH={1100} playhead={0.6}>
            <Plate id={14} len={L} push={[1.08, 1.12]} dim={0.2} />
            <div style={{position: 'absolute', left: 40, top: 60}}>
              <Badge at={-200} size={360} full />
            </div>
            <SpeechBubble at={4} x={360} y={130} />
            <Driver at={6} x={414} y={657} px={7} pose="wave" />
          </EditorChrome>
        </>
      );
    case 15:
      return (
        <>
          <Plate id={15} len={L} push={[1.0, 1.08]} drift={[20, -20]} />
          <PromptBar text="Pull the fleet for race weekend." typeAt={8} cps={1.4} sendAt={66} />
        </>
      );
    case 16:
      return (
        <>
          <StatusCard lines={['Pulling cars, dates, and pickup times…']} chip="Building cards for the Las Vegas fleet." dur={L} />
        </>
      );
    case 17:
      return (
        <>
          <FleetPanel />
        </>
      );
    case 18:
      return (
        <>
          <AssetBoard />
        </>
      );
    case 19:
      return (
        <>
          <ScrubTimeline dur={L} />
        </>
      );
    case 20:
      return (
        <>
          <Plate id={20} len={L} push={[1.0, 1.1]} />
          <PromptBar text="Map the drive from pickup to the Strip." typeAt={6} cps={1.6} sendAt={76} />
        </>
      );
    case 21:
      return (
        <>
          <Plate id={21} len={L} push={[1.1, 1.2]} shake={14} />
          <Slam text="ROUTE!" at={4} />
        </>
      );
    case 22:
      return (
        <>
          <Plate id={22} len={L} push={[1.1, 1.18]} />
        </>
      );
    case 23:
      return (
        <>
          <StatusCard lines={['Mapped.', 'Five stops. One route.']} dur={L} />
        </>
      );
    case 24:
      return (
        <>
          <MapBuild />
        </>
      );
    case 25:
      return (
        <>
          <StatusCard lines={['Pulling every stop…']} chip="Pulling frames from the fleet footage." dur={L} />
        </>
      );
    case 26:
      return (
        <>
          <MapFull dur={L} />
        </>
      );
    case 27:
      return (
        <>
          <Plate id={27} len={L} push={[1.0, 1.12]} drift={[0, -80]} />
        </>
      );
    case 28:
      return (
        <>
          <Plate id={28} len={L} push={[1.04, 1.1]} />
          <PromptBar text="Hold the GT3 RS for race weekend." typeAt={10} cps={1.3} sendAt={100} />
        </>
      );
    case 29:
      return (
        <>
          <GlowReveal />
        </>
      );
    case 30:
      return (
        <>
          <Ignition dur={L} />
        </>
      );
    case 31:
      return (
        <>
          <Plate id={31} len={L} push={[1.0, 1.16]} shake={4} />
          <PromptBar text="Lock it in and send the confirmation!" typeAt={8} cps={1.5} sendAt={80} />
        </>
      );
    case 32:
      return (
        <>
          <Plate id={32} len={L} push={[1.12, 1.0]} grade="night" />
        </>
      );
    case 33:
      return (
        <>
          <Plate id={33} len={L} push={[1.0, 1.06]} />
          <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.4), rgba(0,0,0,0) 45%)'}} />
          <TextBubble at={16} typingFrom={4} text={short ? 'Looks perfect! Booked.' : 'Looks perfect! Booked. Next: the whole crew for the rally.'} y={520} />
        </>
      );
    case 34:
      return (
        <>
          <Plate id={34} len={L} push={[1.0, 1.1]} dim={0.25} grade="night" />
          <Driver at={10} x={656} y={1113} px={8} pose="happy" hop />
          <CtaLine at={20} />
        </>
      );
    case 35:
      return (
        <>
          <EndCard dur={L} />
        </>
      );
    default:
      return null;
  }
};

// ---------- the cuts: the 76 s reference (T) and the 30 s ad (src/cut30.json) ----------
type Cut = {id: number; from: number; len: number}[];
const CUT76: Cut = T.map(([a, b], i) => ({id: i + 1, from: s2f(a), len: s2f(b) - s2f(a)}));
export const CUT30: Cut = (cut30.shots as [number, number][]).reduce<Cut>((acc, [id, n]) => {
  const prev = acc[acc.length - 1];
  return [...acc, {id, from: prev ? prev.from + prev.len : 0, len: n}];
}, []);
export const TOTAL30 = CUT30[CUT30.length - 1].from + CUT30[CUT30.length - 1].len;

const Cutdown: React.FC<{cut: Cut; audio: string; short?: boolean}> = ({cut, audio, short = false}) => {
  const f = useCurrentFrame();
  const at = (n: number) => cut.find((c) => c.id === n);
  const inShot = (n: number) => {
    const c = at(n);
    return !!c && f >= c.from && f < c.from + c.len;
  };
  const white = [11, 16, 23, 25].some(inShot);
  const hideBug = f >= at(35)!.from || f < cut[0].from + 20;
  // hard-cut punch flashes on a few cuts, like the reference
  const flashes: [number, number, number][] = short ? [[12, 0.25, 4], [21, 0.5, 5], [30, 0.3, 4]] : [[3, 0.35, 4], [12, 0.25, 4], [21, 0.5, 5]];
  return (
    <AbsoluteFill style={{background: C.asphalt}}>
      {cut.map((c) => (
        <Sequence key={c.id} from={c.from} durationInFrames={c.len}>
          {shot(c.id, c.len, short)}
        </Sequence>
      ))}

      {/* global overlays */}
      {!hideBug && <HandleBug dark={white} opacity={0.9} />}
      <Finish vignette={!white} />
      {flashes.map(([n, peak, l]) => at(n) && <Flash key={n} at={at(n)!.from} peak={peak} len={l} />)}
      {at(29) && <Flash at={at(29)!.from} color={C.yellow} peak={0.4} len={5} />}

      {/* sound */}
      <Audio src={staticFile(audio)} />
    </AbsoluteFill>
  );
};

export const Ad: React.FC = () => <Cutdown cut={CUT76} audio="audio/soundtrack.wav" />;
export const Ad30: React.FC = () => <Cutdown cut={CUT30} audio="audio/soundtrack30.wav" short />;
