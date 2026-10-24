# How a door lock works: beat plan (75 s, 1080x1920, EN, Eleven v4 Turbo "Liam")

Register for every beat: **concept** → hero is the 3D cross-section (Blender Cycles), never a screenshot.
Zones (px): type band y 150–430 · 3D hero y 430–1450 · captions y 1480–1700 (clear of platform UI).
Labels sit in the side margins of the hero zone with leader lines to anchors projected from Blender
(per-frame screen coordinates exported from the camera, so leaders track the real part).
Cues are words, resolved against assets/vo/audio_meta.json (chained "next occurrence after previous cue").

| beat | from cue | to cue | hero (Blender) | type (Tesseract) | SFX |
|---|---|---|---|---|---|
| B1 hook | How | Let's | painted front door, brass cylinder; key flies in from camera, stops at keyway on "door" | "HOW DOES YOUR KEY KNOW?" top band | air whoosh (key), metal tick on stop |
| B2 split | Let's | This | camera orbits front→side; front half of lock slides off on "half" (cutaway reveal) | — | riser → metal slice "shing" on "half" |
| B3 parts | This | Drilled | studio cutaway; shell glows on "shell", plug glows + twitches on "plug" | labels CYLINDER / SHELL / PLUG with leaders | soft pop per label |
| B4 chambers | Drilled | Each | 5 chambers light up left→right | counter 1→5 "CHAMBERS" | 5 ticks on the count |
| B5 stack | Each | The | push-in on stack 3 | SPRING / TOP PIN / BOTTOM PIN labels on "spring", "top", "bottom" | 3 pops |
| B6 springs | The (springs) | That | pins drop, springs extend; top pins cross the gap | — | spring boing + metal clicks |
| B7 shear | That | While | glowing shear line wipes along plug/shell boundary | "SHEAR LINE" label on "shear" | clear ping on "shear" |
| B8 jam | While | Now (slide) | crossing top pins flash red; plug tries to turn, blocked | slam "NOTHING TURNS" on "Nothing" | metal clunk + rattle |
| B9 key in | Now | Watch | key slides in; each pin rides its cut (computed from key profile) | "EACH CUT = ONE HEIGHT" type band | key scrape + ratchet click per pin |
| B10 align | Watch | Now (plug) | push-in on gaps; every split lands on the shear line | "ALL 5" + counter ticks on "All five" | 5 ticks + ping on "same" |
| B11 turn | Now | Turn | plug + key rotate; cam pulls bolt (bolt slides) | "OPEN" on "opens" | rotation click, bolt clunk |
| B12 relock | Turn | Try | turn back, key out, springs snap pins down | "LOCKED" small on "locked" | snap clicks |
| B13 wrong key | Try | The (idea) | wrong key in; stack 3 too high, crosses line → red; jam | "WRONG KEY" then "STILL LOCKED" | scrape, buzz-thud denial |
| B14 history | The (idea) | In | lock turns to wood | "4,000 YEARS" counter + "ANCIENT EGYPT" | wood knock, whoosh |
| B15 Yale | In | So | lock shrinks to pocket size, camera pulls back | "1800s · YALE" | downlifter whoosh |
| B16 recap | So | Follow | wide cutaway, right key in, aligned line glowing | slams "5 PINS" / "1 LINE" / "1 KEY" on each word | three hits |
| B17 CTA | Follow | end | slow orbit | "FOLLOW · Hidden In Your Home" | soft impact + ping |

Gates: no dead air > 1.2 s (every beat has a moving hero), exits start ~0.42 s before the next cue,
every counter is a number the narration speaks (5, 4,000, 1800s), captions never overlap labels.
