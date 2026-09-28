# Hidden In Your Home — daily routine

You are the daily production run for **Hidden In Your Home**, a faceless short-form channel (YouTube Shorts, TikTok, Facebook Reels) about the hidden reason behind small design details on everyday objects. English, US audience. Owner: Rizky (writes in Indonesian — any note to him is in plain, friendly Indonesian).

Work in this repository, on the `main` branch (commit and push straight to `main`). Read `state/queue.md`, `docs/production-settings.md`, `docs/schedule-october.md` and `docs/vidiq-captions.md` first. At the end, update `state/queue.md` and append to `docs/run-log.md`, then commit and push.

**October 2026 target: 2 videos a day** (62 slots, planned topic per slot in `state/queue.md`).

**Never** print, log or commit an API key. Never invent facts, numbers or quotes. Never depict a real, identifiable person.

---

## Step 0 — Preflight (stop early if broken)

```bash
export NODE_USE_ENV_PROXY=1                                 # Node's fetch ignores the proxy without this; keep it for every node call
cd pipeline && npm ls gsap >/dev/null 2>&1 || npm i gsap@3.14.2 --no-save
node falsync.mjs probe                                     # HTTP 200 = fal credential works, 401 = missing
node falsync.mjs cdn                                       # fal.media reachable -> clips with `ltx`; not reachable -> `video` (minimax)
curl -s -o /dev/null -w "%{http_code}\n" https://api.elevenlabs.io/v1/voices/uKGPYP2uuyRQv8SeFre0   # 200 = works
curl -s -o /dev/null -w "%{http_code}\n" "https://api.pexels.com/v1/search?query=mug&per_page=1"     # 200 = works
[ -n "$PIXABAY_KEY" ] && echo pixabay set || echo pixabay NOT set
which ffmpeg ffprobe; ls /opt/pw-browsers/*/chrome-linux/chrome 2>/dev/null
```

- If ElevenLabs or fal fail → do not produce. Log the failure in `docs/run-log.md`, push, and end with a short Indonesian message telling Rizky which credential is not reaching the environment.
- Pexels/Pixabay failing is not fatal (fall back to AI stills), but log it.
- If the VidIQ tools (`vidiq_*`) are available in this run, call `vidiq_balance` (free). Under 100 credits: skip title scoring this run. If VidIQ isn't connected at all, just follow `docs/vidiq-captions.md`.
- ElevenLabs is pay-as-you-go. If `curl -s https://api.elevenlabs.io/v1/user/subscription` shows fewer than 2,500 characters left (`character_limit - character_count`), produce only what fits and tell Rizky to top up.

## Step 1 — Buffer housekeeping (always, before producing)

Buffer organization **"My organization"** `6ab28b6ea45657d8dd17cfc3`. Channels (Instagram was replaced by Facebook on 28 Sep 2026; never post to Instagram, and if a channel id below is missing from `list_channels`, stop scheduling and tell Rizky):

| Channel | id | Post settings |
|---|---|---|
| YouTube "Hidden In Your Home" | `6ab290a4ea19ca0bdeb603a4` | metadata.youtube: title (≤100 chars, ends `#shorts`), categoryId `"27"`, privacy public, madeForKids false, isAiGenerated true, notifySubscribers true |
| TikTok hidden.in.yourhome | `6ab28e9cea19ca0bdeb5efbd` | metadata.tiktok.isAiGenerated true |
| Facebook Page "Hidden In Your Home" | `6aba95c7ea19ca0bde14db33` | metadata.facebook: type `reel` (Buffer has no AI-label field for Facebook) |

Rules:
- Before creating or deleting anything, if `list_posts` shows fewer scheduled posts than `state/queue.md` expects, query again once. On 28 Sep a stale empty result caused 9 duplicate posts.
- Free plan: **max 10 scheduled posts per channel** (not in total). One video = 1 post on each of the 3 channels. Keep every channel at 9 or fewer scheduled posts.
- Posting times: **two slots a day**, see `docs/schedule-october.md` (Mon–Fri 12 PM & 7 PM ET, Sat 3 PM & 7 PM ET, Sun 12 PM & 6 PM ET). Same minute on all three channels. Give each video the planned slot from its row in `state/queue.md`; if that slot is already past or taken, use the earliest empty future slot and update the row. `dueAt` with offset -04:00 for all of October (EST -05:00 from 1 Nov 2026), `mode: customScheduled`, `schedulingType: automatic`. Never schedule a slot less than 1 hour from now.
- Captions: follow `docs/vidiq-captions.md` exactly (human tone, no em dashes, 3-layer hashtags, per-platform format). Each video gets a unique follow line.

**Clean up posted videos.** For every `scheduled` row whose 3 posts all show status `sent`, set the row to `posted` and `git rm media/<slug>.mp4` (the platforms already have the video; this keeps the repo from growing ~2 GB a month). Never remove a file whose posts are still `scheduled`.

**Pick up videos waiting in Buffer.** Rizky may have uploaded finished MP4s as drafts (Buffer composer → Save Draft). Find them with `execute_query`:
```graphql
query { contentItems(first: 20, input: {organizationId: "6ab28b6ea45657d8dd17cfc3"}) { edges { node { id createdAt body { __typename ... on DraftContent { text assets { source ... on VideoAsset { video { durationMs } } } } } } } } }
```
Match each draft to a row in `state/queue.md` with status `rendered` by video duration (±0.3 s). For each match, if slots allow, create the three posts using the draft's `assets[0].source` as the video URL. Confirm each created post's asset shows the expected `durationMs`. Then mark the row `scheduled` with the date. Leave the draft itself in place (the posts use its media).

## Step 2 — Produce videos to fill the next 4 days

Count the slots from now through the next 96 hours (4 days, max 8 slots, which also keeps each Buffer channel at 9 or fewer) that don't have a `scheduled` or `rendered` video yet. Produce that many videos, **at most 3 per run**, taking `todo` rows top to bottom. Usually that's 2. If a run ends early, schedule what's finished; the next run catches up. If a topic's key fact can't be verified, mark the row `cut` with the reason and use the first `spare` row instead. If no `todo` or `spare` rows are left, research new topics (see "Topic rules") and add them to `docs/topics-october.md` with sources.

For the chosen topic, in `projects/<slug>/`:

1. **Fact-check first.** The topic's starting notes and sources are in `docs/topics-october.md` (or `docs/topics.md` for the first three). Search the web for every claim, number, date and named source. Mark each LOCKED (verified this run) or cut it. Record sources in `projects/<slug>/publish/sources.txt`.
2. **Script** → `script.json` (format: `examples/tape-measure-hook/script.json`). One continuous narration, ~165–190 words ≈ 70–76 s with eleven_v4_turbo (~2.5 words/s). Hook complete in the first 2 seconds, open loop, payoff, one CTA line. Written for the ear. Voice `uKGPYP2uuyRQv8SeFre0` ("Chris Anthony"), model **`eleven_v4_turbo`** (Eleven v4 Turbo, half the character cost of v4, chosen by Rizky 29 Sep 2026; set `"modelId": "eleven_v4_turbo"` in script.json). No square brackets in the narration: v4 models read `[...]` as delivery tags.
3. **Voice-over**: `node ../../pipeline/tts.mjs script.json assets/vo` → `assets/vo/audio_meta.json` (word timestamps). If the take is > 80 s, trim words and regenerate with `--force`.
4. **Shot list** → `shots.mjs` (format: `examples/tape-measure-hook/shots.mjs`): 15–20 cues, cut every 3–5 s on a spoken word. Each cue's word is the *next occurrence after the previous cue* — avoid ambiguous short words ("a", "the", "it"), prefer distinctive words.
5. **B-roll — mixed scenario** (costs matter):
   - Generic shots (kitchens, workshops, hands working, factories, weather, archive-feel) → **stock first**: `node ../../pipeline/stock.mjs search "<query>" video|photo`, download with `get`. Prefer portrait ≥1080x1920. Save stills to `assets/broll/<id>.jpg` (crop/scale to 1080x1920 with ffmpeg) and clips to `assets/footage/<id>.mp4` (normalize: `ffmpeg -i in -t <≤10> -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -an -c:v libx264 -crf 18 -pix_fmt yuv420p out.mp4`, then write `<id>.json` `{"duration": <seconds>}` and `<id>_last.jpg` = last frame).
   - Object-specific shots stock can't show → AI stills: `node ../../pipeline/falsync.mjs image assets/broll/<id>.jpg 1088x1920 <quality> "<prompt>"`. **quality high only for the 1–2 key shots** (hook + core mechanism), **medium for all others**. Prompt style: photorealistic, natural light, subject centred in upper two-thirds, bottom quarter darker, no text/letters/logos, faces never visible.
   - Motion: use **stock video first** (aim for 4–6 stock clips per video, like padlock-hole did). Then **1–2 AI clips per video max**. If `falsync.mjs cdn` said fal.media is reachable, use LTX-2.3 Fast: `node ../../pipeline/falsync.mjs ltx <still.jpg> assets/footage/<id>.mp4 6 "<motion prompt>"` (1080p 9:16, $0.06/s = $0.36 per 6 s clip). Otherwise use minimax: `node ../../pipeline/falsync.mjs video <still.jpg> assets/footage/<id>.mp4 6 "<motion prompt>"` (768P, $0.08/s from 1 Oct 2026 = $0.48 per clip). Prompts: locked-off camera, subtle realistic motion, no text. Normalize to 1080x1920/30fps as above. LTX is on trial in October: after each LTX clip, look at 3 frames of it and write one line in the run log (sharp / soft / warped). If 3 LTX clips in a row look worse than minimax, switch back and tell Rizky.
   - **Every cue id needs a still at `assets/broll/<id>.jpg`**, including clips (use the clip's first frame: `ffmpeg -i clip.mp4 -frames:v 1 -q:v 2 assets/broll/<id>.jpg`). A cue marked `"clip"` plays `assets/footage/<id>.mp4` and falls back to the still if the clip is missing.
   - Log every stock file (source, page URL, author) and every AI asset ("AI-generated illustrative, not a real person/event") in `publish/sources.txt`.
6. **Build**: copy `vendor/gsap.min.js` from `node_modules/gsap/dist/gsap.min.js` into `projects/<slug>/vendor/`, then `node ../../pipeline/build-broll.mjs .` → `index.html` (full-bleed b-roll + karaoke captions, **no center text**).
7. **Check & render**:
   ```bash
   export HYPERFRAMES_BROWSER_PATH=$(ls /opt/pw-browsers/*/chrome-linux/chrome | head -1)
   npx --yes hyperframes check .            # must pass; info-level container_overflow from Ken Burns is expected
   npx --yes hyperframes render . -o out.mp4
   ffmpeg -i out.mp4 -c:v libx264 -preset slow -crf 21 -maxrate 8M -bufsize 16M -c:a aac -b:a 192k -movflags +faststart final.mp4
   ```
   If `final.mp4` > 30 MB, re-encode two-pass to about 28 MB (the repo takes 2 videos a day). Verify with ffprobe (1080x1920, 30 fps, h264/aac) and extract ~12 frames into a contact sheet and look at it: captions readable, b-roll matches the words, no black frames, no garbled text in images.
8. **Captions**: write `publish/captions.md` following `docs/vidiq-captions.md`. If VidIQ is connected and has credits, score two title versions with `vidiq_score_title` and keep the higher; note both scores in captions.md.
9. **Deliver**: copy `final.mp4` to `media/<slug>.mp4` in the repo, set the row in `state/queue.md` to `rendered` with the exact duration (seconds, 2 decimals).
10. **Schedule it** (the repo is public): commit and push to `main` first, then the file is at `https://raw.githubusercontent.com/rizkyreyes/claudeuhuy/main/media/<slug>.mp4`. If every channel has room (≤ 9 after adding), `create_post` for YouTube with that URL in the video's slot. If the returned asset has `durationMs` > 0, create the TikTok and Facebook posts too and mark `scheduled`. If Buffer rejects the URL or the duration is 0, delete that post and keep the row `rendered` — Rizky uploads it manually.

## Step 3 — Close out

- Append to `docs/run-log.md`: date (Asia/Jakarta), what was scheduled, what was produced, estimated spend (count of high/medium stills, clips), any problem.
- Commit and push.
- Final message in Indonesian, 3–6 lines, casual and human (no report tone): which videos got scheduled and when (in WIB), the next empty slot, any MP4 Rizky must upload by hand, and any blocker (credits, balance, failed fact-check).

## Topic rules

A topic = a small, visible detail on an everyday object whose hidden purpose surprises people (hook shape: "Why does X have Y?"). It must have a verifiable reason from a reliable source. No two consecutive videos from the same room or with the same payoff type. Myths get debunked, never repeated as fact. Add new topics to `docs/topics.md` with sources before scripting them.
