# Run log

Newest at the bottom. One entry per run: date (Asia/Jakarta), scheduled, produced, spend estimate, problems.

- **2026-09-23** — Batch 1 made interactively (3 videos) and scheduled for 24–26 Sep 7 PM ET on YouTube, TikTok and Instagram (9 posts).
- **2026-09-24** — Daily routine couldn't produce: API keys weren't available in the scheduled-task environment. Pipeline moved to this repo; keys go into the cloud environment's API credentials / environment variables.
- **2026-09-24 23:35 WIB** — Run blocked at Step 0 (preflight): repo had only `README.md`/`ROUTINE.md`, so `pipeline/`, `state/queue.md`, `docs/production-settings.md`, `examples/tape-measure-hook/`, and `media/` referenced by ROUTINE.md didn't exist yet, and `cd pipeline` failed. Credential checks that could run independently: ElevenLabs 200 OK, Pexels 200 OK, `PIXABAY_KEY` set, fal.ai not testable (script missing); `ffmpeg`/`ffprobe` not installed. No spend, no facts invented. Needed pipeline code, initial queue/settings files, and ffmpeg on the runtime image before the next run could proceed.
