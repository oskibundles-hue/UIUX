import React from 'react';
import {AbsoluteFill, Img, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {evolvePath} from '@remotion/paths';
import {C, F, lin, rnd} from './theme';
import {Still} from './core';

const ISLAND =
  'M 140 330 C 120 220, 260 150, 380 170 C 470 110, 620 120, 700 180 C 820 170, 920 260, 900 380 C 960 470, 930 600, 860 660 C 880 770, 800 880, 680 900 C 600 980, 430 990, 340 930 C 220 940, 110 850, 120 740 C 50 650, 60 520, 110 460 C 90 410, 110 360, 140 330 Z';
const ROUTE = 'M 610 860 C 470 830, 300 760, 270 640 C 240 520, 250 470, 280 440 C 360 470, 450 520, 520 560 C 560 560, 600 520, 640 500 C 700 470, 760 430, 800 470';

// photo cards only where the footage really is that place (Las Vegas night); the others are drawn in the map's style
export const STOPS: {x: number; y: number; name: string; img?: string; draw?: 'rock' | 'lake'}[] = [
  {x: 610, y: 860, name: 'PICKUP', img: 'stop_pickup'},
  {x: 280, y: 440, name: 'RED ROCK', draw: 'rock'},
  {x: 520, y: 560, name: 'THE STRIP', img: 'stop_skyline'},
  {x: 640, y: 500, name: 'THE SPHERE', img: 'stop_sphere'},
  {x: 800, y: 470, name: 'LAKE MEAD', draw: 'lake'},
];

const DrawnStop: React.FC<{kind: 'rock' | 'lake'}> = ({kind}) => (
  <svg viewBox="0 0 250 190" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
    <rect width="250" height="190" fill="#F6D9A6" />
    <rect y="112" width="250" height="78" fill={C.sand} />
    <line x1="0" y1="112" x2="250" y2="112" stroke={C.asphalt} strokeWidth={4} />
    {kind === 'rock' ? (
      <>
        {[[70, 112, 1.25], [150, 112, 1.6], [215, 112, 1.0], [30, 112, 0.8]].map(([x, y, s], i) => (
          <g key={i} transform={`translate(${x} ${y}) scale(${s})`}>
            <path d="M -50 0 L -8 -70 L 12 -48 L 50 0 Z" fill={C.rock} stroke={C.asphalt} strokeWidth={4} strokeLinejoin="round" />
            <path d="M -16 -26 L -8 -70 L 6 -42 Z" fill="#E28A62" />
          </g>
        ))}
        <path d="M 60 190 C 100 160, 150 150, 190 112" stroke={C.asphalt} strokeWidth={14} fill="none" />
        <path d="M 60 190 C 100 160, 150 150, 190 112" stroke={C.yellow} strokeWidth={3} fill="none" strokeDasharray="10 8" />
      </>
    ) : (
      <>
        {[[40, 112, 0.8], [210, 112, 1.0]].map(([x, y, s], i) => (
          <path key={i} transform={`translate(${x} ${y}) scale(${s})`} d="M -50 0 L 0 -52 L 50 0 Z" fill="#C98B5E" stroke={C.asphalt} strokeWidth={4} strokeLinejoin="round" />
        ))}
        <path d="M 20 150 C 40 118, 110 116, 150 124 C 200 116, 240 132, 232 156 C 220 182, 130 186, 80 178 C 30 176, 6 168, 20 150 Z" fill={C.lake} stroke={C.asphalt} strokeWidth={4} />
        {[[70, 146], [130, 158], [175, 142]].map(([x, y], i) => (
          <path key={i} d={`M ${x} ${y} q 8 -6 16 0 q 8 6 16 0`} stroke={C.chalk} strokeWidth={3} fill="none" strokeLinecap="round" />
        ))}
      </>
    )}
    {Array.from({length: 7}).map((_, i) => (
      <circle key={i} cx={20 + rnd(i * 5 + (kind === 'rock' ? 1 : 2)) * 210} cy={120 + rnd(i * 11) * 60} r={4 + rnd(i * 3) * 3} fill="#9BAA5A" opacity={kind === 'lake' && i % 2 ? 0 : 0.85} />
    ))}
  </svg>
);

const Pin: React.FC<{x: number; y: number; at: number; label?: string}> = ({x, y, at, label}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f - at, fps, config: {damping: 8, stiffness: 160}});
  if (f < at) return null;
  return (
    <g transform={`translate(${x} ${y - (1 - sp) * 160})`}>
      <ellipse cx={0} cy={4} rx={18 * sp} ry={6 * sp} fill="rgba(0,0,0,0.3)" transform={`translate(0 ${(1 - sp) * 160})`} />
      <path d="M0 0 C 0 0 -24 -30 -24 -46 A 24 24 0 1 1 24 -46 C 24 -30 0 0 0 0 Z" fill={C.red} stroke={C.asphalt} strokeWidth={4} />
      <circle cx={0} cy={-46} r={9} fill={C.chalk} />
      {label && (
        <g opacity={lin(f, at + 6, at + 12)}>
          <rect x={-70} y={-118} width={140} height={34} rx={17} fill={C.asphalt} />
          <text x={0} y={-95} textAnchor="middle" fontFamily="Archivo" fontWeight={800} fontSize={18} fill={C.chalk} letterSpacing={1}>{label}</text>
        </g>
      )}
    </g>
  );
};

export const MapIsland: React.FC<{base: number; full?: boolean; pins?: boolean; pinAt?: number}> = ({base, full, pins, pinAt = 0}) => {
  const f0 = useCurrentFrame();
  const f = full ? 999 : f0 - base;
  const rise = lin(f, 0, 16);
  const lake = lin(f, 10, 24);
  const strip = lin(f, 18, 34);
  const route = evolvePath(lin(f, 28, 58), ROUTE);
  const mts = [
    [190, 470, 1.2],
    [250, 430, 1.6],
    [310, 470, 1.1],
    [220, 520, 0.9],
    [150, 560, 1.0],
  ];
  return (
    <svg viewBox="0 0 1000 1050" width={1000} height={1050} style={{overflow: 'visible', transform: `translateY(${(1 - rise) * 240}px) scale(${0.85 + rise * 0.15})`, opacity: Math.min(1, rise * 2)}}>
      {/* extrusion */}
      <path d={ISLAND} transform="translate(0 46)" fill={C.sandDark} />
      <path d={ISLAND} transform="translate(0 46)" fill="none" stroke={C.asphalt} strokeWidth={6} />
      <path d={ISLAND} fill={C.sand} stroke={C.asphalt} strokeWidth={6} />
      {/* scrub dots */}
      {Array.from({length: 70}).map((_, i) => {
        const x = 170 + rnd(i) * 680, y = 220 + rnd(i * 3) * 650;
        const o = lin(f, 6 + (i % 10), 14 + (i % 10));
        return <circle key={i} cx={x} cy={y} r={5 + rnd(i * 7) * 5} fill="#9BAA5A" opacity={0.75 * o} />;
      })}
      {/* lake mead */}
      <path d="M 760 400 C 820 360, 880 400, 870 460 C 900 520, 840 580, 780 560 C 730 590, 700 520, 730 480 C 700 440, 720 410, 760 400 Z" fill={C.lake} stroke={C.asphalt} strokeWidth={5} transform={`translate(800 480) scale(${lake}) translate(-800 -480)`} />
      {/* red rock */}
      {mts.map(([x, y, s], i) => {
        const p = lin(f, 14 + i * 3, 24 + i * 3);
        return (
          <g key={i} transform={`translate(${x} ${y}) scale(${s * p})`}>
            <path d="M -60 0 L 0 -90 L 60 0 Z" fill={C.rock} stroke={C.asphalt} strokeWidth={5} strokeLinejoin="round" />
            <path d="M -20 -30 L 0 -90 L 16 -50 Z" fill="#E28A62" />
          </g>
        );
      })}
      {/* the strip */}
      <line x1={520} y1={240} x2={520} y2={240 + 640 * strip} stroke={C.asphalt} strokeWidth={22} strokeLinecap="round" />
      <line x1={520} y1={240} x2={520} y2={240 + 640 * strip} stroke={C.chalk} strokeWidth={4} strokeDasharray="18 16" />
      {/* towers along strip */}
      {[300, 380, 450, 610, 690].map((y, i) => {
        const p = lin(f, 30 + i * 2, 40 + i * 2);
        const h = 40 + (i % 3) * 22;
        return <rect key={i} x={540} y={y - h * p} width={26} height={h * p} fill={i % 2 ? C.magenta : C.blue} stroke={C.asphalt} strokeWidth={4} />;
      })}
      {/* sphere */}
      <circle cx={640} cy={500} r={34 * lin(f, 36, 46)} fill={C.magenta} stroke={C.asphalt} strokeWidth={5} />
      <circle cx={628} cy={488} r={10 * lin(f, 40, 48)} fill="#ffd1ea" />
      {/* route */}
      <path d={ROUTE} stroke={C.asphalt} strokeWidth={20} fill="none" strokeLinecap="round" strokeDasharray={route.strokeDasharray} strokeDashoffset={route.strokeDashoffset} />
      <path d={ROUTE} stroke={C.yellow} strokeWidth={11} fill="none" strokeLinecap="round" strokeDasharray={route.strokeDasharray} strokeDashoffset={route.strokeDashoffset} />
      {pins && STOPS.map((s, i) => <Pin key={i} x={s.x} y={s.y} at={pinAt + i * 5} label={s.name} />)}
    </svg>
  );
};

const Bg: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: '#121214'}}>
      <svg width="1080" height="1920" style={{position: 'absolute', opacity: 0.6}}>
        {Array.from({length: 36}).map((_, i) => (
          <path key={i} d="M 540 960 L 520 -1400 L 560 -1400 Z" fill={i % 2 ? '#1a1a1d' : '#121214'} transform={`rotate(${i * 10 + f * 0.2} 540 960)`} />
        ))}
      </svg>
    </AbsoluteFill>
  );
};

export const MapBuild: React.FC = () => (
  <AbsoluteFill>
    <Bg />
    <div style={{position: 'absolute', left: 40, top: 430}}>
      <MapIsland base={0} />
    </div>
  </AbsoluteFill>
);

// full route map with title, pins, photo cards, cursor click (shot 26)
export const MapFull: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const title = lin(f, 0, 12);
  const cards = [
    {s: 1, x: 40, y: 650, r: -5},
    {s: 3, x: 760, y: 610, r: 4},
    {s: 4, x: 770, y: 1000, r: -3},
    {s: 2, x: 40, y: 1080, r: 3},
    {s: 0, x: 690, y: 1430, r: -4},
  ];
  // cursor path
  const cx = lin(f, 40, 62, 300, 610);
  const cy = lin(f, 40, 62, 1700, 1300);
  const click = f - 62;
  return (
    <AbsoluteFill>
      <Bg />
      <div style={{position: 'absolute', left: 64, top: 210, opacity: title, transform: `translateY(${(1 - title) * 30}px)`}}>
        <div style={{display: 'flex', gap: 14, alignItems: 'center'}}>
          <Img src={staticFile('brand/mono.svg')} style={{height: 40}} />
          <div style={{fontFamily: F.ui, fontWeight: 800, fontSize: 24, letterSpacing: 4, color: C.yellow}}>LAS VEGAS · F1 WEEKEND</div>
        </div>
        <div style={{fontFamily: F.display, fontSize: 92, lineHeight: 0.95, color: C.chalk, marginTop: 10}}>RACE WEEKEND<br />ROUTE</div>
        <div style={{display: 'flex', gap: 12, marginTop: 18}}>
          {['5 STOPS', '1 ROUTE'].map((t, i) => (
            <div key={t} style={{fontFamily: F.ui, fontWeight: 800, fontSize: 22, padding: '8px 18px', borderRadius: 30, background: [C.yellow, C.red, C.chalk][i], color: i === 1 ? C.chalk : C.asphalt, opacity: lin(f, 6 + i * 3, 12 + i * 3)}}>
              {t}
            </div>
          ))}
        </div>
      </div>
      <div style={{position: 'absolute', left: 40, top: 560, transform: 'scale(0.98)', transformOrigin: '50% 0%'}}>
        <MapIsland base={0} full pins pinAt={6} />
      </div>
      {cards.map((c, i) => {
        const sp = spring({frame: f - (20 + i * 5), fps, config: {damping: 11, stiffness: 190}});
        const st = STOPS[c.s];
        return (
          <div key={i} style={{position: 'absolute', left: c.x, top: c.y, width: 270, transform: `rotate(${c.r}deg) scale(${sp})`, background: C.chalk, padding: 10, paddingBottom: 14, boxShadow: '0 18px 40px rgba(0,0,0,0.5)'}}>
            <div style={{height: 190, overflow: 'hidden'}}>
              {st.draw ? <DrawnStop kind={st.draw} /> : <Still src={st.img!} />}
            </div>
            <div style={{display: 'flex', justifyContent: 'space-between', marginTop: 10, fontFamily: F.ui, fontWeight: 800, fontSize: 21, color: C.asphalt}}>
              <span>{st.name}</span>
            </div>
          </div>
        );
      })}
      {f > 38 && (
        <div style={{position: 'absolute', left: cx, top: cy}}>
          {click > 0 && click < 18 && <div style={{position: 'absolute', left: -60 * (click / 18) - 4, top: -60 * (click / 18) - 4, width: 120 * (click / 18) + 8, height: 120 * (click / 18) + 8, borderRadius: '50%', border: `4px solid ${C.yellow}`, opacity: 1 - click / 18}} />}
          <svg width="56" height="70" viewBox="0 0 20 25" style={{transform: `scale(${click > 0 && click < 4 ? 0.85 : 1})`}}>
            <path d="M1 1 L1 19 L6 14.5 L9.5 22.5 L12.5 21 L9 13.5 L15.5 13.5 Z" fill="#fff" stroke="#000" strokeWidth="1.4" strokeLinejoin="round" />
          </svg>
        </div>
      )}
    </AbsoluteFill>
  );
};
