# Cover: pipe-under-river (3 options, Rizky picks)

Separate Blender hero render of the whole crossing (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` with the gas main installed, own camera + key light, no labels, arrows, rings or mud.
Render with `bash pipeline3d/bin/render.sh 2026-11-16-pipe-under-river hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "THEY DRILLED / UNDER IT?!"** on `cover/hero_A.png`: the crossing as a cut block from above-left: river, banks, trees, and the glowing yellow gas main arcing under the riverbed on the cut face. (suggested) Check on GPU: the black corner bottom right falls outside the 3:4 crop.
- **B: "A PIPE / UNDER THIS?!"** on `cover/hero_B.png`: straight-on section: a boat on the river, the glowing pipe far below the riverbed. Check the boat reads as a boat (simple hull).
- **C: "IT STEERS / UNDERGROUND?!"** on `cover/hero_C.png`: the drill rig on the near bank, its rod diving under the river, drill head glowing mid-way.
- Titles via Remotion: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-16-pipe-under-river` (fallback: `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`).
