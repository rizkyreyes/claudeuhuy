#!/usr/bin/env bash
# Cover heroes for wine-bottle-punt-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-05-wine-bottle-punt-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels on the bottle, no signs, no logos, no brand names, no people, no hands, no animals. Leave the top fifth of the image calm and simple."
B="a plain dark green glass wine bottle with no label, with a deep dome-shaped dent (punt) pushed up into the center of its base"
PA="Photoreal premium CGI 3D cutaway of $B, cut exactly in half from top to bottom to show the glass wall thickness as a glowing orange cut edge, the dome-shaped dent in the base clearly visible in the cross-section, dark red wine inside. The bottle stands on a dark wooden table, dark studio backdrop with a warm key light and a cool blue rim light, dramatic glowing cut edges. Vertical 9:16 composition, the whole bottle big in the middle, the base and its dome in the lower third. $N"
PB="Photoreal premium CGI macro of the bottom of $B, the bottle tipped toward the camera so we look straight into the glass dome of the base, a thin glowing gold ring of light around the standing rim, warm sunset light streaming through the green glass from behind, a vineyard at golden hour softly blurred in the background. Vertical 9:16 composition, the round base big in the middle. $N"
PC="Photoreal premium CGI x-ray cutaway of a heavy dark green champagne bottle with a cork and wire cage, cut in half to show its thick glass walls and a deep dome-shaped dent in the base, golden sparkling wine with streams of bubbles inside, glowing red pressure arrows pushing outward on the walls and the dome. Night city skyline with bokeh lights in the background, high-tech cinematic look. Vertical 9:16 composition, the bottle big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
