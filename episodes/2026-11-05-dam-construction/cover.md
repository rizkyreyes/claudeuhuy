# Cover: dam-construction (2 options, Rizky picks)

Our own Blender render only (playbook, 2 Nov 2026): no stock photos, nothing AI-generated. Laptop copies the full-res final frames:
`cp frames_final/f_0650.png cover/frame_A.png` and `cp frames_final/f_1290.png cover/frame_B.png` (or `render.sh <ep> cover <frame>` if a camera tweak is needed).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white ~150 px + red ~112 px, 35 % dark band behind the title only. Inside the 3:4 crop (y 240-1680).

- **A: frame 650 (21.6 s), "WHERE DID / THE RIVER GO?!"** (white 140 px + red 112 px): both cofferdams across the canyon, the riverbed between them drained dry,
  the river still running in the tunnel groove in the cut face. The paradox in the picture: a dry riverbed with the river right next to it. Matches the YouTube title. Title at the top (y 245-535).
- **B: frame 1290 (43.0 s), "125 YEARS / TO COOL?!"** (white 150 px + red 112 px): the one-pour dam glowing hot orange with red cracks running down the section.
  Title at the top (y 245-535), over the sky.
- Build with `OPT=A node thumb.js` / `OPT=B node thumb.js`; image assets `thumbA` = cover/frame_A.png, `thumbB` = cover/frame_B.png.
- My pick: **A** (same question as the title and the dry riverbed reads at a glance). On the GPU frame check that the drained bed and the tunnel water read at phone size;
  if the water looks too dark, use a frame 5-15 later (camera settles at 21.4 s, cut 2 starts at 21.85 s, so stay below frame 655).
