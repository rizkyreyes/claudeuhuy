# Cover: suspension-bridge-p2 (3 options, Rizky picks)

Separate Blender hero render of the whole bridge (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py`, frozen at a chosen moment, own camera + key light, no labels, arrows, ghosts or net.
Render with `bash pipeline3d/bin/render.sh 2026-11-12-suspension-bridge-p2 hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "HANGING / ON ROPES?!"** on `cover/hero_A.png`: low from the water under the finished deck, the road hanging from the suspender ropes, tower on the left, nothing under the span. Same claim as the hook. (suggested)
- **B: "ROAD LIFTED / FROM A BOAT?!"** on `cover/hero_B.png`: the gantry crane on the main cables lifting a deck section off the barge, mid-air. Check on GPU that the gantry and the section read at thumbnail size.
- **C: "HALF / A ROAD?!"** on `cover/hero_C.png`: high three-quarter of the whole bridge mid-build, deck growing out from both towers with the gap still open in the middle.
- Build with `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`.
