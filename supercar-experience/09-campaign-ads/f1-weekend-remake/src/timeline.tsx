import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {C, F, inOut, lin, rnd} from './theme';
import DUR from '../public/thumbs/clips.json';

// The editor shots (13, 19) as a real edit of this ad: every clip is a filmstrip cut from the ad's own
// plates (tools/filmstrips.py), the monitor shows the frame under the playhead.

type Plate = keyof typeof DUR;
const FILE: Record<Plate, string> = {
  s02: 'amg.mov',
  s03: 'sto.mp4',
  s04: 'mcl750.mov',
  s05: 'sto.mp4',
  s12: 'sto.mp4',
  s15: 'mcl750.mov',
  s20: 'urus.mp4',
  s22: 'mcl750.mov',
  s27: 'gt3_white.mov',
  s28: 'gt3_white.mov',
  s32: 'amg.mov',
  s33: 'gt3_livery.mov',
  s34: 'sto.mp4',
};

const BG = '#0f0f11';
const VID = '#4F7FE0';
const GFX = '#C2569B';
const AUD = '#2F9E68';
const SFX = C.teal;

const tc = (s: number) => {
  const t = Math.max(0, s);
  const ss = Math.floor(t);
  const ff = Math.min(29, Math.floor((t - ss) * 30));
  return `00:00:${String(ss).padStart(2, '0')}:${String(ff).padStart(2, '0')}`;
};

// ---------------------------------------------------------------- shared pieces
const Monitor: React.FC<{plate: Plate; t: number; progress: number}> = ({plate, t, progress}) => {
  const f = useCurrentFrame();
  const side: React.CSSProperties = {position: 'absolute', top: 74, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 16, letterSpacing: 1, color: '#77756e'};
  return (
    <div style={{position: 'absolute', left: 40, right: 40, top: 170, height: 640, background: '#0b0b0d', border: `1px solid ${C.rule}`, borderRadius: 10, overflow: 'hidden', fontFamily: F.mono}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 12, height: 46, padding: '0 18px', borderBottom: `1px solid ${C.rule}`, fontSize: 18, color: '#9a988f'}}>
        <div style={{width: 10, height: 10, borderRadius: 5, background: C.red}} />
        <span style={{color: C.chalk}}>PROGRAM</span>
        <span>F1_RACE_WEEKEND_v12</span>
        <span style={{marginLeft: 'auto', color: C.yellow, fontSize: 26}}>{tc(t)}</span>
      </div>
      <div style={{position: 'absolute', left: '50%', top: 58, width: 320, height: 569, marginLeft: -160, overflow: 'hidden', background: '#000'}}>
        <Img src={staticFile(`thumbs/${plate}.jpg`)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${1.03 + 0.02 * Math.sin(f * 0.08)})`}} />
        <div style={{position: 'absolute', inset: '5%', border: '1px solid rgba(255,255,255,0.16)'}} />
        <div style={{position: 'absolute', inset: '10%', border: '1px dashed rgba(255,255,255,0.12)'}} />
      </div>
      <div style={{...side, left: 22}}>
        <span>SEQUENCE</span>
        <span style={{color: '#b9b7b0'}}>F1_RACE_WEEKEND</span>
        <span>1080 × 1920</span>
        <span>30 FPS</span>
      </div>
      <div style={{...side, right: 22, alignItems: 'flex-end'}}>
        <span>CLIP</span>
        <span style={{color: '#b9b7b0'}}>{FILE[plate]}</span>
        <span>{DUR[plate].toFixed(2)} S</span>
        <span>FIT · FULL</span>
      </div>
      {/* audio meters */}
      {[0, 1].map((k) => {
        const lvl = 0.55 + 0.3 * rnd(Math.floor(f / 2) * 2 + k) + 0.1 * Math.sin(f * 0.5 + k);
        return (
          <div key={k} style={{position: 'absolute', right: 30 + k * 16, top: 250, width: 10, height: 330, background: '#1a1a1d'}}>
            <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: `${lvl * 100}%`, background: `linear-gradient(0deg, ${AUD} 0%, ${AUD} 60%, ${C.yellow} 85%, ${C.red} 100%)`, backgroundSize: '100% 330px', backgroundPosition: 'bottom'}} />
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 0, bottom: 0, height: 4, width: `${progress * 100}%`, background: C.yellow}} />
    </div>
  );
};

// a clip on a track: coloured name bar, then a filmstrip of the plate (or nothing for graphics/audio)
const STRIP_W = 648 / 192; // filmstrip width per px of height (6 frames at 9:16)
const Clip: React.FC<{x: number; w: number; h: number; color: string; label: string; strip?: Plate; dark?: boolean; children?: React.ReactNode}> = ({x, w, h, color, label, strip, dark = true, children}) => {
  const ih = h - 26;
  const sw = ih * STRIP_W;
  return (
    <div style={{position: 'absolute', left: x, top: 0, width: Math.max(0, w), height: h, boxSizing: 'border-box', border: `2px solid ${color}`, borderRadius: 5, overflow: 'hidden', background: '#141418'}}>
      <div style={{height: 24, background: color, color: dark ? '#0b0b0c' : C.chalk, fontFamily: F.mono, fontSize: 15, lineHeight: '24px', padding: '0 8px', whiteSpace: 'nowrap', overflow: 'hidden'}}>{label}</div>
      {strip &&
        Array.from({length: Math.ceil(w / sw)}).map((_, k) => (
          <Img key={k} src={staticFile(`thumbs/${strip}_strip.jpg`)} style={{position: 'absolute', left: k * sw, top: 24, height: ih, width: sw}} />
        ))}
      {children}
    </div>
  );
};

const Diamond: React.FC<{x: number; y: number; on: boolean}> = ({x, y, on}) => (
  <div style={{position: 'absolute', left: x - 7, top: y - 7, width: 14, height: 14, transform: 'rotate(45deg)', background: on ? C.yellow : C.chalk, border: '2px solid #0b0b0c', boxShadow: on ? '0 0 8px rgba(242,197,0,0.8)' : undefined}} />
);

// ---------------------------------------------------------------- shot 13: one day per track, the playhead lands on Saturday
const DAYS = [
  {day: 'THU', date: 'NOV 19', what: 'PICKUP', plate: 's12' as Plate, c: C.yellow},
  {day: 'FRI', date: 'NOV 20', what: 'DESERT RUN', plate: 's15' as Plate, c: C.chalk},
  {day: 'SAT', date: 'NOV 21', what: 'RACE NIGHT', plate: 's02' as Plate, c: C.red},
];

export const DayTimeline: React.FC = () => {
  const f = useCurrentFrame();
  const ph = lin(f, 2, 24, 0.04, 0.82, inOut);
  const d = DAYS[Math.min(2, Math.floor(ph * 3))];
  const LW = 290;
  const TW = 1080 - LW - 30;
  return (
    <AbsoluteFill style={{background: BG, fontFamily: F.mono}}>
      <Monitor plate={d.plate} t={ph * 24} progress={ph} />
      <div style={{position: 'absolute', left: 40, top: 846, display: 'flex', alignItems: 'baseline', gap: 22}}>
        <span style={{color: C.yellow, fontSize: 40}}>{d.date}</span>
        <span style={{color: C.chalk, fontSize: 30}}>
          {d.day} · {d.what}
        </span>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 920}}>
        {DAYS.map((r, i) => {
          const p = lin(f, i * 4, i * 4 + 10);
          return (
            <div key={r.day} style={{display: 'flex', alignItems: 'center', height: 230, borderBottom: `1px solid ${C.rule}`, opacity: p, transform: `translateY(${(1 - p) * 60}px)`}}>
              <div style={{width: LW, padding: '0 30px 0 40px', boxSizing: 'border-box', display: 'flex', gap: 16, alignItems: 'center'}}>
                <div style={{width: 18, height: 18, flexShrink: 0, background: r.c}} />
                <div>
                  <div style={{fontFamily: F.display, fontSize: 44, lineHeight: 1, color: C.chalk}}>{r.day}</div>
                  <div style={{fontSize: 18, color: C.mute, marginTop: 6, whiteSpace: 'nowrap'}}>{r.date}</div>
                </div>
              </div>
              <div style={{position: 'relative', width: TW, height: 196}}>
                <Clip x={(i * TW) / 3} w={(TW / 3) * p - 6} h={196} color={r.c} dark={i < 2} label={`${r.what} · ${FILE[r.plate]}`} strip={r.plate} />
              </div>
            </div>
          );
        })}
        <div style={{position: 'absolute', top: -24, height: 714, left: LW + TW * ph - 2, width: 4, background: C.yellow, boxShadow: '0 0 12px rgba(242,197,0,0.8)'}}>
          <div style={{position: 'absolute', left: -12, top: 0, width: 28, height: 22, background: C.yellow, clipPath: 'polygon(0 0, 100% 0, 100% 60%, 50% 100%, 0 60%)'}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- shot 19: the whole edit scrubs past under the playhead
const ORDER: Plate[] = ['s02', 's03', 's04', 's05', 's12', 's15', 's20', 's22', 's28', 's27', 's32', 's33', 's34'];
const V1 = ORDER.reduce<{plate: Plate; t0: number; d: number}[]>((a, p) => {
  const t0 = a.length ? a[a.length - 1].t0 + a[a.length - 1].d : 0;
  return [...a, {plate: p, t0, d: DUR[p]}];
}, []);
const V2 = [
  {t0: 0.4, d: 1.4, label: 'TITLE · RENT A SUPERCAR'},
  {t0: 3.0, d: 2.2, label: 'BUBBLE · F1 WEEKEND?'},
  {t0: 6.9, d: 2.4, label: 'PROMPT BAR'},
  {t0: 10.6, d: 1.8, label: 'FLEET LIST'},
  {t0: 13.4, d: 2.6, label: 'MAP · ROUTE'},
  {t0: 17.2, d: 2.0, label: 'BOOKING KIT'},
  {t0: 20.4, d: 2.8, label: 'RACE WEEKEND PASS'},
  {t0: 24.6, d: 2.4, label: 'CTA · TEXT OR DM'},
  {t0: 28.4, d: 2.2, label: 'END CARD'},
];
const SFX_NAMES = ['whoosh', 'pop', 'click', 'riser', 'impact', 'swipe', 'pop', 'confirm'];
const A2 = Array.from({length: 26}).map((_, i) => ({t0: i * 1.2 + rnd(i * 7) * 0.5, d: 0.45 + rnd(i * 13) * 0.4, label: `${SFX_NAMES[i % SFX_NAMES.length]}.wav`}));

const SECTORS = [
  ['S1', 'THU'],
  ['S2', 'FRI'],
  ['S3', 'SAT'],
  ['', 'RACE NIGHT'],
] as const;

const HEAD = 128;
const PH = 520;
const ROWS = {ruler: [0, 44], v2: [52, 100], v1: [160, 260], a1: [428, 150], a2: [586, 90]} as const;

const TrackHead: React.FC<{name: string; y: number; h: number; audio?: boolean}> = ({name, y, h, audio}) => (
  <div style={{position: 'absolute', left: 0, top: y, width: HEAD - 8, height: h, background: '#17171a', borderRadius: 4, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 8, padding: '0 14px', boxSizing: 'border-box'}}>
    <span style={{fontSize: 20, color: C.chalk}}>{name}</span>
    <div style={{display: 'flex', gap: 6}}>
      {(audio ? ['M', 'S'] : ['◉', '⌀']).map((t) => (
        <div key={t} style={{width: 24, height: 20, border: `1px solid ${C.rule}`, borderRadius: 3, fontSize: 13, lineHeight: '18px', textAlign: 'center', color: C.mute}}>
          {t}
        </div>
      ))}
    </div>
  </div>
);

export const ScrubTimeline: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const T = 1.2 + f * 0.3;
  const z = 1 + 0.5 * Math.min(1, f / dur);
  const pps = 118 * z;
  const X = (t: number) => PH - HEAD + (t - T) * pps;
  const cur = V1.find((c) => T >= c.t0 && T < c.t0 + c.d) ?? V1[V1.length - 1];
  const end = V1[V1.length - 1].t0 + V1[V1.length - 1].d;
  const vis = (t0: number, d: number) => X(t0 + d) > -20 && X(t0) < 1080 - HEAD + 20;
  const lane = (k: keyof typeof ROWS, children: React.ReactNode) => (
    <div style={{position: 'absolute', left: HEAD, right: 0, top: ROWS[k][0], height: ROWS[k][1], overflow: 'hidden'}}>{children}</div>
  );
  // ruler ticks
  const t0 = Math.floor(T - (PH - HEAD) / pps);
  const ticks = [];
  for (let t = t0; t < T + (1080 - PH) / pps + 1; t += 0.5) {
    if (t < 0) continue;
    const x = X(t);
    const major = t % 1 === 0;
    ticks.push(<div key={`k${t}`} style={{position: 'absolute', left: x, bottom: 0, width: 2, height: major ? 18 : 9, background: major ? '#77756e' : '#45443f'}} />);
    if (t % 2 === 0) ticks.push(<div key={`l${t}`} style={{position: 'absolute', left: x + 6, top: 4, fontSize: 14, color: '#8a887f'}}>{tc(t)}</div>);
  }
  // music waveform, fixed to timeline time so it scrolls with the clips
  const wave: string[] = [];
  const mid = (ROWS.a1[1] - 24) / 2 + 24;
  for (let x = 0; x < 1080 - HEAD; x += 3) {
    const t = T + (x - (PH - HEAD)) / pps;
    if (t < 0) continue;
    const a = (0.3 + 0.35 * Math.abs(Math.sin(t * 2.3)) + 0.35 * rnd(Math.floor(t * 28) + 9000)) * (mid - 30);
    wave.push(`M${x} ${(mid - a).toFixed(1)}L${x} ${(mid + a).toFixed(1)}`);
  }
  return (
    <AbsoluteFill style={{background: BG, fontFamily: F.mono}}>
      <Monitor plate={cur.plate} t={T} progress={T / end} />
      {/* race-weekend sector strip: each sector lights as the edit scrubs through it */}
      <div style={{position: 'absolute', left: 40, right: 40, top: 832, height: 120, display: 'flex', gap: 8, padding: 8, background: 'rgba(11,11,12,0.88)', border: `2px solid ${C.rule}`, borderRadius: 10, boxSizing: 'border-box', opacity: lin(f, 0, 8)}}>
        {SECTORS.map(([s, d], k) => {
          const on = lin(f, 10 + k * 14, 16 + k * 14);
          const last = k === SECTORS.length - 1;
          return (
            <div key={d} style={{flex: last ? 1.3 : 1, position: 'relative', overflow: 'hidden', borderRadius: 6, background: C.panel2}}>
              <div style={{position: 'absolute', inset: 0, background: last ? C.red : C.yellow, transform: `scaleX(${on})`, transformOrigin: '0% 50%'}} />
              <div style={{position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 18px', color: on > 0.5 ? (last ? C.chalk : C.asphalt) : C.mute}}>
                {s && <div style={{fontSize: 20}}>{s}</div>}
                <div style={{fontFamily: F.display, fontSize: last ? 28 : 36, lineHeight: 1}}>{d}</div>
              </div>
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 976, height: 760, background: '#121214', borderTop: `1px solid ${C.rule}`}}>
        <div style={{position: 'absolute', left: HEAD, right: 0, top: 0, height: 44, borderBottom: `1px solid ${C.rule}`, overflow: 'hidden'}}>{ticks}</div>
        <TrackHead name="V2" y={ROWS.v2[0]} h={ROWS.v2[1]} />
        <TrackHead name="V1" y={ROWS.v1[0]} h={ROWS.v1[1]} />
        <TrackHead name="A1" y={ROWS.a1[0]} h={ROWS.a1[1]} audio />
        <TrackHead name="A2" y={ROWS.a2[0]} h={ROWS.a2[1]} audio />
        {lane(
          'v2',
          V2.filter((c) => vis(c.t0, c.d)).map((c) => (
            <Clip key={c.label} x={X(c.t0)} w={c.d * pps - 4} h={ROWS.v2[1]} color={GFX} dark={false} label={c.label}>
              <div style={{position: 'absolute', left: 0, right: 0, top: 58, height: 2, background: 'rgba(255,255,255,0.18)'}} />
              {[0.25, c.d - 0.3].map((k) => (
                <Diamond key={k} x={k * pps} y={59} on={X(c.t0 + k) < PH - HEAD} />
              ))}
            </Clip>
          )),
        )}
        {lane(
          'v1',
          V1.filter((c) => vis(c.t0, c.d)).map((c) => (
            <Clip key={c.t0} x={X(c.t0)} w={c.d * pps - 3} h={ROWS.v1[1]} color={VID} dark={false} label={`${FILE[c.plate]} · Scale`} strip={c.plate}>
              <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 30, background: 'rgba(8,8,10,0.72)'}} />
              {[0.12, c.d * 0.62].map((k) => (
                <Diamond key={k} x={k * pps} y={ROWS.v1[1] - 15} on={X(c.t0 + k) < PH - HEAD} />
              ))}
            </Clip>
          )),
        )}
        {lane(
          'a1',
          <Clip x={X(0)} w={end * pps} h={ROWS.a1[1]} color={AUD} label="soundtrack.wav">
            <svg width={1080 - HEAD} height={ROWS.a1[1]} style={{position: 'absolute', left: -X(0), top: 0}}>
              <path d={wave.join('')} stroke="#7FE0AA" strokeWidth={2} />
            </svg>
          </Clip>,
        )}
        {lane(
          'a2',
          A2.filter((c) => vis(c.t0, c.d)).map((c, i) => (
            <Clip key={i} x={X(c.t0)} w={c.d * pps} h={ROWS.a2[1]} color={SFX} dark={false} label={c.label}>
              <svg width={c.d * pps} height={ROWS.a2[1] - 26} style={{position: 'absolute', left: 0, top: 24}}>
                <path d={`M0 ${(ROWS.a2[1] - 26) / 2} ${Array.from({length: Math.max(2, Math.floor((c.d * pps) / 3))}).map((_, k) => `L${k * 3} ${(ROWS.a2[1] - 26) / 2 + (k % 2 ? 1 : -1) * (24 * Math.exp(-k / 14) * (0.4 + rnd(i * 50 + k)))}`).join(' ')}`} stroke="#9FE6DF" strokeWidth={1.5} fill="none" />
              </svg>
            </Clip>
          )),
        )}
        {/* footer: zoom */}
        <div style={{position: 'absolute', left: 40, right: 40, top: 700, display: 'flex', alignItems: 'center', gap: 18, fontSize: 16, color: C.mute}}>
          <span>ZOOM</span>
          <div style={{position: 'relative', width: 300, height: 4, background: C.rule}}>
            <div style={{position: 'absolute', left: `${(z - 0.8) * 100}%`, top: -7, width: 18, height: 18, borderRadius: 9, background: C.chalk}} />
          </div>
          <span style={{marginLeft: 'auto'}}>4 TRACKS · {V1.length + V2.length + A2.length + 1} CLIPS</span>
        </div>
        {/* playhead */}
        <div style={{position: 'absolute', left: PH - 2, top: 0, height: 680, width: 4, background: C.yellow, boxShadow: '0 0 14px rgba(242,197,0,0.85)'}}>
          <div style={{position: 'absolute', left: -12, top: 0, width: 28, height: 24, background: C.yellow, clipPath: 'polygon(0 0, 100% 0, 100% 60%, 50% 100%, 0 60%)'}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
