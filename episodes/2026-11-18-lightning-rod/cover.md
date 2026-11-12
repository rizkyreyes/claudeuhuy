# Cover: lightning-rod (3 options, Rizky picks)

Separate Blender hero render of the whole house with its lightning protection (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` at the storm strike: bolt on ridge rod 2, both cables + ground rods glowing, windows lit. No labels, arrows or rings.
Render with `bash pipeline3d/bin/render.sh 2026-11-18-lightning-rod hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "HIT BY LIGHTNING / STILL FINE?!"** on `cover/hero_A.png`: the whole house on its cut lawn block, the bolt on the ridge, the gold current outlining roof edge + both corners down into the glowing ground rods, warm windows. (suggested: the paradox is in the picture)
- **B: "IT DOESN'T / PULL IT IN?!"** on `cover/hero_B.png`: from above the gable end, the row of ridge rods, the bolt landing on one, glow along the roof edge.
- **C: "WHERE DOES / IT GO?!"** on `cover/hero_C.png`: the front-left corner, the glowing cable diving into the cyan ground rod in the cut soil, the bolt above.
- Titles via Remotion: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-18-lightning-rod` (fallback: `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`).
- Check on GPU: the gold glow reads gold, not cream (CurrentGold emission 4.0; lower if it clips); in A the bolt sits behind where the title band goes, keep the title above the roof.
