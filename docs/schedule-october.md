# Posting schedule: October 2026 (1 video a day from 5 Oct)

**Changed 3 Oct 2026 by Rizky:** from **Mon 5 Oct 2026** the channel posts **one video a day**, not two. The Shorts that went out close together (two a day from 30 Sep) got almost no views on YouTube (toothpaste 6, microwave 38, pizza saver 4, against 300–1,950 for the ones posted once a day at 7 PM). Every video still goes to YouTube, TikTok and Instagram at the same minute.

## Daily slot (from Mon 5 Oct 2026)

All of October is Eastern **Daylight** Time, so every `dueAt` uses offset **-04:00**. (DST ends Sun 1 Nov 2026. From 1 Nov the offset is -05:00.)

| Day | Slot (ET) | `dueAt` | Rizky's time (WIB) |
|---|---|---|---|
| Every day, Mon–Sun | 7:00 PM | `T19:00:00-04:00` | 06:00 the next morning |

One slot a day, same time every day, so the upload pattern stays predictable. 27 slots from Mon 5 Oct to Sat 31 Oct; the planned topic for each is in `state/queue.md`. Topics that don't fit in October roll over to November.

Until Sun 4 Oct the old two-a-day slots apply (already scheduled): Sat 3 PM & 7 PM, Sun 12 PM & 6 PM.

## Why these times

- 7 PM ET is the slot every video from 24–29 Sep used, and those are the ones that got views. The noon slot was added on 30 Sep and is dropped again.

- VidIQ `subscriber_insights` for our channel (UCNsUhFLkRc9hwR4c8QWkq8A) returned no activity data yet, because the channel is only a few days old. There is no channel-specific "best time" yet, so we use US-wide patterns.
- VidIQ analytics for 20–27 Sep: about 1,005 of 1,124 country-attributed views came from the US (~89%). 97% of views came from the Shorts feed, not search. So we time posts for US lunch and US evening.
- General US Shorts data (Hopper HQ roundup of Buffer's 1.8M-video study plus YouTube guidance): weekdays around 11 AM–2 PM and 6–9 PM local; Saturday afternoon 2–5 PM; Sunday evening 5–8 PM is strongest, Sunday morning weakest. Posting at ET covers the biggest US time zone. Central is 1 hour earlier and Pacific 3 hours earlier, so 7 PM ET still reaches the West Coast at 4 PM.

## Review

At the end of October, and every week on the "evaluasi mingguan" run, call `vidiq_subscriber_insights` (timezoneOffset `-04:00`) again. Once `bestThreeHourWindows` is not empty, move slots toward those windows and note the change here.

## Buffer limit

Free plan = **10 scheduled posts per channel** (not 10 total; confirmed on buffer.com/pricing and in practice on 28 Sep, when 12 posts were queued across 3 channels). At 1 video a day the daily run keeps 3 days queued. Keep each channel at **9 or fewer** so there's always room for a fix.

## Carousels (added 30 Sep 2026)

Instagram + TikTok only: **Monday, Wednesday, Friday at 9:00 AM ET** (`T09:00:00-04:00`, 20:00 WIB). First one Fri 2 Oct. Plan in `state/carousels.md`, procedure in `docs/CAROUSELS.md`. To leave Buffer room for them, the daily run keeps **3 days** of videos queued.
