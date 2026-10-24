# Hidden In Your Home — production pipeline

> **From 24 Oct 2026 the channel makes one 3D cross-section explainer a day (Blender + Tesseract).** The nightly cloud run follows `ROUTINE.md` and `docs/3d-playbook.md`, preps one episode in `episodes/<date>-<slug>/`, and the laptop does the GPU render, assembly and (after Rizky approves) Buffer scheduling. Queue: `state/queue-3d.md`. Examples: `pipeline3d/`. The b-roll pipeline below is archived (`docs/archive/ROUTINE-broll.md`).

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
