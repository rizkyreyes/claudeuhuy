#!/usr/bin/env bash
# Cover heroes for hair-dryer-plug-block-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-01-hair-dryer-plug-block-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands. Leave the top fifth of the image calm and simple."
B="a chunky white plastic block-shaped plug at the end of a black hair dryer cord, two flat metal prongs on top and two round push buttons (one dark grey, one white) on its front"
PA="Photoreal premium CGI 3D cutaway of $B, the front half of the plastic shell removed: inside, a green circuit board, a glowing copper ring-shaped coil with two wires passing through its hole (one wire glowing gold, one glowing cyan), a small copper solenoid and tiny copper contacts. It stands on a dark wet bathroom counter next to a white sink, warm golden light from the side, a soft blue backlight, water droplets on the counter. Vertical 9:16 composition, the block big and centred. $N"
PB="Photoreal premium CGI product shot at sunset: a black hair dryer lying on a white marble bathroom counter by a window with orange evening light, its cord leading to $B that is cut open like a cross-section, its copper ring coil and circuit glowing warm orange inside. Shallow depth of field, the cut-open block sharp and large in the lower middle, the dryer soft behind it. Vertical 9:16 composition. $N"
PC="Photoreal premium CGI exploded-view cutaway of $B floating in front of a dark stormy blue bathroom with rain on the window: the shell pieces, prongs and buttons separated slightly from the glowing internals, a bright copper ring-shaped coil in the middle with a gold wire and a cyan wire through it, a small red glow on the tiny contacts as they snap open. Dramatic rim light. Vertical 9:16 composition, the internals big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
