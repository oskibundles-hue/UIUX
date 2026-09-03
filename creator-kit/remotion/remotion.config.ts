import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setCodec("h264");
Config.setCrf(18);

// Without this Remotion writes yuvj420p tagged bt470bg - full range, wrong
// primaries. Instagram expects limited-range Rec.709, and a mistagged file
// plays washed out on some devices and oversaturated on others.
Config.setColorSpace("bt709");
Config.setPixelFormat("yuv420p");
