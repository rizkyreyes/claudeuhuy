# Cover: escalator-steps (2 options, Rizky picks)

Curiosity contrast, Anton title, one strong red, everything inside the 3:4 profile-grid crop (y 240–1680). No brand line, no caption tag.

- **A: "WHERE DO / THE STAIRS GO?"** (white 200 px / red 140 px). Frame **1110** (t = 37.0 s, "Near the top… both tracks level off"): the cutaway where the staircase bends and flattens into a floor. Red ring (12 px) around the flattening steps, centre (560, 900), 760x360.
  `blender -b -P build_scene.py -- --stills 1110 --pct 100 --samples 24 --out cover` → asset `thumbA`
- **B: "ALWAYS / LEVEL?!"** (white 210 px / red 160 px). Frame **1040** (t = 34.7 s, "stays level"): one step mid-slope, side cutaway, both wheels and the cyan second track visible. Red level line laid across the tread (x 236–656, y 912).
  `blender -b -P build_scene.py -- --stills 1040 --pct 100 --samples 24 --out cover` → asset `thumbB`
- Build with `OPT=A node thumb.js` or `OPT=B node thumb.js` (writes `editable-thumb.json`; uses the laptop template if one is in the folder). Dark shade (45 %) behind the title band.
- Checked against the 25 % CPU stills (`checks/still_1110.png`, frame 1040 check render): the flattening steps sit around y 800–1000 and the hero tread at y ≈ 925, both inside the crop and clear of the title band. Recheck the ring/line positions on the 100 % GPU frame before export.
- My pick: **A** (the picture itself shows the paradox: stairs turning into floor).
