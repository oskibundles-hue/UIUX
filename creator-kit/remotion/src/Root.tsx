import React from "react";
import { Composition } from "remotion";
import { Reel, type ReelProps } from "./Reel";

const FPS = 30;
const SECONDS = 33.8;

// Real content, not lorem: this is the garage walkthrough, cut to the shape a
// Reel actually wants. Swap `phrases` for your own lines and timings.
const defaultProps: ReelProps = {
  src: "clip.mp4",
  hook: "30 days ago this was an empty building",
  handle: "@nq.young",
  endCard: "Send this to whoever you'd bring on the first drive",
  endCardAt: 29,
  showProgress: true,
  phrases: [],
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Reel"
      component={Reel}
      durationInFrames={Math.round(FPS * SECONDS)}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
    />
    {/* Same template with the progress bar off, for when the footage is busy
        at the top of frame. */}
    <Composition
      id="ReelNoProgress"
      component={Reel}
      durationInFrames={Math.round(FPS * SECONDS)}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={{ ...defaultProps, showProgress: false }}
    />
  </>
);
