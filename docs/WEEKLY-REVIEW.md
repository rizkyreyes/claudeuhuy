# Hidden In Your Home: weekly review

You are the weekly review run for **Hidden In Your Home**, a faceless Shorts / TikTok / Instagram Reels channel about the hidden reason behind small design details on everyday objects. **Audience: Americans.** Owner: Rizky, who reads Indonesian.

Your job every Sunday: pull the numbers for everything that went out, figure out what viewers liked and what they skipped, and change the recipe for next week's videos. The daily production run reads `docs/playbook.md` before making anything, so **the playbook is where your decisions land**. This review runs **inside the Sunday daily run** (ROUTINE.md Step 0.5, ~11:01 WIB), before that day's videos are made, so they already use your changes. (A separate weekly routine couldn't get the Buffer and VidIQ connectors.)

Never print or commit an API key. Never invent numbers: if a metric isn't available, write `n/a`. Never change a fact in a video or caption without a source.

---

## Step 1. Collect the numbers

Buffer organization `6ab28b6ea45657d8dd17cfc3`. Channels: YouTube `6ab290a4ea19ca0bdeb603a4`, TikTok `6ab28e9cea19ca0bdeb5efbd`, Instagram `6abbd80aea19ca0bde2429ba`. YouTube channel id for VidIQ: `UCNsUhFLkRc9hwR4c8QWkq8A`.

**Which videos:** everything with status `sent` whose `sentAt` is in the last 8 days. Only judge a post once it is **at least 48 hours old**; younger ones go in the report as "too early" and get judged next week. Also re-check last week's "too early" posts.

**Per post (Buffer):** `list_posts` with `status: ["sent"]`, `includeMetrics: true`, filtered by the three channel ids. Buffer returns these, depending on the platform:

| Metric | YouTube | TikTok | Instagram |
|---|---|---|---|
| views | yes | yes | yes |
| reactions (likes) | yes | yes | yes |
| comments | yes | yes | yes |
| shares | no | yes | yes |
| saves | no | no | yes |
| averageTimeWatched (s) | no, use VidIQ | yes | yes |
| reach | no | yes | yes |

Buffer's own `engagementRate` shows 0 for YouTube, so **compute it yourself** for every platform:
`ER % = (likes + comments + shares + saves) / views × 100` (missing fields count as 0).
**Retention %** = average watch time ÷ video length × 100 (length = `assets[0].video.durationMs`).

**YouTube detail (VidIQ, ~5 credits per call):**
- `vidiq_channel_analytics` with `dimensions: ["video"]`, `metrics: ["views","averageViewDuration","averageViewPercentage","likes","comments","subscribersGained"]` for the last 8 days → retention and subscribers gained per video.
- `vidiq_channel_analytics` `report: "audience_geography"` → share of views from the US.
- `vidiq_channel_analytics` `report: "traffic_sources"` → Shorts feed vs search.
- For the single worst YouTube video, `report: "audience_retention"` with `filters: "video==<id>"` → the second where people leave.

**Followers / subscribers (save a snapshot every week in `docs/metrics-history.md`):**
- YouTube: `vidiq_channel_stats` → subscribers (plus `subscribersGained` above).
- Instagram: `vidiq_instagram_owner_insights` or `vidiq_ig_profile` for `hidden.in.yourhome` → followers.
- TikTok: no direct tool. Try Buffer `execute_query` (use `introspect_schema` to look for follower or audience fields on the channel). If nothing works, write `n/a` and ask Rizky for the number in the summary.
- New followers this week = this week's number minus last week's snapshot.

Keep VidIQ use under ~60 credits per review. Check `vidiq_balance` first.

**Carousels** (`state/carousels.md`): collect Instagram views, reach, likes, comments, shares and **saves**, and TikTok views and likes. Score them separately from videos: on Instagram the key signal is (saves + shares) ÷ reach. Say in the report whether carousels are pulling their weight (new followers, saves) or just filling slots, and suggest keeping, changing (theme, cover line, slide count) or dropping them.

## Step 2. Score each video

Work out the week's **median** views, ER and retention per platform. Then label each video:

- **Winner:** views ≥ 1.5× the platform median, or top 2 of the week on that platform.
- **Weak:** views < 0.5× the median **or** retention below the floor below.
- **Normal:** everything else.

Starting floors. The channel is new, so treat these as a first guess. Recalibrate in the playbook once there are 30+ videos of data.

| | YouTube | TikTok | Instagram |
|---|---|---|---|
| Retention floor (avg % watched) | 60% | 25% | 25% |
| ER floor | 2% | 3% | 2% |

**The week is "not good enough" if 2 or more of these are true:**
1. Median views dropped more than 20% from last week on 2+ platforms.
2. Median retention is below the floor on 2+ platforms.
3. Total new followers/subscribers is lower than last week.
4. Median ER is below the floor on 2+ platforms.
5. Zero comments across all platforms for the whole week.

## Step 3. Diagnose: what are viewers telling us?

Always compare **winners against weak videos**: hook line, first 2 seconds of visuals, topic/room, payoff type (safety, history, hack, myth-bust), length, title, posting slot. Read the scripts in `projects/<slug>/script.json` and the captions in `projects/<slug>/publish/captions.md`. Use this map to decide what to change:

| What the numbers show | What it usually means | What to change |
|---|---|---|
| Viewers leave around 30 s (retention curve drops in the middle third) | The story loses tension, or nothing tells them the best part is still coming | Check CTA 1 (playbook rule 4): is the "stay" line there at 12–20 s and is its promise specific? Check that a curiosity reloop lands at 25–35 s. Tighten the story (rule 9): cut any fact that doesn't move it forward. |
| Avg watch under ~8 s on TikTok/Instagram | People scroll past in the first seconds; the hook isn't landing | Object on screen at 0.0 s. Say the surprising claim in the first 1.5 s. First cut at 1.5 s or sooner. Open on the "wrong belief" or a close-up of the detail, not a wide shot. |
| Good retention early, big drop in the middle (YouTube retention curve) | The middle explains too slowly | Shorter video (try 45–60 s). Cut background history. New shot every 2–3 s. Check the curiosity reloops (playbook rule 8): is there one just before the drop, and does its payoff arrive fast? |
| Good retention, low views | Topic or packaging doesn't pull people in | Rewrite title patterns, move stronger categories earlier in `state/queue.md`, adjust hashtags (`docs/vidiq-captions.md`). |
| Good views, low likes/comments | People watch but don't react | End on a question Americans want to answer ("Which one did you have growing up?", "Be honest, did you know this?"). Rotate it; never the same line twice in a row. |
| Low new followers even on good videos | No reason to follow | Name the series in the last line ("Part of a series on stuff in your house that's smarter than it looks"). Keep one consistent follow reason. |
| One category wins over and over (e.g., kitchen, myth-busts) | Audience preference | Put more of that category earlier in the queue, still without two of the same room in a row. |
| US share of views drops below ~70% | Content or timing drifting away from Americans | Check references (US units first: inches, °F, gallons; US brands/stores only as generic descriptions), and posting slots. |

**Viewer requests:** every video now ends by asking what people want explained next (playbook rule 4). Read the comments on the week's videos (`vidiq_video_comments` for YouTube, Buffer for TikTok and Instagram). Any request that is a real everyday object with a verifiable reason goes into `docs/topics-october.md` and near the top of the `todo` rows in `state/queue.md`, with a note "viewer request". Mention in the report which requests were picked up.

## Step 4. Change the recipe (only when the week is "not good enough", or one change clearly won)

- Change **at most 2 things per week**. Otherwise we never know what worked.
- Every change is an **experiment** with a hypothesis and the metric that proves it, e.g. "Hook shows the object at 0.0 s → TikTok avg watch goes from 7 s to 12 s+".
- Next week: if the metric improved, the change becomes a **permanent rule**. If not, **revert** it.
- Write all of this into `docs/playbook.md`: update "Current rules", add or close "Experiments", and log the week under "History". Keep the file short. Merge rules instead of piling them up.
- If the change affects topic order, reorder only `todo` rows in `state/queue.md` and keep the planned slot column in time order.
- Keep the non-negotiables: vertical 1080x1920, karaoke captions at the bottom, **no text in the middle of the screen**, AI-generated label on, facts sourced, no real identifiable people.

**How the videos and captions should sound (always, not just after a bad week):**
- Casual American English, like a friend explaining something over the kitchen counter. Contractions (it's, you'll, don't). Second person ("your sink", "you've seen this").
- Short sentences. One idea per sentence. Plain words: "use" not "utilize", "make sure" not "ensure", "made so" not "designed to allow".
- No robotic filler: no "Did you know?!", "game-changer", "mind-blowing", "delve", "unlock", "This simple product design feature ensures…", no em dashes, no emojis.
- US units first (inches, °F, gallons). US spelling ("color", "center").
- Before → after example:
  - Robotic: "This simple product design feature ensures your hands always land in the correct position for efficient typing."
  - Human: "Your index fingers find those bumps without looking, so every other finger lands in the right spot."

## Step 5. Report and push

1. Write the full report to `docs/weekly/<YYYY>-W<week>.md` (English is fine), with a table per platform: video, views, likes, comments, shares, saves, ER %, retention %, label. Add followers/subscribers this week vs last week, top 3 videos, bottom 3, the diagnosis, and the changes you made.
2. Append this week's follower snapshot to `docs/metrics-history.md`.
3. Commit and push to `main` (`Weekly review <date>: <one-line summary>`).
4. Finish with a message to Rizky **in casual Indonesian**, 5–10 lines, no report tone, like texting a friend:
   - Total views this week per platform, plus new followers/subscribers.
   - Which video did best and why you think so. Which did worst and why.
   - What you changed for next week (max 2 things) and what you expect to see.
   - Anything Rizky needs to do (for example, send the TikTok follower count, or check a setting).
