# Cover: city-sewers (3 options, Rizky picks)

Separate Blender hero render of the subject (playbook Cover section; Packaging rules 7 Nov: 3 options, <= 5 words, subject big):
`build_cover.py` re-uses the model of `build_scene.py` at a chosen moment with its own camera + key light. No labels, captions or tracked arrows from the typography
(the gold route and the cyan slope arrows are 3D objects of the scene).
Render with `bash pipeline3d/bin/render.sh 2026-11-19-city-sewers hero` (A, B and C).
Title Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke, white + red, dark band behind the title only. Inside the 3:4 crop (y 240-1680).
CPU checks at 25 %: `checks/cover_A_25.png`, `checks/cover_B_25.png`, `checks/cover_C_25.png`.

- **A: "WHERE DOES / IT GO?!"** on `cover/hero_A.png`: the house cut open (bathroom, basement), the gold route from the toilet down the stack, under the slab and along the tilted lateral to the street. (suggested: it is the viewer's own house and the question the title of the video answers)
- **B: "IT ALL ROLLS / DOWNHILL?!"** on `cover/hero_B.png`: the street cut along its sewer main, houses on top, the main tilting downhill with the flow, cyan slope arrows.
- **C: "PUMPED / UPHILL?!"** on `cover/hero_C.png`: the lift station: wet well full of sewage, float switch, the pump lit, the force main glowing cyan up to the higher manhole.
- Titles via Remotion: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-19-city-sewers` (fallback: `OPT=A node thumb.js` / `OPT=B` / `OPT=C`; image assets `thumbA`, `thumbB`, `thumbC`).
- Check on GPU: in A the gold route is thin at full size (curve bevel 0.08 m): if it does not read, raise it in `build_scene.py` (RouteA) for the cover only; the lower ~35 % of A and B is plain soil (title band goes on top, the subject sits mid-frame).
