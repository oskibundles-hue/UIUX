import React from 'react';
import {Composition} from 'remotion';
import {Ad, TOTAL} from './Ad';
import {FPS, W, H} from './theme';
export const Root: React.FC = () => (
  <Composition id="RaceWeekend" component={Ad} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
);
