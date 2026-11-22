#!/usr/bin/env bash
# Cover heroes for shower-drain (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-11-30-shower-drain/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
. ../../pipeline3d/bin/env.sh
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no signs, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cross-section of a modern tiled shower at night, the bathroom floor cut open like a cake: under the shower drain a white U-shaped P-trap pipe full of glowing cyan water, sickly green sewer gas held back below it, a white vent pipe rising behind. Warm bathroom light above, dark floor cavity with wooden joists below. Vertical 9:16 composition, the glowing U-bend big in the lower middle. $N"
PB="Photoreal premium CGI cutaway of a two-storey suburban house at sunset, the front wall removed: a glowing cyan water path running from the upstairs shower down through a white U-shaped trap, along a sloped pipe into a vertical stack, down under the concrete slab and out to a big round city sewer pipe under the street; the vent pipe pokes out of the roof. Vertical 9:16 composition, the shower and its trap big in the upper middle. $N"
PC="Photoreal premium CGI extreme close-up cutaway of a white plastic P-trap under a shower drain, half of the pipe cut away: a small pool of crystal-clear water sitting in the bottom of the U, catching light like a lens, faint green gas behind the water seal. Moody blue studio backlight, shallow depth of field. Vertical 9:16 composition, the U-bend filling the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
