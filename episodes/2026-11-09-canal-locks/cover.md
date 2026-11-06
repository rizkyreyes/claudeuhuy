# Cover: canal-locks (2 options, Rizky picks)

Separate Blender hero render of the whole lock flight (playbook Cover section, 2 Nov 2026): `build_cover.py` re-uses the model of `build_scene.py` with the near wall put back (uncut), frozen with the chambers stepped 5 / 10 / 15 and the ship on the top step, own camera + key light, no video frame, no photos. Render with `bash pipeline3d/bin/render.sh 2026-11-09-canal-locks hero`.
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680). CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`.

- **A: "85 FT UPHILL / NO PUMPS?!"** on `cover/hero_A.png`: high front three-quarter view, the container ship big on the top step, the lower steps (glowing water) falling away to the left. Same claim as the hook. (pick)
- **B: "SHIPS CLIMB / STAIRS?!"** on `cover/hero_B.png`: from above the lake behind the ship, looking down the staircase of three chambers to the sea.
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA`, `thumbB`.
- Check on GPU: in A the ship's stern sits close to the near wall; if the hull reads too hidden, raise the camera (z 62 -> 70).
