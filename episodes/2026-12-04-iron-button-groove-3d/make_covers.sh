#!/usr/bin/env bash
# Cover heroes for iron-button-groove-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-04-iron-button-groove-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands, no animals. Leave the top fifth of the image calm and simple."
B="a modern white and teal household steam iron with a pointed aluminum soleplate, a shallow button groove running along the front edge of the soleplate just above its bottom lip"
PA="Photoreal premium CGI 3D cutaway of $B, cut in half lengthwise to show the inside: a glowing orange heating element cast into the aluminum soleplate, a small steam chamber with steam holes, a translucent water tank with blue water, a thin bimetal strip thermostat. White steam puffs out of the holes underneath onto a light blue cotton shirt. Dark studio backdrop with a cool blue rim light and warm key light, dramatic glowing internals. Vertical 9:16 composition, the iron big in the middle, tip pointing up-right. $N"
PB="Photoreal premium CGI macro of the tip of $B resting on a light blue cotton dress shirt placket, a white plastic shirt button tucked into the glowing gold groove at the edge of the soleplate, soft steam curling around the tip. Bright sunny laundry room by a window, morning daylight, shallow depth of field, crisp product-shot look. Vertical 9:16 composition, the tip and the button big in the middle. $N"
PC="Photoreal premium CGI x-ray view of $B on an ironing board, the body semi-transparent and glowing cyan to reveal the heating element glowing orange inside the soleplate, the water tank and a thin valve dripping into the steam chamber, the button groove at the tip outlined in glowing gold, a row of shirt buttons nearby. Moody evening light, deep purple and blue gradient background, high-tech cinematic look. Vertical 9:16 composition, the iron big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
