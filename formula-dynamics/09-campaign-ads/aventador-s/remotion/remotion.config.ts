import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setCodec("h264");
// Chromium is pre-installed in this environment; do not let Remotion fetch one.
Config.setChromiumOpenGlRenderer("swangle");
