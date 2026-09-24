# Hidden In Your Home — production pipeline

Everything the daily routine needs to make a video and schedule it through Buffer.

- `ROUTINE.md` — the daily procedure (the routine reads this first)
- `state/queue.md` — which topics are done / rendered / scheduled
- `docs/` — production settings, topic bank, run log
- `pipeline/` — generator + helpers
  - `build-broll.mjs`, `gen-shared.mjs` — HyperFrames composition: full-bleed b-roll + karaoke captions
  - `falsync.mjs` — fal.ai images/clips returned inline (sync mode)
  - `stock.mjs` — Pexels / Pixabay search + download
  - `tts.mjs` — ElevenLabs voice-over with word timestamps. Adapted from the MIT-licensed
    hyperframe-pro plugin (github.com/buildwithhanif/hyperframe-pro); change: the key is optional so a
    cloud-environment API credential can supply it.
- `examples/tape-measure-hook/` — a finished script + shot list to copy the format from
- `media/` — finished MP4s waiting for Buffer

API keys never go in this repo. They live in the cloud environment:
fal.ai / ElevenLabs / Pexels as **API credentials**, `PIXABAY_KEY` as an **environment variable**.
