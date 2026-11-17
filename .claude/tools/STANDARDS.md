# Finishing standards (all three styles)

Every video from this plugin ends the same way unless the user asks for something else.

## Project rules (claudeAnimatedShorts; these override anything below)
- Always 9:16 vertical (1080x1920 or 2K vertical), never 16:9. Length 60-120 s (check with ffprobe before delivery).
- Always generate the voice and the music + SFX mix, and mux them into the mp4 (never deliver a silent video).
- Always burn subtitles into the picture, in every style (Vox included), and write an `.srt` alongside.
- Every output file goes inside this repo's `out/` folder (`out/<name>/`). Never create folders outside `out/`.

## Voice and timing
- Never edit or re-time the voice. The picture follows the voice.
- **Voiceover file given:** `python -I tools/words.py voice.mp3 work/words.json` (add `tl`, `es`, `auto`, ... for other languages). If the user also gave the script, correct misheard words in `work/words.json` against it (keep the times).
- **Script only:** `python tools/tts.py script.txt voice.mp3 --words work/words.json` makes a free Microsoft Edge neural voice (default Andrew, `--voice en-US-AvaNeural` etc. for others, `--rate -5%` for slower). It writes the exact word timings, so Whisper isn't needed. Read `voice_spoken.txt` and fix anything TTS would misread (abbreviations, units, URLs), then re-run. Send the mp3 to the user straight away.
- Total frames = round(duration x 30). Everything runs at 30 fps.

## Sound: voice first
- Write the music + SFX cue sheet in `audio/audio.py` (it already has a worked example; keep the synths, rewrite the cues for the new story). It writes `music.wav` and `sfx.wav`.
- Convert the voice first: `ffmpeg -y -i voice.mp3 -ar 48000 -ac 2 audio/voice48.wav`, then inside `audio/`: `python audio.py` and `python mix.py voice48.wav music.wav sfx.wav`.
- `mix.py` sets the music bed at -16 dB under the voice with a dip at 1-4 kHz, ducks it about 5 dB more while the voice talks, keeps SFX at -11 dB with peaks below the voice, and finishes at -14 LUFS with a -1 dBFS limiter. Check the printed levels. If the user says the voice is hard to hear, lower `MUSIC` (0.12) and `DUCK` (-7).
- Lock the picture timing before the sound. Any timing change means re-running audio.py and mix.py.

## Captions
- **Always (9:16 Shorts / Reels, every style):** burn in word-highlight captions: `python tools/captions.py work/words.json work/captions.ass`, then add `-vf "subtitles=work/captions.ass"` to the final ffmpeg encode (run ffmpeg from the project folder so the relative path works). 1-3 words per chunk, uppercase Arial Black, the spoken word turns yellow (`&H00F5FF&`, rest white) on its exact word start time. This is mandatory: never ship captions where the whole chunk is one colour. Word timings must come from the real voice (`words.json`), not estimated.
- Also write the `.srt` next to the video: `python -I tools/srt.py work/words.json out/subtitles_en.srt`.
- ~~16:9 long-form / Vox no-caption rules~~ are disabled in this project: 16:9 is not used, and Vox-style videos also get burned captions.

## Thumbnails: always two
- Make two curiosity thumbnails, A and B, and recommend one. Always 1080x1920 (9:16).
- Background: a story frame with an expressive face or the mystery object and empty space for text.
- Text: 2-4 huge words that open a question and don't repeat the title (e.g. "THIS WAS / MEDICINE?!"). A white line plus a bigger yellow `#FFD21F` line. Keep text in the top quarter on Shorts and everything important above the bottom 20 % (the Shorts UI covers it).
- Tool for the cartoon style: `node tools/thumbnail.mjs thumb/thumb_a.json` (spec: `bg`, `out`, `lines[]`, optional `ring`, `arrow`, `badge`; see the example spec in the kit). The Vox style renders its thumbnails as Remotion `<Still>`s.

## Post text
- Finish with copy-ready **title + description/caption + hashtags** in chat and in `out/post_text.txt`. No emojis.

## Rendering on a home PC
- Render in the foreground and keep the PC awake: a sleeping PC freezes the render. On Windows, tell the user to set Sleep to "Never" while rendering, or ask for keep-awake if the app offers it.
- Send a stills contact sheet before the long render (`python tools/sheet.py <stills_dir> <sheet.jpg>`), then QA the final video with a contact sheet of about 12 frames.
- Keep the previous version as `*_v1.mp4` when re-rendering.

## Content rules
- Stories, characters and shots are original. Never recreate another creator's video, characters or branding.
- No real living people as cartoon characters, no brand logos or mascots.
- If the video presents something as true, check the key facts with a web search and tell the user about anything that's off.
