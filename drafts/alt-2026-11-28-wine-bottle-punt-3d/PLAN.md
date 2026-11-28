# Beat plan: wine-bottle-punt-3d (cues = words of take 3, 73.36 s VO -> 74.74 s video, 2242 frames)
| Beat | Words (s, video time) | Hero (Blender) | Type | SFX |
|---|---|---|---|---|
| B1 hook | "The dent in the bottom of a wine bottle" 0.3 | still-wine bottle (label band, capsule, no text) tipped toward the camera, slowly spinning; gold ring flashes on the punt rim on "dent"; slow push-in | NOT A SIGN OF QUALITY (frame 0), THE DENT label | impact, clink |
| B2 stake | "But in a bottle of champagne" 5.1 | champagne bottle cut in half (mint glass section, pale wine, cork + foil + cage), bubbles rising; cyan pressure arrows appear on "sits" on the walls, the dome and the cork; push toward the base | IN CHAMPAGNE, counter UP TO ~90 PSI + note POUNDS PER SQUARE INCH | whoosh, creak, fizz, ticks + ping |
| B3 tire | "That's about three times your car tire" 11.1 | wide: champagne next to a small car tire with 6 short arrows (about 1/3) | ABOUT 3X YOUR CAR TIRE, CAR TIRE label | impact |
| B4 punt | "It's called a punt" 13.6 | close on the champagne base: dome + gold ring | IT'S CALLED A PUNT, PUNT label, A GLASSBLOWER'S FIX | impact, pop |
| B5 hand-blown | "Back when every bottle was blown by hand" 17.3 | glowing orange bottle on a blowpipe (grows from a bubble), furnace mouth glowing behind, sparks | BLOWN BY HAND | whoosh, furnace roar |
| B6 seam | "the bottom came out with a rough seam" 19.8 | close on the base: pointed bottom + rough nub, red ring | A ROUGH SEAM, SEAM label | deny, pop |
| B7 wobble (flaw first) | "Stand that on a table and it wobbles" 22.4 | cooled pointy bottle drops onto a wooden board, released on "wobbles" (rigid body): rocks and ends crooked on its point + rim; dust puff; cut close on the sharp point (red ring) | IT WOBBLES, SHARP POINT label | clink, glass wobble, deny |
| B8 push | "So the glassblower pushed that seam up" 26.9 | back to the hot bottle: a steel tool slides in, pushes the point up into the bottle (shape key point -> dome), nub rides into the dent, sparks; tool pulls back | PUSH THE SEAM UP | scrape, spark, impact |
| B9 level | "Now it stands level on a smooth ring" 30.5 | half-cut finished bottle drops onto the board, gold ring at the rest ring on "level", nub tucked at the top of the dent; low close; cyan arch line on "stronger" | STANDS LEVEL, SMOOTH RING label, SHARP BIT TUCKED INSIDE, MAYBE STRONGER, TOO | clink, ping, pop |
| B10 machine | "Today, machines do it" 37.3 | steel mold cut in half (bottle cavity, the punt bump in its floor), glowing gob hangs, drops in on "drops" (Mantaflow molten drop if baked), lands; on "air" cyan arrows down the neck and the hot glass inflates to fill the cavity (shape key); close on the base for "dent and all" | TODAY: MACHINES, counter ~2,000°F, GLOB OF GLASS label, INTO A MOLD, AIR BLOWS IT INTO SHAPE, DENT AND ALL + DENT label | clamp, glob thud, air hiss |
| B11 tradition | "Those bottles are tough" 45.9 | high wide over a cooling belt full of finished green bottles (GN scatter) | STILL WINE: MOSTLY TRADITION | clamp, clink |
| B12 sparkling | "Sparkling wine is different" 50.0 | champagne cutaway again, bubbles, arrows brighten on "pushes" | SPARKLING IS DIFFERENT, 2ND FERMENTATION, GAS PUSHES ON EVERY INCH | impact, fizz, creak |
| B13 spread | "The curved punt helps spread that push" 58.5 | close on the dome: arrows down onto the punt, cyan lines run along the dome to the ring, gold ring glows | SPREADS THE PUSH | ping |
| B14 sediment | "The sediment story?" 62.4 | deep-punt bottle cut open, dark specks in the trough around the punt (GN scatter), red ring | THE SEDIMENT STORY?, NEVER PROVEN | whoosh, deny |
| B15 deeper | "A deeper dent doesn't mean a better wine" 65.2 | shallow vs deep punt bottles side by side; on "more" the deep base's extra glass glows gold | DEEPER DENT, NOT BETTER WINE, SHALLOW + DEEP labels, MORE GLASS | clink, pop, ping |
| B16 CTA | "Have you ever checked the bottom of a bottle" 70.1 | hook bottle again, base toward us, gold ring glows on "bottom", slow pull-out, fade over the last 0.8 s | EVER CHECKED THE BOTTOM BEFORE BUYING? + TELL ME IN THE COMMENTS, NEXT: WHEN A BREAKER TRIPS (last 2 s) | clink, impact, ping |

Gates: hook moves at frame 0 (bottle spin + push-in, title slam), longest pause between words in the take 0.52 s (no dead air > 1.2 s),
counters only for spoken numbers (ninety -> ~90 PSI, two thousand degrees -> ~2,000°F; "three times" is a title). Every C.<cue>, EV.<event>
and label anchor in timeline.js exists in timeline.json (node check 28 Nov). Labels GLOB OF GLASS, CORK, CURVED PUNT are skipped
automatically (anchor outside the label band); the titles carry those beats.
fx power-ups: hdri (bundled "studio", light only, dark backdrop), glare (hot glass, gold rings, cyan arrows), particles x3 (sparks at the hot
glass x2, dust when the pointy bottle hits the board), rigid body (the pointy bottle rocking on the board, kinematic until "wobbles", baked),
Mantaflow (molten gob dropping into the mold, res 64, ~1.5 s, laptop `--bake-fluid`, hidden without the cache; the animated gob tells it
anyway), Geometry Nodes scatter x2 (finished bottles on the cooling belt, sediment specks), engine Cycles.
