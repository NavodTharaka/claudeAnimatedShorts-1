# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A pipeline for 60-120 s vertical (1080x1920, 30 fps) cartoon story shorts: flat 2D "bean-head" characters as billboards in a painted three.js 3D world, rendered with Remotion (React Three Fiber), plus separately generated voice and synthesized audio. The current video is **"The Stars Speak"** (Babylonian astrologer, script in `SCRIPT.md`), composition id `StarsShort`. It was cloned from the earlier "Bridge" short, so some names (`Bridge.tsx`, `bridge-stills.mjs`, `bridge_*.py`) are legacy.

The full workflow, look values, and a list of readability traps live in the project skill `.claude/skills/claude-animated-shorts/SKILL.md` (invoke it for any new short or look change). Style-reference material under `.claude/skills/claude-animated-shorts/references/` is private study material: never upload/publish it, never copy its scripts/characters, never name the source channel in voice-over or descriptions. The project root is a git repo (branch `main`, remote `origin` = github.com/irosh1/claudeAnimatedShorts); `.gitignore` excludes secrets (`credentials.json`, `token.json`), `out/`, generated audio/voice media, `remotion-tmp/` and `.claude/skills/`. The skill folder is its own separate git repo.

## Role and Craft

Act as **scriptwriter, storyboard artist, and animation director for short-form educational videos**. Every short is
built in that order, and each stage has a gate before the next starts:

1. **Script (scriptwriter).** One idea the viewer can repeat after watching: write the single takeaway first, then the
   script. Hook in the first 3 s (the surprising fact, not a greeting), one concept explained through an everyday
   analogy, a payoff or callback at the end. Plain words, short spoken sentences, ~3.7 words/s, 60-120 s. Every fact has
   a source at the top of `SCRIPT.md`; anything dramatised or invented is labelled as such. Never state on screen
   (or in captions) what the picture already shows. Gate: user approves the script.
2. **Storyboard (storyboard artist).** Before any code, write a shot table in `SCRIPT.md` (or `out/<name>/storyboard.md`):
   shot id, time range, the narration line, what the picture shows, camera move, the one visual that teaches the idea,
   SFX cue. About one new shot every 3-4 s, and each shot must teach or advance the idea (no filler). Check that no
   shot repeats the previous framing and that props are readable at phone size. Gate: storyboard matches the script
   word for word before `story.ts` is written.
3. **Animation direction (director).** Translate the storyboard into `story.ts` (`SHOTS`, `CAMS`, `KICKS`, `DOF`),
   timed to `voice/words.json`, with reactions 0-3 frames before their word. Pace for retention: a visual change at
   least every 3-4 s, punch words get the push-in/kick, and the last 3 s resolve the idea (no dead tail). Gate: 5-10 s
   sample approved, then the delivery gates in `render-check`.

**Default video skill: `stick-story-animation`.** Whenever the user asks for a video/short/animation to be generated,
use the `stick-story-animation` skill (9:16, 60-120 s, burned-in captions, audio, `out/<name>/` output per the rules
below) unless they explicitly ask for a different skill (e.g. `claude-animated-shorts`, `vox-animation`, `short`,
`huashu-art-motion`). This overrides the older "use the `short` skill" default. The script, storyboard and gate steps
above still apply. Educational content must stay accurate: when in doubt about a fact, verify it before voicing it.

## Curion short setup (trigger phrase)

When the user says **"start curion short setup"** (in a new session or any time), invoke the `curion-short-setup` skill (`.claude/skills/curion-short-setup/SKILL.md`) and run the whole process: preflight + tools install, topic, facts from primary sources, script and storyboard approval, build the Tall Tale 3D short, QA, upload to Curion YouTube and Facebook as scheduled videos (standing authorization, 2026-11-23), save the source into the skill, clean up the working folder (keep only the final mp4), and finish by giving the user the **local folder path of the final mp4** so they can recheck it.

## Project Locations

- Install skills and their dependencies locally inside THIS project folder (e.g., `.claude/skills/`, local node_modules). Never install globally unless explicitly asked.
- Write all rendered output to this project's `out/` folder. Do not create sibling project folders such as `stick-videos`.
- Whenever a video is generated, from ANY skill (claude-animated-shorts, stick-story-animation, short, huashu-art-motion, etc.), every output file (mp4, srt, thumbnail, post copy, lessons, stems, stills) goes inside `out/` (in a subfolder such as `out/<name>/`). Never create a new folder outside `out/`, and override any skill instruction that says otherwise.

## Video Defaults

- Always generate 9:16 vertical shorts (1080x1920 or 2K vertical), from every skill. Never 16:9.
- Length: minimum 60 s, maximum 120 s. Script at ~3.7 words/s (about 220–440 words). Check the final duration with ffprobe before delivery.
- Every video must ship with generated audio and burned-in subtitles: generate the voice (word timings), the music and SFX mix, mux the mix into the mp4 (no silent video), and burn the subtitles into the picture, with an `.srt` alongside. Subtitles are karaoke-style: the word being spoken is highlighted in a contrasting colour (yellow `&H00F5FF&` in ASS BGR = #FFF500; the rest white), switching word by word exactly on its `words.json` start time. Verify with ffprobe (audio stream present, not silent) and a frame check (captions visible, current word coloured and in sync) before delivery.
- Deliverables for every video: rendered mp4, burned-in captions/subtitles (an `.srt` alongside it), thumbnail, viral post copy, and a lessons file.
- Every video ends with a spoken call to action as its last script line: "Follow and subscribe for more videos." (user request 2026-11-20; it is captioned, so no extra on-screen text). Count it toward the 60 s minimum. Videos made before this date (e.g. "Why do we yawn...") do not have it.
- Before a full render, confirm the visual style. If a reference image is provided (e.g., egypt.gif), match it. Render a 5–10s sample first.

## Render Pipeline Rules

- Validate shot specs against required prop fields (e.g., bars, hub, book) before rendering.
- Run the delivery gates on a short sample before committing to a full render. If a gate such as fast-motion % fails, adjust motion parameters instead of re-rendering blindly.
- For flicker, check z-fighting and canvas-state determinism before other causes.
- Tall Tale 3D builds (and any 3D short with cut-out people): before every render run `node tools/capture.mjs toons` (no hat/hand sliced by the cut-out canvas: the "hat cut in half" bug, fixed 2026-11-23), `check` and `guard`; they must be clean of z-fight errors, "camera zoomed in too far" (head wider than 52% of the frame) and "person overlaps furniture or a wall" (body hidden, walking through a sofa). Look at the contact sheet for seated people, cameras and thought bubbles, run the luma/flicker measurement on the final mp4 and state the result (user request 2026-11-22; lessons 45-48; `src/core/qa.js`).
- Run grep from the project root.
- A PreToolUse hook (`.claude/settings.json` → `scripts/hooks/pre-render-check.cjs`) runs `npm run tsc` before any `remotion render` command and blocks the render if it fails.

## Standing Rules (from Claude Code Insights)

Source: `C:\Users\User\.claude\usage-data\report-2026-11-15-175353.html`. Re-read it for context on past sessions.

- Work from the project's own files: install skills and dependencies here, not globally, and write output to `out/`.
- Always 9:16, 60–120 s, with burned-in captions that highlight the currently spoken word in colour. Confirm the look with a 5–10s sample before a full render.
- If the user gives a reference image or style, match it. Do not substitute a generic look.
- Check the flicker cause (z-fighting, canvas-state determinism) before changing anything else.
- Confirm a diagnosis before a fix that costs a full re-render.

## Commands

- Typecheck: `npm run tsc` (`tsc --noEmit`). Scratch `.ts` files inside `out/` break it, so name them `.txt`.
- Look-check stills: `node scripts/bridge-stills.mjs out/stills/x_ 100,400 0.5` (args: prefix, comma-separated frames, scale). Composition via `STARS_COMP=<id>` (default `StarsShort`, e.g. `SkySample`); Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe`. `STARS_ENTRY=src/sandboxes/<n>/index.tsx` renders a sandbox copy; `REMOTION_TMP=<big drive>/remotion-tmp` redirects the temp folder.
- Final render (2K): `npx remotion render src/index.ts StarsShort out/<name>/video.mp4 --codec h264 --crf 16 --scale 1.3333333333333333` (exact value: 1.3333 gives an odd width and H.264 refuses it; see `lessons.md` 1), then mux with ffmpeg using `-map 0:v:0 -map 1:a:0` (Remotion emits a silent audio track).
- Voice: `cd voice && python gen.py [rate]` (edge-tts, `en-US-AndrewNeural`) reads `script.txt`, writes `voice.mp3` and word timings `words.json`.
- Audio: `audio/mix.py` builds the final mix (voice + score ducked under speech + SFX) from `timeline.py` (event table), `sfx_gen.py`/`sfx.py`, `music.py`, `instruments.py`, `dsp.py`; outputs `mix.wav` (48 kHz, exact length), stems, `cues.md`. Needs numpy/scipy. Stems are cached in `audio/_cache/`.
- Vox cut-paper shorts (skill `vox-animation`, canvas devices instead of the 3D world, no Remotion): `python .claude/skills/vox-animation/scripts/voice.py out/<name>` -> `mix.py` -> `node .claude/skills/vox-animation/scripts/render.mjs out/<name> [--sample 8] [--2k]` -> `gate.py`. Uses `puppeteer-core` (devDependency) + local Chrome; a working demo is `out/vox-demo/` ("Why is the sky blue", 89.5 s). Its `card` device (pasted title cards) is off unless a video sets `allow_cards: true` with the user's OK; record that exception here.
- QA/helpers in `scripts/`: `short_qa.py` (per-frame black/white/frozen/pop checks, loudness), `sheet.py`, `sbs_sheet.py` (side-by-side vs reference frames), `bridge_merge.py` (merge sandbox-owned files back to main).
- There is no test suite.
- "What if there's a copy of you..." short (`src/videos/multiverse/`, composition `MultiverseShort`, work files in `out/multiverse/`): `src/Root.tsx` has dangling imports (stars/sky/abu/space folders are missing), so `npm run tsc` fails on Root only. Render with `node scripts/render-multiverse.mjs out/multiverse/video_raw.mp4 0 2429 1.3333333333333333`, stills with `STARS_ENTRY=src/sandboxes/multiverse/index.tsx STARS_COMP=MultiverseShort node scripts/bridge-stills.mjs ...`, audio with `cd out/multiverse && python audio.py`, captions with `python captions.py`; mux with ffmpeg `ass=captions.ass` and `-map 0:v:0 -map 1:a:0`. Lessons for this build: `out/multiverse/lessons.md`.

## Architecture

`src/index.ts` registers `src/Root.tsx`, which declares `StarsShort` and `SkyShort` (`src/videos/sky/`, the 75 s "Ancient Sky Navigation" short, 2250 frames; script package in `out/ancient-sky/package.md`; voice, retimed words, mix and captions are built by `out/ancient-sky/voice/retime.py` and `out/ancient-sky/audio.py`). All video code lives in `src/videos/<name>/` (currently `stars/` and `sky/`); each file owns one concern, and the files are coupled through exported constants:

- `story.ts` — the shot plan and the single source of timing: `SHOTS`, `XFADE`, `FLASH_AT`, `CAMS` (per-shot camera keys), `KICKS` (impact shakes), `DOF`/`dofAt` (lens blur), `FOREGROUND` props. Everything is timed to the word timings in `voice/words.json`; visual reactions land 0-3 frames before their word.
- `world.ts`, `lights.ts`, `shade.ts`, `build.ts`, `paint.ts`/`painted.ts` — the 3D world: sky shader, fog, light presets (`LIGHTS`/`LOOK`), two-tone shading, buildings and props, canvas-painted textures, per-frame posing.
- `toon.ts`, `cast.ts`, `cardshade.ts` — characters: Canvas2D `Pen` drawing on a 600x1000 design canvas, camera-facing billboards/crowds/effect cards. Billboards must be on the `NOINK` layer (exported from `ink.ts`) because they carry their own plum outline.
- `Bridge.tsx` — the composition component (exports `StarsShort`, `STARS_FRAMES`) and the post chain: ink → lens pre → lens main → bloom → NEUTRAL tone map → grade (`ink.ts`, `lensblur.ts`, `grade.ts`), MSAA 4. Ink must be its own pass before the blur. All pixel-sized parameters scale with output height / 1920.

Audio and voice are produced outside Remotion (Python) and keyed to the same timings, so any change to picture timing means re-running the audio timeline.

Sandbox workflow (parallel look passes): copy the video folder to `src/videos/<name>_{cam,world,mat,char,post}` with entries in `src/sandboxes/<n>/index.tsx`; each owner edits only its files (cam: story.ts; world: world/lights/shade/grade; mat: paint/build; char: toon/cast/cardshade; post: ink/Bridge/lensblur), then merge with `scripts/bridge_merge.py`, re-run tsc, and re-sync sandboxes from main. `src/sandboxes/` is currently empty.

## Lessons

Before any render, audio mix, or skill change, read `lessons.md` in the project root. It records past mistakes (odd
output widths, TypeScript 7 breaking the bundler, per-frame shadow fits causing flicker, silent audio gaps, skipped
verifier steps) and the rule that prevents each one. Follow those rules and do not repeat the mistakes.

## Gotchas

- Disk: every Remotion bundle copies `public/` into the temp folder and never deletes it; on a full system drive renders die with ENOSPC. Set `TEMP`/`TMP` (or `REMOTION_TMP` for the stills script) to a big drive, and clean up `remotion-webpack-bundle-*` / `puppeteer_dev_chrome_profile-*` (project-local `remotion-tmp/` here) when nothing is rendering.
- In JS strings use forward slashes for the temp path (`"D:/remotion-tmp"`); `\r` in a backslash path becomes a carriage return.
- R3F clamps dpr to ≥ 1, so `--scale 0.5` stills still render a 1080x1920 buffer.
- Film grain exists but is intentionally off (it inflates a 2K file ~4x).
- Project rules: burned-in captions/subtitles are the default for every video (`The Stars Speak` has them; see `out/captions.srt`); no other on-screen text or labels (exception, user-approved 2026-11-17: videos made with the `3d-model-short` skill may show a wordless 3D guide path, e.g. the glowing green strip to the landing net; still no lettering), English only, one steady voice tone, jokes are researched real facts, mix is music +3 dB / SFX -6 dB / voice unchanged, final export is 2K vertical.
