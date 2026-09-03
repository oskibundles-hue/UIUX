import React from "react";
import { Composition } from "remotion";
import { Reel, type ReelProps } from "./Reel";

const FPS = 30;
const SECONDS = 24;

// Real content, not lorem: this is the garage walkthrough, cut to the shape a
// Reel actually wants. Swap `phrases` for your own lines and timings.
const defaultProps: ReelProps = {
  src: "clip.mp4",
  hook: "This building was empty 30 days ago",
  handle: "@nq.young",
  endCard: "Send this to whoever you'd bring on the first drive",
  endCardAt: 20,
  showProgress: true,
  phrases: [
    { text: "This is the whole space", start: 3.0, end: 5.2 },
    { text: "right here", start: 5.2, end: 6.3 },
    { text: "Nothing was in here", start: 6.6, end: 8.6 },
    { text: "when I signed the lease", start: 8.6, end: 10.6 },
    { text: "Lifts go along that wall", start: 11.0, end: 13.4 },
    { text: "Detail bay in the back", start: 13.8, end: 16.0 },
    { text: "First car lands next month", start: 16.4, end: 19.0 },
  ],
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Reel"
      component={Reel}
      durationInFrames={FPS * SECONDS}
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
      durationInFrames={FPS * SECONDS}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={{ ...defaultProps, showProgress: false }}
    />
  </>
);
