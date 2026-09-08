import React from "react";
import { Composition } from "remotion";
import { Reel, type ReelProps } from "./Reel";
import { Motion, type MotionProps } from "./Motion";
import { Intro, type IntroProps } from "./Intro";

const FPS = 29.97;
const SECONDS = 32.1;

/**
 * Duration follows the props: `--props=reel.json` carrying `durationSeconds`
 * (written by scripts/assemble_reel.py) sizes the composition to the footage,
 * so one composition serves any cut without editing this file.
 */
const fromProps = ({ props }: { props: ReelProps }) => ({
  durationInFrames: Math.round(FPS * (props.durationSeconds ?? SECONDS)),
});

/**
 * Matches the reference edit: footage plus captions, no other overlays.
 *
 * `phrases` is empty because there is no transcript for this clip yet. Drop
 * the real lines in here (or pass --props) and the captions appear; inventing
 * words and burning them in as the speaker's would be worse than none.
 */
const mimic: ReelProps = {
  src: "clip.mp4",
  phrases: [],
};

/** Style proof: the caption renderer with the reference's own wording. */
const styleProof: ReelProps = {
  src: "clip.mp4",
  phrases: [{ text: "Alexa has completed", start: 0, end: 3.0 }],
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Reel4K"
      component={Reel}
      durationInFrames={Math.round(FPS * SECONDS)}
      fps={FPS} width={2160} height={3840}
      defaultProps={mimic}
      calculateMetadata={fromProps}
    />
    <Composition
      id="Reel1080"
      component={Reel}
      durationInFrames={Math.round(FPS * SECONDS)}
      fps={FPS} width={1080} height={1920}
      defaultProps={mimic}
      calculateMetadata={fromProps}
    />
    <Composition
      id="Motion4K"
      component={Motion}
      durationInFrames={Math.round(FPS * SECONDS)}
      fps={FPS} width={2160} height={3840}
      defaultProps={{ src: "clip.mp4", words: [] } as MotionProps}
      calculateMetadata={({ props }: { props: MotionProps }) => ({ durationInFrames: Math.round(FPS * (props.durationSeconds ?? SECONDS)) })}
    />
    <Composition
      id="Intro4K"
      component={Intro}
      durationInFrames={Math.round(FPS * 5)}
      fps={FPS} width={2160} height={3840}
      defaultProps={{ line1: "Omari'e", line2: "Young", sub: "Anti Stock · Formula Dynamics", handles: ["@nq.young", "@Youngomarie"] } as IntroProps}
      calculateMetadata={({ props }: { props: IntroProps }) => ({ durationInFrames: Math.round(FPS * (props.durationSeconds ?? 5)) })}
    />
    <Composition
      id="StyleProof"
      component={Reel}
      durationInFrames={72}
      fps={FPS} width={2160} height={3840}
      defaultProps={styleProof}
    />
  </>
);
