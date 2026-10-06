# Carousels: "Myth vs fact"

Photo carousels between the videos, decided with Rizky on 30 Sep 2026. **History:** c01 was a photo carousel. c02 (5 Oct) went out as a slideshow video with music because Rizky wanted a background track. On 6 Oct 2026 he decided to go **back to photos** from c03 on. So: no video, no music. `pipeline/slideshow.mjs` and `pipeline/music/` stay in the repo but are not used.

- **Platforms:** Instagram (carousel post) and TikTok (photo post). Not YouTube.
- **When:** Monday, Wednesday, Friday at **9:00 AM ET** (`T09:00:00-04:00` in October; -05:00 from 1 Nov). That's 20:00 WIB. First one: Fri 2 Oct 2026.
- **No @handle anywhere in a carousel** (Rizky, 30 Sep 2026): not on the slides, not in the closing line, not in the captions. The slide footer shows only "Hidden In Your Home".
- **Format:** 7 slides. Slide 1 cover, slides 2–6 one myth each (MYTH struck through, then FACT and a short source line), slide 7 closing question + follow line + sources. Instagram 1080x1350 (4:5), TikTok 1080x1920 (9:16). Text on the image is fine for carousels. The "no text in the middle of the screen" rule is for videos only.
- **Audience:** Americans. Casual American English, contractions, US units (°F, inches, gallons), no robotic phrasing, no em dashes, no emojis.
- **Plan and status:** `state/carousels.md`. Themes and starting notes: the same file.

## How to make one (daily run, ROUTINE.md Step 2B)

1. **Pick the theme** from the first `todo` row in `state/carousels.md`.
2. **Research 5 myths** for that theme. Every myth needs a reliable source for the fact: a government agency (DOE, EPA, USDA, FDA, FTC, CPSC), the manufacturer, a university extension, or a reputable publication (Popular Science, Consumer Reports, Snopes for myth-busts). Cut anything you can't verify. No medical or health claims. Don't bust a myth that an **upcoming** video is about (check `state/queue.md`); myths from videos that already posted are fine.
3. **Write `projects/carousels/<id>-<slug>/carousel.json`** (format: `projects/carousels/c01-energy-myths/carousel.json`). Myth line under ~90 characters, fact under ~200, source line short ("U.S. Department of Energy", "Energizer battery FAQ").
4. **Backgrounds:** one photo per slide from Pexels (`node pipeline/stock.mjs search "<query>" photo`, then download `<url>?auto=compress&cs=tinysrgb&w=1400`). Portrait if possible. No faces, no readable brand names or logos. Put them in `projects/carousels/<id>-<slug>/bg/` (don't commit them). Make a contact sheet and look at it before rendering.
5. **Render:** `node pipeline/carousel.mjs projects/carousels/<id>-<slug>/carousel.json media/carousels/<id>-<slug> both`. Look at a contact sheet of slides 1, 2 and 7 in both sizes: text readable, nothing cut off, no brand names.
6. **Captions** in `projects/carousels/<id>-<slug>/captions.md`:
   - Instagram: 2–3 sentences, ask people to save it or tag someone, blank line, a short `Follow for …` line (fresh ending, **no @handle**), blank line, 7–9 hashtags ending `#hiddeninyourhome`. Always include `#mythbusting`.
   - TikTok: one short teaser line, then 4–5 hashtags ending `#fyp`.
7. **Sources** in `projects/carousels/<id>-<slug>/sources.txt` (fact → source URL, photo ids).
8. **Commit and push** to `main`, then schedule from the raw URLs `https://raw.githubusercontent.com/rizkyreyes/claudeuhuy/main/media/carousels/<id>-<slug>/ig/01.jpg` … `07.jpg` (and `/tt/` for TikTok):
   - Instagram `6abbd80aea19ca0bde2429ba`: `metadata.instagram: { type: "post", shouldShareToFeed: true }`, assets = the 7 `ig` images in order, each with `metadata.altText` (the slide's text).
   - TikTok `6ab28e9cea19ca0bdeb5efbd`: assets = the 7 `tt` images in order, no extra metadata.
   - `mode: customScheduled`, `schedulingType: automatic`, `dueAt` = the carousel slot.
   - Check the created post lists 7 image assets. If Buffer rejects TikTok photo posts, post Instagram only and log it.
9. Set the row in `state/carousels.md` to `scheduled`.

**Buffer limit:** max 10 scheduled posts per channel on the free plan. Videos + carousels together must stay at **9 or fewer** on Instagram and TikTok. If there's no room, the carousel waits for the next slot.

**Clean-up:** when both carousel posts show `sent`, set the row to `posted` and `git rm -r media/carousels/<id>-<slug>` (for c02, the one slideshow video: `git rm media/carousels/c02-kitchen-myths.mp4`).

**Weekly review:** judge carousels by saves and shares per view (Instagram) and views plus likes (TikTok), separately from videos. Photo carousels don't have watch time. c02 was the only slideshow video; compare it with the photo ones.
