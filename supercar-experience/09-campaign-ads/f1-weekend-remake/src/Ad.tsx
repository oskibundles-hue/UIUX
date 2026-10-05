import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {noise2D} from '@remotion/noise';
import {C, F, clamp, lin, s2f} from './theme';
import {Bokeh, Finish, Flash, FloatWords, HandleBug, Plate, PromptBar, StatusCard, TextBubble} from './core';
import {Driver, PixelCode, PixelFire, Sparks} from './pixel';
import {AssetBoard, Badge, EditorChrome, FleetPanel} from './editor';
import {DayTimeline, ScrubTimeline} from './timeline';
import {MapBuild, MapFull} from './map';
import {EndCard, GlowReveal, Poster, TitleLockup} from './poster';

// shot timings (seconds) matched 1:1 to the Higgsfield reel
export const T: [number, number][] = [
  [0, 2.3], [2.3, 4.0], [4.0, 8.0], [8.0, 11.6], [11.6, 12.7], [12.7, 15.0], [15.0, 16.7], [16.7, 17.6], [17.6, 19.0], [19.0, 22.0],
  [22.0, 23.3], [23.3, 26.0], [26.0, 27.0], [27.0, 28.3], [28.3, 31.0], [31.0, 32.4], [32.4, 33.2], [33.2, 34.5], [34.5, 37.0], [37.0, 40.0],
  [40.0, 41.2], [41.2, 42.0], [42.0, 43.2], [43.2, 45.4], [45.4, 46.7], [46.7, 49.6], [49.6, 50.8], [50.8, 55.0], [55.0, 56.3], [56.3, 60.0],
  [60.0, 63.5], [63.5, 64.5], [64.5, 68.0], [68.0, 72.5], [72.5, 76.5],
];
export const TOTAL = s2f(76.5);
const from = (n: number) => s2f(T[n - 1][0]);
const len = (n: number) => s2f(T[n - 1][1]) - s2f(T[n - 1][0]);

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

export const Ad: React.FC = () => {
  const f = useCurrentFrame();
  const white = [11, 16, 23, 25].some((n) => f >= from(n) && f < from(n) + len(n));
  const hideBug = f >= from(35) || f < from(1) + 20;
  return (
    <AbsoluteFill style={{background: C.asphalt}}>
      {/* 1 title */}
      <Sequence from={from(1)} durationInFrames={len(1)}>
        <Plate id={1} len={len(1)} push={[1.18, 1.06]} dim={0.45} grade="night" />
        <Bokeh n={18} speed={2} />
        <TitleLockup />
      </Sequence>
      <Sequence from={from(2)} durationInFrames={len(2)}>
        <Plate id={2} len={len(2)} push={[1.0, 1.16]} grade="night" />
      </Sequence>
      <Sequence from={from(3)} durationInFrames={len(3)}>
        <Plate id={3} len={len(3)} push={[1.08, 1.0]} drift={[-30, 30]} grade="night" />
      </Sequence>
      <Sequence from={from(4)} durationInFrames={len(4)}>
        <Plate id={4} len={len(4)} push={[1.05, 1.12]} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.45), rgba(0,0,0,0) 50%)'}} />
        <TextBubble at={14} typingFrom={2} text="Need a supercar for F1 weekend. ASAP." y={560} />
      </Sequence>
      <Sequence from={from(5)} durationInFrames={len(5)}>
        <Plate id={5} len={len(5)} push={[1.1, 1.2]} grade="night" />
      </Sequence>
      <Sequence from={from(6)} durationInFrames={len(6)}>
        <Plate id={6} len={len(6)} push={[1.04, 1.08]} dim={0.1} />
        <Driver at={4} x={60} y={554} px={14} poses={[{at: 10, pose: 'wave'}, {at: 30, pose: 'idle'}]} />
        <FloatWords words={[{t: 'What', at: 22, x: 640, y: 640, rot: -4}, {t: 'is it', at: 28, x: 600, y: 720, rot: 3}, {t: 'this time?', at: 34, x: 560, y: 800, rot: -2}]} />
      </Sequence>
      <Sequence from={from(7)} durationInFrames={len(7)}>
        <Plate id={7} len={len(7)} push={[1.04, 1.08]} dim={0.1} />
        <Driver at={-20} x={60} y={554} px={14} pose="think" think={[{car: 'evo', at: 2}, {car: 'm750', at: 26}]} />
        <FloatWords words={[{t: 'Coupe?', at: 4, x: 640, y: 660, rot: -3}]} out={24} />
        <FloatWords words={[{t: 'Spyder?', at: 28, x: 640, y: 660, rot: 3}]} />
      </Sequence>
      <Sequence from={from(8)} durationInFrames={len(8)}>
        <Plate id={8} len={len(8)} push={[1.06, 1.14]} grade="hot" shake={8} />
        <PixelFire at={0} x={460} y={1160} burst={12} />
        <Sparks at={12} x={460} y={980} n={60} spread={1400} />
        <FloatWords words={[{t: 'Launch?', at: 2, x: 640, y: 600, rot: -5}]} />
        <Flash at={12} color="#FFB040" peak={0.7} len={8} />
      </Sequence>
      <Sequence from={from(9)} durationInFrames={len(9)}>
        <Plate id={9} len={len(9)} push={[1.04, 1.1]} dim={0.2} />
        <Sparks at={0} x={300} y={1300} n={30} spread={700} />
        <PixelCode lines={['rpm * 9000', 'launch(3.0)']} at={2} x={70} y={700} cps={1.5} />
        <FloatWords words={[{t: 'Specs?', at: 20, x: 700, y: 560, rot: 4}]} />
      </Sequence>
      <Sequence from={from(10)} durationInFrames={len(10)}>
        <Plate id={10} len={len(10)} push={[1.03, 1.1]} dim={0.15} />
        <Driver at={0} x={60} y={514} px={14} poses={[{at: 4, pose: 'think'}, {at: 20, pose: 'thumb'}]} />
        <Stack x={560} y={560} items={[{t: 'Wait', at: 4}, {t: 'No', at: 12}, {t: 'Let me book it', at: 20}]} />
        <PromptBar text="I need a car for F1 weekend. Fast. No mistakes." typeAt={30} cps={1.6} sendAt={82} />
      </Sequence>
      <Sequence from={from(11)} durationInFrames={len(11)}>
        <StatusCard lines={['Booking request received.', 'Checking the fleet for race weekend.']} dur={len(11)} />
      </Sequence>
      <Sequence from={from(12)} durationInFrames={len(12)}>
        <BadgeBuild dur={len(12)} />
      </Sequence>
      <Sequence from={from(13)} durationInFrames={len(13)}>
        <DayTimeline />
      </Sequence>
      <Sequence from={from(14)} durationInFrames={len(14)}>
        <EditorChrome comp="Race_Weekend_Pass" viewerH={1100} playhead={0.6}>
          <Plate id={14} len={len(14)} push={[1.08, 1.12]} dim={0.2} />
          <div style={{position: 'absolute', left: 40, top: 60}}>
            <Badge at={-200} size={360} full />
          </div>
          <SpeechBubble at={4} x={360} y={130} />
          <Driver at={6} x={414} y={657} px={7} pose="wave" />
        </EditorChrome>
      </Sequence>
      <Sequence from={from(15)} durationInFrames={len(15)}>
        <Plate id={15} len={len(15)} push={[1.0, 1.08]} drift={[20, -20]} />
        <PromptBar text="Pull the fleet for race weekend." typeAt={8} cps={1.4} sendAt={66} />
      </Sequence>
      <Sequence from={from(16)} durationInFrames={len(16)}>
        <StatusCard lines={['Pulling cars, dates, and pickup times…']} chip="Building cards for the Las Vegas fleet." dur={len(16)} />
      </Sequence>
      <Sequence from={from(17)} durationInFrames={len(17)}>
        <FleetPanel />
      </Sequence>
      <Sequence from={from(18)} durationInFrames={len(18)}>
        <AssetBoard />
      </Sequence>
      <Sequence from={from(19)} durationInFrames={len(19)}>
        <ScrubTimeline dur={len(19)} />
      </Sequence>
      <Sequence from={from(20)} durationInFrames={len(20)}>
        <Plate id={20} len={len(20)} push={[1.0, 1.1]} />
        <PromptBar text="Map the drive from pickup to the Strip." typeAt={6} cps={1.6} sendAt={76} />
      </Sequence>
      <Sequence from={from(21)} durationInFrames={len(21)}>
        <Plate id={21} len={len(21)} push={[1.1, 1.2]} shake={14} />
        <Slam text="ROUTE!" at={4} />
      </Sequence>
      <Sequence from={from(22)} durationInFrames={len(22)}>
        <Plate id={22} len={len(22)} push={[1.1, 1.18]} />
      </Sequence>
      <Sequence from={from(23)} durationInFrames={len(23)}>
        <StatusCard lines={['Mapped.', 'Five stops. One route.']} dur={len(23)} />
      </Sequence>
      <Sequence from={from(24)} durationInFrames={len(24)}>
        <MapBuild />
      </Sequence>
      <Sequence from={from(25)} durationInFrames={len(25)}>
        <StatusCard lines={['Pulling every stop…']} chip="Pulling frames from the fleet footage." dur={len(25)} />
      </Sequence>
      <Sequence from={from(26)} durationInFrames={len(26)}>
        <MapFull dur={len(26)} />
      </Sequence>
      <Sequence from={from(27)} durationInFrames={len(27)}>
        <Plate id={27} len={len(27)} push={[1.0, 1.12]} drift={[0, -80]} />
      </Sequence>
      <Sequence from={from(28)} durationInFrames={len(28)}>
        <Plate id={28} len={len(28)} push={[1.04, 1.1]} />
        <PromptBar text="Hold the GT3 RS for race weekend." typeAt={10} cps={1.3} sendAt={100} />
      </Sequence>
      <Sequence from={from(29)} durationInFrames={len(29)}>
        <GlowReveal />
      </Sequence>
      <Sequence from={from(30)} durationInFrames={len(30)}>
        <Poster dur={len(30)} />
      </Sequence>
      <Sequence from={from(31)} durationInFrames={len(31)}>
        <Plate id={31} len={len(31)} push={[1.0, 1.16]} shake={4} />
        <PromptBar text="Lock it in and send the confirmation!" typeAt={8} cps={1.5} sendAt={80} />
      </Sequence>
      <Sequence from={from(32)} durationInFrames={len(32)}>
        <Plate id={32} len={len(32)} push={[1.12, 1.0]} grade="night" />
      </Sequence>
      <Sequence from={from(33)} durationInFrames={len(33)}>
        <Plate id={33} len={len(33)} push={[1.0, 1.06]} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.4), rgba(0,0,0,0) 45%)'}} />
        <TextBubble at={16} typingFrom={4} text="Looks perfect! Booked. Next: the whole crew for the rally." y={520} />
      </Sequence>
      <Sequence from={from(34)} durationInFrames={len(34)}>
        <Plate id={34} len={len(34)} push={[1.0, 1.1]} dim={0.25} grade="night" />
        <Driver at={10} x={656} y={1113} px={8} pose="happy" hop />
        <CtaLine at={20} />
      </Sequence>
      <Sequence from={from(35)} durationInFrames={len(35)}>
        <EndCard dur={len(35)} />
      </Sequence>

      {/* global overlays */}
      {!hideBug && <HandleBug dark={white} opacity={0.9} />}
      <Finish vignette={!white} />
      {/* hard-cut punch flashes on a few cuts, like the reference */}
      <Flash at={from(3)} peak={0.35} len={4} />
      <Flash at={from(12)} peak={0.25} len={4} />
      <Flash at={from(21)} peak={0.5} len={5} />
      <Flash at={from(29)} color={C.yellow} peak={0.4} len={5} />

      {/* sound */}
      <Audio src={staticFile('audio/soundtrack.wav')} />
    </AbsoluteFill>
  );
};
