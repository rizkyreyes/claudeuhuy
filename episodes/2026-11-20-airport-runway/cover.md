# Cover: airport-runway (3 options, Rizky picks)

Rule of 14 Nov 2026 (playbook Cover section): video 100 % Blender, cover = fal.ai `openai/gpt-image-2`, quality MEDIUM, 1088x1920, one image per option.
Text = ONLY the object's name, Poppins ExtraBold, inside the 3:4 crop (y 240-1680), added in Tesseract/Remotion, never by the AI.

**BLOCKER (cloud run 14 Nov):** fal.ai answered `401 credential has been revoked` for all three images. Nothing was generated or paid.
On the laptop, after renewing the fal key: `bash episodes/2026-11-20-airport-runway/make_covers.sh` (writes cover/hero_A/B/C.png), then
`bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-20-airport-runway` (fallback `OPT=A node thumb.js`).
Fallback if fal stays down: a GPU still of the hook frame (frame 16, plane landing over the cut layers) as hero_A.

- **A: "AIRPORT / RUNWAY"** on `cover/hero_A.png` (suggested: matches the hook frame, plane landing behind the layered cutaway)
  fal prompt: "Photoreal premium CGI 3D cutaway of an airport runway, a giant cross-section slice cut out of the ground in the foreground showing the layers: a thick grey concrete slab on top, a cement-treated base, crushed stone subbase, compacted brown soil below, steel dowel bars glowing cyan at a joint between slabs. A plain white twin-engine airliner is landing on the runway behind, landing gear down, tire smoke. Golden sunset sky, dramatic warm light, runway edge lights glowing, high-tech engineering visualization, vertical 9:16 composition, the cutaway big and centered. No text, no letters, no logos, no airline livery, no people. Leave the top fifth of the image calm and simple."
- **B: "AIRPORT / RUNWAY"** on `cover/hero_B.png` (gear close-up, storm, load cone)
  fal prompt: "Photoreal premium CGI close-up of a plain white airliner's six-wheel main landing gear resting on a runway that is cut open beneath it like a cross-section, revealing a thick concrete slab, cement base, crushed stone and compacted soil layers, a glowing cyan cone showing the weight spreading down through the layers. Stormy dark blue sky with rain, wet reflective runway with saw-cut grooves, dramatic rim light, vertical 9:16 composition, the gear and the layers big and centered. No text, no letters, no logos, no airline livery, no people. Leave the top fifth of the image calm and simple."
- **C: "AIRPORT / RUNWAY"** on `cover/hero_C.png` (exploded layer stack, blue hour, takeoff)
  fal prompt: "Photoreal premium CGI aerial three-quarter view of a long airport runway at blue hour, the near end of the runway lifted out as an exploded cutaway showing its stacked layers floating apart: grooved concrete slabs on top, cement base, crushed stone subbase, compacted soil, with glowing gold outlines on each layer. A plain white airliner taking off in the distance, city lights on the horizon, vertical 9:16 composition, the layer stack big in the middle. No text, no letters, no logos, no airline livery, no people. Leave the top fifth of the image calm and simple."
- Check each image: it must match the video (generic white twin-engine jet, 6-wheel gear, concrete/base/stone/soil layers), no readable text or airline marks; otherwise regenerate once only if Rizky asks.
