# Cover: water-well (3 options, Rizky picks)

Separate Blender hero render of the whole well (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` frozen with everything installed (cap, casing, screen, grout, pump, pipe, pressure tank), own camera
+ key light, no labels, counters, bars, rain or flow arrows (A/B keep the cyan water dots in the pipe and the pump glowing gold = the paradox: it pushes up).
Render with `bash pipeline3d/bin/render.sh 2026-11-15-water-well hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "140 FEET / DOWN?!"** on `cover/hero_A.png`: the yard as a cut block from above-left: lawn, trees, house, and the well running down the cut face into the blue aquifer, pump glowing at the bottom. Matches the depth reveal. (suggested) Check on GPU: the black corner bottom right falls outside the 3:4 crop.
- **B: "IT PUSHES / UP?!"** on `cover/hero_B.png`: down at the bottom: the glowing pump inside the cased hole, slotted screen below, cyan water rising up the pipe. Matches the "push, don't pull" beat. Check on GPU that the pump reads warm gold, not cream (lower Emission Strength if so).
- **C: "WATER FROM / YOUR YARD?!"** on `cover/hero_C.png`: from the lawn: the well cap and the casing dropping into the ground past the grout seal, house and trees behind.
- Titles via Remotion: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-15-water-well` (fallback: `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`).
