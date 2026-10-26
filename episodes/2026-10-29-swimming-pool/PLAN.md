# How a swimming pool is built: beat plan (73.8 s, 1080x1920, EN, Eleven v4 Turbo "Liam")

Take 2: 72.64 s VO, 231 words, + 0.30 s lead-in + 0.75 s tail = **73.77 s** (2,213 frames @ 30 fps). Take 1 (243 words) ran 76.5 s, so 12 words were cut.
Register: **construction cutaway** in a daylight yard (Poly Haven grass/soil/concrete/tile textures + sky HDRI). Set A is a backyard cut at y = 0
through the pool's long axis (shallow end with steps on the left, deep end right, equipment pad far right). Set C (x = -1000) is a dark studio
with a concrete beam. Set B (x = 2000) is a generic early-1900s museum facade with a two-chamber cement gun on a cart. Sizes are illustrative,
none are spoken. No people anywhere (excavator cab and spray nozzle have no operator; Akeley appears only as a name on screen).
Zones (px): type band y 200–500 · 3D hero y 430–1300 · captions y 1320–1470 (safe area x 60–950).
Cues are words, resolved against assets/vo/audio_meta.json (chained "next occurrence after previous cue"); times include the 0.30 s lead-in.

| beat | from cue | to cue | hero (Blender) | type (Tesseract) | SFX |
|---|---|---|---|---|---|
| B1 hook | How 0.30 | First 4.86 | high 3/4 push-in on a finished backyard pool; on "open" the front half (mirrored copy) drops out of frame, showing the section | "HOW IS A POOL ACTUALLY BUILT?" rise | whoosh, riser, slab drop |
| B2 dig | First 4.86 | Next 8.30 | hard cut to the empty lawn: excavator arm cycles, dirt chunks fly, the hole sinks layer by layer; cyan ghost outline of the shell inside the bigger hole on "bigger" | "DIG THE HOLE" · label EXCAVATOR · "A LITTLE BIGGER" (cyan) | excavator ×2, impact, ping |
| B3 steel | Next 8.30 | Concrete 13.66 | rebar bars appear: floor first, then walls (back-wall grid), then steps; bars glow gold | "STEEL CAGE" · labels FLOOR, WALLS, STEPS | clanks + tie ticks |
| B4 beam | Concrete 13.66 | Then 19.26 | hard cut to the studio beam: gold arrows squeeze (fine), red arrows pull → it cracks in two (red glow); then a beam with a gold bar inside holds | "CONCRETE" · "SQUEEZED: FINE" · "PULLED: CRACKS" (red) · "STEEL TAKES THE PULL" · label STEEL BAR | creak, crack + deny, clank |
| B5 plumbing | Then 19.26 | Now 24.70 | back in the yard: main drain + sump, skimmer box at the waterline, return jets, pipes in the cut plane to the pump + filter pad | "PLUMBING" · labels MAIN DRAIN, SKIMMER, RETURN JETS | impact, pvc clicks |
| B6 shotcrete | Now 24.70 | Then 34.30 | a nozzle on a hose (no person) sweeps left to right, grey spray bits fly onto the steel, the shell grows behind it (boolean sweep); rough → smooth on "smooths" | "NOW THE FUN PART" · label CONCRETE HOSE · "GUNITE" + DRY MIX · "SHOTCRETE" + WET MIX · "SMOOTHED BY HAND" | riser, spray loop ×2, impacts, trowel |
| B7 cure | Then 34.30 | Tile 36.54 | mist puffs drift over the bare shell | "KEPT WET WHILE IT CURES" (cyan) | ping, mist |
| B8 finishes | Tile 36.54 | Fill 44.62 | blue waterline tile, coping stones + deck, white plaster skin; on "bare" the plaster goes, the shell glows red and cyan drops seep out into the soil | labels WATERLINE TILE, COPING · "PLASTER SEALS IT" · "BARE CONCRETE SEEPS" (red) · label WATER SEEPS OUT | tile taps, stone set, impact, deny |
| B9 loop | Fill 44.62 | Here's 52.62 | water rises (boolean level); gold pulses drain + skimmer → pump → filter, cyan pulses back to the jets, jet streams in the water | "FILL IT UP" · "THE LOOP" · labels PUMP, FILTER · "BACK OUT THE JETS" | water fill, pump hum |
| B10 float | Here's 52.62 | That's 58.14 | water drains, the soil turns blue as groundwater rises, cyan arrows push up, the empty pool lifts 1.7 m and tilts (red glow) | "HERE'S THE SCARY PART" (red) · "DRAIN IT EMPTY" · "HIGH GROUNDWATER" (cyan) · "IT FLOATS UP!" (red) | riser, downlifter, impact, deny, pool lift |
| B11 valve | That's 58.14 | And 61.50 | hard cut: the pool is back down; close on the relief valve under the main drain (gold), cyan groundwater flows in through it | label RELIEF VALVE · "LETS GROUNDWATER IN" (cyan) | ping, glug |
| B12 history | And 61.50 | Would 68.86 | hard cut to the museum: the cement gun on its cart, nozzle sprays, fresh plaster climbs the dark old facade | "THE CONCRETE GUN" · label CEMENT GUN · "A TAXIDERMIST" · "CARL AKELEY" · "100+ YEARS AGO" · "A CHICAGO MUSEUM" · label FRESH PLASTER | whoosh, gun loop ×2, impacts, tick |
| B13 CTA | Would 68.86 | end 73.77 | hard cut to the finished pool, loop pulses running, slow pull back; render push-in 100→106 % | "CONCRETE POOL OR ABOVE-GROUND?" (Poppins ExtraBold, white) · "TELL ME IN THE COMMENTS" (Poppins, gold) | whoosh, ping |

Gates: hook moves in the first second (camera push + title at 0.30 s); longest VO gap 0.48 s and something moves in every beat (excavator,
spray, mist, pulses, drops), so no dead air > 1.2 s; no counters (the only spoken number is "a hundred", shown as a static "100+ YEARS AGO").
58 of 91 caption groups dropped as title duplicates (playbook rule). Labels end automatically when their 3D anchor leaves the frame.
CTA is a question, no channel name, no "follow". No people in the scene.
