# Playbook: what the audience likes right now

The weekly review (`docs/WEEKLY-REVIEW.md`) updates this file every Sunday. **The daily run reads it before making any video. Where it conflicts with `docs/production-settings.md` or `docs/vidiq-captions.md`, this file wins.**

## Current rules

1. Audience is American. Casual American English in scripts and captions, contractions, second person, US units first (inches, °F, gallons), US spelling. No robotic phrasing, no em dashes, no emojis, no "Did you know?!".
2. Hook: the object (or the detail) is on screen at 0.0 s, and the surprising claim is spoken inside the first 1.5 s. **The opening must move** (Rizky, 3 Oct 2026: the toothpaste video held one slow shot for 5 s). Shot 1 is either a still (the builder adds a fast punch-in toward its `focus` point in the first 0.45 s) or a clip where something visibly moves in the first half second (a hand turning the object over, a finger pointing at the detail). **Cut to a second angle inside the first 2 s**: a tighter crop of the same still (`{ zoom: 1.6, focus: "..." }`) or a hand shot. `build-broll.mjs` refuses to build if the first shot holds longer than 2 s. No shot longer than 3 s in the first 8 s.
3. Length: aim for 60–75 s. With eleven_v4_turbo that's roughly 185–230 words (it speaks about 3.1 words per second).
4. End with one short, natural follow line that changes every video. It's OK to end on a question people want to answer in the comments.
5. Framing: **crop tight** (Rizky, 3 Oct 2026: too much empty space around the object). The subject fills about 70–85% of the frame width and the detail the video is about is easy to see on a phone. AI still prompts say "tight close-up, subject fills the frame, no empty background". Loose stock or AI shots get cropped: stills with `{ zoom, focus }` in `shots.mjs`, clips with `node pipeline/crop.mjs`. Keep the subject in the upper two-thirds, since captions cover the bottom. Don't zoom a 1080-wide still past about 1.6 (it goes soft); regenerate it tighter instead.
6. Captions on screen: big bold karaoke text (70 px) inside a semi-transparent dark box, current word yellow (Rizky, 3 Oct 2026: the old ones were small and hard to read). This is built into `pipeline/gen-shared.mjs`. Don't shrink it or remove the box.
7. Non-negotiables: 1080x1920, karaoke captions at the bottom, no text in the middle of the screen, AI-generated label on, every fact sourced, no real identifiable people.

8. **Curiosity reloops** (Rizky, 3 Oct 2026): the narration has to keep reopening the viewer's curiosity so they stay to the end. Every script uses **2 or 3 reloops**, ideally one of each type, each a short spoken line placed right before the next piece of information:
   - **The missing piece**: tell them there's still something important they don't know. "But nobody tells you this part." / "Here's the piece you're missing."
   - **Escalation**: tell them something even better is coming. "But that's not even the craziest part." / "Now here's the part that got me."
   - **The method**: make them curious how it actually works. "Here's exactly how they do it." / "This is the part that makes it work."

   How to use them:
   - **Placement:** first reloop at about 8–12 s (right after the hook pays off its first answer, where TikTok and Instagram viewers leave), second around 25–35 s, third around 45–55 s. Never two in a row.
   - **Pay it off within about 10 seconds**, and the payoff has to be real. Don't say "the craziest part" unless what follows really is the most surprising sourced fact in the video. Order the facts so the strongest one comes last. If a topic only has two good beats, use two reloops, not three.
   - **Fresh wording every video.** The lines above are patterns, not a script. Write a new version that fits the object ("But the color isn't even the weird part." / "So why is it there at all? This is where the factory comes in."). Don't reuse the same reloop line within the last 10 videos (check recent `projects/*/script.json`).
   - Still casual American English, one short sentence each, no "Did you know?!". Reloops count toward the word budget in rule 3; cut background detail to make room, never the payoff.
   - Cut on the reloop: the shot changes on the first word of the reloop line or of its payoff.
   - Example (toothpaste square): "...and it's completely wrong. **But nobody tells you what that square is really for.** It's called an eye mark. **Here's exactly how it works.** Back at the factory, a light sensor watches for that square... **And that's not even the best part.** The color means nothing, it just has to stand out, which is why the same toothpaste shows up with different colors."

## Experiments

None running yet. The first weekly review (Sun 4 Oct 2026) picks at most 2.

## Early signals (before the first review; small numbers, don't over-read them)

- **TikTok and Instagram lose people fast.** fj-key-bumps on TikTok: 99 views, average watch 6.85 s of a 77 s video (about 9%). pen-cap-hole on Instagram: average watch 5.9 s. Batch 1 on TikTok was better: tape measure 21.9 s (30%), pan handle 17.7 s (24%). The first seconds are the likely weak spot on those two platforms.
- **YouTube is carrying the channel.** Views so far: tape measure 1,949, jeans pocket 1,368, pen cap 1,169, F/J keys 770, pan handle 320. Tape measure averaged about 90% viewed.
- **Jeans pocket got by far the most reactions:** 87 likes and 11 comments on 1,368 views (ER ≈ 7.2%); every other video had 0 comments. Its live YouTube title is "You'll Never Guess What That Tiny Pocket on Your Jeans Was Originally For", which was changed on YouTube after it was scheduled (not by the daily run). A curiosity-gap title plus a clothing/history topic may be what worked. Worth testing.
- "Looks broken but is actually engineered" (tape measure) beat a plain kitchen tip (pan handle) by about 6x on YouTube.

## History

- 29 Sep 2026: playbook created from the first week of data (numbers above, from Buffer and VidIQ on 29 Sep).
- 3 Oct 2026: Rizky's notes on the toothpaste-square video became rules 2 (opening must move, second angle inside 2 s), 5 (crop tight) and 6 (bigger captions in a dark box). These are permanent rules, not experiments. They apply to videos made from the next run on; videos already scheduled through Mon 5 Oct keep the old look. The weekly review should compare average watch time on TikTok and Instagram before and after.
- 3 Oct 2026: Rizky added rule 8, curiosity reloops (missing piece, escalation, method), to raise watch time. Permanent rule. The weekly review should check average watch time and retention on videos made with reloops against the earlier ones.
