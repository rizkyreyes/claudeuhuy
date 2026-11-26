#!/usr/bin/env bash
# Cover heroes for septic-drain-field-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-04-septic-drain-field-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands, no animals. Leave the top fifth of the image calm and simple."
B="a home septic drain field: a buried concrete septic tank, a small concrete distribution box, and three parallel white perforated pipes with holes on the underside, each lying in a long trench of grey gravel under a green lawn"
PA="Photoreal premium CGI 3D cross-section of a suburban backyard cut open like a cake, showing $B. Glowing cyan water drips from the pipe holes down through the gravel into brown soil layers, a thin blue groundwater layer far below. A simple family house on the left edge, golden-hour sunset sky, dramatic warm rim light, glowing internals. Vertical 9:16 composition, the trenches big in the middle. $N"
PB="Photoreal premium CGI close-up cutaway of one drain-field trench under a lawn: a white perforated pipe resting in grey gravel, glowing cyan water dripping from holes on its underside, tiny glowing green specks in the dark soil below, grass and soil layers sliced cleanly. Overcast daylight, crisp macro product-shot look, shallow depth of field. Vertical 9:16 composition, the pipe big in the middle. $N"
PC="Photoreal premium CGI aerial three-quarter view of a backyard lawn made semi-transparent like an x-ray, revealing $B glowing cyan underneath, a few dark wet patches and unusually bright green stripes of grass above the trenches, stormy dramatic sky, high-tech cinematic look. Vertical 9:16 composition. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
