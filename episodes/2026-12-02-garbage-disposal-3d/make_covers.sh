#!/usr/bin/env bash
# Cover heroes for garbage-disposal-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-02-garbage-disposal-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands, no knife blades. Leave the top fifth of the image calm and simple."
B="a generic black cylindrical kitchen garbage disposal unit mounted under a stainless steel sink drain"
PA="Photoreal premium CGI 3D cutaway of $B: the front half of the unit cut away to show the steel grinding chamber, a flat round steel spinning plate with two small blunt metal lugs on top, a stationary grind ring with vertical teeth and narrow slots around it, bits of carrot and lettuce flung against the ring, glowing cyan water flowing down, copper motor windings glowing gold below. Dark modern kitchen cabinet interior, warm key light, soft blue rim light. Vertical 9:16 composition, the cutaway unit big in the middle. $N"
PB="Photoreal premium CGI cross-section of $B seen from a low angle inside a kitchen sink cabinet at golden hour, orange evening sunlight through a window, the steel chamber sliced open to show the spinning plate with two swivel lugs and the toothed grind ring, food scraps mid-air, the white PVC P-trap pipe curving away to the side. Shallow depth of field, the plate and ring sharp and large. Vertical 9:16 composition. $N"
PC="Photoreal premium CGI exploded technical view of $B floating in a dark stormy blue studio: sink flange, steel grinding chamber, toothed grind ring glowing gold, flat spinning plate with two blunt lugs glowing cyan, electric motor with copper windings, all stacked vertically with small gaps, dramatic rim light, high-tech look. Vertical 9:16 composition, the whole stack big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
