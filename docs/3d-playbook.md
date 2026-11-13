# 3D explainer playbook (from 24 Oct 2026)

Hidden In Your Home switched from b-roll videos to **3D cross-section explainers made in Blender** (Rizky, 24 Oct 2026). These rules come from producing the first two 3D videos (road layers, door lock) and from Rizky's feedback. They override older docs where they conflict.

## Format
- Vertical 1080x1920, 30 fps, **about 75 s** (target 70–78 s). English narration, US audience.
- One topic per day. **New topics after the current queue: big systems only** (Rizky, 2 Nov 2026; ROUTINE.md Step 1). Scope was broad: "how it works" AND "how it's built" (household objects, construction, infrastructure, machines). Not only things in the home.
- Register: the hero is always a **3D cross-section / cutaway** rendered in Blender Cycles: dark studio backdrop for objects, real-world terrain (Poly Haven CC0 textures, HDRI) for construction.
- Topic must have evergreen proof (old uploads still getting views) and be buildable procedurally in a Blender Python script.

## Script and voice
- **Hook = lead with the claim, not the question** (Rizky, 1 Nov 2026; replaces the question hook of 24 Oct): the first sentence states the surprising fact the video then explains, as a statement ("Skyscrapers don't sit on rock. Many are held up by friction." / "Bridge pillars are built in the river, bone dry."), not "Why don't skyscrapers sink?". Name the concrete thing, never vague phrasing; it must be true per `sources.txt`. Complete in the first 2 seconds, shown as the opening title (the claim in 2-6 words, e.g. "HELD UP BY FRICTION"). YouTube titles stay questions (Rizky cancelled claim-first titles for 3D) but **start with the search phrase** (Rizky, 2 Nov 2026): "How <X> Works: <question>? #shorts", e.g. "How a Toilet Flush Works: Why Doesn't It Overflow? #shorts". Details in ROUTINE.md Step 7.
- **TAIL RULE (Rizky 12 Nov 2026, from retention data, overrides the lines below): the spoken tail after the last fact is max ~3 s: "<question>? Next up: <2-5 words>." Do NOT say "Tell me in the comments" or "Follow so you don't miss it" in the VO; keep them only as on-screen text over the final pull-out shot. No separate end card; cut hard so it loops. Sentence 2 must already give the answer/claim (no "Let's cut it open" filler).**
- **CTA = a question to the viewer** (Rizky, 24 Oct 2026): the last line asks something about the topic that people can answer in one comment, then "Tell me in the comments." Example: "Would you work down there, with a river right over your head?" Then ONE closing follow line that **names the next episode** (Rizky, 1 Nov 2026, replaces the fixed "If you found this useful" line): **"Next up: <the next episode's hook in 4-8 words>. Follow so you don't miss it."** (e.g. "Next up: what really happens when you flush. Follow so you don't miss it."). On screen with it: "NEXT: <2-4 WORDS>" (white) + "FOLLOW SO YOU DON'T MISS IT" (gold), Poppins ExtraBold, with a pop + ping. See "Follower growth" below. Still **never the channel name** (no "Hidden In Your Home" on screen or in the VO). On screen: the question as the closing title (Poppins ExtraBold, white) + "TELL ME IN THE COMMENTS" (Poppins, gold). One continuous take. ~3 words/s; v4 Turbo talks fast: 235 words ≈ 74 s.
- ElevenLabs model **`eleven_v4_turbo`**, voice **Liam** (voiceId `TX3LPaxmHKxFdv7VOQHJ`, "Liam - Energetic, Social Media Creator"), language `en`. v4 Turbo ignores the `speed` setting: fix length by adding/cutting words, never by speeding up audio.
- Word-level timestamps from `/with-timestamps`. Every animation cue is a WORD, resolved as "next occurrence after the previous cue".
- Facts: verify on reputable sources before writing; if sources disagree, drop the specific claim (e.g. door lock: "a father and son named Yale", no patent year). Log sources in the episode's `sources.txt`.

## Follower growth (Rizky, 1 Nov 2026: views are fine, follows are low)
1. **Tease the next episode in the follow line** (see Script and voice). The next episode = the next row in `state/queue-3d.md` after this one (research the next batch first if the queue would run out). Once a video teasing episode X is scheduled, X stays the next episode posted: do not reorder or drop it.
2. **No series label** (Rizky, 5 Nov 2026): do NOT put "CUTAWAY #<n>" or any series or episode number on screen, from 3d-15 on. This replaces the earlier gold pill. The channel name still never appears.
3. **Profile**: bio and pinned videos live in `docs/profile.md`; refresh the pin list each Monday from Buffer metrics (top 3 by views per platform) and tell Rizky, he pins them by hand.
4. **Reply to comments**: the morning laptop run drafts replies to new comments on the last 3 posted videos (YouTube via vidIQ `vidiq_video_comments` / `vidiq_generate_comment_replies`; TikTok/IG: Rizky pastes the comments or they come from vidIQ IG tools if connected). Short, friendly, human English, answers the question, often ends with a question back. Nothing is posted without Rizky's OK for that batch. A comment that asks for a topic goes into `docs/topic-bank-3d.md` as a candidate ("requested in comments"), and for TikTok mark it as a good video-reply candidate.
6. **Two-parters, sometimes**: about 1 topic in every 7-topic batch (a big build like a dam, an oil rig, a skyscraper) is split into Part 1 / Part 2 on consecutive days, each a full 70-78 s video with its own CUTAWAY number. Part 1 ends on a real cliffhanger and its follow line is "Part two tomorrow: <hook>. Follow so you don't miss it." (on screen "PART 2 TOMORROW"). Part 2 opens with a 1-sentence recap inside the hook. Mark them in the queue as `<slug>-p1` / `<slug>-p2`.

## Packaging rules (Rizky, 7 Nov 2026, from Paddy Galloway's "5 principles" article)
- **Glance test**: title and cover must be understood in under a second. YouTube title ≤ 60 characters before " #shorts"; cover text ≤ 5 words; 1-3 focus points on the cover, the subject big and unblocked (a ship hidden behind a lock wall fails); text must not blend into the background.
- **Every hook has a stake**: a consequence or danger the viewer feels (sewer gas in your bathroom, 52 million gallons lost per ship, a tank that rusts through), in the first two sentences.
- **3 cover options** (A/B/C), not 2: hero renders are cheap. Rizky still picks one.
- **Moat filter**: every topic needs a moment only a 3D cutaway can show (inside the wall, under the seabed, through the pipe). If anyone with a phone camera could film it, pick another angle or topic.
- Packaging (idea, title, cover) is about half of a video's performance: spend real time on it, not the last 5 %.

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
- **Cover = a separate Blender hero render of the WHOLE subject, not a frame from the video and not a photo** (Rizky, 2 Nov 2026: "buat benda yang kita bahas"; e.g. the fridge episode = a complete, closed fridge rendered in Blender with heat glowing out of it). `<episode>/build_cover.py` is its own small scene: re-use the subject's model from `build_scene.py`, shown whole and uncut, filling the 3:4 crop, clean dark studio or simple real setting, strong key light, one visual cue for the paradox (heat glow, water pushing up, a snapped cable). Two options = `--opt A|B`, two clearly different angles or looks. No labels, captions or arrows from the video. Rendered on the laptop with `render.sh <ep> hero` -> `cover/hero_A.png`, `cover/hero_B.png`. No stock photos, nothing AI-generated.
- Then add the words: **Poppins ExtraBold** title, a more modern font than Anton (Rizky, 26 Oct 2026); in Tesseract family `Poppins`, style `ExtraBold`, ALL CAPS, tracking about -10, white line ~150 px + red line ~112 px, 10 px black stroke (white line + red line), dark gradient behind the text only if needed for contrast; no rings or diagrams unless they make the paradox clearer.
- 1080x1920. Make it a **curiosity contrast**, not a plain label (Rizky rejected "UNDER THE RIVER" as flat): show the paradox in the picture (e.g. crew standing dry below a red river-level line) and title it as a surprise or question ("BONE DRY / UNDERWATER?!", "WORKING / UNDER A RIVER"). Offer 3 options (A/B/C).
- Research-backed style: extreme close-up of the mechanism, one strong contrast colour (red), 2–3 word title in Poppins ExtraBold (not Anton). Keep title + subject inside the central **3:4 crop (y 240–1680)** so the profile grid shows it whole. No brand line, no caption tag on the cover.

## Publishing (Buffer) — per-platform US peak slot for that weekday (ET)
| Day | TikTok | Instagram Reels | YouTube Shorts |
|---|---|---|---|
| Mon | 6 PM | 12 PM | 8 PM |
| Tue | 6 PM | 7 PM | 8 PM |
| Wed | 10 PM | 12 PM | 7 PM |
| Thu | 5 PM | 9 AM | 7 PM |
| Fri | 6 PM | 10 PM | 4 PM |
| Sat | 5 PM | 9 PM | 7 PM |
| Sun | 9 AM | 9 PM | 7 PM |
**One video per ET day, never two** (Rizky, 27 Oct 2026). Before scheduling, list the scheduled posts in Buffer; if the target day already has a video, move the new one (and the rest of the queue) to the next free day. Days Rizky blocks stay empty: **Thu 29 Oct 2026 = no posts**.
Offset −04:00 until 31 Oct 2026, −05:00 from 1 Nov 2026. Buffer free plan: max 10 scheduled posts per channel. Nothing is published without Rizky's "setuju" on the final video + caption.

## Laptop scripts (pipeline3d/bin)
Covers (Rizky, 10 Nov 2026): the title is composited with **Remotion**, not Tesseract thumb.js: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" <ep>` reads the A/B/C titles from `cover.md` (`**A: "LINE1 / LINE2"**`) and `cover/hero_<X>.png`, writes `cover/cover_<X>.png` + `previews/covers.png`. Same look (Poppins ExtraBold, white + red, black stroke, dark band, 3:4 safe crop). thumb.js stays only as a fallback.
`render.sh <ep> stills|final|cover <frame>`, `assemble.sh <ep>`, `publish-prep.sh <ep> A|B` (upload file + push + Buffer payloads), `buffer-plan.mjs`, `mark-scheduled.mjs`. Episode files must keep these names: build_scene.py, timeline.js (reads RENDER_ID/RENDER_MS), synth_sfx.js, publish.md (bold `...#shorts` title, `## Caption` section), cover/cover_A.png + cover_B.png.

## Viral format scan before every episode: ROUTINE.md Step 1b (item 3), output episodes/<ep>/format-scan.md

## Weekly review — every Monday, laptop run (Rizky 11 Nov 2026; YouTube-growth list items 5, 7, 8)
Data: vidIQ `vidiq_channel_analytics` on the Hidden In Your Home YouTube channel (must be authorized in vidIQ; today only "Everyday Ways" is connected) + Buffer metrics for TikTok/IG.
1. Per video of the last 7 days: views, engagedViews, averageViewPercentage, subscribersGained; CTR from Studio when available. Log in `state/weekly-review.md`.
2. Retention curve (report `audience_retention`) for the best and the worst video: note the second where the biggest drop happens and what was on screen/said there.
3. Pick ONE "10% better" focus for the next 7 videos (hook, pacing, cover, CTA, topic) from that drop, write it at the top of `state/weekly-review.md`; the cloud prep reads it before writing scripts.
4. Cut rule for scripts: a beat that sits on a known drop pattern gets cut or shortened.
5. Under-average after 48 h (engagedViews < 70% of the 14-day median): swap to cover B/C or the backup title once.

## Long-form (item 10) — Shorts feed long-form
One 8-12 min 16:9 video every 2 weeks, stitched from winning Shorts topics of one theme (water, power, under the city, construction), re-voiced as one story, new transitions, chapters. Each Short in that theme gets the long video as its Related video. Plan: `drafts/longform-plan.md`.
