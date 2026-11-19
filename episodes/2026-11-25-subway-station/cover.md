# Cover: subway-station (3 options, Rizky picks)

Rule of 14 Nov 2026 (playbook Cover section): video 100 % Blender, cover = fal.ai `openai/gpt-image-2`, quality MEDIUM, 1088x1920, one image per option (generated in the cloud run 19 Nov, 3 images, no retries).
Text = ONLY the object's name, Poppins ExtraBold, inside the 3:4 crop (y 240-1680), added by Remotion `cover.sh` (fallback `OPT=A node thumb.js`), never by the AI.
Laptop: `bash "D:/01 Konten/Bahan Bikin Konten/tesseract/remotion/cover.sh" 2026-11-25-subway-station`

- **A: "SUBWAY / STATION"** on `cover/hero_A.png` (golden hour: cars on the road deck, below it the deep braced hole with yellow struts, an excavator and work lights = exactly the hook frame of the video; strong moat). Busy at the top (skyline + cars), title needs the dark band.
  fal prompt: `make_covers.sh` PA ("Photoreal premium CGI 3D cross-section of a busy city street while a subway station is built underneath it ...")
- **B: "SUBWAY / STATION"** on `cover/hero_B.png` (suggested: blue-hour rainy avenue on top, the ground cut open to a glowing finished station with island platform, two trains, columns and mezzanine = the video's B13-B14 payoff; one big glowing subject, passes the glance test best). Shows two trains, the video one; same object type and key parts.
  fal prompt: `make_covers.sh` PB
- **C: "SUBWAY / STATION"** on `cover/hero_C.png` (overcast: crane + clamshell bucket over a slurry trench with a rebar cage = B4-B6). Weakest: the trench reads as a narrow tube and doesn't say "subway" at a glance.
  fal prompt: `make_covers.sh` PC
- Checked at preview size: no readable text, no logos, no people in any of the three. Check the train fronts in B at full size on the laptop (no route signs/logos). A's skyline is generic, not a copy of a real photo.
