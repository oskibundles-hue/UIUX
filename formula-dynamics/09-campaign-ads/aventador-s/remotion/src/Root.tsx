import React from "react";
import { Composition, staticFile } from "remotion";
import { AventadorAd } from "./AventadorAd";
import cue from "./cue.json";

// Bebas Neue is bundled in the kit (07-fonts, SIL OFL) and copied into public/.
const font = new FontFace(
  "Bebas",
  `url(${staticFile("BebasNeue-Regular.ttf")}) format("truetype")`
);
font.load().then(() => document.fonts.add(font));

export const RemotionRoot: React.FC = () => (
  <Composition
    id="AventadorAd"
    component={AventadorAd}
    durationInFrames={Math.round(cue.duration * cue.fps)}
    fps={cue.fps}
    width={cue.width}
    height={cue.height}
  />
);
