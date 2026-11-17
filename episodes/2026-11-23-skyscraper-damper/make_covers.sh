#!/usr/bin/env bash
# Cover heroes for skyscraper-damper (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-23-skyscraper-damper/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cutaway of the top of a very tall stepped glass supertall skyscraper at golden hour, the front glass walls of the upper floors sliced away to reveal a giant glowing gold steel ball pendulum hanging on thick steel cables inside the cut-open floors, eight silver hydraulic dampers angled beneath it, warm interior light, a big city far below, dramatic orange and violet sunset sky. Vertical 9:16 composition, the gold ball big and centered in the upper middle. $N"
PB="Photoreal premium CGI of a very tall stepped green glass supertall skyscraper bending slightly in a violent typhoon at night, heavy rain streaks and lightning, the upper floors shown in a glowing x-ray cutaway revealing a giant gold steel ball pendulum swinging inside, glowing cyan wind streaks flowing past the tower, a city of lights below. Vertical 9:16 composition, low angle, the whole tower tall and centered. $N"
PC="Photoreal premium CGI close-up of a giant gold steel ball made of stacked horizontal steel plates, hanging on thick steel cables inside a cut-open skyscraper floor, eight polished silver hydraulic dampers below it glowing orange-hot at the joints, floor slabs cut away in section, floor-to-ceiling windows with a bright blue daytime sky and clouds behind. Vertical 9:16 composition, the ball big and centered. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
