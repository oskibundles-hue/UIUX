import React from "react";
import { Composition } from "remotion";
import { Reel, type ReelProps } from "./Reel";

const FPS = 30;
const SECONDS = 32.1;

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
    />
    <Composition
      id="Reel1080"
      component={Reel}
      durationInFrames={Math.round(FPS * SECONDS)}
      fps={FPS} width={1080} height={1920}
      defaultProps={mimic}
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
