# 3D explainer playbook (from 24 Oct 2026)

Hidden In Your Home switched from b-roll videos to **3D cross-section explainers made in Blender** (Rizky, 24 Oct 2026). These rules come from producing the first two 3D videos (road layers, door lock) and from Rizky's feedback. They override older docs where they conflict.

## Format
- Vertical 1080x1920, 30 fps, **about 75 s** (target 70–78 s). English narration, US audience.
- One topic per day. Scope is broad: "how it works" AND "how it's built" (household objects, construction, infrastructure, machines). Not only things in the home.
- Register: the hero is always a **3D cross-section / cutaway** rendered in Blender Cycles: dark studio backdrop for objects, real-world terrain (Poly Haven CC0 textures, HDRI) for construction.
- Topic must have evergreen proof (old uploads still getting views) and be buildable procedurally in a Blender Python script.

## Script and voice
- **Hook = always a question** (Rizky, 24 Oct 2026): the first sentence asks the question the video answers ("How do you build a bridge pillar in the middle of a river?"), complete in the first 2 seconds, shown as the opening title.
- **CTA = a question to the viewer** (Rizky, 24 Oct 2026): the last line asks something about the topic that people can answer in one comment, then "Tell me in the comments." Example: "Would you work down there, with a river right over your head?" No "follow" line, and **never the channel name** (no "Hidden In Your Home" on screen or in the VO). On screen: the question as the closing title (Poppins ExtraBold, white) + "TELL ME IN THE COMMENTS" (Poppins, gold). One continuous take. ~3 words/s; v4 Turbo talks fast: 235 words ≈ 74 s.
- ElevenLabs model **`eleven_v4_turbo`**, voice **Liam** (voiceId `TX3LPaxmHKxFdv7VOQHJ`, "Liam - Energetic, Social Media Creator"), language `en`. v4 Turbo ignores the `speed` setting: fix length by adding/cutting words, never by speeding up audio.
- Word-level timestamps from `/with-timestamps`. Every animation cue is a WORD, resolved as "next occurrence after the previous cue".
- Facts: verify on reputable sources before writing; if sources disagree, drop the specific claim (e.g. door lock: "a father and son named Yale", no patent year). Log sources in the episode's `sources.txt`.

## Visual rules
- Beat plan first (PLAN.md): job → hero → type → SFX per beat, cues are words. No dead air > 1.2 s.
- Blender 5.2, Cycles. Gotchas: easing helpers must clamp (an unclamped `p*p` once sent pins to z=-486); Blender 5 ignores the CONSTANT keyframe preference (use separate objects/booleans for hold states); parent with identity inverse at the origin; hair-particle "NOR" rotation maps the instance's local +Y to the surface normal; particles on a moving emitter need their own hide keys.
- Final render: 24 samples + OptiX denoise, adaptive threshold 0.03, motion blur OFF (it multiplies render time). Stills for checks at 25–50 %.

## Typography (Tesseract)
- Fonts: **Poppins ExtraBold for everything** (titles, counters, captions, labels, covers). Anton is retired (Rizky, 26 Oct 2026: "biar semua seragam", more modern). In Tesseract: family `Poppins`, style `ExtraBold`. In `timeline.js` set `const DISPLAY = { fontFamily: "Poppins", fontStyle: "ExtraBold" }` and scale the old Anton sizes by about 0.75 (Poppins is much wider; e.g. 170 -> 128, 118 -> 88), tracking about -10 on titles, then check every title fits its box on 1-2 lines in the filmstrip. Do not import Anton any more.
- Palette: white, gold `#FABD45`, cyan `#4DEBFF` (the glowing technical line), red `#FF4D3D` (failure/danger).
- Kinetic titles land on their word (slam / pop / rise) with a sound. Counters only for numbers the narration says.
- Part labels: dot + leader line + label, **tracked to the 3D part** with per-frame projected coordinates exported from Blender; labels flip side automatically to stay on screen.
- Captions: 1–3 word groups, gold for key terms. **Drop a caption while a title already shows the same words** (numbers and spelled-out forms count as the same).

## Platform safe area (TikTok / Reels / Shorts UI)
- Keep all text inside x 60–950 and y 200–1500. Captions sit at y ≈ 1320–1470, x 70–950. Labels never cross x 950.

## Sound
- Every typography entrance gets a matching accent (pop, impact, whoosh, tick, ping). Every mechanical event gets foley (clicks timed to the simulation, scrapes, thuds, clunks). Important failure beats ("jammed", "too high") get a strong stinger (deny thud + metal clunk).
- Quiet ambient pad under everything. Mix target −16 to −14 LUFS, true peak ≤ −1 dBTP. A mono VO reads ~3 LU hotter in the stereo mix.

## Cover / thumbnail
- **Cover photo = a REAL photo of the subject, not a frame from the video** (Rizky, 26 Oct 2026). Search Pexels first, then Pixabay (`pipeline/stock.mjs`, portrait). Pick a sharp, well-lit photo where the object fills the frame and reads at thumbnail size. Only free-licence stock (Pexels / Pixabay licence, commercial use OK); no identifiable faces, no readable brand logos or watermarks; never AI-generated. Save it as `<episode>/cover/photo_A.jpg` and `photo_B.jpg` (two different photos), and log photographer + page URL in `sources.txt`. If no usable real photo exists, fall back to a Blender frame and say so in `cover.md`.
- Then just add the words: **Poppins ExtraBold** title, a more modern font than Anton (Rizky, 26 Oct 2026); in Tesseract family `Poppins`, style `ExtraBold`, ALL CAPS, tracking about -10, white line ~150 px + red line ~112 px, 10 px black stroke (white line + red line), dark gradient behind the text only if needed for contrast; no rings or diagrams unless they make the paradox clearer.
- 1080x1920. Make it a **curiosity contrast**, not a plain label (Rizky rejected "UNDER THE RIVER" as flat): show the paradox in the picture (e.g. crew standing dry below a red river-level line) and title it as a surprise or question ("BONE DRY / UNDERWATER?!", "WORKING / UNDER A RIVER"). Offer 2 options.
- Research-backed style: extreme close-up of the mechanism, one strong contrast colour (red), 2–3 word title in Poppins ExtraBold (not Anton). Keep title + subject inside the central **3:4 crop (y 240–1680)** so the profile grid shows it whole. No brand line, no caption tag on the cover.

## Publishing (Buffer) — per-platform US peak slot for that weekday (ET)
| Day | TikTok | Instagram Reels | YouTube Shorts |
|---|---|---|---|
| Mon | 1 PM | 7 PM | 8 PM |
| Tue | 6 AM | 7 PM | 8 PM |
| Wed | 10 PM | 12 PM | 7 PM |
| Thu | 1 PM | 9 AM | 7 PM |
| Fri | 6 PM | 10 PM | 4 PM |
| Sat | 5 PM | 9 PM | 7 PM |
| Sun | 9 AM | 9 PM | 7 PM |
Offset −04:00 until 31 Oct 2026, −05:00 from 1 Nov 2026. Buffer free plan: max 10 scheduled posts per channel. Nothing is published without Rizky's "setuju" on the final video + caption.
