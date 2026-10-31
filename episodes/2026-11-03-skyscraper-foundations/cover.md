# Cover: skyscraper-foundations (2 options, Rizky picks)

Real stock photos (playbook: cover = a real photo), Pexels licence, no faces, no readable logos, not AI. Already cropped to 1080x1920 in `cover/`.
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white ~150 px + red ~112 px, 35 % dark band behind the title only. Inside the 3:4 crop (y 240-1680).

- **A: "WHY DOESN'T / IT SINK?!"** (white 140 px + red 112 px) on `cover/photo_A.jpg` (Juan Carlos Guzmán): worm's-eye view of a glass tower rising over a brick corner, blue sky and a cloud.
  Title in the sky at the top (y 245-535). The paradox: something this heavy, standing on plain dirt. Same question as the hook.
- **B: "WHAT'S / UNDER IT?!"** on `cover/photo_B_inset.jpg` = `cover/photo_B.jpg` (Fernando Martins, slim residential tower on a clean deep-blue sky)
  + our own Blender cutaway (`cover/inset_B.png`, frame 2026 at 100 %, 64 samples, CPU: raft + front row of piles + tower base) in a rounded box with a gold #FABD45 border and a soft shadow,
  on the left sky (x 34-390, y 600-1100), so it never covers the tower (the lower right corner only touches the building edge). Title in the sky above it (y 245-535).
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA` = photo_A.jpg, `thumbB` = photo_B_inset.jpg.
- My pick: **B** (the inset answers the curiosity gap the title opens; A is the cleaner, punchier photo). If the laptop's GPU render looks better, re-make the inset from the GPU frame 2026.
