# Cover: undersea-tunnel (2 options, Rizky picks)

Curiosity contrast, Anton title, one strong red, everything inside the 3:4 profile-grid crop (y 240–1680). No brand line, no caption tag.

- **A: "WHY DOESN'T / THE SEA LEAK IN?"** (white 170 px / red 124 px, title at the bottom, y 1300–1620, so the sea at the top stays clear).
  Frame **150** (t = 5.0 s, hook): the sea band on top, the gold machine digging just under the seabed. Red line laid along the seabed edge
  (centre 540, 600, rotated −6°): the paradox is water right above a dry machine.
  `blender -b -P build_scene.py -- --stills 150 --pct 100 --samples 24 --out <abs path>/cover` → asset `thumbA`
- **B: "BURIED / ON PURPOSE?!"** (white 220 px / red 150 px). Frame **2150** (t = 71.6 s): Channel section, the British machine turned down
  into the clay, glowing red, the finished drive above it. Red ring (12 px) around it, centre (565, 1050), 300x230.
  `blender -b -P build_scene.py -- --stills 2150 --pct 100 --samples 24 --out <abs path>/cover` → asset `thumbB`
- Build with `OPT=A node thumb.js` or `OPT=B node thumb.js` (writes `editable-thumb.json`; uses the laptop template if one is in the folder). Dark shade (45 %) behind the title band.
- Checked on 25 % CPU stills: frame 150 seabed edge runs about y 540–660 across the frame, machine at y 840–1280; frame 2150 `uk_tbm` anchor at (565, 1060).
  Recheck the line/ring positions on the 100 % GPU frame before export (the ring may need to grow if the rubble block is included).
- My pick: **B** (the picture alone raises the question; nobody expects a machine to be left in the rock). A is the safer, more literal one.
