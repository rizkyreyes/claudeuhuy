# 3D explainer playbook (from 24 Oct 2026)

Hidden In Your Home switched from b-roll videos to **3D cross-section explainers made in Blender** (Rizky, 24 Oct 2026). These rules come from producing the first two 3D videos (road layers, door lock) and from Rizky's feedback. They override older docs where they conflict.

## Format
- Vertical 1080x1920, 30 fps, **about 75 s** (target 70–78 s). English narration, US audience.
- One topic per day. Scope is broad: "how it works" AND "how it's built" (household objects, construction, infrastructure, machines). Not only things in the home.
- Register: the hero is always a **3D cross-section / cutaway** rendered in Blender Cycles: dark studio backdrop for objects, real-world terrain (Poly Haven CC0 textures, HDRI) for construction.
- Topic must have evergreen proof (old uploads still getting views) and be buildable procedurally in a Blender Python script.

## Script and voice
- **Hook = always a question** (Rizky, 24 Oct 2026): the first sentence asks the question the video answers ("How do you build a bridge pillar in the middle of a river?"), complete in the first 2 seconds, shown as the opening title.
- **CTA = a question to the viewer** (Rizky, 24 Oct 2026): the last line asks something about the topic that people can answer in one comment, then "Tell me in the comments." Example: "Would you work down there, with a river right over your head?" Then ONE closing follow line that **names the next episode** (Rizky, 1 Nov 2026, replaces the fixed "If you found this useful" line): **"Next up: <the next episode's hook in 4-8 words>. Follow so you don't miss it."** (e.g. "Next up: what really happens when you flush. Follow so you don't miss it."). On screen with it: "NEXT: <2-4 WORDS>" (white) + "FOLLOW SO YOU DON'T MISS IT" (gold), Poppins ExtraBold, with a pop + ping. See "Follower growth" below. Still **never the channel name** (no "Hidden In Your Home" on screen or in the VO). On screen: the question as the closing title (Poppins ExtraBold, white) + "TELL ME IN THE COMMENTS" (Poppins, gold). One continuous take. ~3 words/s; v4 Turbo talks fast: 235 words ≈ 74 s.
- **Video titles (YouTube, and the caption's first line) lead with the claim, not the question** (Rizky, 1 Nov 2026): "Skyscrapers Are Held Up by Friction", not "Why Don't Skyscrapers Sink?". The question buries the shock; name the concrete thing (object, place, number), never vague phrasing. The claim must be true per `sources.txt`. The spoken hook and the opening title on screen stay a question.
- ElevenLabs model **`eleven_v4_turbo`**, voice **Liam** (voiceId `TX3LPaxmHKxFdv7VOQHJ`, "Liam - Energetic, Social Media Creator"), language `en`. v4 Turbo ignores the `speed` setting: fix length by adding/cutting words, never by speeding up audio.
- Word-level timestamps from `/with-timestamps`. Every animation cue is a WORD, resolved as "next occurrence after the previous cue".
- Facts: verify on reputable sources before writing; if sources disagree, drop the specific claim (e.g. door lock: "a father and son named Yale", no patent year). Log sources in the episode's `sources.txt`.

## Follower growth (Rizky, 1 Nov 2026: views are fine, follows are low)
1. **Tease the next episode in the follow line** (see Script and voice). The next episode = the next row in `state/queue-3d.md` after this one (research the next batch first if the queue would run out). Once a video teasing episode X is scheduled, X stays the next episode posted: do not reorder or drop it.
2. **Series label**: every video is a numbered episode of the series **"CUTAWAY"**, number = the queue number (3d-11 -> `CUTAWAY #11`). On screen: a small gold pill "CUTAWAY #11" (Poppins ExtraBold ~40 px, tracking 60) above the hook title from frame 0 to the end of the hook (~2.5 s), inside the safe area (y >= 200), with a soft tick. Not spoken. The series name is not the channel name; the channel name still never appears.
3. **Profile**: bio and pinned videos live in `docs/profile.md`; refresh the pin list each Monday from Buffer metrics (top 3 by views per platform) and tell Rizky, he pins them by hand.
4. **Reply to comments**: the morning laptop run drafts replies to new comments on the last 3 posted videos (YouTube via vidIQ `vidiq_video_comments` / `vidiq_generate_comment_replies`; TikTok/IG: Rizky pastes the comments or they come from vidIQ IG tools if connected). Short, friendly, human English, answers the question, often ends with a question back. Nothing is posted without Rizky's OK for that batch. A comment that asks for a topic goes into `docs/topic-bank-3d.md` as a candidate ("requested in comments"), and for TikTok mark it as a good video-reply candidate.
6. **Two-parters, sometimes**: about 1 topic in every 7-topic batch (a big build like a dam, an oil rig, a skyscraper) is split into Part 1 / Part 2 on consecutive days, each a full 70-78 s video with its own CUTAWAY number. Part 1 ends on a real cliffhanger and its follow line is "Part two tomorrow: <hook>. Follow so you don't miss it." (on screen "PART 2 TOMORROW"). Part 2 opens with a 1-sentence recap inside the hook. Mark them in the queue as `<slug>-p1` / `<slug>-p2`.

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
- **Option B = real photo + cutaway inset** (Rizky, 31 Oct 2026, first used on 3d-09 fridge): the same kind of real photo, plus a crop of our own Blender render (a still at 100 %, 64 samples, from the beat that shows the hidden mechanism) in a rounded box with a gold #FABD45 border and a soft shadow, placed over a plain part of the photo so it never covers the subject, inside the 3:4 crop. Composite it onto the photo first (`cover/photo_B_inset.jpg`), then add the title in `thumb.js` as usual. Option A stays photo-only, so the two can be compared.
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
**One video per ET day, never two** (Rizky, 27 Oct 2026). Before scheduling, list the scheduled posts in Buffer; if the target day already has a video, move the new one (and the rest of the queue) to the next free day. Days Rizky blocks stay empty: **Thu 29 Oct 2026 = no posts**.
Offset −04:00 until 31 Oct 2026, −05:00 from 1 Nov 2026. Buffer free plan: max 10 scheduled posts per channel. Nothing is published without Rizky's "setuju" on the final video + caption.

## Laptop scripts (pipeline3d/bin)
`render.sh <ep> stills|final|cover <frame>`, `assemble.sh <ep>`, `publish-prep.sh <ep> A|B` (upload file + push + Buffer payloads), `buffer-plan.mjs`, `mark-scheduled.mjs`. Episode files must keep these names: build_scene.py, timeline.js (reads RENDER_ID/RENDER_MS), synth_sfx.js, publish.md (bold `...#shorts` title, `## Caption` section), cover/cover_A.png + cover_B.png.
