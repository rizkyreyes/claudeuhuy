# Beat plan: sump-pump-3d (cues = words of take 1, 75.92 s VO -> 77.30 s video, 2319 frames)
| Beat | Words (s, video time) | Hero (Blender) | Type | SFX |
|---|---|---|---|---|
| B1 hook | "Many basements have a hole" 0.3 | close on the pit in the basement floor (gold ring), pump running, beads up the pipe, slow pull-back | A HOLE ON PURPOSE (frame 0), SUMP PIT label | impact, motor, hum |
| B2 catch | "catch the water" 3.9 | wide section: blue groundwater in the soil around the basement | CATCHES THE GROUNDWATER | whoosh |
| B3 stake | "If the pump inside it stops during a storm" 6.2 | night exterior, rain, lightning, windows + basement lamp go dark; cut inside: pit overflows, water spreads over the floor (Mantaflow overflow if baked + rising flood slab) | PUMP STOPS IN A STORM..., BASEMENT FLOODS, USUALLY NOT COVERED + note | thunder, power-down, gurgle, rush, deny |
| B4 rain | "After heavy rain or snowmelt" 12.9 | right side section: rain, groundwater rises in the soil | HEAVY RAIN OR SNOWMELT, THE SOIL FILLS UP, GROUNDWATER label | rain, whoosh |
| B5 pressure | "That water presses" 17.5 | full section: cyan arrows push on both walls and up under the slab; left wall: red crack flash | PRESSES ON WALLS + FLOOR, EVERY CRACK, CRACK label | impact, deny |
| B6 drain tile | "So builders lay a pipe full of holes" 21.7 | x-ray: front soil slice hidden, black perforated drain tile along the footing (gold glow, holes), footing | A PIPE FULL OF HOLES, DRAIN TILE label, AROUND THE FOOTING | impact, pop |
| B7 to the pit | "Water seeps in" 26.5 | beads seep from the soil into the tile, run through the footing pipe into the pit, liner glows gold | SEEPS IN, THE LOWEST SPOT, THE SUMP PIT | drips, whoosh, impact |
| B8 float | "As the pit fills" 31.4 | pit close: water rises, orange float rides the rod, hits the top stop, switch LED green | THE FLOAT RIDES UP, FLOAT + SWITCH labels, FLIPS THE SWITCH, PUMP ON | click, impact, motor |
| B9 impeller | "An impeller spins fast" 37.8 | macro on the half-cut pump: impeller blades spinning; then up the pipe, out through the rim, onto the lawn far from the wall | SPINS FAST, UP THE PIPE, OUT OF THE HOUSE, AWAY FROM THE WALLS | motor, rush, yard |
| B10 off | "When the level drops" 43.2 | pit: level drops, float falls, LED off, flap shuts | LEVEL DROPS, PUMP OFF | down, thunk |
| B11 full pipe | "But that pipe is still full" 46.7 | vertical pipe, cyan column standing in it | STILL FULL OF WATER | pop |
| B12 check valve | "Without a one-way flap" 49.0 | valve close: clear body + gold flap; on "all" the valve is crossed out red: column falls back (red beads), pit refills, pump restarts twice | A ONE-WAY FLAP, CHECK VALVE label, NO VALVE?, IT ALL FALLS BACK, THE SAME WATER AGAIN + AGAIN | impact, ping, deny, rush, click, gurgle |
| B13 wear | "wearing itself out" 56.3 | motor close: copper windings glow red, sparks | WEARS ITSELF OUT, MOTOR label | spark, deny |
| B14 power | "And the worst part" 57.7 | storm exterior: lightning, branch breaks off the tree onto the service line (rigid body), sparks, all lights out, pit rising | THE WORST PART, POWER OUT | riser, thunder, branch, spark, power-down |
| B15 backup | "That's why many homes add a battery backup pump" 62.1 | basement in the dark: battery box glows green, backup pump on the bracket runs, green beads up its line into the main pipe | BATTERY BACKUP PUMP, BATTERY + BACKUP PUMP labels | impact, click, motor |
| B16 stuck | "Floats can get stuck" 64.9 | pit close: float tilts and jams on the liner wall (red ring), water rises past it | STUCK FLOAT | deny |
| B17 frozen | "in winter the pipe outside" 67.1 | outdoor pipe end on the lawn: white-blue ice plug grows, red beads blocked behind it | FROZEN PIPE, ICE label | ice, impact |
| B18 lifespan | "Most pumps only last about seven to ten years" 70.2 | pump close: body rusts (noise mask) | 7-10 YEARS + note | impact |
| B19 CTA | "Is there a pump pit in your basement?" 73.2 | section pull-out over the whole basement, gold ring around the pit, fade over the last 0.8 s | IS THERE A PUMP PIT IN YOUR BASEMENT? + TELL ME IN THE COMMENTS, NEXT: THE DENT IN A WINE BOTTLE (last 2 s) | impact, ping |

Gates: hook moves at frame 0 (pump running, beads, camera pull-back, title slam), longest pause between words in the take 0.28 s (no dead air
> 1.2 s), the only number on screen (7-10 YEARS) is spoken. Every C.<cue>, EV.<event> and label anchor in timeline.js exists in
timeline.json (node check 27 Nov).
fx power-ups: hdri (bundled "night", background on: storm night), glare, particles x4 (rain in the stake, rain in the storm, sparks at the
service line, sparks at the worn motor), rigid body (the branch falling onto the line, kinematic until "knock", baked), Mantaflow (pit
overflow onto the basement floor, res 64, ~3.3 s, laptop `--bake-fluid`, hidden without the cache; the rising flood slab tells it anyway),
Geometry Nodes scatter x6 (gravel stones on the gravel section faces x3, grass tufts x3), engine Cycles.
