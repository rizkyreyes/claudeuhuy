# 3D explainer playbook (from 24 Oct 2026)

Hidden In Your Home switched from b-roll videos to **3D cross-section explainers made in Blender** (Rizky, 24 Oct 2026). These rules come from producing the first two 3D videos (road layers, door lock) and from Rizky's feedback. They override older docs where they conflict.

## Format
- Vertical 1080x1920, 30 fps, **about 75 s** (target 70–78 s). English narration, US audience.
- **Two 3D episodes per ET day from Tue 1 Dec 2026** (Rizky, 23 Nov 2026): an AM slot and a PM slot, both full Blender episodes. **New topics: hidden systems in or right under the home first** (Rizky 23 Nov, from FB + Buffer data 21-22 Nov: P-trap, anode rod, septic beat big systems on FB/TikTok/YouTube); big systems now and then. (Old, superseded: big systems only, 2 Nov 2026; ROUTINE.md Step 1.) Scope was broad: "how it works" AND "how it's built" (household objects, construction, infrastructure, machines). Not only things in the home.
- Register: the hero is always a **3D cross-section / cutaway** rendered in Blender Cycles: dark studio backdrop for objects, real-world terrain (Poly Haven CC0 textures, HDRI) for construction.
- Topic must have evergreen proof (old uploads still getting views) and be buildable procedurally in a Blender Python script.

## Script and voice
- **Hook = lead with the claim, not the question** (Rizky, 1 Nov 2026; replaces the question hook of 24 Oct): the first sentence states the surprising fact the video then explains, as a statement ("Skyscrapers don't sit on rock. Many are held up by friction." / "Bridge pillars are built in the river, bone dry."), not "Why don't skyscrapers sink?". Name the concrete thing, never vague phrasing; it must be true per `sources.txt`. Complete in the first 2 seconds, shown as the opening title (the claim in 2-6 words, e.g. "HELD UP BY FRICTION"). YouTube titles stay questions (Rizky cancelled claim-first titles for 3D) but **start with the search phrase** (Rizky, 2 Nov 2026): "How <X> Works: <question>? #shorts", e.g. "How a Toilet Flush Works: Why Doesn't It Overflow? #shorts". Details in ROUTINE.md Step 7.
- **ENDING (Rizky 19-20 Nov 2026, overrides the LOOP ENDING below): never cut off mid-sentence. The last fact sentence is complete, then a short SPOKEN viewer question + "Tell me in the comments." (~5 s, e.g. "Is the transformer at your house on a pole, or a green box on the ground? Tell me in the comments."), with the question as a big on-screen title (Poppins ExtraBold, white + gold line), word captions, small "NEXT: <2-4 WORDS>" over the last 2 s, fade out. Rizky rejected the open loop on power-grid ("videonya terputus", "tidak ada CTA diakhir").**
- **(superseded 19 Nov) LOOP ENDING (Rizky 15 Nov 2026, from the channel audit: audience falls from ~70% to 41% in the last ~5 s; overrides the TAIL RULE and CTA lines below): the VO ends ON THE PAYOFF FACT. No spoken question, no "Next up", no "Follow". Write the last sentence so it flows back into the first line (loop), e.g. last line "...and that is why the pillar is built" + first line "bone dry, in the middle of a river". Cut hard on the last word; the 2 cover frames stay. The viewer question moves to the caption/pinned comment; "NEXT: <2-4 WORDS>" may appear as small on-screen text over the last 1-2 s only, never spoken.**
- **(superseded 15 Nov) TAIL RULE (Rizky 12 Nov 2026, from retention data, overrides the lines below): the spoken tail after the last fact is max ~3 s: "<question>? Next up: <2-5 words>." Do NOT say "Tell me in the comments" or "Follow so you don't miss it" in the VO; keep them only as on-screen text over the final pull-out shot. No separate end card; cut hard so it loops. Sentence 2 must already give the answer/claim (no "Let's cut it open" filler).**
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

## Cover / thumbnail (rule changed by Rizky, 14 Nov 2026 — replaces the Blender-hero + statement-title cover)
- **Video stays 100% Blender.** Only the cover/thumbnail is made with fal.ai (`openai/gpt-image-2` via `pipeline/falsync.mjs`, quality MEDIUM — Rizky 14 Nov 2026, high cost ~$0.15/image; 1088x1920; one image per option, no extra retries unless Rizky asks).
- Image = the episode's subject, whole, looking high-tech and premium: photoreal-CGI 3D cutaway/cross-section, VARIED backgrounds per episode and per option (daylight sky, sunset, storm, real street or landscape, studio — never the same dark blue every time), dramatic light, glowing internals (reference look: @american_civil_works wind-turbine reel). It must still match what the video shows (same type of object and the same key parts), so the viewer is not misled.
- Text = **only the object's name**, e.g. "WIND TURBINE", "CITY SEWERS". Poppins ExtraBold, 1–3 words, no statement/claim, no question, no brand line. Added in Tesseract on top of the AI image, never drawn by the AI.
- Keep title + subject inside the central **3:4 crop (y 240–1680)**.
- Three options per episode (A/B/C) = three different AI images (angle / setting / cutaway depth), same name text. Files: cover/cover_A.png, cover_B.png, cover_C.png.
- Note in cover.md the fal prompt used for each option.

## Escalation hook + share line (Rizky, 14 Nov 2026, from @hiddenhome.3d scan)
- Where the topic allows, frame title + opening line as an escalation: "How one [small everyday thing] ends up needing [giant machine]" (e.g. "How one runway crack ends up needing a 400-ton roller"). Small familiar thing -> absurdly big engineering. Their versions draw 70-119 shares per post; their best IG reel hit 662K. Keep claim-first and the 60-char limit.
- Instagram caption only: first line = "Send this to someone who [relatable situation] 👇" (drives DM shares). TikTok and YouTube keep the current caption with the closing question.
- Do NOT copy their volume (5-10 uploads/day): on TikTok every one stalls at 0.3-11K. We stay one polished video/day.

## Blender power-ups — use ALL in every episode (Rizky, 15 Nov 2026) — `pipeline3d/fx.py`
In build_scene.py: `sys.path.insert(0, <repo>/pipeline3d); import fx`. Every call is defensive (prints `[fx] ... skipped` instead of crashing). Tested on Blender 5.2.
1. `fx.hdri(name)` — real sky + light. Blender bundled: city, courtyard, forest, interior, night, studio, sunrise, sunset; or Poly Haven ids in assets/polyhaven (fetch_polyhaven.js). Pick to fit the story, vary per episode. `show_background=False` = HDRI light with a plain backdrop.
2. `fx.glare()` — bloom on glowing parts (cores, sparks, lightning, lamps) in the compositor.
3. `fx.particles(obj, "dust"|"sparks"|"rain"|"mud", start, end)` — at least one particle moment per episode (impact, drilling, flowing, weather).
4. `fx.rigid(active, passive)` + `fx.bake_rigid(a, b)` — real falling/collapsing (soil caving in, bricks, failure "what if" beat). Bake before rendering.
5. `fx.fluid_domain(domain, flow, eff, res)` + `fx.bake_fluid(domain)` — Mantaflow water ONLY for 1–2 short shots (≤ 4 s, res ≤ 128); everything else keeps animated water planes. Cache dir inside the episode folder, never committed.
6. `fx.scatter(surface, instance, density)` — Geometry Nodes scatter for rocks, trees, houses, gravel: richer worlds without hand-placing.
7. `fx.engine("eevee")` for simple shots / fast previews, `fx.engine("cycles")` for hero shots and final if time allows; note the choice and render time in the run log.
Check the `[fx]` lines in the render log; a "skipped" line must be fixed or explained in the run log.

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
**Two videos per ET day from Tue 1 Dec 2026** (Rizky, 23 Nov 2026; replaces "one per day, never two" of 27 Oct): PM video = the table above, AM video = TikTok 9 AM, Instagram 9 AM, YouTube 12 PM ET, every day. At least 6 h between the two on one platform. Buffer free plan: 10 scheduled posts per channel = only ~5 days ahead, so schedule in order and hold the rest (buffer-full rule). Before scheduling, list the scheduled posts in Buffer; if the target day already has a video, move the new one (and the rest of the queue) to the next free day. Days Rizky blocks stay empty: **Thu 29 Oct 2026 = no posts**.

**Instagram is NOT scheduled in Buffer from 24 Nov 2026 (first: jeans-rivets-3d, 29 Nov).** Rizky uploads each reel by hand from the Instagram app with "Share to Facebook" on (API posts do not cross-post to the FB Page). The laptop task `fb-page-push` sends him the MP4 + title + Instagram caption 1 h before the slot: AM video 9 AM ET, PM video and single-video days 7 PM ET (published FB studies, 23 Nov 2026). Buffer = TikTok + YouTube only. The Instagram caption in publish.md is still written.
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

## Tags (Rizky 15 Nov 2026, channel audit)
5-10 accurate tags per YouTube video: the object, the search phrase ("how X works"), 2-3 related engineering terms, "3d animation", "how it works". Never other creators' names (b1m, zack d films, roger wakefield, jared owen...), celebrities, brands or unrelated topics: YouTube's spam policy treats misleading tags as a violation.

## Named series + compilations (Rizky 15 Nov 2026, channel audit)
- Series name **"How It's Built"** lives in the YouTube playlist and the description's first line ("How It's Built #<n>"), never on screen (the 5 Nov no-label rule stands). Every new 3D Short goes into the playlist.
- One long-form compilation per ~10 strong Shorts: "How 10 Impossible Structures Were Built" (16:9 re-frame or 9:16 centered, chapters, ~12 min). First one planned in `state/compilations.md`.

## Short captions + titles (Rizky 15 Nov 2026, overrides longer caption rules)
- Caption (TikTok/IG/YouTube text): ONE short line (claim or stake, max ~12 words) + the viewer question + an emoji, then a blank line and 5 relevant hashtags (topic, topic variant, field, #howitworks or #engineering, #3danimation). No paragraph retelling the video. IG keeps the "Send this to someone who … 👇" first line.
- YouTube title (Rizky, 21 Nov 2026, replaces every older title rule): **short, max ~30 characters, NO hashtags in the title** (no "#shorts", no topic hashtag), the search phrase or the hook only, e.g. "How Pipe Lining Works", "Taipei 101's Giant Steel Ball". Hashtags: exactly 5, only in the caption. YouTube tags: 5 only.
