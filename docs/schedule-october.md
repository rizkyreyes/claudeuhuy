# Posting schedule: October 2026 (2 videos a day)

Decided 28 Sep 2026 with Rizky. Every video goes to YouTube, TikTok and Instagram at the same minute.

## Daily slots

All of October is Eastern **Daylight** Time, so every `dueAt` uses offset **-04:00**. (DST ends Sun 1 Nov 2026. From 1 Nov the offset is -05:00.)

| Day | Slot A (ET) | Slot B (ET) | `dueAt` A | `dueAt` B | Rizky's time (WIB) |
|---|---|---|---|---|---|
| Mon–Fri | 12:00 PM | 7:00 PM | `T12:00:00-04:00` | `T19:00:00-04:00` | 23:00 same day, 06:00 next morning |
| Saturday | 3:00 PM | 7:00 PM | `T15:00:00-04:00` | `T19:00:00-04:00` | 02:00 and 06:00 Sunday |
| Sunday | 12:00 PM | 6:00 PM | `T12:00:00-04:00` | `T18:00:00-04:00` | 23:00 Sunday, 05:00 Monday |

62 slots from Thu 1 Oct to Sat 31 Oct. The planned topic for every slot is in `state/queue.md`.

## Why these times

- VidIQ `subscriber_insights` for our channel (UCNsUhFLkRc9hwR4c8QWkq8A) returned no activity data yet, because the channel is only a few days old. There is no channel-specific "best time" yet, so we use US-wide patterns.
- VidIQ analytics for 20–27 Sep: about 1,005 of 1,124 country-attributed views came from the US (~89%). 97% of views came from the Shorts feed, not search. So we time posts for US lunch and US evening.
- General US Shorts data (Hopper HQ roundup of Buffer's 1.8M-video study plus YouTube guidance): weekdays around 11 AM–2 PM and 6–9 PM local; Saturday afternoon 2–5 PM; Sunday evening 5–8 PM is strongest, Sunday morning weakest. Posting at ET covers the biggest US time zone. Central is 1 hour earlier and Pacific 3 hours earlier, so 7 PM ET still reaches the West Coast at 4 PM.

## Review

At the end of October, and every week on the "evaluasi mingguan" run, call `vidiq_subscriber_insights` (timezoneOffset `-04:00`) again. Once `bestThreeHourWindows` is not empty, move slots toward those windows and note the change here.

## Buffer limit

Free plan = **10 scheduled posts per channel** (not 10 total; confirmed on buffer.com/pricing and in practice on 28 Sep, when 12 posts were queued across 3 channels). At 2 videos a day that is up to 5 days queued. Keep each channel at **9 or fewer** so there's always room for a fix.
