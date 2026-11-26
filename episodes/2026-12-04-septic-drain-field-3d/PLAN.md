# Beat plan: septic-drain-field-3d (cues = words of take 3, 75.04 s VO -> 76.42 s video, 2293 frames)
| Beat | Words (s, video time) | Hero (Blender) | Type | SFX |
|---|---|---|---|---|
| B1 hook | "If your home is on septic" 0.3 | backyard cross-section (house, lawn, cut soil): glowing cyan water runs house -> tank -> D-box -> trench pipe from frame 0, slow push | UNDER YOUR LAWN (frame 0), SEPTIC TANK label | impact, rush, yard air |
| B2 holes | "leaking out of pipes full of holes" 4.5 | cut to the trench pipe close: gold hole glows, drips fall through the gravel into the soil | PIPES FULL OF HOLES, ON PURPOSE | impact, ping, drips |
| B3 stake | "If they clog" 7.9 | lawn surface: dark sewage puddles spread on the grass | IF THEY CLOG..., SEWAGE COMES BACK UP | whoosh, deny, squelch |
| B4 one in five | "More than one in five" 12.5 | row of five houses, the middle one lights gold with its tank + field glowing under it | 1 IN 5 U.S. HOMES + note (EPA) | impact |
| B5 tank -> box | "Liquid leaves the tank" 15.8 | tank section (scum, liquid, sludge), beads run downhill to the D-box; push into the D-box | SEPTIC TANK, DOWNHILL, DISTRIBUTION BOX label, A SMALL CONCRETE BOX | whoosh, rush |
| B6 plan | "One outlet per trench" 20.2 | soil + grass vanish: top view of D-box + 3 trenches on gravel strips; cyan level line on "dead level", beads split into all 3 | 1 OUTLET PER TRENCH, DEAD LEVEL, EQUAL SHARE | pop, set-ping |
| B7 pipe | "Then it flows into pipes" 24.9 | pipe end (section: 4-inch circle), pull back along the trench (pipe glows), cut low on the holes (gold) | 4 INCHES WIDE, LAID FLAT, IN TRENCHES OF GRAVEL, GRAVEL label, HOLES POINTING DOWN | impact, pop |
| B8 soil | "It drips out" 31.7 | drips leave the holes, through the gravel, into the soil | DRIPS INTO THE SOIL, THE REAL CLEANING | whoosh, drips, sewer drips |
| B9 bacteria | "The soil is packed with bacteria" 35.8 | green glowing bacteria (GN scatter) light up under the trench | PACKED WITH BACTERIA, SOIL BACTERIA label | ping |
| B10 germs | "Within a few feet" 39.3 | wider: red germ dots ride the drips and shrink to nothing; blue groundwater glows far below | A FEW FEET, MOST GERMS GONE, GROUNDWATER label | down, pop |
| B11 air | "But those bacteria need air" 43.1 | lawn + shallow trench: white air beads sink from the grass into the soil | THEY NEED AIR, SHALLOW TRENCHES, ONLY GRASS ON TOP | whoosh, pop |
| B12 car | "Park a car on it" 49.2 | generic car drops onto the field (rigid body), dark crushed layer grows under it, air beads under it stop | PARK ON IT..., CRUSHED SOIL, NO AIR | car-thud, crumble, deny |
| B13 biomat | "Over the years" 52.3 | trench bottom close: black glossy biomat grows along it | OVER THE YEARS, A BLACK, SLIMY LAYER, BIOMAT label, SLOWS THE WATER | riser, impact, down |
| B14 solids | "Skip pumping the tank" 59.3 | tank: sludge rises; brown solids ride out to the trench; gravel darkens, biomat thickens | SKIP PUMPING, SLUDGE label, SOLIDS WASH OUT, CLOGS FASTER | impact, whoosh, deny |
| B15 rise | "nowhere to go but up" 64.5 | water fills the trench and rises through the soil to the lawn | NOWHERE TO GO BUT UP | gurgle, rush |
| B16 signs | "The grass turns bright green" 66.4 | lawn: field strip turns bright green, puddles spread, mud particles bubble up | BRIGHT GREEN, SPONGY GRASS, EVEN IN DRY WEATHER, SEWAGE SURFACES + note | pop, deny, squelch x2 |
| B17 CTA | "Do you know where your drain field is?" 72.2 | high wide shot, lawn back to normal green, glowing cyan outline of the trenches + gold tank outline on the grass, slow pull-out, fade over the last 0.8 s | DO YOU KNOW WHERE YOUR DRAIN FIELD IS? + TELL ME IN THE COMMENTS, DRAIN FIELD label, NEXT: THE NOTCH ON YOUR IRON (last 2 s) | impact, ping |

Gates: hook moves at frame 0 (flow beads + camera push + title), no pause between words > 0.6 s in the take (no dead air > 1.2 s), the only numbers on screen (1 IN 5, 4 INCHES) are spoken. Every C.<cue> and EV.<event> in timeline.js exists in timeline.json (node check 26 Nov).
fx power-ups: hdri (bundled "forest", background on), glare, particles (mud bubbling at "sewage can surface"), rigid body (the car dropping onto the field), Geometry Nodes scatter x4 (grass tufts, field tufts, gravel stones, soil bacteria), engine Cycles. Mantaflow NOT used: water seeping through gravel and soil is not a free liquid; a fluid sim would look wrong and cost bake time (drips = beads, rising water = animated volume boxes).
