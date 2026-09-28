# Captions and hashtags (VidIQ-curated, 28 Sep 2026)

Data came from VidIQ keyword research (country US) and outlier/title scoring. Numbers are VidIQ's monthly YouTube search estimates on 27 Sep 2026. Refresh this file once a month. Specific-object keywords ("padlock hole", "padlock drainage hole") show <750 searches. That's normal: Shorts get found in the feed, not search, so hashtags are for **topic signals**, not search traffic.

## 1. How to sound like a person (applies to every caption)

- Write the way you'd text a friend who asked "wait, why does it have that?" Short sentences. Contractions (it's, don't, you'll).
- **No em dashes (—) at all.** Use a period or a comma. No "Did you know?!", no "Here's the thing", no "game-changer", "mind-blowing", "unlock", "delve", "elevate".
- Say the actual answer in the first sentence of YouTube and Instagram. TikTok only teases.
- One idea per sentence. If a sentence has two commas and a "which", split it.
- No emojis (Rizky's rule). No ALL CAPS words.
- The follow line changes every video, and it should sound like something a person would say, e.g. "Follow if you like knowing why your stuff looks the way it does." Never reuse one within 10 videos. Check `projects/*/publish/captions.md` for the last 10.
- Read it out loud once. If it sounds like an ad or a press release, rewrite it.

Bad: "That tiny hole isn't decoration — it's a clever safety feature that protects your lock from the elements!"
Good: "That tiny hole under your padlock lets rainwater drain out, so the lock doesn't rust or crack when it freezes."

## 2. Titles (YouTube)

VidIQ `score_title` (short-form, our channel), 28 Sep:

| Title | Score |
|---|---|
| Why Does a Padlock Have a Hole in the Bottom? #shorts | 97 |
| Every Padlock Has a Second Hole. It's Not for the Key | 97 |
| The Hidden Purpose of the Tiny Hole Under Your Padlock | 90 |

So use either a **"Why does X have Y?"** question or a **two-sentence "It's not what you think"** statement. Skip "The Hidden Purpose of…" (lower score and overused by competitors). Keep it ≤ 70 characters before ` #shorts`.

If the VidIQ connector is available in the run, score 2 versions with `vidiq_score_title` (type `short`, channelId `UCNsUhFLkRc9hwR4c8QWkq8A`) and use the higher. It costs 5 credits per call. The account has ~2,000 credits a month, renewing on the 27th.

## 3. Hashtags

Pick from three layers. Total: YouTube 6–7 (last one `#shorts`), TikTok 4–5 (last one `#fyp`), Instagram 7–9 (last one `#hiddeninyourhome`).

**Layer 1: object tag (1 tag).** The object itself in plain words: `#padlock`, `#microwave`, `#toothbrush`. Use it even when volume is tiny, because it tells the algorithm what's in the video.

**Layer 2: channel core (pick 2–3, rotate).**

| Tag | VidIQ US signal | Notes |
|---|---|---|
| `#interestingfacts` | 409K US searches/mo, +156% vs baseline, competition 43.5 (score 79) | best overall opportunity, use on most videos |
| `#howthingswork` | 130K global, 22K US, score 70 | fits every video |
| `#funfacts` | 94K US, +47% | alternate with #interestingfacts |
| `#randomfacts` | 62K US, +149% | alternate |
| `#hiddendesign` | 9.4K, +84%, competition 39.5 | niche, growing |
| `#everydaydesign` | 4.6K, competition 24.9 (low) | niche |
| `#commonobjects` | 4.9K, competition 24.4 (low) | niche |

**Layer 3: room / category (pick 1–2).**

| Category | Tags (VidIQ US signal) |
|---|---|
| kitchen, packaging | `#kitchenhacks` (20K US, +28%), `#kitchentips`, `#cookingtips` (16K US) |
| cleaning, laundry | `#cleaninghacks` (9.6K US, +32%), `#cleaningtips`, `#cleaningmotivation` (14K US, +57%) |
| car | `#cartricks` (12.7K US, +126%), `#carmaintenance` (12K US, +23%), `#carcare` |
| garage, tools | `#tooltips` (+241%), `#woodworking` (61K US), `#diy` |
| home, bathroom, bedroom, living room, yard | `#homehacks` (+35%), `#householditems` (+17%), `#lifehacks` |
| tech | `#tech` (110K US), `#techfacts` |
| clothing, carry, office | `#lifehacks`, `#design`, `#history` (not VidIQ-checked, use sparingly) |

Avoid: `#didyouknow` on every post (we overused it in September), `#shorts` on TikTok/Instagram, `#fyp` on YouTube, and anything unrelated just because it's big (`#learnenglish`, `#brightside`).

## 4. Per-platform format

**YouTube**: title (section 2). Description: 2–3 plain sentences with the real answer, blank line, one follow line, blank line, hashtags.

**TikTok**: one short line that teases without giving the answer, then hashtags. Under 150 characters total.

**Instagram**: 2–3 sentences with the answer (can differ in wording from YouTube), blank line, `Follow @hidden.in.yourhome …` with a fresh ending, blank line, hashtags.

## 5. Worked example (padlock-hole, scheduled Wed 30 Sep 7 PM ET)

YouTube title: `Why Does a Padlock Have a Hole in the Bottom? #shorts`

YouTube description:
> That tiny hole under your padlock lets rainwater drain out, so the lock doesn't rust or crack when it freezes. It's also where you add lube when the shackle gets stiff. Use dry graphite or a PTFE spray, not household oil. Oil grabs dirt and turns into gunk inside the lock.
>
> Follow for more everyday stuff that's smarter than it looks.
>
> #padlock #howthingswork #interestingfacts #hiddendesign #diy #homehacks #shorts

TikTok:
> That little hole under your padlock isn't a second keyhole. #padlock #howthingswork #interestingfacts #diy #fyp

Instagram:
> That tiny hole under your padlock lets rainwater drain out, so the lock doesn't rust or crack in a freeze. It's also where the lube goes when the shackle gets stiff. Grab dry graphite or PTFE spray, not the oil can. Oil holds onto dirt and gums up the lock.
>
> Follow @hidden.in.yourhome if you like finding out why your stuff looks the way it does.
>
> #padlock #howthingswork #interestingfacts #hiddendesign #funfacts #diy #homehacks #hiddeninyourhome

## 6. What worked for competitors (VidIQ outliers, Shorts, last 6 months)

Small channels breaking out in this niche use short, concrete titles about ONE object: "The Hidden Purpose Of This Tiny Door In Ships" (187 subscribers, 107K views), "This Little Lunchbox Has a BIG Purpose" (8.3K subscribers, 805K views). Both are about one object with a plain, curious title, which fits our one-object-per-video format.
