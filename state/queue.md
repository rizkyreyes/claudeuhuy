# Production queue

Channels (from 29 Sep 2026): **YouTube, TikTok, Instagram** (Instagram re-connected with a new id; Facebook was used 28–29 Sep and dropped).

Status values: `todo` → `rendered` (MP4 in `media/`, waiting for Buffer) → `scheduled` (posts created in Buffer) → `posted`.
`duration` = exact final MP4 length in seconds (used to match Buffer drafts to videos).
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
| o-01 | sink-overflow | Overflow hole in a bathroom sink | scheduled | 73.13 | Thu 1 Oct 2026 12 PM | produced by the 28 Sep run; scheduled 28 Sep on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep) from main/media |
| o-02 | toothpaste-square | Colored square on a toothpaste tube | posted | 60.44 | Wed 30 Sep 2026 12 PM | produced 29 Sep, scheduled on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep); took the empty Wed noon slot |
| o-03 | window-weep-holes | Weep holes in a window frame | scheduled | 75.11 | Thu 1 Oct 2026 7 PM | produced 29 Sep, scheduled on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep) |
| o-04 | microwave-door-mesh | Metal mesh dots in the microwave door | scheduled | 69.73 | Fri 2 Oct 2026 12 PM | produced 29 Sep, scheduled on YouTube, TikTok, Facebook (FB post removed with the channel; Instagram Reel added by hand 29 Sep) |
| o-05 | pizza-saver-table | Little plastic "table" in a pizza box | scheduled | 76.77 | Fri 2 Oct 2026 7 PM | produced 30 Sep, scheduled on YouTube, TikTok, Instagram from main/media; took the empty Fri 7 PM slot (planned Sat 3 PM) |
| o-06 | care-label-dots | Dots inside laundry care symbols | scheduled | 78.85 | Sat 3 Oct 2026 3 PM | produced 30 Sep, scheduled on all 3 channels; small brand name visible on washer panel ~1.5 s |
| o-07 | jeans-rivets | Copper rivets on jeans pockets | scheduled | 75.40 | Sat 3 Oct 2026 7 PM | produced 30 Sep, scheduled on all 3 channels (planned Sun 12 PM) |
| o-08 | trash-can-vents | Vent holes near the top of a trash can | todo | | Sun 4 Oct 2026 6 PM | cleaning · convenience · docs/topics-october.md |
| o-09 | pillow-law-tag | "Do not remove under penalty of law" pillow tag | todo | | Mon 5 Oct 2026 12 PM | bedroom · myth-bust · docs/topics-october.md |
| o-10 | heinz-57-tap-spot | Embossed "57" on a glass Heinz bottle | todo | | Mon 5 Oct 2026 7 PM | packaging · hack · docs/topics-october.md |
| o-11 | pot-lid-hole | Small hole in a pot or slow-cooker lid | todo | | Tue 6 Oct 2026 12 PM | kitchen · myth-bust · docs/topics-october.md |
| o-12 | iron-button-groove | Notch at the tip of an iron's soleplate | todo | | Tue 6 Oct 2026 7 PM | laundry · hack · docs/topics-october.md |
| o-13 | hair-dryer-plug-block | Chunky block on a hair dryer plug | todo | | Wed 7 Oct 2026 12 PM | bathroom · safety · docs/topics-october.md |
| o-14 | zipper-lock-tab | Fold-down tab on a jeans zipper | todo | | Wed 7 Oct 2026 7 PM | clothing · hack · docs/topics-october.md |
| o-15 | mattress-handles | Handles on the side of a mattress | todo | | Thu 8 Oct 2026 12 PM | bedroom · myth-bust · docs/topics-october.md |
| o-16 | vacuum-suction-valve | Sliding vent on a vacuum hose handle | todo | | Thu 8 Oct 2026 7 PM | cleaning · hack · docs/topics-october.md |
| o-17 | toothbrush-indicator-bristles | Blue bristles on a toothbrush | todo | | Fri 9 Oct 2026 12 PM | bathroom · convenience · docs/topics-october.md |
| o-18 | rice-cooker-cup | The measuring cup that comes with a rice cooker | todo | | Fri 9 Oct 2026 7 PM | kitchen · hack · docs/topics-october.md |
| o-19 | smoke-alarm-date | Date on the back of a smoke alarm | todo | | Sat 10 Oct 2026 3 PM | bedroom · safety · docs/topics-october.md |
| o-20 | egg-carton-pack-date | Three-digit number on an egg carton | todo | | Sat 10 Oct 2026 7 PM | packaging · hack · docs/topics-october.md |
| o-21 | knife-hollow-edge-dimples | Oval dimples along a santoku blade | todo | | Sun 11 Oct 2026 12 PM | kitchen · convenience · docs/topics-october.md |
| o-22 | he-detergent-logo | "HE" logo on laundry detergent | todo | | Sun 11 Oct 2026 6 PM | laundry · hack · docs/topics-october.md |
| o-23 | bottle-cap-teeth | Crimped teeth on a metal bottle cap | todo | | Mon 12 Oct 2026 12 PM | packaging · history · docs/topics-october.md |
| o-24 | running-shoe-extra-eyelet | Extra eyelet at the top of running shoes | todo | | Mon 12 Oct 2026 7 PM | clothing · hack · docs/topics-october.md |
| o-25 | spaghetti-spoon-hole | Hole in the middle of a spaghetti spoon | todo | | Tue 13 Oct 2026 12 PM | kitchen · myth-bust · docs/topics-october.md |
| o-26 | dustpan-comb-teeth | Row of teeth on a dustpan edge | todo | | Tue 13 Oct 2026 7 PM | cleaning · hack · docs/topics-october.md |
| o-27 | wine-bottle-punt | Dent in the bottom of a wine bottle | todo | | Wed 14 Oct 2026 12 PM | packaging · myth-bust · docs/topics-october.md |
| o-28 | washer-debris-filter-door | Small door at the bottom of a front-load washer | todo | | Wed 14 Oct 2026 7 PM | laundry · hack · docs/topics-october.md |
| o-29 | brogue-shoe-holes | Holes on wingtip shoes | todo | | Thu 15 Oct 2026 12 PM | clothing · history · docs/topics-october.md |
| o-30 | plunger-flange | Extra rubber flap under a plunger cup | todo | | Thu 15 Oct 2026 7 PM | bathroom · hack · docs/topics-october.md |
| o-31 | child-resistant-cap-test | Push-and-turn cap on cleaning products | todo | | Fri 16 Oct 2026 12 PM | cleaning · safety · docs/topics-october.md |
| o-32 | crisper-drawer-slider | Humidity slider on a crisper drawer | todo | | Fri 16 Oct 2026 7 PM | kitchen · hack · docs/topics-october.md |
| o-33 | plastic-resin-code | Number inside the recycling arrows | todo | | Sat 17 Oct 2026 3 PM | packaging · myth-bust · docs/topics-october.md |
| o-34 | tape-measure-black-diamonds | Black diamonds on a tape measure | todo | | Sat 17 Oct 2026 7 PM | garage · hack · docs/topics-october.md |
| o-35 | party-cup-lines | Lines on a red party cup | todo | | Sun 18 Oct 2026 12 PM | kitchen · myth-bust · docs/topics-october.md |
| o-36 | sticky-notes-yellow | Yellow sticky notes | todo | | Sun 18 Oct 2026 6 PM | office · history · docs/topics-october.md |
| o-37 | sd-card-lock-switch | Lock switch on an SD card | todo | | Mon 19 Oct 2026 12 PM | tech · myth-bust · docs/topics-october.md |
| o-38 | fire-hydrant-cap-colors | Colored cap on a fire hydrant | todo | | Mon 19 Oct 2026 7 PM | yard · safety · docs/topics-october.md |
| o-39 | headrest-window-myth | Removable car headrest | todo | | Tue 20 Oct 2026 12 PM | car · myth-bust · docs/topics-october.md |
| o-40 | tamper-resistant-outlets | Hidden shutters in newer outlets | todo | | Tue 20 Oct 2026 7 PM | living-room · safety · docs/topics-october.md |
| o-41 | do-not-duplicate-key | "Do Not Duplicate" on a key | todo | | Wed 21 Oct 2026 12 PM | carry · myth-bust · docs/topics-october.md |
| o-42 | stapler-anvil-pinning | Rotating plate under a stapler | todo | | Wed 21 Oct 2026 7 PM | office · hack · docs/topics-october.md |
| o-43 | phillips-cam-out-myth | Phillips screws that strip | todo | | Thu 22 Oct 2026 12 PM | garage · myth-bust · docs/topics-october.md |
| o-44 | plug-prong-holes | Holes in plug prongs | todo | | Thu 22 Oct 2026 7 PM | tech · manufacturing · docs/topics-october.md |
| o-45 | fuel-gauge-arrow | Arrow next to the fuel gauge | todo | | Fri 23 Oct 2026 12 PM | car · hack · docs/topics-october.md |
| o-46 | utility-marking-flags | Colored flags in your yard | todo | | Fri 23 Oct 2026 7 PM | yard · safety · docs/topics-october.md |
| o-47 | privacy-knob-hole | Tiny hole in a bathroom doorknob | todo | | Sat 24 Oct 2026 3 PM | living-room · hack · docs/topics-october.md |
| o-48 | backpack-lash-tab | Diamond patch on a backpack | todo | | Sat 24 Oct 2026 7 PM | carry · history · docs/topics-october.md |
| o-49 | windshield-frit-dots | Black dots around the windshield | todo | | Sun 25 Oct 2026 12 PM | car · manufacturing · docs/topics-october.md |
| o-50 | snap-off-blade | Snap-off lines on a box cutter blade | todo | | Sun 25 Oct 2026 6 PM | garage · history · docs/topics-october.md |
| o-51 | mailbox-flag-color | Flag on a curbside mailbox | todo | | Mon 26 Oct 2026 12 PM | yard · myth-bust · docs/topics-october.md |
| o-52 | yellow-pencils | Yellow pencils | todo | | Mon 26 Oct 2026 7 PM | office · history · docs/topics-october.md |
| o-53 | two-by-four-size | A 2x4 isn't 2 by 4 | todo | | Tue 27 Oct 2026 12 PM | garage · manufacturing · docs/topics-october.md |
| o-54 | keypad-number-order | Phone keypad vs calculator order | todo | | Tue 27 Oct 2026 7 PM | tech · history · docs/topics-october.md |
| o-55 | hexagonal-pencils | Six-sided pencils | todo | | Wed 28 Oct 2026 12 PM | office · manufacturing · docs/topics-october.md |
| o-56 | coin-reeded-edges | Ridges on dimes and quarters | todo | | Wed 28 Oct 2026 7 PM | carry · history · docs/topics-october.md |
| o-57 | ferrite-bead-cable | Lump on a laptop charger cord | todo | | Thu 29 Oct 2026 12 PM | tech · safety · docs/topics-october.md |
| o-58 | ceiling-fan-switch | Switch on a ceiling fan | todo | | Thu 29 Oct 2026 7 PM | living-room · hack · docs/topics-october.md |
| o-59 | passenger-mirror-warning | "Objects in mirror are closer than they appear" | todo | | Fri 30 Oct 2026 12 PM | car · safety · docs/topics-october.md |
| o-60 | glasses-frame-numbers | Tiny numbers inside your glasses arm | todo | | Fri 30 Oct 2026 7 PM | carry · hack · docs/topics-october.md |
| o-61 | curb-ramp-bumps | Bumpy pad at the curb ramp | todo | | Sat 31 Oct 2026 3 PM | yard · safety · docs/topics-october.md |
| o-62 | iphone-camera-mic-hole | Tiny hole next to the phone camera | todo | | Sat 31 Oct 2026 7 PM | tech · convenience · docs/topics-october.md |
| sp-1 | ykk-zipper | "YKK" on zipper pulls | spare | | | only if a topic above is cut · docs/topics-october.md |
| sp-2 | seat-belt-button | Button on a seat belt strap | spare | | | only if a topic above is cut · docs/topics-october.md |
| sp-3 | shampoo-bottle-ridges | Ridges on the side of a shampoo bottle | spare | | | only if a topic above is cut · docs/topics-october.md |
| sp-4 | outlet-ground-pin-orientation | Outlet ground hole up or down | spare | | | only if a topic above is cut · docs/topics-october.md |
