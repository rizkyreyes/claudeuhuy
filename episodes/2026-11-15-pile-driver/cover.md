# Cover: pile-driver (3 options, Rizky picks)

Separate Blender hero render of the hammer / rig (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` at the moment the blast throws the ram up, own camera + key light, no labels or arrows.
Render with `bash pipeline3d/bin/render.sh 2026-11-15-pile-driver hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "IT LIFTS / ITSELF?!"** on `cover/hero_A.png`: the hammer on top of the pile from below, the leads rising into the sky, the ram flying out of the cylinder, orange blast glow. Check on GPU: the subject is thin (a tall, narrow rig); if it reads small, lower the lens to 15 or move the camera closer.
- **B: "DIESEL / INSIDE?!"** on `cover/hero_B.png`: the cut hammer up close: orange fire in the gap, the dark ram thrown up out of the yellow cylinder. (suggested: biggest subject, one strong contrast)
- **C: "WHAT HOLDS / IT UP?!"** on `cover/hero_C.png`: the finished tower standing on its piles in the cut ground, the rig firing on the next pile.
- Titles via Remotion: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-15-pile-driver` (fallback: `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`).
