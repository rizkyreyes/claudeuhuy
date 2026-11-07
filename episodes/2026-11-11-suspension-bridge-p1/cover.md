# Cover: suspension-bridge-p1 (3 options, Rizky picks)

Separate Blender hero render of the whole bridge (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py`, frozen after the cables are finished (no deck yet), own camera + key light,
no labels, arrows or ghost deck. Render with `bash pipeline3d/bin/render.sh 2026-11-11-suspension-bridge-p1 hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "27,572 WIRES / IN ONE CABLE?!"** on `cover/hero_A.png`: low from the water at the left tower, the two finished main cables sweeping up to the saddles. Same claim as the hook. (suggested)
- **B: "SPUN IN / THE SKY?!"** on `cover/hero_B.png`: high over the catwalk, the gold spinning wheel mid-span, the sea far below. Check on GPU that the wheel reads at thumbnail size.
- **C: "A BRIDGE / WITH NO ROAD?!"** on `cover/hero_C.png`: wide three-quarter of the whole bridge, towers + cables + catwalks, no deck (the cliffhanger).
- Build with `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`.
