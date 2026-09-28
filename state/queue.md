# Production queue

Status values: `todo` → `rendered` (MP4 in `media/`, waiting for Buffer) → `scheduled` (posts created in Buffer) → `posted`.
`duration` = exact final MP4 length in seconds (used to match Buffer drafts to videos).

| # | slug | topic | status | duration | scheduled for (ET) | notes |
|---|---|---|---|---|---|---|
| b1-1 | tape-measure-hook | Loose hook on a tape measure | posted | 73.23 | Thu 24 Sep 2026 7 PM | batch 1, confirmed sent on all 3 channels |
| b1-2 | pot-handle-hole | Hole at the end of a pan handle | posted | 74.20 | Fri 25 Sep 2026 7 PM | batch 1, confirmed sent on all 3 channels |
| b1-3 | jeans-watch-pocket | Tiny pocket in jeans | posted | 74.57 | Sat 26 Sep 2026 7 PM | batch 1, confirmed sent on all 3 channels |
| b2-1 | pen-cap-hole | Hole in a ballpoint pen cap | posted | 74.77 | Sun 27 Sep 2026 7 PM | confirmed sent on all 3 channels 27 Sep |
| b2-2 | fj-key-bumps | Bumps on the F and J keys | scheduled | 77.01 | Mon 28 Sep 2026 7 PM | confirmed live in Buffer (created 26 Sep on branch gwdfjw) — a stale scheduled-posts read early in the 28 Sep run briefly said this was missing; re-checked and it was there all along, see run-log |
| b2-3 | foil-box-tabs | Locking tabs on a foil box | scheduled | 71.40 | Tue 29 Sep 2026 7 PM | confirmed live in Buffer (created 27 Sep on branch lgumw6) — same stale-read issue, re-checked and confirmed fine |
| b2-4 | padlock-hole | Hole in the bottom of a padlock | scheduled | 72.87 | Wed 30 Sep 2026 7 PM | confirmed live in Buffer (created 27 Sep, points at main branch media URL) — same stale-read issue, re-checked and confirmed fine |
| b2-5 | sink-overflow | Overflow hole in a bathroom sink | rendered | 73.13 | | captions in projects/sink-overflow/publish/captions.md, waiting for a Buffer slot (only 1/10 free after this batch) |
| b2-6 | toothpaste-square | Colored square on a toothpaste tube | todo | | | myth-bust |
| b2-7 | window-weep-holes | Weep holes in a window frame | todo | | | |
