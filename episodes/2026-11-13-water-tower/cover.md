# Cover: water-tower (3 options, Rizky picks)

Separate Blender hero render of the whole tower (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` with the near half put back (whole, uncut), own camera + key light, no labels, arrows, bars or gauges.
Render with `bash pipeline3d/bin/render.sh 2026-11-13-water-tower hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "WHY SO / HIGH?!"** on `cover/hero_A.png`: worm's-eye from the street, the legs and riser converging up to the tank in the sky, houses tiny at the bottom. Matches the tease in suspension-bridge-p2 ("why water towers are built so high"). (suggested)
- **B: "NO PUMP / NEEDED?!"** on `cover/hero_B.png`: the town at night, tower over the dark houses, lit windows and street lamps, moonlit rim on the tank. Check on GPU that the tank reads against the night sky (raise CoverRim if not).
- **C: "HEIGHT IS / PRESSURE?!"** on `cover/hero_C.png`: from above the rooftops, the tank towering over the whole town.
- Build with `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`.
