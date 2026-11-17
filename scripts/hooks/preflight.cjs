// SessionStart hook: report what this project needs before rendering. Read-only and never blocks the session;
// its output is added to Claude's context. Install problems are fixed by the `animation-setup` skill.
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = process.env.CLAUDE_PROJECT_DIR || path.resolve(__dirname, "../..");
const has = (cmd, args = ["-version"]) => spawnSync(cmd, args, { encoding: "utf8", shell: process.platform === "win32" }).status === 0;
const pyOk = (mod) => spawnSync("python", ["-c", `import ${mod}`], { encoding: "utf8" }).status === 0;
const chrome = "C:/Program Files/Google/Chrome/Application/chrome.exe";

const checks = [
  ["node", has("node", ["--version"]), "install Node.js LTS"],
  ["npm", has("npm", ["--version"]), "install Node.js LTS (includes npm)"],
  ["ffmpeg", has("ffmpeg"), "winget install -e --id Gyan.FFmpeg"],
  ["ffprobe", has("ffprobe"), "winget install -e --id Gyan.FFmpeg"],
  ["node_modules", fs.existsSync(path.join(root, "node_modules")), "run `npm install` in the project root"],
  ["Chrome (stills script)", fs.existsSync(chrome), `expected at ${chrome}; edit scripts/bridge-stills.mjs if it lives elsewhere`],
  ["python numpy/scipy", pyOk("numpy") && pyOk("scipy"), "pip install numpy scipy"],
  ["python edge_tts", pyOk("edge_tts"), "pip install edge-tts"],
  ["voice/words.json", fs.existsSync(path.join(root, "voice", "words.json")), "run `cd voice && python gen.py`"],
  ["out/ folder", fs.existsSync(path.join(root, "out")), "create out/ (rendered output goes here)"],
];

const missing = checks.filter(([, ok]) => !ok);
const lines = ["Project preflight (StarsShort):"];
for (const [name, ok] of checks) lines.push(`  ${ok ? "OK     " : "MISSING"} ${name}`);
for (const [name, , fix] of missing) lines.push(`  fix ${name}: ${fix}`);
if (missing.length === 0) lines.push("All checks passed.");
process.stdout.write(lines.join("\n") + "\n");
process.exit(0);
