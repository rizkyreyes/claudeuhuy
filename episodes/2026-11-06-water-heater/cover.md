# Cover: water-heater (2 options, Rizky picks)

Separate Blender hero render of the whole water heater (playbook Cover section, 2 Nov 2026): `build_cover.py`, not a video frame, no photos. Render with `bash pipeline3d/bin/render.sh 2026-11-06-water-heater hero`.
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680); CPU check at 25 % put the heater between y ~600 and ~1660.

- **A: "A ROD THAT ROTS / ON PURPOSE?!"** on `cover/hero_A.png`: front right, the anode rod pulled halfway out of the top, eaten away with red-glowing pits and falling flakes. Same claim as the hook. (pick)
- **B: "IS IT ROTTING / INSIDE?!"** on `cover/hero_B.png`: low from the front left, rust streaks running down the lower jacket, burner light leaking under the access panel, rusty puddle.
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA`, `thumbB`.
