# Cover: nuclear-power-plant (3 options, Rizky picks)

Separate Blender hero render of the whole plant (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` at t = 1 s (containment closed, whole, uncut), own camera + key light, no labels,
flow dots, bubbles or arrows. The paradox cue is the white vapor plume: the plant is a giant kettle.
Render with `bash pipeline3d/bin/render.sh 2026-11-14-nuclear-power-plant hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "A GIANT / KETTLE?!"** on `cover/hero_A.png`: worm's-eye from the grass, the dome close on the left, the cooling tower and its white plume towering on the right. Matches the hook. (suggested)
- **B: "IT JUST / BOILS WATER?!"** on `cover/hero_B.png`: aerial three-quarter of the whole plant: dome, turbine hall, pylon and the steaming tower. Matches the YouTube title.
- **C: "URANIUM / KETTLE?!"** on `cover/hero_C.png`: golden-hour light, long shadows, the plume lit warm against a deep sky.
- Build with `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`.
