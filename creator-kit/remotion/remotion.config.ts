import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// Graphics-only renders (compose_reel.sh) go out as ProRes 4444 with alpha,
// which takes neither a CRF nor a yuv420p pixel format:
//   REMOTION_ALPHA=1 npx remotion render ... --codec=prores --prores-profile=4444 --image-format=png
const alpha = process.env.REMOTION_ALPHA === "1";
if (!alpha) {
  Config.setCodec("h264");
  Config.setCrf(18);
}

// Without this Remotion writes yuvj420p tagged bt470bg - full range, wrong
// primaries. Instagram expects limited-range Rec.709, and a mistagged file
// plays washed out on some devices and oversaturated on others.
Config.setColorSpace("bt709");
if (!alpha) Config.setPixelFormat("yuv420p");
