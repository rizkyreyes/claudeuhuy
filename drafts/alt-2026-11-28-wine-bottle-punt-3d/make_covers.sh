#!/usr/bin/env bash
# Cover heroes for wine-bottle-punt-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-05-wine-bottle-punt-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands, no animals. Leave the top fifth of the image calm and simple."
B="a plain dark green glass wine bottle with a deep dome-shaped dent (punt) pushed up into the bottom of the bottle"
PA="Photoreal premium CGI 3D cutaway of $B, sliced in half from top to bottom so the thickness of the glass shows as a glowing mint-green edge; dark red wine inside, the curved dome of the punt at the bottom outlined in glowing gold, the bottle resting on a smooth glowing gold ring. Elegant wine cellar at dusk behind it, soft bokeh of oak barrels and warm amber light, cool blue rim light on the glass. Vertical 9:16 composition, the whole bottle big in the middle. $N"
PB="Photoreal premium CGI view looking up at the bottom of $B tilted toward the camera, the deep punt glowing gold from inside like a lit dome, crisp reflections on the glass, a few golden sparks of light. Dramatic stormy sunset sky behind, deep orange and violet clouds, cinematic low angle. Vertical 9:16 composition, the bottle base big in the middle. $N"
PC="Photoreal premium CGI x-ray cutaway of a heavy dark green champagne bottle with a deep punt and a mushroom cork held by a wire cage, the glass semi-transparent, pale golden sparkling wine full of rising bubbles, glowing cyan arrows inside pushing outward on the walls and down onto the curved punt. Bright daylight on a sunlit vineyard terrace, blue sky, rows of vines softly blurred. Vertical 9:16 composition, the whole bottle big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
