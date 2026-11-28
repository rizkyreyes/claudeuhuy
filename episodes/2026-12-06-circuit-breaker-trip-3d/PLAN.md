# Beat plan: circuit-breaker-trip-3d (cues = words of take 2, 75.20 s VO -> 76.58 s video, 2297 frames)
| Beat | Words (s, video time) | Hero (Blender) | Type | SFX |
|---|---|---|---|---|
| B1 hook | "A circuit breaker isn't there to protect your TV" 0.3 | living room: TV on a console, slow push-in, screen blinks on "TV" | NOT HERE TO PROTECT YOUR TV (frame 0) | impact, power-down |
| B2 claim | "It's there to keep the wires" 3.2 | cut: wall cut open, studs, the cable glows gold, then red-hot, flames + smoke at one spot | IT PROTECTS THE WIRES, FROM CATCHING FIRE | impact, deny, fire |
| B3 stake | "In the US, wiring, cords and lights" 6.9 | pull-out on the burning wall | US HOMES, WIRING CORDS + LIGHTS, ~32,000 FIRES A YEAR counter + NFPA note | pop, ticks, ping |
| B4 two troubles | "Every breaker watches" 12.7 | the panel, door open, target breaker glows | TWO KINDS OF TROUBLE, BREAKER label | whoosh, pop |
| B5 inside | "Inside, the current runs" 15.7 | cut: breaker cut in half (studio), cyan current beads stab -> contacts -> arm -> coil -> bimetal -> lug; bimetal layers glow on "strip"/"two" | CURRENT label, A STRIP OF TWO METALS, BIMETAL STRIP label | hum, pop |
| B6 overload | "Plug a space heater and a hair dryer" 19.7 | house wide: heater grill glows, dryer on, fast beads + warm cable in the wall | OVERLOAD, heater/dryer labels, ONE CIRCUIT, CURRENT CLIMBS | impact, fan, dryer, riser |
| B7 heats + bends | "The strip heats up" 24.1 | bimetal close-up: glows orange, bends toward the latch | IT HEATS UP, EXPAND AT DIFFERENT SPEEDS, IT BENDS | pop, impact |
| B8 trip | "Once it bends far enough" 30.5 | mechanism: strip pushes the latch, latch slides from under the arm tail, spring snaps the arm open, sparks, handle to the middle, beads stop | LATCH / SPRING / CONTACTS labels, SNAP!, POWER CUT | thermo click, snap, spark, deny |
| B9 power cut | "the power is cut" 35.5 | house: heater grill goes dark | POWER CUT | power-down |
| B10 short | "The second kind of trouble is a short circuit" 37.1 | cavity: a nail goes into the cable, hot touches neutral, white flash + sparks | SHORT CIRCUIT, HOT TOUCHES NEUTRAL OR GROUND | nail, bang, spark |
| B11 amps | "Thousands of amps can rush in" 42.1 | cutaway: dense white-hot beads | THOUSANDS OF AMPS | impact |
| B12 magnet | "That turns a little coil into a magnet" 44.1 | coil glows cyan, field rings pulse, plunger yanked into the coil, latch kicks, arm opens (slow) | COIL = MAGNET, COIL / PLUNGER labels, INSTANTLY | ping, clunk, snap |
| B13 arc | "Pulling the contacts apart makes an arc" 49.7 | blue-white arc between the parting contacts (light flickers) | AN ARC | zap |
| B14 chute | "It's pushed into a stack of metal plates" 52.0 | arc slides into the arc chute, splits into 7 small arcs between the plates, fades, gas puff from the vents | ARC CHUTE label, SPLIT IT, KILL IT | zap, pop, deny |
| B15 handle | "On most breakers, the handle stops in the middle" 56.0 | exterior (front half on), handle glows in the middle, pushed OFF, then ON | TRIPPED = MIDDLE, HANDLE label, OFF, THEN ON | pop, reset click, snap |
| B16 trip-free | "And you can't cheat" 60.9 | cutaway: gold block holds the handle ON, the strip bends, latch releases, contacts open anyway | HOLD IT ON?, STILL TRIPS, BUILT TRIP-FREE note | press, snap, deny |
| B17 mistake | "If one keeps tripping" 64.8 | panel: target breaker trips again and again, pulled out, falls to the floor (rigid body), a bigger red breaker slides in | KEEPS TRIPPING?, NEVER A BIGGER BREAKER | snaps, whoosh, drop, deny |
| B18 cook | "The wire stays the same" 68.5 | cavity: the same cable glows red, scorched band, smoke, melted insulation drips (Mantaflow if baked) | SAME WIRE, IT CAN COOK + "find the cause" note | sizzle, deny |
| B19 CTA | "Which breaker in your panel trips the most?" 72.2 | the panel, slow pull-out, panel trim glows gold, fade over the last 0.8 s | the question + TELL ME IN THE COMMENTS, YOUR PANEL label, NEXT: THE TEETH ON A BOTTLE CAP (last 2 s) | impact, ping |

Gates: hook moves at frame 0 (camera push, title slam), longest pause between words 0.32 s (no dead air > 1.2 s), the only counter (~32,000)
is spoken ("thirty-two thousand"). Every C.<cue>, EV.<event> and label anchor in timeline.js exists in timeline.json (node check 28 Nov).
fx power-ups: hdri (bundled "interior", background off), glare, particles x5 (fire smoke, short-circuit sparks, contact sparks, vent gas puff,
cook smoke), rigid body (the old breaker falls out of the panel, kinematic until "swap", baked), Mantaflow (melted insulation dripping off the
cooking cable, res 48, ~2.5 s, laptop `--bake-fluid`, hidden without the cache; the red glow + smoke tell it anyway), Geometry Nodes scatter x2
(rug tufts, studio grit), engine Cycles.
