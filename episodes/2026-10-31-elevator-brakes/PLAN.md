# Why elevators don't fall: beat plan (76.6 s, 1080x1920, EN, Eleven v4 Turbo "Liam")

Take 1: 75.44 s VO, 238 words, + 0.30 s lead-in + 0.83 s tail = **76.57 s** (2,297 frames @ 30 fps). Inside the 70-78 s window, so no re-take.
Register: **studio cutaway** of a traction-elevator shaft (dark studio, front wall of the shaft removed at y = -1.3): car on two guide rails,
3 hoist ropes over the traction sheave to a counterweight, machine on top (sheave, motor, drum brake with springs + electromagnet),
overspeed governor with its own rope loop to a tension pulley in the pit, safety lever + wedges on the car, spring + oil buffers in the pit.
Set B (x = 2000) is an 1854-style hoisting platform between two toothed wooden posts with a wagon spring. No people anywhere (the platform
rides empty, Otis is only a name on screen). After the ropes snap the explainer runs in slow motion (car 0.25 -> 0.7 -> 0.06 m/s).
Zones (px): type band y 200-500 · 3D hero y 430-1300 · captions y 1320-1470 (safe area x 60-950).
Cues are words, resolved against assets/vo/audio_meta.json (chained "next occurrence after previous cue"); times include the 0.30 s lead-in.

| beat | from cue | to cue | hero (Blender) | type (Tesseract) | SFX |
|---|---|---|---|---|---|
| B1 hook | What 0.30 | car 4.94 | push-in on the closed concrete shaft with landing doors; on "open" the front wall drops out of frame, car mid-shaft | "WHAT STOPS AN ELEVATOR FALLING?" rise | whoosh, riser, slab drop |
| B2 ropes | car 4.94 | heavy 10.86 | close on the crosshead: 3 ropes glow gold on "three" | label CAR · "AT LEAST 3 STEEL ROPES" · "MANY TIMES STRONGER" | impact, rope strain |
| B3 counterweight | heavy 10.86 | Up 14.94 | wide: brake releases, car rises 12 -> 16 m while the counterweight drops; counterweight + motor glow | label COUNTERWEIGHT · "MOTOR LIFTS THE DIFFERENCE" | magnet release, motor hum, clamp |
| B4 brake | Up 14.94 | But 25.66 | machine room: drum brake; springs glow on "springs" (shut), magnet glows cyan and the arms open on "pulls", sheave turns; on "out" the room dims, magnet off, shoes slam shut | "A BRAKE THAT WORKS BACKWARDS" · label SPRINGS · "SPRINGS: SHUT" · "POWER: OPEN" · label ELECTROMAGNET · "POWER OUT" (red) · "BRAKE CLAMPS ON" · label BRAKE SHOE | impact, clamp, release, motor, power-down, clamp |
| B5 snap | But 25.66 | Here's 28.14 | hard cut to the crosshead: ropes glow red, break on "snapped" (stubs on the car, loose ends on the sheave), car drops | "EVERY ROPE SNAPPED?" (red) | riser, rope snap + deny, counterweight landing |
| B6 governor | Here's 28.14 | The 40.46 | hard cut wide: governor loop glows cyan (car -> governor -> pit pulley), car sinking in slow motion; close on the governor face: spokes + flyweights spin, faster on "spin", weights slide out on "fly", pawl drops on "catch", wheel stops on "lock" | "THE CLEVER PART" · label GOVERNOR ROPE · "GOVERNOR" · label SPINNING WEIGHTS · "TOO FAST?" (red) · "WEIGHTS FLY OUT" · "LOCKED" (red) | whoosh, whirr x2, pawl clack, lock + deny |
| B7 safeties | The 40.46 | Still 55.26 | hard cut to the car's left bottom corner tracking the car: lever swings up on "yanks", wedges rise into the rail blade on "jams" (glow), sparks; pull back to both sides; car grinds to a stop | "ROPE STOPS. CAR DOESN'T." · labels GOVERNOR ROPE, SAFETY LEVER, WEDGE, GUIDE RAIL · "STEEL WEDGES" · "BOTH SIDES" · "ITS OWN WEIGHT DRIVES THEM IN" · "NO ROPE NEEDED" (cyan) | lever yank, wedge bite, rail grind, impact |
| B8 buffers | Still 55.26 | This 61.58 | hard cut to the pit: counterweight resting on the oil buffer, car comes down onto the coil spring on "catch" (spring compresses) | "STILL NOT ENOUGH?" (red) · "BUFFERS" · labels SPRING, OIL PISTON | riser, impact, pops, buffer spring, oil hiss |
| B9 history | This 61.58 | Do 71.94 | hard cut to Set B: the platform rises between the toothed posts; on "cut" the rope parts, the wagon spring flattens into the teeth, platform drops 14 cm and holds | "1854" · "NEW YORK" · "ELISHA OTIS" · label RATCHET TEETH · "CUT THE ROPE!" (red) · label WAGON SPRING · "IT HELD" (gold) | whoosh, impact, tick, wood creak, rope cut + ratchet catch |
| B10 CTA | Do 71.94 | end 76.57 | hard cut to the intact shaft, car riding up slowly, slow pull back; render push-in 100 -> 106 % | "ELEVATOR OR STAIRS?" (Poppins ExtraBold, white) · "TELL ME IN THE COMMENTS" (Poppins, gold) | whoosh, ping, motor |

Gates: hook moves in the first second (camera push + title at 0.30 s); longest VO gap 0.40 s and something moves in every beat (wall drop,
car, sheave, governor, sparks, spring, platform), so no dead air > 1.2 s; no counters (spoken numbers "three" and "1854" are static titles).
51 of 90 caption groups dropped as title duplicates (playbook rule). Labels end automatically when their 3D anchor leaves the frame.
CTA is a question, no channel name, no "follow". No people in the scene.
