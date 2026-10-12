# Beat-plan method (test video: o-23 bottle-cap-teeth, Sun 18 Oct 2026)

Rizky asked on 12 Oct 2026 to use the steps from Hanif's "programmatic video" article (hyperframe-pro, @hanifproduktif) for the video posted on 18 Oct. This file is how those steps fit our pipeline. **Only row o-23 uses it for now.** The 25 Oct weekly review compares o-23 with the videos around it (views, average watch time, retention at 30 s) and decides whether it becomes the default.

Everything in `docs/playbook.md` still applies: 60–75 s, story structure, 2–3 curiosity reloops, two CTAs, one-word captions, tight crop, second angle inside 2 s. The article's 2-minute four-step format is **not** used: we change the method, not the format, so the result can be compared.

Already in our pipeline (keep doing it): one continuous voice take with word timestamps (`tts.mjs`), cues anchored on spoken words (`shots.mjs` + TA chaining), a contact-sheet check before scheduling, AI clips at most 10 s with a locked-off camera.

## What is new for o-23

### 1. Script (Step 2 of ROUTINE, plus these)
- The first sentence puts the viewer inside the moment (the cap coming off), not a statement about caps.
- **Every number that will appear on screen is said out loud** (21, 24, 1892 if used). If a number can't be spoken naturally, it doesn't go on screen.
- End with one action only: the CTA2 comment ask from the playbook. No "follow and share and comment".
- In `script.json` set `"voiceSettings": { "stability": 0.5, "similarity_boost": 0.85, "style": 0.3, "speed": 1.0, "use_speaker_boost": true }` (speed **1.0**, not faster). If the take is long, shorten pauses (step 3), never raise the speed.

### 2. Voice
`node ../../pipeline/tts.mjs script.json assets/vo` as usual. One take.

### 3. Cap the pauses (new)
```bash
python3 ../../pipeline/cap-pauses.py .          # pauses over 0.24 s cut to 0.24 s (0.34 s after a full stop)
```
Same recording, no new TTS, word timestamps re-timed exactly. Listen to 2–3 joins in the result; if anything sounds clipped, re-run with `0.28 0.38`. It always works from the backup (`*.orig`), so re-running is safe.

### 4. Beat plan BEFORE the shot list (new)
Write `plan.json` (format at the top of `pipeline/lint-plan.mjs`) with 8–12 beats. Each beat: the word it starts on, its **job**, one **hero**, a **register**, a **framing**, the shot ids it uses, and every number on screen in that beat. Decide all of it before picking any b-roll.

Rules:
- Two beats in a row with the same framing → change one.
- A beat with two heroes → split it. A beat with no hero is where people skip.
- **Register decides the hero**, per beat:

| The beat is about… | register | hero |
|---|---|---|
| an event happening (the cap popping off, a seal failing, gas escaping) | `photoreal` | a generated clip (LTX) or real stock footage |
| a real record (the 1892 patent drawing, a label, a manual page) | `document` | the **real** document, sourced with a URL in `publish/sources.txt`. Never generate a document, a patent, a label or any text |
| the object itself (teeth, lip of the bottle) | `still` | tight AI still or stock photo |
| a place or process (bottling line, factory) | `stock` | Pexels clip |
| an idea with nothing to photograph | `drawn` | a simple diagram still with no text, only if really needed |

- **The hook beat is `photoreal` and moves**: the first shot is a clip.
- Never show William Painter or any real person (no portrait, no generated likeness). The patent drawing is fine: US patent drawings are public domain (Google Patents, US 468,226).

### 5. Photoreal hook plate (prompt style)
For the hook still (`falsync.mjs image … high`) describe the camera, not the beauty:
- the rig: "macro photo on a fixed tripod, close to a brown glass bottle neck on a kitchen counter"
- the glass: "100mm macro lens, shallow depth of field, slight lens softness at the edges"
- the sensor: "natural window light, mild sensor grain, true-to-life colour, not cinematic, not CGI"
- the hand: "a real adult hand holding a metal bottle opener, skin texture visible, no face in frame"
- safety: "no text, no letters, no logos, no brand marks on cap or bottle"
- frame: "vertical 9:16, cap and bottle neck fill about 75% of the frame width"

Motion prompt for the clip (`falsync.mjs ltx … 6`): "Camera completely locked off on a tripod, it never moves, pans or zooms. The opener levers the cap and it pops off the bottle neck. Real physics, no text." If a phone or screen is anywhere in the frame: "the screen is completely black and switched off for the whole shot, no interface ever appears". Generate one, look at it, and change the prompt rather than re-rolling the same prompt.

### 6. Shot list, then the lint gate (new)
Write `shots.mjs` from the plan, then:
```bash
node ../../pipeline/lint-plan.mjs .
```
It fails the build (exit 1) on: a beat with no hero or no register, the same framing twice in a row, a hook that isn't photoreal, a shot playing inside a beat that doesn't list it (a visual outstaying its step), **dead air** (any one picture held over 4.5 s; our b-roll is always full-bleed, so this is our version of the article's 1.2 s empty-frame gate), a cut to the identical picture, the opening holding past 2 s, a number on screen or in the thumbnail label that is never spoken, a document shot with no source URL, and anything over 2:59. Fix and re-run until it prints PASS. Warnings (length outside 60–75 s, long pauses, voice speed over 1.0) should be fixed too unless there's a reason; write the reason in the run log.

### 7. Render, loudness, contact sheet at 1 fps
Render as in ROUTINE Step 7, but the final encode normalises loudness to **-14 LUFS, true peak under -0.5 dBTP** (the platforms' own target, so nothing gets turned down or sounds quiet next to other Shorts):
```bash
ffmpeg -i out.mp4 -c:v libx264 -preset slow -crf 21 -maxrate 8M -bufsize 16M -af "loudnorm=I=-14:TP=-1.0:LRA=11" -ar 48000 -c:a aac -b:a 192k -movflags +faststart final.mp4
ffmpeg -hide_banner -i final.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12   # I ≈ -14 (±1), True peak < -0.5
ffmpeg -v error -i final.mp4 -vf "fps=1,scale=180:320,tile=10x8:padding=4" -frames:v 1 -y sheet.jpg   # one frame per second
```
Look at the 1 fps sheet (not 12 frames): every second must have something hero-sized and on-topic, no black frames, no garbled text, captions readable, nothing static for more than about 4 seconds.

### 8. Fixing one line
If one sentence is wrong after the voice is done, fix just that sentence in the script and regenerate the take with `--force` (it's cheap at this length), then re-run steps 3, 6 and 7. Do not speed the voice up to make it fit.

## What to write in the run log for o-23
One line each: speech length before and after `cap-pauses.py`, lint-plan result (PASS, warnings), measured loudness (I and true peak), how the LTX hook clip looked (sharp / soft / warped), and the cost of AI calls if known. The 25 Oct review reads these.
