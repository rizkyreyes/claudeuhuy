# Cover: septic-tank (2 options, Rizky picks)

Curiosity contrast, Anton title, one strong red, everything inside the 3:4 profile-grid crop (y 240–1680). No brand line, no caption tag.

- **A: "ALWAYS / FULL?!"** (white 220 px / red 170 px, title at the top, y 260–600). Frame **915** (t = 30.5 s): the cut-open tank,
  layers settled, the cyan level line glowing right at the outlet pipe. A red line (12 px, black outline) laid over the level line
  (centre 540, 850): the paradox is a tank filled to the brim that never overflows.
  `blender -b -P build_scene.py -- --stills 915 --pct 100 --samples 24 --out <abs path>/cover` → asset `thumbA`
- **B: "IT NEVER / FILLS UP?!"** (white 200 px / red 150 px). Frame **1150** (t = 38.3 s): sludge, clear liquid and scum, cyan arrows
  flowing into the T outlet. Red ring (12 px) around the outlet tee, centre (680, 930), 260x330.
  `blender -b -P build_scene.py -- --stills 1150 --pct 100 --samples 24 --out <abs path>/cover` → asset `thumbB`
- Build with `OPT=A node thumb.js` or `OPT=B node thumb.js` (writes `editable-thumb.json`; uses the laptop template if one is in the folder). Dark shade (45 %) behind the title band.
- Positions come from the projected anchors in timeline.json (frame 915: level anchor (858, 852); frame 1150: tee anchor (679, 931)).
  Recheck the line/ring on the 100 % GPU frame before export; the level line runs slightly downhill to the left in perspective.
- My pick: **A** (one word plus a red line says the whole video). B is the safer, more literal one.
