# Cover: bridge-pillars-underwater

- Frame: **1576** (t = 52.5 s, "dry concrete, below the river"): the drained pit with the two generic mannequins on the seal, the river still high outside the steel wall. Render it at 100 % with the final settings (24 samples + OptiX) → asset `thumbA`.
  `blender -b -P build_scene.py -- --stills 1576 --pct 100 --samples 24 --out cover`
- Title (Anton): **UNDER** (white, 210 px, y 360) / **THE RIVER** (red #FF4D3D, 170 px, y 545); dark shade behind the title band.
- Red rounded ring (12 px) around the dry pit, centre (540, 900), 740x520.
- Everything sits inside the 3:4 profile-grid crop (y 240–1680). No brand line, no caption tag.
- Build with `node thumb.js` (writes `editable-thumb.json`; uses the laptop template if one is in the folder).
- Checked on the 25 % still `checks/still_1576.png`: the pit and the outside water line both sit inside the ring; the title shade covers the sheet tops only.
