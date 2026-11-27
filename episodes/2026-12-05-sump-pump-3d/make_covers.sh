#!/usr/bin/env bash
# Cover heroes for sump-pump-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-05-sump-pump-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands, no animals. Leave the top fifth of the image calm and simple."
B="a home basement sump pit: a round black plastic pit liner sunk into the concrete basement floor, half full of water, a blue submersible sump pump sitting at the bottom with an orange float on a vertical rod beside it, and a white PVC discharge pipe rising straight up out of the pit with a clear check valve in it"
PA="Photoreal premium CGI architectural cross-section diagram of a suburban home basement, showing $B, with the pump shown in a cutaway view revealing its motor and impeller. Around the concrete foundation walls the surrounding soil holds glowing blue groundwater, and a black perforated drain pipe runs along the footing. Rainy evening outside, warm basement light inside, cinematic rim light, glowing cyan water. Vertical 9:16 composition, the pit large in the lower middle. $N"
PB="Photoreal premium CGI close-up cutaway of $B, sliced cleanly in half to show the copper motor windings, the spinning impeller and glowing cyan water being pushed up the pipe. Crisp product-shot lighting on a dark concrete floor, gravel and soil layers visible around the pit. Vertical 9:16 composition, the pump big in the middle. $N"
PC="Photoreal premium CGI three-quarter view of a whole family house made semi-transparent like an x-ray on a rainy evening street, revealing glowing blue groundwater rising in the soil around the basement and $B glowing inside, water arcing out of the discharge pipe onto the lawn far from the wall. Dramatic sunset storm sky, high-tech cinematic look. Vertical 9:16 composition. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
