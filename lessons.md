# Lessons (mistakes to avoid)

Read this before any render, audio, or skill change. Each entry: what went wrong, why, and the rule to follow.

## Rendering

1. **Odd output width from `--scale 1.3333`.** 1080 x 1.3333 = 1439.9999... and H.264 refused it.
   Rule: use the exact value `--scale 1.3333333333333333` (1440 x 2560), and check the width is even before a long render.

2. **Full render crashed at frame 195 on a `dispose` call.** I assumed the ink pass had a `dispose` method. It did not
   fail at type-check time, only at run time. Rule: after any change to effects or the composer, render a 10-frame test
   (`--frames=190-200`) before starting the 25-minute full render.

3. **Remotion bundler failed with `typescript.sys` undefined.** `npm i typescript` pulled TypeScript 7, which Remotion
   cannot load. Rule: pin `typescript@5.6.x`. Check `node -e "require('typescript').version"` after installs.

4. **Temp disk.** Every bundle copies `public/` into the temp folder. Rule: always set `TEMP`/`TMP` to a big drive
   (project-local `remotion-tmp/` here) before rendering.

5. **Stills script ran the wrong composition id.** It still pointed at `BridgeShort` after the rename. Rule: after renaming
   a composition, grep for the old id in `scripts/` and in `CLAUDE.md`.

## Flicker and look

6. **Flicker from a per-frame shadow fit.** The sun shadow frustum was resized every frame from camera distance. The
   shadow map shifted. This was NOT the cause of the 752-776 flicker, though the fix is still kept as good practice.
   Rule: shadow frustum size and focus are fixed per shot. Never recompute them per frame.

6b. **Real cause: z-fighting.** The ziggurat's top tier face and its blue glaze rim had the same top height (y = 46).
    The GPU alternated between them frame by frame, which looked like flicker. I found it by turning shadows off for
    that shot: the dithered pattern stayed, so shadows were not the cause. Rule: never put two faces at the same height.
    Offset the overlay (for example +3 cm), and check any flicker with a shadow-off test before changing the shadow code.

7. **QA spikes were trusted as real without looking.** The frame-diff pops at 538, 584, 633, 752-776 and 844 were only
   checked after the fact, by eye, at the end. Rule: when QA flags a pop, extract those exact frames and look before
   changing code. Check whether it is a planned cut, a light change, or a real bug.

8. **Night shots with a moon light.** The eclipse tint (`uLitCol`) and per-frame sun/moon settings change the lit colour.
   Rule: any light parameter that changes over time must change smoothly, and be tested across the change.

## Audio

9. **Audio gaps.** The mix had silent stretches (for example 42.2 s). A silent gap in the mix reads as a dropout.
   Rule: run `silencedetect` on every mix. Any gap over about 0.3 s needs a bed (pad) or a deliberate reason to be silent.

10. **Too many sound effects.** Crickets, crowd murmurs, gulps and extra whooshes were added without need. Rule: each
    SFX must mark a visible event or a scene change. Otherwise leave it out. Keep scene-change whooshes only at place
    changes, not at every cut.

11. **Word timings and script text can drift apart.** The `words.json` tokens did not match `script.txt` one-to-one
    (253 tokens against 252 timings) until I aligned them by hand. Rule: check token counts match before timing any
    picture or sound to them.

## Project rules and process

12. **Skill's "no captions" rule vs. the user's request.** The skill says "No captions or labels in the video". The user
    later asked for subtitles on this video, and I added them. Rule: project rules in `CLAUDE.md` and the skill are
    defaults. When the user changes one for a video, record the exception in `CLAUDE.md`, so later work does not
    reapply the old rule.

13. **Skill installed to the wrong place first.** I put it in the global `~/.claude/skills/`, and the user asked for the
    project folder. Rule: when the user says "this folder, not global", install into the project and check the path
    before reporting.

14. **Verifier agents were skipped and not clearly reported.** The skill requires Opus verifier rounds. I checked
    stills by eye instead. Rule: name every skipped pipeline step in the final report, with the reason.

15. **Blocked wait commands.** A long `sleep` in the foreground was blocked. Rule: wait on background jobs with
    `Monitor` or a `run_in_background` command that exits when the condition is met.

16. **Caption burn-in was not checked on all frames.** Subtitles were checked on one frame only. Rule: check caption
    timing on a few lines at start, middle and end, and confirm each line appears on the right word.

17. **Guessing the cause of a flicker.** The first fix (shadow frustum) was a guess from code reading, and it did not
    fix the pops. Rule: when QA flags a flicker, reproduce it with two or three stills first, then test one change at a
    time with stills. Full renders take about 25 minutes, so only start one after a still shows the fix works.

18. **Rules drifted out of sync between files.** The skill and CLAUDE.md said `--scale 1.3333` (odd width) while lesson 1
    said the exact value, and the skill still named `BRIDGE_ENTRY` after the script moved to `STARS_ENTRY`. Rule: when a
    command, flag or env var changes, grep `CLAUDE.md`, `lessons.md` and every `.claude/skills/*/SKILL.md` for the old
    form and update them in the same pass.

19. **Building before the storyboard matched the script.** Shots written straight into `story.ts` drift from the narration.
    Rule: write the shot table first, check it against `script.txt` word for word, then code `story.ts`.

## Vox skill install (2026-11-17)

26. **edge-tts drops requests at random** (`NoAudioReceived`, even on short plain sentences that worked a moment before).
    Rule: pace requests and retry with backoff, and cache each recorded line so a re-run only redoes what is missing
    (`vox-animation/scripts/voice.py` does both). Do not treat one failure as a bad script.
27. **A third-party skill shipped author-machine paths and 16:9 defaults** (`~/Desktop/infographic-generator/...`, 1920x1080,
    output beside the script). Rule: before reporting an imported skill installed, grep its scripts for absolute paths,
    sizes and output folders, and make them match CLAUDE.md; then run it end to end on a demo and read the gate output.
28. **ffprobe `-of csv=p=0` prints a trailing comma for some entries** (`240,`), so `Number()` gave NaN and silently
    disabled a truncation guard. Rule: use `-of default=nw=1:nk=1` when a script parses a single value.

## Ancient Sky Navigation (2026-11-16)

20. **ffmpeg `subtitles=` drew nothing on an .srt in this build** (no error). Rule: convert the .srt to a styled .ass with
    `PlayResX/Y 1080x1920` (pixel units) and burn with the `ass` filter. libass's default 384x288 canvas puts `MarginV=300`
    off-screen. When checking a burned frame use `-i video -ss t` (output seek); `-ss` before `-i` restarts the clock and the
    caption is not due yet.
21. **Voice ran 71.2 s for a 75 s short.** Slowing the TTS rate would have moved the approved sample's timings. Rule: keep the
    single TTS pass and insert pauses between sections (`voice/retime.py`, cuts in the middle of the existing gap), which
    leaves earlier timings untouched and also writes the retimed `words75.json`.
22. **New 3D places had cameras inside geometry** (sail in front of the lens, a house wall, a full-footprint glaze box that was
    the whole terrace floor, a shrine filling the frame, a heel stone covering the sun, a pull-back that went underground).
    Rule: render one still per shot of every new place before any video render, and check what is between the lens and the
    subject (a tall prop, a flat box top, the ground plane when pulling a low camera back).
23. **DOF focused on the camera look-target blurred the foreground subject** (the priest). Rule: when the subject sits in front
    of the look-point, give that shot's DOF entry a `focus` function.
24. **TTS merges tokens** ("4,500 years" came back as one word, 152 tokens vs 153 script words). Rule: align `words.json` to
    `script.txt` by normalized text and assert nothing is left over before building captions.
25. **A character card too close to the lens filled the frame** (priest, 2.7 m away, 25 frames; found only by QA flagging the pop).
    Rule: for each shot check the nearest card to the lens, and when only a few frames are wrong re-render just that frame
    range (`--frames=a-b`) and splice it from the raw render in one encode, instead of redoing the whole short.
