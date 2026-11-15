#!/usr/bin/env bash
# Cover heroes for wind-turbine-p1 (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-21-wind-turbine-p1/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cutaway of a modern three-blade wind turbine standing on a green prairie, the ground in the foreground sliced open like a cross-section revealing the huge buried concrete foundation: a wide round tapered concrete slab with a glowing cyan steel rebar cage inside and a ring of glowing gold anchor bolts rising into the bottom of the white steel tower, brown soil piled back on top of the slab. Golden sunrise sky, dramatic warm rim light, distant wind farm on the horizon, high-tech engineering visualization, vertical 9:16 composition, the turbine and the cut-open foundation big and centered. $N"
PB="Photoreal premium CGI of a huge yellow lattice-boom crawler crane lifting a white wind turbine nacelle to the top of a tall white steel tower, the nacelle shown as a cutaway with a glowing gold gearbox and a glowing cyan generator inside, the tower made of stacked steel sections with visible bolted flange rings. Dramatic stormy sky with sunbeams breaking through, prairie below, vertical 9:16 composition, low angle looking up, tower and nacelle big and centered. $N"
PC="Photoreal premium CGI exploded cutaway of a whole wind turbine at blue hour: three long white blades and the hub floating slightly apart from the nacelle, the tower split into stacked steel sections with gold glowing flange bolts, and below ground a cross-section of the wide round concrete foundation with a cyan glowing rebar cage, each part with thin glowing outlines. Deep blue twilight sky with the last orange glow on the horizon, vertical 9:16 composition, the full turbine from foundation to blade tips filling the frame. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
