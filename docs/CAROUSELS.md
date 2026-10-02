# Carousels: "Myth vs fact" slideshow videos

Decided with Rizky on 30 Sep 2026 as photo carousels. **Changed 2 Oct 2026:** Rizky wants background music, and Instagram/TikTok don't let schedulers attach sounds from their music libraries, so each carousel is now rendered as a **slideshow video with quiet royalty-free music inside the file** and posted as an Instagram Reel and a TikTok video. (c01 went out as a photo carousel before this change.)

- **Platforms:** Instagram (Reel) and TikTok (video). Not YouTube unless Rizky asks.
- **When:** Monday, Wednesday, Friday at **9:00 AM ET** (`T09:00:00-04:00` in October; -05:00 from 1 Nov). That's 20:00 WIB. First one: Fri 2 Oct 2026.
- **No @handle anywhere in a carousel** (Rizky, 30 Sep 2026): not on the slides, not in the closing line, not in the captions. The slide footer shows only "Hidden In Your Home".
- **Format:** one 1080x1920 video, about 45–55 s. Cover (2.6 s), then 5 myths: each shows the MYTH alone for 2.2 s, then strikes it through and reveals the FACT with a short source line (4.5–8.5 s depending on length), then a closing question + follow line + sources (4.5 s). Text on screen is the whole point here; the "no text in the middle of the screen" rule is for the narrated videos only.
- **Music:** royalty-free instrumentals in `pipeline/music/`, rotated automatically, mixed very quietly at about -30 LUFS with a fade in and out (Rizky found -22 too loud on 2 Oct 2026; do not raise it). **Never use a commercial or trending song** (copyright; the platforms mute or remove those).
- **Audience:** Americans. Casual American English, contractions, US units (°F, inches, gallons), no robotic phrasing, no em dashes, no emojis.
- **Plan and status:** `state/carousels.md`. Themes and starting notes: the same file.

## How to make one (daily run, ROUTINE.md Step 2B)

1. **Pick the theme** from the first `todo` row in `state/carousels.md`.
2. **Research 5 myths** for that theme. Every myth needs a reliable source for the fact: a government agency (DOE, EPA, USDA, FDA, FTC, CPSC), the manufacturer, a university extension, or a reputable publication (Popular Science, Consumer Reports, Snopes for myth-busts). Cut anything you can't verify. No medical or health claims. Don't bust a myth that an **upcoming** video is about (check `state/queue.md`); myths from videos that already posted are fine.
3. **Write `projects/carousels/<id>-<slug>/carousel.json`** (format: `projects/carousels/c01-energy-myths/carousel.json`). Myth line under ~90 characters, fact under ~200, source line short ("U.S. Department of Energy", "Energizer battery FAQ").
4. **Backgrounds:** one photo per slide from Pexels (`node pipeline/stock.mjs search "<query>" photo`, then download `<url>?auto=compress&cs=tinysrgb&w=1400`). Portrait if possible. No faces, no readable brand names or logos. Put them in `projects/carousels/<id>-<slug>/bg/` (don't commit them). Make a contact sheet and look at it before rendering.
5. **Render the frames and the video:**
   ```bash
   node pipeline/carousel.mjs  projects/carousels/<id>-<slug>/carousel.json projects/carousels/<id>-<slug>/work frames
   node pipeline/slideshow.mjs projects/carousels/<id>-<slug>/carousel.json projects/carousels/<id>-<slug>/work/frames media/carousels/<id>-<slug>.mp4
   ```
   Extract ~8 frames into a contact sheet and look at it: text readable and clear of the bottom 20% of the frame, nothing cut off, no brand names. Check with ffprobe that the file has an audio stream. Don't commit the `work/` folder.
6. **Captions** in `projects/carousels/<id>-<slug>/captions.md`:
   - Instagram: 2–3 sentences, ask people to save it or tag someone, blank line, a short `Follow for …` line (fresh ending, **no @handle**), blank line, 7–9 hashtags ending `#hiddeninyourhome`. Always include `#mythbusting`.
   - TikTok: one short teaser line, then 4–5 hashtags ending `#fyp`.
7. **Sources** in `projects/carousels/<id>-<slug>/sources.txt` (fact → source URL, photo ids, which music track).
8. **Commit and push** to `main`, then schedule from `https://raw.githubusercontent.com/rizkyreyes/claudeuhuy/main/media/carousels/<id>-<slug>.mp4`:
   - Instagram `6abbd80aea19ca0bde2429ba`: `metadata.instagram: { type: "reel", shouldShareToFeed: true }`.
   - TikTok `6ab28e9cea19ca0bdeb5efbd`: video asset, no extra metadata.
   - `mode: customScheduled`, `schedulingType: automatic`, `dueAt` = the carousel slot. Confirm `durationMs` > 0 on both posts.
9. Set the row in `state/carousels.md` to `scheduled`.

**Buffer limit:** max 10 scheduled posts per channel on the free plan. Videos + carousels together must stay at **9 or fewer** on Instagram and TikTok. If there's no room, the carousel waits for the next slot.

**Clean-up:** when both posts show `sent`, set the row to `posted` and `git rm media/carousels/<id>-<slug>.mp4` (for c01: `git rm -r media/carousels/c01-energy-myths`).

**Weekly review:** judge these separately from the narrated videos: views, average watch time ÷ length, saves and shares (Instagram), likes (TikTok). Compare c01 (photo carousel, no music) with the later slideshow videos.
