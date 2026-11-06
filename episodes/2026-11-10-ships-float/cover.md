# Cover: ships-float (3 options, Rizky picks)

Separate Blender hero render of the whole ship (playbook Cover section, 2 Nov 2026; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` with the near half put back (uncut ship), loaded at its waterline, own camera + key light,
no video frame, no photos, no labels or arrows. Render with `bash pipeline3d/bin/render.sh 2026-11-10-ships-float hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "SOLID STEEL / STILL FLOATS?!"** on `cover/hero_A.png`: low from the water at the bow quarter, the loaded ship towering over the lens. Same claim as the hook. (suggested)
- **B: "HOW IS THIS / NOT SINKING?!"** on `cover/hero_B.png`: over-under view, the sea cut in front of the ship, the red hull below the waterline seen through the water.
- **C: "THIS FLOATS" (top) / "THIS SINKS?!" (bottom)** on `cover/hero_C.png`: over-under, the ship floating above, a small steel block on the sea bed below it.
- Build with `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`.
