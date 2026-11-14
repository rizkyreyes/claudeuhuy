# Beat plan: airport-runway (3d-27), VO 76.16 s -> video 77.39 s (2322 frames @ 30 fps)

Cues are words of the take (timeline.json `cues`, VO offset 0.30 s). Hero = the runway cut open at y = 0 (real layer thicknesses) and three side sets in a dark studio.
Gates: the plane moves from frame 1 (landing toward camera), longest VO gap 0.24 s, every counter is a spoken number (300,000 LB, 200+ PSI). fx.py: hdri (sunset, light only, own sky gradient), glare (edge lights, dowels, arrows), particles (tire smoke, roller dust, drop dust, rain, saw slurry, hydro spray, truck spray), rigid body (cracked slab falls in), Mantaflow (hydro shot, 66.6-68.9 s, res 64, bake on laptop with --bake-fluid), GN scatter (subbase stones), Cycles.

| # | t (s) | cue words | job | hero / camera | type | SFX |
|---|---|---|---|---|---|---|
| 1 | 0.0-3.9 | This runway has nineteen inches ... concrete | claim | airliner lands toward camera above the cut layers (lens 60), push in onto the 19 in slab | "19 INCHES OF CONCRETE" slam 0.15 s; label CONCRETE | jet roar, tire screech at touchdown 1.02 |
| 2 | 3.9-5.9 | nearly double a highway | contrast | studio: runway slab vs ~10 in highway slab, both pop | "NEARLY 2X A HIGHWAY"; labels RUNWAY / HIGHWAY | whoosh, 2 thuds |
| 3 | 5.9-7.4 | that's only the top layer | reveal | back on the cut face, pull down; base / subbase / subgrade glow in turn | "ONLY THE TOP LAYER" | 3 ticks |
| 4 | 7.4-12.1 | Jets slam down ... slabs crack | stake | studio demo: wheel pair slams a slab, soft ground sinks red, slab pieces fall in (rigid body) | "JETS SLAM DOWN", "THE GROUND GIVES" (red), "SLABS CRACK" (red) | gear thud 8.34, deny, slab crack 10.35 |
| 5 | 12.1-19.4 | Here's one landing gear ... 300,000 pounds | load | 6-wheel main gear at the cut, wing chunk above, gold load arrow | "ONE LANDING GEAR"; counter 0 -> 300,000 LB PER LEG; label MAIN GEAR | gear thud, ticks + ping |
| 6 | 19.4-24.0 | tires ... two hundred PSI ... six times your car's | pressure | close on the tires, a car tire pops in beside them | "200+ PSI" (cyan), "6X YOUR CAR TIRE"; label CAR TIRE | rush, pop |
| 7 | 24.0-27.4 | All that weight ... dirt | spread | cut face under the gear, cyan load cone grows down through the layers | "SPREAD IT OUT"; label DIRT | riser |
| 8 | 27.4-30.2 | So a runway is built like a layer cake | build-up starts | wide cut face: layers separate, then fly up and away | "A LAYER CAKE" | whoosh x2 |
| 9 | 30.2-33.7 | First, the soil is packed hard. That's the subgrade. | 1 | loose light subgrade, yellow roller crosses with dust, soil darkens | "1. PACKED SOIL"; label SUBGRADE | roller rumble |
| 10 | 33.7-36.2 | Next, a subbase of crushed stone | 2 | subbase drops in, close on the stones (GN scatter) | "2. CRUSHED STONE"; label SUBBASE | layer thud |
| 11 | 36.2-38.5 | Then a base mixed with cement | 3 | base drops in | "3. CEMENT BASE"; label BASE | layer thud |
| 12 | 38.5-41.6 | Then the concrete, poured in giant slabs | 4 | six slabs drop in one after another | "4. CONCRETE SLABS"; label CONCRETE | 3 thuds |
| 13 | 41.6-46.4 | Joints ... expand and shrink ... steel dowels ... load across | joints | close on the joint at x = 0: gap closes/opens, concrete turns see-through, dowels glow cyan, cyan arrow across | "JOINTS", "STEEL DOWELS"; labels JOINT / DOWELS | ticks, steel ting, whoosh |
| 14 | 46.4-52.5 | How thick? ... soil and the planes ... Weaker soil means thicker layers | design | wide cut face; soil turns grey wet clay; every layer grows 45 % | "HOW THICK?", "SOIL + PLANES", "WEAK SOIL = THICKER" (red) | pop, down, riser |
| 15 | 52.5-57.8 | Now the surface ... crown ... rain runs off | crown | low view over the cut edge down the runway, cyan crown arrows slide out, rain | "THE SURFACE", "A GENTLE CROWN" | rain |
| 16 | 57.8-60.1 | Then saws cut grooves across it | grooves | grooving machine drives up the runway, grooves appear behind it, slurry | "SAW-CUT GROOVES" | saw whine |
| 17 | 60.1-62.6 | a quarter inch deep, every inch and a half | size | macro specimen end face, 1/4 x 1/4 in notches 1.5 in apart (true scale) | "1/4 INCH DEEP", "EVERY 1.5 INCHES"; label GROOVE | ticks |
| 18 | 62.6-68.9 | At landing speed ... water ski. The grooves give that water a way out. | hydroplaning | studio: tire spins on a water film, wedge grows, tire lifts; grooved surface, tire drops, spray (+ Mantaflow) | "LIKE A WATER SKI" (red), "A WAY OUT" (cyan); label WATER | water hiss, deny, spray |
| 19 | 68.9-72.8 | Every touchdown leaves rubber ... crews blast it off | upkeep | touchdown zone, rubber streaks grow, tire puffs; water-blast truck cleans the left track | "RUBBER BUILDUP", "BLASTED OFF"; label RUBBER | screech, whoosh, spray |
| 20 | 72.8-77.4 | Which layer surprised you? Next up: wind turbines. | tail (3.8 s) | wide: cut layers in front, plane taking off down the runway; 6 % push-in | "WHICH LAYER SURPRISED YOU?" + "TELL ME IN THE COMMENTS"; "NEXT: WIND TURBINES" + "FOLLOW SO YOU DON'T MISS IT" | impact, ping, pop, jet |

Dead air: none > 1.2 s (longest gap 0.24 s). Studio sets: compare x = -600, demo x = -700, macro x = -720, hydro x = -740.
