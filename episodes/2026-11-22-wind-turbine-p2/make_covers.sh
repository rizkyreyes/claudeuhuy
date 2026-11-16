#!/usr/bin/env bash
# Cover heroes for wind-turbine-p2 (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-22-wind-turbine-p2/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cutaway of a modern three-blade wind turbine nacelle high above green prairie, the side wall of the white nacelle sliced open to reveal the drivetrain: a thick glowing gold main shaft from the hub, a two-stage gearbox with big and small gold gears meshing, a glowing cyan fast shaft running into a cut-open generator with copper coils and red and blue magnets glowing, the three long white blades and hub in front. Dramatic sunset sky with orange and violet clouds, warm rim light, vertical 9:16 composition, nacelle and hub big and centered, blades extending out of frame. $N"
PB="Photoreal premium CGI of a tall white three-blade wind turbine in a dark thunderstorm, heavy rain streaks, the three blades turned edge-on to the wind (feathered) with glowing gold rings at the blade roots, the rotor stopped, lightning far in the distance, a few glowing cyan wind streaks flowing past, wet prairie below. Vertical 9:16 composition, low angle looking up, the whole turbine big and centered. $N"
PC="Photoreal premium CGI cross-section of a single wind turbine blade cut through like a slice, the airfoil profile glowing cyan at the cut, glowing cyan and white airflow streamlines curving over and under it, a soft blue glow of low pressure above the curved top, a gold arrow pointing up for lift, the rest of the turbine and its spinning rotor behind it in a bright midday blue sky with white clouds. Vertical 9:16 composition, blade section big and centered. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
