// usage: node scripts/render-multiverse.mjs <out.mp4> [startFrame] [endFrame] [scale]
// Renders the MultiverseShort composition from its own entry (src/sandboxes/multiverse) so the unrelated broken
// imports in src/Root.tsx do not matter. Needs REMOTION_TMP on a big drive. Audio is muxed separately with ffmpeg.
import fs from "node:fs";
if (process.env.REMOTION_TMP) { fs.mkdirSync(process.env.REMOTION_TMP, { recursive: true }); process.env.TEMP = process.env.TMP = process.env.REMOTION_TMP; }
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [out, a = "0", b, scale = "1"] = process.argv.slice(2);
const browserExecutable = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const chromiumOptions = { gl: "angle" };
const serveUrl = await bundle({ entryPoint: path.resolve("src/sandboxes/multiverse/index.tsx"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: "MultiverseShort", browserExecutable, chromiumOptions });
const frameRange = [Number(a), b ? Number(b) : composition.durationInFrames - 1];
let last = 0;
await renderMedia({ composition, serveUrl, codec: "h264", crf: 16, outputLocation: out, scale: Number(scale), frameRange, browserExecutable, chromiumOptions,
  timeoutInMilliseconds: 180000, concurrency: 4,
  onProgress: ({ renderedFrames }) => { if (renderedFrames - last >= 60) { last = renderedFrames; console.log("frames", renderedFrames); } } });
console.log("done", out);
