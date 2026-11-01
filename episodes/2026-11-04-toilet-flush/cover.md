# Cover: toilet-flush (2 options, Rizky picks)

Our own Blender render only (playbook, 2 Nov 2026): no stock photos, nothing AI-generated. Laptop copies the full-res final frames:
`cp frames_final/f_1000.png cover/frame_A.png` and `cp frames_final/f_0470.png cover/frame_B.png` (or `render.sh <ep> cover <frame>` if a camera tweak is needed).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white ~150 px + red ~112 px, 35 % dark band behind the title only. Inside the 3:4 crop (y 240-1680).

- **A: frame 1000 (33.3 s), "IT DOESN'T PUSH / IT SUCKS?!"** (white 120 px + red 112 px): the trapway completely full with the striped flow, the bowl still full above it,
  water falling into the drain pipe. The paradox in the picture: the water goes UP the bend before it goes down. Title in the dark area at the top (y 245-535).
- **B: frame 470 (15.6 s), "WHY DOESN'T / IT OVERFLOW?!"** (white 140 px + red 112 px): the extra water pouring into the bowl with the cyan level line through the top of the bend
  and drops spilling over into the drain. Matches the YouTube title question. Title at the top (y 245-535).
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA` = cover/frame_A.png, `thumbB` = cover/frame_B.png.
- My pick: **B** (same question as the title and the picture answers it at a glance; A is the stronger "wait, what?" if the GPU frame shows the full trap clearly).
  Check on the GPU frames that the level line and the spill drops read at phone size; if not, use a frame 3-6 later.
