# Playbook: what the audience likes right now

The weekly review (`docs/WEEKLY-REVIEW.md`) updates this file every Sunday. **The daily run reads it before making any video. Where it conflicts with `docs/production-settings.md` or `docs/vidiq-captions.md`, this file wins.**

## Current rules

1. Audience is American. Casual American English in scripts and captions, contractions, second person, US units first (inches, °F, gallons), US spelling. No robotic phrasing, no em dashes, no emojis, no "Did you know?!".
2. Hook: the object (or the detail) is on screen at 0.0 s, and the surprising claim is spoken inside the first 1.5 s. **The opening must move** (Rizky, 3 Oct 2026: the toothpaste video held one slow shot for 5 s). Shot 1 is either a still (the builder adds a fast punch-in toward its `focus` point in the first 0.45 s) or a clip where something visibly moves in the first half second (a hand turning the object over, a finger pointing at the detail). **Cut to a second angle inside the first 2 s**: a tighter crop of the same still (`{ zoom: 1.6, focus: "..." }`) or a hand shot. `build-broll.mjs` refuses to build if the first shot holds longer than 2 s. No shot longer than 3 s in the first 8 s.
3. Length: aim for 60–75 s. With eleven_v4_turbo that's roughly 185–230 words (it speaks about 3.1 words per second).
4. **Two CTAs in every script** (Rizky, 3 Oct 2026: viewers only watch about 30 s of a 60–75 s video).
   - **CTA 1, the "stay" line, at about 12–20 s** (before the 30-second mark where people leave). It tells the viewer to keep watching and gives a concrete reason tied to this video's payoff: "Stay to the end, because the last part is the one you'll actually use tonight." / "Stick with me, the real reason shows up in about twenty seconds and it's not what you'd guess." The promise has to be true and has to be paid off.
   - **CTA 2, the closing line**: one ask only. A question people want to answer in the comments, or a follow line. Short, natural, tied to the story.
   - Both are written fresh for every video. Don't reuse a CTA line from the last 10 videos. CTA 1 is not a curiosity reloop and doesn't replace one (rule 8); don't put them back to back.
5. Framing: **crop tight** (Rizky, 3 Oct 2026: too much empty space around the object). The subject fills about 70–85% of the frame width and the detail the video is about is easy to see on a phone. AI still prompts say "tight close-up, subject fills the frame, no empty background". Loose stock or AI shots get cropped: stills with `{ zoom, focus }` in `shots.mjs`, clips with `node pipeline/crop.mjs`. Keep the subject in the upper two-thirds, since captions cover the bottom. Don't zoom a 1080-wide still past about 1.6 (it goes soft); regenerate it tighter instead.
6. Captions on screen: **one word at a time** (Rizky, 3 Oct 2026), big bold white text (104 px) inside a semi-transparent dark box, each word popping in as it's spoken. This is built into `pipeline/gen-shared.mjs`. Don't go back to multi-word lines, don't shrink it, don't remove the box.
7. Non-negotiables: 1080x1920, word-by-word captions at the bottom, no text in the middle of the screen, AI-generated label on, every fact sourced, no real identifiable people.

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

9. **Tell it as a story, not a list of facts** (Rizky, 3 Oct 2026). Every script follows one story from start to finish:
   - **Scene:** open inside a moment the viewer has lived, in the present tense and second person ("You're wrestling a full trash bag out of the can and it won't budge."), or inside a real moment in history, but only one your sources actually describe (a named inventor, a patent year, what the product was like before).
   - **Problem:** what goes wrong, or the question nobody answers. Make it matter a little (the mess, the cost, the danger, the annoyance).
   - **Turn:** the detail on the object turns out to be the answer. The curiosity reloops (rule 8) and CTA 1 (rule 4) sit on these turns.
   - **Resolution:** how it works and why it was made that way, strongest fact last.
   - **Button:** one line that lands the story (back to the opening scene works well), then CTA 2.
   - Link sentences with "but" and "so", not "and also". If a fact doesn't move the story forward, cut it.
   - **Never invent a person, a quote, a date or an anecdote to make the story work.** If there's no sourced history, the story is the viewer's own ("you"). Named people, years and numbers only when they're in `publish/sources.txt`.
   - Rules 2, 4 and 8 still apply in full: the claim is spoken in the first 1.5 s, 2–3 reloops, two CTAs.
10. **Posting: 1 video a day from Mon 5 Oct 2026**, every day at 7:00 PM ET (Rizky, 3 Oct 2026: the videos posted close together got almost no views on YouTube). See `docs/schedule-october.md`.

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
- 3 Oct 2026 (evening): YouTube views on the newest Shorts collapsed (toothpaste 6, microwave 38, pizza saver 4, against 300–1,950 on earlier ones), and Rizky sees viewers leaving at about 30 s. His decisions, all permanent rules: 1 video a day at 7 PM ET from 5 Oct (rule 10), storytelling scripts (rule 9), two CTAs (rule 4), one-word-at-a-time captions (rule 6). Curiosity reloops (rule 8) stay. The weekly review should watch YouTube views per video and the 30-second retention point before and after 5 Oct.
