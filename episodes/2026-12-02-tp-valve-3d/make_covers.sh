#!/usr/bin/env bash
# Cover heroes for tp-valve-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-02-tp-valve-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no signs, no logos, no brand names, no people, no hands. Leave the top fifth of the image calm and simple."
B="a generic white residential tank water heater with a small brass temperature and pressure relief valve on the upper side and a white discharge pipe running straight down to the floor"
PA="Photoreal premium CGI 3D cutaway of $B: the front half of the tank cut away to show glowing orange hot water inside, the steel inner tank and yellow foam insulation, a dark flue tube in the middle, blue gas burner flames at the bottom, and the brass valve also cut in half showing its spring, disc and a long probe reaching into the top of the tank, the valve glowing gold. Dark utility room, warm key light, soft blue rim light. Vertical 9:16 composition, the whole heater big in the middle. $N"
PB="Photoreal premium CGI macro cross-section of the brass temperature and pressure relief valve on the side of $B, the valve sliced in half: steel spring, rubber disc on its brass seat, test lever on top, a copper probe reaching into the tank, hot orange water and wisps of steam escaping down the discharge pipe. Garage at sunset, orange light through a window, shallow depth of field, the valve huge and sharp. Vertical 9:16 composition. $N"
PC="Photoreal premium CGI of $B shown dramatically mid-launch, blasting upward through a broken wooden ceiling with chunks of drywall and a huge cloud of white steam below it, the brass relief valve glowing red as a warning, inside a dark basement with a stormy blue night sky visible through the hole. High-tech, cinematic, the whole heater big in the middle. Vertical 9:16 composition. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
