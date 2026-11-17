# Claude Animated Shorts

A pipeline for making **60-120 s vertical (1080x1920, 30 fps) cartoon story shorts** for YouTube Shorts and Facebook Reels.
Flat 2D "bean-head" characters stand as billboards inside a painted three.js 3D world. The video is rendered with
[Remotion](https://www.remotion.dev) (React Three Fiber). Voice, music and sound effects are generated separately in
Python and muxed into the final mp4. Captions are burned in.

---

## 1. Requirements

| Tool | Used for |
|---|---|
| Node.js (18+ recommended, tested on 24) and npm | Remotion, three.js, TypeScript |
| Python 3.10+ | voice, audio synthesis, QA, uploaders |
| ffmpeg and ffprobe (on PATH) | muxing audio, duration/stream checks, thumbnails |
| Google Chrome | stills script (`C:/Program Files/Google/Chrome/Application/chrome.exe`) |
| Python packages | `numpy`, `scipy`, `edge-tts`, `requests`, `pillow`, `google-api-python-client`, `google-auth-oauthlib` |

Note: `.claude/skills/` is a separate git repo and is git-ignored here, so a plain clone does not include the skills or the upload scripts; copy that folder over separately.

A disk with several GB free is needed: every Remotion bundle copies `public/` into the temp folder.

## 2. Setup

```bash
git clone https://github.com/irosh1/claudeAnimatedShorts.git
cd claudeAnimatedShorts

npm install                      # keep typescript on 5.6.x (`~5.6.3`); TypeScript 7 breaks the Remotion bundler
pip install numpy scipy edge-tts requests pillow google-api-python-client google-auth-oauthlib

npm run tsc                      # typecheck, should be clean
```

Inside Claude Code, the `animation-setup` skill checks and installs Node, Python, ffmpeg and the packages for you
(`"check my setup"`). A SessionStart hook (`scripts/hooks/preflight.cjs`) also verifies these on every session.

On a nearly full system drive, point temp files at a big drive and use forward slashes:
`REMOTION_TMP=D:/remotion-tmp` (stills script) or set `TEMP` / `TMP`.

## 3. How a short is made

Order: **script, storyboard, animation, voice and audio, render, QA, upload.** Each stage has an approval gate.

1. **Script.** One takeaway, a hook in the first 3 s, ~3.7 words/s, sources listed at the top of `SCRIPT.md`.
2. **Storyboard.** A shot table (shot id, time, narration, picture, camera move, SFX cue), about one shot every 3-4 s.
3. **Animation.** The shot plan (shots, camera moves, kicks, depth of field) is timed to `voice/words.json`.
4. **Voice.**
   ```bash
   cd voice && python gen.py        # reads script.txt, writes voice.mp3 and words.json (edge-tts, en-US-AndrewNeural)
   ffmpeg -y -i voice.mp3 voice.wav # the audio mix reads voice/voice.wav
   ```
5. **Audio.**
   ```bash
   python audio/make_audio.py       # voice + ducked score + SFX -> audio/out/mix.wav (48 kHz), stems, cues.md
   ```
   Driven by `audio/timeline.py`. Any change to picture timing means re-running this.
6. **Look check (stills).**
   ```bash
   node scripts/bridge-stills.mjs out/stills/x_ 100,400 0.5     # prefix, frames, scale
   STARS_COMP=SkyShort node scripts/bridge-stills.mjs out/stills/y_ 100 0.5
   ```
7. **Render a 5-10 s sample first, then the full 2K render** (exact scale value matters, see `lessons.md`):
   ```bash
   npx remotion render src/index.ts StarsShort out/<name>/video.mp4 --codec h264 --crf 16 --scale 1.3333333333333333
   ```
   Then mux the mix (Remotion emits a silent track):
   ```bash
   ffmpeg -i out/<name>/video.mp4 -i audio/out/mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest out/<name>/final.mp4
   ```
   A `PreToolUse` hook runs `npm run tsc` before any `remotion render` and blocks the render if it fails.
8. **QA.**
   ```bash
   python scripts/short_qa.py <video.mp4> <outdir> [shots.json]   # black / white / frozen / pop frames, loudness
   ffprobe out/<name>/final.mp4     # 9:16, 60-120 s, audio stream present
   ```
9. **Deliverables** in `out/<name>/`: mp4, `.srt`, thumbnail, post copy (`post.txt`), `lessons.md`.

All output goes under `out/`. Nothing is written outside it.

## 4. Skills

Skills live in `.claude/skills/` and are used from Claude Code (type `/<skill-name>` or just ask in plain words).
That folder is its own git repo and is git-ignored in this one.

| Skill | What it does | Example request |
|---|---|---|
| `short` | Entry point. Makes a 9:16 captioned educational short as scriptwriter, storyboard artist and director, stopping at each approval gate. | "make a short about black holes" |
| `claude-animated-shorts` | The build recipe for the "2D characters in a 3D world" look: world, characters, camera, audio. Called by `short`. | "another video like the bridge one" |
| `render-check` | Typecheck, 10 s sample render and `short_qa.py`, then fixes problems (max 3 rounds). Run before a full render. | "run render-check" |
| `style-explore` | Builds 2-4 look variants side by side in sandbox copies so you can pick one. | "try three different looks" |
| `youtube-upload` | Uploads mp4, thumbnail and captions to YouTube, then cross-posts to a Facebook Page as a Reel. | "upload it to my channel" |
| `stick-story-animation` | Alternative style: bean-shaped stick figures in flat sets (forced to 9:16 here). | "stick figure story about X" |
| `huashu-art-motion` | Third-party art/video animation toolkit with many styles and narration-driven clips. | "make a motion piece in style X" |
| `animation-setup` | Installs and verifies Node, Python, ffmpeg and packages. | "set up the animation studio" |

### How to use the skills

Open the project folder in Claude Code (terminal or VS Code), then talk to it. Either type the skill name as a slash
command (`/short`) or describe what you want and the matching skill is picked.

1. **First time on a computer:** `/animation-setup` ("check my setup"). Fix anything it reports as missing.
2. **Make a video:** `/short make a short about <topic>`. Claude works in order and stops at each gate for your OK:
   script (with sources) -> storyboard (shot table) -> 5-10 s sample -> full video.
3. **Compare looks (optional):** "try 3 different looks for the sky" runs `style-explore`.
4. **Check before delivery:** `/render-check` runs typecheck, a 10 s sample render and the QA script, and fixes problems.
5. **Full render:** ask "render the full 2K video". The result, captions, thumbnail and post copy land in `out/<name>/`.
6. **Publish (only when you ask):** "upload it to my channel" or "schedule it for tomorrow". `youtube-upload` shows the
   schedule, does a dry run, uploads (private by default), then cross-posts to Facebook with the same visibility and time.

Skill notes:
- `short` is the normal entry point and calls `claude-animated-shorts` for the actual build.
- `youtube-upload` needs the credentials from sections 5a and 5b below.
- `stick-story-animation` and `huashu-art-motion` are alternative styles; ask for them by name.

Rules the project enforces: always 9:16, 60-120 s, generated audio muxed in, burned-in captions, English only, one steady
voice tone, jokes are researched real facts, every fact sourced in `SCRIPT.md`. Read `lessons.md` before any render,
audio mix or skill change.

## 5. Connected platforms

| Platform | How | Used by |
|---|---|---|
| **YouTube** | YouTube Data API v3, OAuth Desktop client (`credentials.json`, cached grant in `token.json`) | `youtube-upload` skill, `yt_upload.py` |
| **Facebook Page (Reels)** | Graph API with a never-expiring Page token (`facebook.json`) | `fb_upload.py` |
| **Edge TTS** | Free Microsoft voices, no key needed | `voice/gen.py` |
| **GitHub** | `origin` = github.com/irosh1/claudeAnimatedShorts | source control |

Uploads are outward-facing, so they run **only when you ask**, never automatically after a render. Defaults are in
`.claude/skills/youtube-upload/config.json`: private by default, US audience time zone with best-time slots, a 7-day
duplicate guard, an AI-generated-content disclosure on both platforms, and cross-promotion links between the two.

### 5a. YouTube credentials

1. Open the [Google Cloud Console](https://console.cloud.google.com), create or pick a project.
2. **APIs & Services > Library**: enable **YouTube Data API v3**.
3. **OAuth consent screen**: set it up (External is fine). While the app is in *Testing* mode, add your Google account
   under **Test users**. Testing-mode grants expire after 7 days, so you will need to re-consent.
4. **Credentials > Create credentials > OAuth client ID**, application type **Desktop app**. Download the JSON.
5. Save it as `credentials.json` in the project root.
6. Run the one-time consent (opens a browser; pick your channel):
   ```bash
   python .claude/skills/youtube-upload/scripts/yt_upload.py --auth-only
   ```
   This creates `token.json`. Later uploads are silent. Delete `token.json` to switch channels.
7. Check the schedule and upload:
   ```bash
   python .claude/skills/youtube-upload/scripts/yt_upload.py --check
   python .claude/skills/youtube-upload/scripts/yt_upload.py out/<name>/video.mp4 \
     --title "..." --description-file out/<name>/post.txt --thumbnail out/<name>/thumb.jpg \
     --captions out/<name>/captions.srt --dry-run          # drop --dry-run to upload
   ```
   Add `--publish-at 2026-11-20T15:00:00Z` to schedule, or `--privacy public` / `unlisted` to override the private default.

Notes: quota is 10,000 units/day and one upload costs about 1,600 (roughly 4-5 videos a day). Custom thumbnails need a
phone-verified channel. A project with an unverified API audit can only create private videos.

### 5b. Facebook credentials

The API can post only to a **Page** (not a personal profile) and you must be its admin. Full guide: `out/facebook-setup.md`.

1. Create a Facebook Page if you do not have one.
2. At [developers.facebook.com](https://developers.facebook.com), **My Apps > Create App** (use case *Other*, type *Business*).
   Leave it in Development mode; no App Review is needed for your own Page.
3. In the [Graph API Explorer](https://developers.facebook.com/tools/explorer), choose your app, generate a **User token**
   with `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `publish_video`, and select your Page.
4. Exchange it for a long-lived user token (`grant_type=fb_exchange_token` with App ID and App Secret from
   **App settings > Basic**), then call `GET /me/accounts`. The Page `access_token` listed there does not expire.
5. Create `facebook.json` in the project root:
   ```json
   {
     "page_id": "YOUR_PAGE_ID",
     "page_access_token": "YOUR_PAGE_TOKEN",
     "api_version": "v21.0"
   }
   ```
6. Verify:
   ```bash
   python .claude/skills/youtube-upload/scripts/fb_upload.py --check
   python .claude/skills/youtube-upload/scripts/fb_upload.py out/<name>/video.mp4 --description-file out/<name>/post.txt --dry-run
   ```

How the Reel mirrors the YouTube upload: private -> Facebook **DRAFT**, `--publish-at` -> **SCHEDULED** for the same time
(Facebook accepts 10 min to 30 days ahead, otherwise it saves a draft), public -> **PUBLISHED**. Upload to YouTube first so
the Facebook caption can link to the Short. Facebook has documented a 90 s Reel limit, so a longer video may need a trimmed cut.

Set `youtube_channel_url` and `facebook_page_url` in `.claude/skills/youtube-upload/config.json` to your own channel and Page.

### Secrets

`credentials.json`, `token.json`, `facebook.json`, `.env*` are git-ignored. Never commit them, paste them into chat, or
put them in post copy. If a token leaks, revoke it (Google Account > Security > third-party access; Meta app dashboard)
and redo the setup.

## 6. Project layout

```
voice/                       script.txt, gen.py, words.json (word timings)
audio/                       timeline.py, make_audio.py, music.py, sfx*.py, dsp.py, instruments.py
scripts/                     stills, QA, sheets, hooks (preflight, pre-render check)
out/<name>/                  every rendered file: mp4, srt, thumbnail, post copy, lessons
SCRIPT.md                    script, sources and shot table for the current short
lessons.md                   past mistakes and the rule that prevents each
CLAUDE.md                    instructions Claude Code follows in this repo
.claude/skills/              the skills listed above
```

See `CLAUDE.md` for architecture details and the sandbox workflow used for parallel look passes.

## 7. Troubleshooting

- **ENOSPC during render:** clean `remotion-tmp/`, `remotion-webpack-bundle-*`, `puppeteer_dev_chrome_profile-*`, or move temp to a bigger drive.
- **H.264 refuses the width:** use the exact scale `1.3333333333333333`, not `1.3333`.
- **Remotion bundler error about `typescript.sys`:** TypeScript 7 got installed; pin `typescript@5.6.x` (`npm i -D typescript@~5.6.3`).
- **Silent video:** Remotion's own audio track is silent; mux `mix.wav` with `-map 0:v:0 -map 1:a:0`.
- **Flicker:** check z-fighting and canvas-state determinism before anything else.
- **YouTube consent keeps expiring:** the OAuth app is in Testing mode; publish it or re-consent weekly.
- **Facebook error 190 / 200:** token expired or a permission is missing; redo 5b steps 3-5 and take the token from `/me/accounts`.
