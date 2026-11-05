# Cover: p-trap (2 options, Rizky picks)

Separate Blender hero render of the whole sink drain (playbook Cover section, 2 Nov 2026): `build_cover.py` re-uses the model of `build_scene.py` with the front halves put back (uncut), frozen at one pose with its own camera + key light, not a video frame, no photos. Render with `bash pipeline3d/bin/render.sh 2026-11-08-p-trap hero`.
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680). CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`.

- **A: "ALWAYS FULL / OF WATER?!"** on `cover/hero_A.png`: the whole sink + white P-trap from the front left, the U-bend in the middle of the frame, trap arm into the wall. Same claim as the hook. (pick)
- **B: "THIS WATER / NEVER LEAVES?!"** on `cover/hero_B.png`: the J-bend taken off (slip nuts loose), seen steeply from above into its open end, the standing water glowing inside.
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA`, `thumbB`.
- Check on GPU: A has a beige drywall panel on the right third; if it looks flat, crop it out by moving the camera left (cam x -11 -> -13).
