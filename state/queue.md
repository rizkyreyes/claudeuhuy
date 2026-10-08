# Production queue

Channels (from 29 Sep 2026): **YouTube, TikTok, Instagram** (Instagram re-connected with a new id; Facebook was used 28–29 Sep and dropped).

Status values: `todo` → `rendered` (MP4 in `media/`, waiting for Buffer) → `scheduled` (posts created in Buffer) → `posted`.
`duration` = exact final MP4 length in seconds (used to match Buffer drafts to videos).
**From Mon 5 Oct 2026: 1 video a day at 7 PM ET** (Rizky, 3 Oct). Planned slots below were re-dated on 3 Oct; topics that no longer fit in October roll over to November.
`scheduled for (ET)` on `todo` rows is the PLANNED slot from `docs/schedule-october.md`. If production falls behind, don't skip topics: give the next `todo` row the earliest empty slot and update this column to the real time.
`spare` rows are only used when a planned topic has to be cut (fact can't be verified).

| # | slug | topic | status | duration | scheduled for (ET) | notes |
|---|---|---|---|---|---|---|
| b1-1 | tape-measure-hook | Loose hook on a tape measure | posted | 73.23 | Thu 24 Sep 2026 7 PM | batch 1, confirmed sent on all 3 channels |
| b1-2 | pot-handle-hole | Hole at the end of a pan handle | posted | 74.20 | Fri 25 Sep 2026 7 PM | batch 1, confirmed sent on all 3 channels |
| b1-3 | jeans-watch-pocket | Tiny pocket in jeans | posted | 74.57 | Sat 26 Sep 2026 7 PM | batch 1, confirmed sent on all 3 channels |
| b2-1 | pen-cap-hole | Hole in a ballpoint pen cap | posted | 74.77 | Sun 27 Sep 2026 7 PM | produced on branch claude/optimistic-ramanujan-vevymc, confirmed live in Buffer, media/sources recovered to main |
| b2-2 | fj-key-bumps | Bumps on the F and J keys | posted | 77.01 | Mon 28 Sep 2026 7 PM | confirmed sent on all 3 channels 28 Sep, media removed 29 Sep |
| b2-3 | foil-box-tabs | Locking tabs on a foil box | posted | 71.40 | Tue 29 Sep 2026 7 PM | produced on branch claude/optimistic-ramanujan-lgumw6, confirmed live in Buffer, media/sources recovered to main |
| b2-4 | padlock-hole | Hole in the bottom of a padlock | posted | 72.87 | Wed 30 Sep 2026 7 PM | scheduled 28 Sep from main/media via raw URL, captions rewritten with VidIQ hashtags |
| o-01 | sink-overflow | Overflow hole in a bathroom sink | posted | 73.13 | Thu 1 Oct 2026 12 PM | produced by the 28 Sep run; scheduled 28 Sep on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep) from main/media |
| o-02 | toothpaste-square | Colored square on a toothpaste tube | posted | 60.44 | Wed 30 Sep 2026 12 PM | produced 29 Sep, scheduled on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep); took the empty Wed noon slot |
| o-03 | window-weep-holes | Weep holes in a window frame | posted | 75.11 | Thu 1 Oct 2026 7 PM | produced 29 Sep, scheduled on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep) |
| o-04 | microwave-door-mesh | Metal mesh dots in the microwave door | posted | 69.73 | Fri 2 Oct 2026 12 PM | produced 29 Sep, scheduled on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep) |
| o-05 | pizza-saver-table | Little plastic "table" in a pizza box | posted | 76.77 | Fri 2 Oct 2026 7 PM | produced 30 Sep, scheduled on YouTube, TikTok, Instagram from main/media; took the empty Fri 7 PM slot (planned Sat 3 PM) |
| o-06 | care-label-dots | Dots inside laundry care symbols | posted | 78.85 | Sat 3 Oct 2026 3 PM | produced 30 Sep, scheduled on all 3 channels; small brand name visible on washer panel ~1.5 s |
| o-07 | jeans-rivets | Copper rivets on jeans pockets | posted | 75.40 | Sat 3 Oct 2026 7 PM | produced 30 Sep, scheduled on all 3 channels (planned Sun 12 PM) |
| o-08 | trash-can-vents | Vent holes near the top of a trash can | posted | 68.61 | Sun 4 Oct 2026 12 PM | produced 1 Oct, scheduled on all 3 channels (planned Sun 6 PM); LTX hook clip warped so a still was used |
| o-09 | pillow-law-tag | "Do not remove under penalty of law" pillow tag | posted | 71.33 | Sun 4 Oct 2026 6 PM | produced 1 Oct, scheduled on all 3 channels (planned Mon 5 Oct 12 PM); gavel stock clip has tiny unreadable pseudo-text ~8 s |
| o-10 | heinz-57-tap-spot | Embossed "57" on a glass Heinz bottle | posted | 72.13 | Mon 5 Oct 2026 7 PM | produced 2 Oct, scheduled on all 3 channels (planned Mon 7 PM); generic unlabeled bottle · packaging · hack · docs/topics-october.md; moved 3 Oct from Mon 5 Oct 12 PM when the channel went to 1 video a day |
| o-11 | pot-lid-hole | Small hole in a pot or slow-cooker lid | posted | 64.93 | Tue 6 Oct 2026 7 PM | produced 2 Oct, scheduled on all 3 channels; topic note corrected (some slow cookers do have a probe hole) · kitchen · myth-bust · docs/topics-october.md; moved 3 Oct from Mon 5 Oct 7 PM when the channel went to 1 video a day |
| o-12 | iron-button-groove | Notch at the tip of an iron's soleplate | posted | 66.84 | Wed 7 Oct 2026 7 PM | produced 3 Oct, scheduled on all 3 channels; LTX t03 warped after 2.6 s so trimmed; laundry · hack · docs/topics-october.md; moved 3 Oct from Tue 6 Oct 7 PM when the channel went to 1 video a day |
| o-13 | hair-dryer-plug-block | Chunky block on a hair dryer plug | scheduled | 76.84 | Thu 8 Oct 2026 7 PM | produced 3 Oct, scheduled on all 3 channels (planned Wed 7 Oct 12 PM); bathroom · safety · docs/topics-october.md; moved 3 Oct from Tue 6 Oct 12 PM when the channel went to 1 video a day |
| o-14 | zipper-lock-tab | Fold-down tab on a jeans zipper | scheduled | 76.70 | Fri 9 Oct 2026 7 PM | produced 7 Oct, scheduled on all 3 channels; LTX t04 pin macro sharp, t06 hand clip warped so a still was used; clothing · hack · docs/topics-october.md |
| o-15 | mattress-handles | Handles on the side of a mattress | todo | | Sat 10 Oct 2026 7 PM | bedroom · myth-bust · docs/topics-october.md |
| o-16 | vacuum-suction-valve | Sliding vent on a vacuum hose handle | todo | | Sun 11 Oct 2026 7 PM | cleaning · hack · docs/topics-october.md |
| o-17 | toothbrush-indicator-bristles | Blue bristles on a toothbrush | todo | | Mon 12 Oct 2026 7 PM | bathroom · convenience · docs/topics-october.md |
| o-18 | rice-cooker-cup | The measuring cup that comes with a rice cooker | todo | | Tue 13 Oct 2026 7 PM | kitchen · hack · docs/topics-october.md |
| o-19 | smoke-alarm-date | Date on the back of a smoke alarm | todo | | Wed 14 Oct 2026 7 PM | bedroom · safety · docs/topics-october.md |
| o-20 | egg-carton-pack-date | Three-digit number on an egg carton | todo | | Thu 15 Oct 2026 7 PM | packaging · hack · docs/topics-october.md |
| o-21 | knife-hollow-edge-dimples | Oval dimples along a santoku blade | todo | | Fri 16 Oct 2026 7 PM | kitchen · convenience · docs/topics-october.md |
| o-22 | he-detergent-logo | "HE" logo on laundry detergent | todo | | Sat 17 Oct 2026 7 PM | laundry · hack · docs/topics-october.md |
| o-23 | bottle-cap-teeth | Crimped teeth on a metal bottle cap | todo | | Sun 18 Oct 2026 7 PM | packaging · history · docs/topics-october.md |
| o-24 | running-shoe-extra-eyelet | Extra eyelet at the top of running shoes | todo | | Mon 19 Oct 2026 7 PM | clothing · hack · docs/topics-october.md |
| o-25 | spaghetti-spoon-hole | Hole in the middle of a spaghetti spoon | todo | | Tue 20 Oct 2026 7 PM | kitchen · myth-bust · docs/topics-october.md |
| o-26 | dustpan-comb-teeth | Row of teeth on a dustpan edge | todo | | Wed 21 Oct 2026 7 PM | cleaning · hack · docs/topics-october.md |
| o-27 | wine-bottle-punt | Dent in the bottom of a wine bottle | todo | | Thu 22 Oct 2026 7 PM | packaging · myth-bust · docs/topics-october.md |
| o-28 | washer-debris-filter-door | Small door at the bottom of a front-load washer | todo | | Fri 23 Oct 2026 7 PM | laundry · hack · docs/topics-october.md |
| o-29 | brogue-shoe-holes | Holes on wingtip shoes | todo | | Sat 24 Oct 2026 7 PM | clothing · history · docs/topics-october.md |
| o-30 | plunger-flange | Extra rubber flap under a plunger cup | todo | | Sun 25 Oct 2026 7 PM | bathroom · hack · docs/topics-october.md |
| o-31 | child-resistant-cap-test | Push-and-turn cap on cleaning products | todo | | Mon 26 Oct 2026 7 PM | cleaning · safety · docs/topics-october.md |
| o-32 | crisper-drawer-slider | Humidity slider on a crisper drawer | todo | | Tue 27 Oct 2026 7 PM | kitchen · hack · docs/topics-october.md |
| o-33 | plastic-resin-code | Number inside the recycling arrows | todo | | Wed 28 Oct 2026 7 PM | packaging · myth-bust · docs/topics-october.md |
| r-01 | toothpaste-square-v2 | REMAKE: colored square on a toothpaste tube | todo | | Thu 29 Oct 2026 7 PM | remake of o-02 `toothpaste-square` (6 YouTube views); new video under the current playbook, see "Remakes" in ROUTINE.md; packaging · myth-bust · facts: `projects/toothpaste-square/publish/sources.txt` |
| r-02 | microwave-door-mesh-v2 | REMAKE: metal mesh dots in the microwave door | todo | | Fri 30 Oct 2026 7 PM | remake of o-04 `microwave-door-mesh` (38 YouTube views); new video under the current playbook, see "Remakes" in ROUTINE.md; kitchen · safety · facts: `projects/microwave-door-mesh/publish/sources.txt` |
| r-03 | pizza-saver-table-v2 | REMAKE: little plastic "table" in a pizza box | todo | | Sat 31 Oct 2026 7 PM | remake of o-05 `pizza-saver-table` (4 YouTube views); new video under the current playbook, see "Remakes" in ROUTINE.md; the patent is Feb 12, 1985 (Carmela Vitale), not 1993; packaging · history · facts: `projects/pizza-saver-table/publish/sources.txt` |
| o-34 | tape-measure-black-diamonds | Black diamonds on a tape measure | todo | | November (rolls over) | garage · hack · docs/topics-october.md; gave up its Thu 29 Oct 7 PM slot to a remake on 4 Oct |
| o-35 | party-cup-lines | Lines on a red party cup | todo | | November (rolls over) | kitchen · myth-bust · docs/topics-october.md; gave up its Fri 30 Oct 7 PM slot to a remake on 4 Oct |
| o-36 | sticky-notes-yellow | Yellow sticky notes | todo | | November (rolls over) | office · history · docs/topics-october.md; gave up its Sat 31 Oct 7 PM slot to a remake on 4 Oct |
| o-37 | sd-card-lock-switch | Lock switch on an SD card | todo | | November (rolls over) | tech · myth-bust · docs/topics-october.md |
| o-38 | fire-hydrant-cap-colors | Colored cap on a fire hydrant | todo | | November (rolls over) | yard · safety · docs/topics-october.md |
| o-39 | headrest-window-myth | Removable car headrest | todo | | November (rolls over) | car · myth-bust · docs/topics-october.md |
| o-40 | tamper-resistant-outlets | Hidden shutters in newer outlets | todo | | November (rolls over) | living-room · safety · docs/topics-october.md |
| o-41 | do-not-duplicate-key | "Do Not Duplicate" on a key | todo | | November (rolls over) | carry · myth-bust · docs/topics-october.md |
| o-42 | stapler-anvil-pinning | Rotating plate under a stapler | todo | | November (rolls over) | office · hack · docs/topics-october.md |
| o-43 | phillips-cam-out-myth | Phillips screws that strip | todo | | November (rolls over) | garage · myth-bust · docs/topics-october.md |
| o-44 | plug-prong-holes | Holes in plug prongs | todo | | November (rolls over) | tech · manufacturing · docs/topics-october.md |
| o-45 | fuel-gauge-arrow | Arrow next to the fuel gauge | todo | | November (rolls over) | car · hack · docs/topics-october.md |
| o-46 | utility-marking-flags | Colored flags in your yard | todo | | November (rolls over) | yard · safety · docs/topics-october.md |
| o-47 | privacy-knob-hole | Tiny hole in a bathroom doorknob | todo | | November (rolls over) | living-room · hack · docs/topics-october.md |
| o-48 | backpack-lash-tab | Diamond patch on a backpack | todo | | November (rolls over) | carry · history · docs/topics-october.md |
| o-49 | windshield-frit-dots | Black dots around the windshield | todo | | November (rolls over) | car · manufacturing · docs/topics-october.md |
| o-50 | snap-off-blade | Snap-off lines on a box cutter blade | todo | | November (rolls over) | garage · history · docs/topics-october.md |
| o-51 | mailbox-flag-color | Flag on a curbside mailbox | todo | | November (rolls over) | yard · myth-bust · docs/topics-october.md |
| o-52 | yellow-pencils | Yellow pencils | todo | | November (rolls over) | office · history · docs/topics-october.md |
| o-53 | two-by-four-size | A 2x4 isn't 2 by 4 | todo | | November (rolls over) | garage · manufacturing · docs/topics-october.md |
| o-54 | keypad-number-order | Phone keypad vs calculator order | todo | | November (rolls over) | tech · history · docs/topics-october.md |
| o-55 | hexagonal-pencils | Six-sided pencils | todo | | November (rolls over) | office · manufacturing · docs/topics-october.md |
| o-56 | coin-reeded-edges | Ridges on dimes and quarters | todo | | November (rolls over) | carry · history · docs/topics-october.md |
| o-57 | ferrite-bead-cable | Lump on a laptop charger cord | todo | | November (rolls over) | tech · safety · docs/topics-october.md |
| o-58 | ceiling-fan-switch | Switch on a ceiling fan | todo | | November (rolls over) | living-room · hack · docs/topics-october.md |
| o-59 | passenger-mirror-warning | "Objects in mirror are closer than they appear" | todo | | November (rolls over) | car · safety · docs/topics-october.md |
| o-60 | glasses-frame-numbers | Tiny numbers inside your glasses arm | todo | | November (rolls over) | carry · hack · docs/topics-october.md |
| o-61 | curb-ramp-bumps | Bumpy pad at the curb ramp | todo | | November (rolls over) | yard · safety · docs/topics-october.md |
| o-62 | iphone-camera-mic-hole | Tiny hole next to the phone camera | todo | | November (rolls over) | tech · convenience · docs/topics-october.md |
| sp-1 | ykk-zipper | "YKK" on zipper pulls | spare | | | only if a topic above is cut · docs/topics-october.md |
| sp-2 | seat-belt-button | Button on a seat belt strap | spare | | | only if a topic above is cut · docs/topics-october.md |
| sp-3 | shampoo-bottle-ridges | Ridges on the side of a shampoo bottle | spare | | | only if a topic above is cut · docs/topics-october.md |
| sp-4 | outlet-ground-pin-orientation | Outlet ground hole up or down | spare | | | only if a topic above is cut · docs/topics-october.md |
