import React from 'react';
import {Composition} from 'remotion';
import {Ad, Ad30, TOTAL, TOTAL30} from './Ad';
import {FPS, W, H} from './theme';
export const Root: React.FC = () => (
  <>
    {/* the 76 s reference: how these pixel-animated ads are built */}
    <Composition id="RaceWeekend" component={Ad} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
    {/* the 30 s ad cut from it (src/cut30.json) */}
    <Composition id="RaceWeekend30" component={Ad30} durationInFrames={TOTAL30} fps={FPS} width={W} height={H} />
  </>
);
