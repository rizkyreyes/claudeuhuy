# Cover: dam-construction (2 options, Rizky picks)

Separate Blender hero renders of the WHOLE dam (`build_cover.py`, playbook Cover section), not video frames. `bash pipeline3d/bin/render.sh <ep> hero` writes cover/hero_A.png + hero_B.png.
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white ~150 px + red ~112 px, 35 % dark band behind the title only. Inside the 3:4 crop (y 240-1680).

- **A: "WHERE DID / THE RIVER GO?!"** (white 140 px + red 112 px): daylight, high three-quarter view from downstream, full lake behind the wall, bone-dry cracked riverbed in front, the river running out of a tunnel in the canyon wall. Matches the YouTube title.
- **B: "125 YEARS / TO COOL?!"** (white 150 px + red 112 px): dusk, low view from the riverbed, the whole wall glowing hot with bright cracks.
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA` = cover/hero_A.png, `thumbB` = cover/hero_B.png.
- My pick: **A** (same question as the title).
