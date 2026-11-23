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

## Tall Tale 3D shorts: yawn, hiccups, brain freeze, wrinkly fingers, sneeze, never blink (2026-11-20)

Per-video lesson files were merged here when the working folders were cleaned up.

29. **Anything drawn above the character canvas is sliced flat.** The 'bun' hair sat above y = 0 of the 600x1000 design canvas, so its top half was cut ("hair in half"). Rule: keep every hat/hair piece inside y >= 0 (head centre y 178, radius 138), put buns ON the head, and check a full-size still of each new look. The base template now draws full hair (side locks, fringe, bun) and has `pattern: 'swimsuit'` and a `yawn` face state.
30. **Coplanar faces flicker.** A tub whose water slab sat exactly on its top face alternated between the two surfaces. Rule: build tubs/pools from walls with the water sunk below the rim and the rim proud of the walls. Verify with six consecutive cropped frames and ffmpeg `signalstats` YDIF (jumps only at cuts, fades and fast motion).
31. **Too much glow.** Default bloom 0.3 at threshold 0.85 haloes every white head and the interior preset is bright. Rule for interiors: bloom 0.04, threshold 0.98, exposure 0.95, interior lights x 0.6.
32. **The project needs yellow spoken-word captions, the skill ships plain white.** The base template's captions.js now highlights the spoken word (#FFF500). `?nocap=1` on the page gives caption-free frames for thumbnails.
33. **Whisper gives some words ~0 s.** Fix only the FIRST word of a line (set to line start + 0.03). A blanket fix once moved good mid-line words ("a", "the", "gulp"); never edit a word that appears more than once without checking all its copies.
34. **Group shots in 9:16 crop people.** Keep people within about 1 m of the look point, wide cameras about 4.5 m away at fov 52-54, and check that the LAST position of a push-in still frames everyone.
35. **Diagrams: nothing may run through another organ, and repeated tiny icons read as clutter.** A nerve was routed through the eye; a row of closed-eye icons with lashes read as "lots of eyelashes". Rule: route lines around features, draw small repeated icons as a single plain curve, and look at every diagram at full size.
36. **Thumbnails:** hook text must not hide the key visual; the character should sit below the top third. For videos with burned-in captions, crop above the caption area.
37. **Verify before voicing.** Facts flagged TO VERIFY in the plan were checked (blink-to-dry, sneeze with eyes open, fades after drying) before the voice was generated; disputed numbers (sneeze speed, screen blink rate, 430 million hiccups) were left out.
38. **Clean up only after upload.** Deleting a project's src/data removes the only copy of its custom props (pig, dog, tub, fair); the reusable engine pieces were copied back into the base template first.

## "What if you never slept?" revision (2026-11-20)

39. **Do not open on the same character close-up for 14 seconds.** The first version used Randy's face in four shots in a row and an empty bedroom for "1963", which felt boring. Rule: vary subject, place and camera in the first 10 s (a striking hook image, then a new location with period cues such as palms, sea, a vintage car and a sepia look, then another room). Give each historical date a real visual, not an empty room.
40. **Show a concept as a clear cause and effect.** "Reaction time slows" as a falling ball and a hand was unreadable. A rested person catching a tossed ball, then a tired one missing it and getting bonked, with a sun/moon icon and a short green vs long red stopwatch, reads at once.
41. **Brains must match the channel's flat style:** two rounded lobes, a centre line, curly folds and a darker stem (`drawBrain` in the never-slept shots, copied from the goosebumps video). A plain ellipse with a few lines looks like bread.
42. **Show what an idiom means, not the object in it.** "A very short fuse" is losing your temper fast: a tiny annoyance (a fly), a red face, steam and an anger mark, not a firecracker. A press conference needs its own room (stage, podium, microphones, press with flashes), not the bedroom again.
43. **The duplicate-title guard fires on "What if you never X?" pairs (83%).** Retitle with a different ending ("...stayed awake for 11 days?") instead of overriding.
44. **Upload times are UTC; Studio shows local time.** A 23:00 UTC slot lands on the next calendar day for viewers east of UTC+1. Ask the user's time zone, or use a mid-day UTC slot, when they care about which calendar day a video appears on.

## Tall Tale 3D builds (2026-11-21, own-voice-45s)

- **Chrome may be missing**: `capture.mjs` needs `CHROME=...`; Microsoft Edge works (`C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`). Skill path from `out/<name>/project/` is `../../../.claude/skills/faceless-shorts`.
- **Run `node tools/capture.mjs guard` before every render** (it is also inside `video`, which refuses to render until GUARD OK). It checks every head and held prop against the screen edge (24 px) AND the character's own 512 px cut-out canvas (a phone held at hand x~511 was cut in half; keep the holding hand at x <= ~440, phone arm `[145, -118]`). Then verify on frames taken from the FINAL mp4, not only from the check tool.
- **Whisper can return a zero-length word** (a caption that never shows): scan `words.json` for `e - s < 0.05` before rendering.
- **Set `visible` and positions BEFORE `shoot()`** renders; changing them after has no effect on that frame.
- **youtube-upload helper scripts** need `PYTHONPATH=.claude/skills/youtube-upload/_deps` (PIL, tzdata) when run with the system Python.
- **Held props that need to move or point sideways (a tickle feather)**: do not draw them inside the Toon cut-out (512 px wide: they get clipped, can't point toward the target and can't animate). Draw them as a screen overlay from the real hand (`px(design(p, hand))`) to a contact point, with a sweeping angle (`sin(t*15)*0.3`), plus small "effect" marks on the target and a reaction on the target person. A plain leaf-shaped paddle does not read as a feather: use a curved shaft, a fringed/serrated vane, barb lines and a tinted tip, and size it ~250 design px.
- **Actors entering from outside the frame fail the edge guard**: start them inside the frame (lean in, or a short step) instead of walking in from off-screen.

## Doorway sample review (2026-11-22): zoom, flicker, sofa overlap

45. **Close-ups were too tight** (head filled the frame; the thought bubble and brain were cut off). Rule: head diameter at most 52% of the 1080 frame width; the guard now fails with "camera zoomed in too far". Make the set deeper (kitchen 4.6 m instead of 2.6 m) instead of pushing the camera into it.
46. **A seated cut-out had half its body hidden by the sofa, and he walked through the sofa.** The seat plus a front cushion (top 0.62 m) stood in front of his plane, hiding everything below the waist; shot 4 started him inside the sofa volume. Rule: seat top about 0.40 m, plane in the middle of the seat, no front cushion, sofa moved so the walking path is clear. The guard (`hitsSolid`) fails when a person overlaps furniture or a wall above waist height (proved by putting the old 0.62 m seat back: guard failed 6.7-10.6 s).
47. **Coplanar faces flicker (z-fighting).** Door-frame bars vs the lintel and jambs, baseboard end caps vs the wall, fridge panels and sofa seat vs arms shared planes. Rule: `coplanar(scene)` runs at build time and `capture.mjs check` prints CHECK FAILED for each shared same-facing face; fix by making one box 1-2 cm proud.
48. **Check for flicker with numbers, not only by eye.** The mean-luma second difference finds single-frame spikes; an up-down-up pixel test on frames where the camera is nearly still finds local flicker. In the final render the only hits were planned (cuts, the bubble pop, caption pop-in, the fridge light ramp). The report must say what was measured, not just "no flicker".
49. **A seated cut-out's legs vanished behind the seat.** First fix (plane in the middle of the seat) still hid the shins behind the seat's front face. Rule: put the plane just in front of the seat's front face so the knees and shins hang over the edge, seat top about 0.36 m, and frame the whole body (head to feet) so the legs are on screen. Look at a still of every seated shot and ask "can I see his legs?".

## Video 1 build "doorway" (2026-11-22)

50. **Moving a THREE.Group by assigning `position.z = 0` teleports it.** The filing-cabinet drawer group sat at z -2.325; resetting it to 0 put a grey drawer in front of the lens (a "blank grey wall" shot). Rule: keep a named base (`CABZ`) and always set `base + offset`; look at a still of every shot that animates a prop.
51. **Furniture that belongs to one shot hides people in others.** Desks stayed in the lab for the "Dr. Lee" and chalkboard shots. Rule: put shot-specific furniture in a `dynamic` group and toggle `visible` per shot (the solids check ignores dynamic parts).
52. **The set's open side shows the void.** The closing pull-back from the kitchen showed black behind Sam (the living room has no front wall). Rule: shoot toward the closed rooms; check what is behind the subject in every shot.
53. **Flicker measurement needs the caption band masked.** Word-by-word captions pop in and out and flood the oscillation test. Mask y 1230-1570 px, skip planned cuts, and read the remaining hits by eye (here: the window-card slam, a head shake, the scratching arm).
54. **Fast limb oscillation (11 rad/s) looks like jitter at 30 fps.** Keep arm swings under about 6 rad/s.

## Video 2 build "jump" (2026-11-22)

55. **A new project folder needs `src/main.js` too.** I copied `src/core` and wrote `shots.js` but not `main.js`; capture waited 2 minutes and died with "boot timeout" and no error text. Rule: when making a project from another, copy the whole `src/` (or at least `main.js` + `core/`), and treat "boot timeout" with empty logs as a missing module.
56. **Draw functions are pure functions of t, so visibility must be reset in every shot.** Two shots hid Sam (`group.visible = false`); later shots then rendered an empty set (found on the contact sheet: only a pulse card floated). Rule: the position helper (`lkAt`) always sets `visible = true`, and every scene has a reset like `homeReset`/`mdHide`.
57. **A patch script that asserts and stops leaves the file unchanged, but the render command after it still ran.** Rule: chain patch -> check -> render with `&&`, and confirm the patch printed OK before reading any render as "after".
58. **Verify an affiliation from the paper's own record, not popular articles.** PubMed was cookie-blocked; Europe PMC's JSON record gave "Florida State University, Department of Psychology" for the first author, so the approved line stayed. Record the lookup in `script.json` sources.
59. **Sensitive topics: keep the picture as careful as the words.** The "jump" exists only as a stick-figure drawing in a notebook and on a card; the thumbnail text says "THE CALL OF THE VOID", not the urge itself; the description carries the help line.

## Video 3 build "song" (2026-11-22)

60. **Stacked rows read as one tower from a high camera.** Six beds in two columns by three rows collapsed into two stacks, and a three-row classroom piled the thought loops on top of each other. Rule: for group shots use at most two rows, wide columns (three across) and check the first contact sheet for overlap before polishing.
61. **A room that ends behind the camera shows black bars when the camera sits outside it.** The classroom floor ended at z 2.5 while the camera stood at z 8: black strips top and bottom. Rule: size the room to include the camera (zf >= camera z + 1).
62. **Crowds and big groups: draw them in 2D.** Ninety beans as Toon cut-outs would need ~90 canvases of 1024x2048; the stadium is drawn with simple 2D beans and runs fast.
63. **The flicker test also fires on thin lines moving 1-2 px per frame** (the stopwatch hand and ticks), because a moving thin line makes a pixel go light-dark-light. Read each hit against the shot's motion before calling it flicker.

## Video 4 build "phone" (2026-11-22)

64. **drawtext breaks on apostrophes and long lines.** "YOUR POCKET BUZZED?" overflowed at 104 px and "DIDN'T" lost its apostrophe. Rule: measure the thumbnail text (about 84 px for 19 characters), avoid apostrophes in drawtext (reword), and read the thumbnail before shipping.
65. **Street sets draw shop names by default.** `WD.mainStreet` paints lettering on every facade; the project rule is no on-screen text. Rule: pass shops with empty names.
66. **Outward actions need their own go-ahead.** A YouTube upload was allowed; a combined command that also posted to Facebook was blocked. Do each outward action as its own command and keep Facebook cross-posts separate until the user says yes.

## Video 5 build "baby" (2026-11-22)

67. **Set pieces that belong to one shot must be hidden in the others.** The scanner ring stayed in the room and showed behind Sam, Dr. Lee and the chalkboard; it is now a `dynamic` group shown only in the scanner shot. Put the ring BEHIND the child (a pod base in front of the cut-out hides it).
68. **Small characters need the camera at 2.7-3.4 m, not 5 m.** A 0.9 m baby at the usual distance is a speck; keep head width above about 15% of the frame (and below the 52% guard).
69. **Check the schedule right before and after an upload.** The user edits Studio in parallel; between my reschedule and the baby upload the phone video, sneeze and never-blinked dates changed and baby landed on the same slot as sneeze (26 Nov 23:00 UTC). Re-read `yt_upload.py --check` and report differences instead of overwriting.

## Video 6 build "marshall-bacteria" (2026-11-23): details in out/marshall-bacteria/lessons.md
70. **Held props (holdL/holdR) are drawn before the head**, so a prop at the mouth is hidden by the face. Use `faceProp` (drawn after the head and hat) for anything that touches the face (drinking, a hand on the mouth).
71. **Anything drawn above or beside the cut-out canvas is sliced** (hats: lesson 29 again, now fixed in the engine: headroom 256, side padding 192; `capture.mjs toons` + the per-frame sliced-cut-out guard must pass before a render).
72. **Check a science story against the PRIMARY source before voicing it** (Marshall's Nobel lecture contradicted the "antibiotics cured him" version, "a cup", "spicy food", the rejected talk).
73. **Shot-specific props must sit in a group that is hidden in every other shot** (piglets leaked into 7 shots).
74. **Two white flashes within 0.3 s are a photosensitivity risk**: one soft flash only.

## Video 7 rebuild "why-brain-freeze" (2026-11-23): details in the skill recipes
75. **A cleaned-up project cannot be re-rendered**: only the mp4 survived the first brain freeze build, so the "re-render" was a full rebuild with a new script. Rule: before cleaning `out/<name>/`, save `script.json` and `shots.js` to the skill's `tall-tale/recipes/` (done for brain freeze and Marshall).
76. **Re-check old science before re-voicing it**: the migraine claim was stated as fact (sources disagree), the artery was drawn on the palate instead of in the brain, "right before the pain" should be "as the pain hit".
77. **Background extras vs the frame guard**: hero people go to the strict guard; crowd extras go in `look.bg` (they still face the camera and get the sliced-canvas check only); keep extras 4+ m from the camera; two tight rows on a step (0.58 m spacing, camera 7.6 m, fov 48) make ten people readable.
78. **One working folder per video**: everything in `out/<name>/work/`, deliverables beside it, so cleanup after upload is one exact-path delete (the safety check blocks glob deletes).
