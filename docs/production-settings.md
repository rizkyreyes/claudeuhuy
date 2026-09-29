# Production settings

## Video
- Vertical 1080x1920, 30 fps, h264 + aac, ~70–78 s. English narration, voice "Chris Anthony" (ElevenLabs `uKGPYP2uuyRQv8SeFre0`, model **`eleven_v4_turbo`** from 29 Sep 2026 (0.5x character cost); before that `eleven_multilingual_v2`), loudness -16 LUFS.
- Full-bleed b-roll, a new shot every 3–5 s, each cut on a spoken word. Stills get a slow Ken Burns drift; several real motion clips per video (stock first, 1–2 AI).
- Karaoke captions at the bottom (current word yellow `#F5C242`, spoken words white, upcoming words dimmed), dark gradient behind them. **No text in the middle of the screen.**
- All three platforms get the "AI-generated" label (the b-roll includes photoreal AI imagery).

## Cost: October 2026 (2 videos a day, decided 28 Sep 2026)
- Stock footage (Pexels / Pixabay) first for anything generic. It's free. Aim for 4–6 stock clips per video.
- AI stills (fal.ai `openai/gpt-image-2`, 1088x1920): **high** only for the 1–2 key shots, **medium** for the rest.
- AI clips: **1–2 per video**. Trying **LTX-2.3 Fast** (`fal-ai/ltx-2.3/image-to-video/fast`, 1080p 9:16, $0.06/s = $0.36 per 6 s clip) instead of minimax h3-max 768P ($0.08/s from 1 Oct = $0.48 per clip). LTX returns the file on fal.media, so the environment must be able to reach `*.fal.media`; if not, the pipeline falls back to minimax.
- Rough fal.ai spend for 62 videos: about $55–90 for the month (stills plus 1–2 LTX clips each). ElevenLabs: ~1,000–1,100 characters per video, so about 65,000 characters for October.

## Captions per platform

See `docs/vidiq-captions.md` (VidIQ-curated hashtags, title scoring, human-tone rules, worked example). Posting times: `docs/schedule-october.md`.

## Batch 1 (already scheduled, 24–26 Sep 2026)
| Video | Duration | Posts at (ET) |
|---|---|---|
| Tape measure loose hook | 73.23 s | Thu 24 Sep, 7:00 PM |
| Pan handle hole | 74.20 s | Fri 25 Sep, 7:00 PM |
| Jeans tiny pocket | 74.57 s | Sat 26 Sep, 7:00 PM |
