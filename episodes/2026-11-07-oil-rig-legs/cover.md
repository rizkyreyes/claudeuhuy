# Cover: oil-rig-legs (2 options, Rizky picks)

Separate Blender hero render of the whole platform (playbook Cover section, 2 Nov 2026): `build_cover.py` re-uses the model of `build_scene.py` at one frozen pose with its own camera, not a video frame, no photos. Render with `bash pipeline3d/bin/render.sh 2026-11-07-oil-rig-legs hero`.
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680); CPU check at 25 % put the platform between y ~300 (derrick tip) and the bottom, deck at y ~600-760, so the title sits in the sky (derrick tip may touch the white line: shift the title up 30 px if it does).

- **A: "WHAT HOLDS / IT UP?!"** on `cover/hero_A.png`: the finished platform (deck on the jacket) in the cut ocean, low 3/4 view from the front left, warm low sun; the legs run all the way down to the seabed and the piles go deep into the mud. The paradox: a tall steel tower standing in open water. (pick)
- **B: "IT FLIPS / UPRIGHT?!"** on `cover/hero_B.png`: the jacket mid-upend at a steep angle, half under the waves, the flooded lower legs glowing cyan.
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA`, `thumbB`.
