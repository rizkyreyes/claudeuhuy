#!/usr/bin/env bash
# Cover heroes for dryer-vent-fire-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-03-dryer-vent-fire-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands. Leave the top fifth of the image calm and simple."
B="a generic white front-load electric clothes dryer with a silver flexible foil vent duct running from its back through the wall to the outside"
PA="Photoreal premium CGI 3D cutaway of $B: the front panel of the dryer removed to show the steel drum full of tumbling clothes and the glowing orange heating coil in its metal housing, and the foil duct cut open lengthwise showing it thickly clogged with grey lint that is starting to glow and smolder orange where it meets the wall, the wall cut open showing studs and pink insulation. Dark laundry room, warm key light, cool blue rim light. Vertical 9:16 composition, the dryer and the duct big in the middle. $N"
PB="Photoreal premium CGI macro cross-section of the inside of a flexible foil dryer vent duct running inside a wall, sliced in half lengthwise: the inner walls thick with fluffy grey lint, only a narrow gap left in the middle, small orange flames and embers racing along the lint, the wall studs and insulation around it. Dramatic orange firelight against a dark blue background, shallow depth of field. Vertical 9:16 composition. $N"
PC="Photoreal premium CGI of the outside wall of a suburban house on a snowy January night: the exterior dryer vent hood with its flap closed, the siding and the wall cut away in a clean cross-section to reveal the duct inside packed with grey lint and glowing orange with fire, and the dryer in the warm laundry room behind it, snowflakes falling, deep blue night sky. High-tech, cinematic. Vertical 9:16 composition, the duct and the dryer big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
