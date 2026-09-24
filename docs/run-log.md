# Run log — Hidden In Your Home

## 2026-09-24 23:35 WIB (Asia/Jakarta)

**Scheduled:** none.
**Produced:** none.
**Estimated spend:** $0 (no fal.ai / ElevenLabs generation calls made).

**Problem — run blocked at Step 0 (preflight), repository not yet set up:**

`ROUTINE.md` requires `state/queue.md`, `docs/production-settings.md`, the
`pipeline/` scripts (`tts.mjs`, `falsync.mjs`, `stock.mjs`, `build-broll.mjs`,
`gen-shared.mjs`), an `examples/tape-measure-hook/` reference, and `media/`.
None of these exist in the repository yet — only `README.md` and
`ROUTINE.md` are present (single commit, "Add files via upload"). Since
`pipeline/` doesn't exist, `cd pipeline && npm ls gsap` (the first Step 0
command) cannot run, so the routine stopped before any topic research,
scripting, TTS, b-roll generation, or rendering was attempted.

Credential/tooling checks that *could* run independently of the missing
pipeline code:

| Check | Result |
|---|---|
| ElevenLabs (`GET /v1/voices/uKGPYP2uuyRQv8SeFre0`) | 200 OK |
| Pexels (`GET /v1/search?query=mug`) | 200 OK |
| `PIXABAY_KEY` env var | set |
| fal.ai (`falsync.mjs probe`) | not testable — script doesn't exist yet |
| `ffmpeg` / `ffprobe` | **not installed** (`which` exit 1 for both) |
| Chromium for HyperFrames | present at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` |
| Node / npm | v22.22.2 / 10.9.7 |

No API key was printed, logged, or committed. No facts, topics, or queue
entries were invented to paper over the missing files.

**Action needed from Rizky:** push the actual pipeline code (`pipeline/`,
`examples/tape-measure-hook/`), the initial `state/queue.md` (topic queue)
and `docs/production-settings.md` (caption formats, per-platform settings)
to this repo/branch, and make sure the runtime image has `ffmpeg`/`ffprobe`
installed. Once those land, the next scheduled run will pick up normally
from Step 0.
