#!/usr/bin/env bash
# Cover heroes for washer-debris-filter-door-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-01-washer-debris-filter-door-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands. Leave the top fifth of the image calm and simple."
B="a generic white front-load washing machine with a round chrome-ringed glass door, its small square access door at the bottom front open"
PA="Photoreal premium CGI 3D cutaway of $B: the lower right corner of the cabinet cut away to reveal a white plastic cylindrical strainer filter with slotted ribs, packed with grey lint, a few copper and silver coins and colourful buttons, glowing cyan water flowing past it into a small drain pump with a glowing impeller. Dark modern laundry room with grey floor tiles, warm key light from the side, soft blue rim light. Vertical 9:16 composition, the filter area big in the lower middle, the washer filling the frame. $N"
PB="Photoreal premium CGI shot at golden hour: $B in a bright laundry room with a window and orange evening sunlight, the white plastic drain filter pulled halfway out of the little door, dripping water into a shallow metal pan on a blue towel, the filter visibly packed with lint, coins and buttons. Low camera close to the floor, shallow depth of field, the filter sharp and large. Vertical 9:16 composition. $N"
PC="Photoreal premium CGI x-ray cross-section of $B floating in a dark stormy blue studio: the cabinet and drum shown as a clean section, glowing cyan water running from the drum down a hose into a white strainer filter at the bottom front, coins and lint caught in it glowing red, the drain hose rising up the back. Dramatic rim light, high-tech look. Vertical 9:16 composition, the whole washer big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
