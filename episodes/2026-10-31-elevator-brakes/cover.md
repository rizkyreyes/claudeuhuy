# Cover: elevator-brakes (2 options, Rizky picks)

Real stock photos (playbook: cover = a real photo, not a video frame), both Pexels licence, no faces, no logos, not AI. Already cropped to
1080x1920 in `cover/`. Title in Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white ~150 px + red ~112 px, a 35 % dark band
behind the title only. Everything inside the 3:4 profile-grid crop (y 240-1680). No brand line, no caption tag.

- **A: "ROPES SNAP / WON'T FALL?!"** on `cover/photo_A.jpg` (Max Vakhtbovych, an empty stainless-steel elevator car, doors open).
  Title on the dark steel back wall, y 815-1115. The paradox: the box you ride every day, and the claim it stays up with no ropes.
- **B: "NO ROPES / STILL SAFE?!"** on `cover/photo_B.jpg` (Simeon Maryska, an old industrial elevator shaft lit from inside).
  Title at the top, y 315-615. More dramatic, but the photo reads as "building/structure" before "elevator" at thumbnail size.
- Build with `OPT=A node thumb.js` or `OPT=B node thumb.js` (writes `editable-thumb.json`; uses the laptop template if one is in the folder;
  image assets `thumbA` / `thumbB` = the two photos, fit "cover"). Check that "ROPES SNAP" fits one line at 150 px (shrink to 140 if not).
- My pick: **A** (instantly an elevator, and the steel wall gives clean contrast for the red line).
