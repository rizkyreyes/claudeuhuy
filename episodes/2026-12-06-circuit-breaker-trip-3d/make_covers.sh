#!/usr/bin/env bash
# Cover heroes for circuit-breaker-trip-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-06-circuit-breaker-trip-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no labels, no logos, no brand names, no people, no hands, no animals. Leave the top fifth of the image calm and simple."
B="a generic black plastic household circuit breaker cut cleanly in half to reveal its inside: a copper contact arm with silver contacts, a stack of steel arc chute plates, a brass-and-steel bimetal strip, a small copper coil around a steel plunger, a spring, and the black toggle handle on top"
PA="Photoreal premium CGI cutaway of $B, shown big as a product shot, a bright blue-white electric arc glowing between the parting contacts and splitting into the steel plates, glowing cyan current lines in the copper. Dark studio with dramatic rim light and a subtle reflection on a glossy floor. Vertical 9:16 composition, the breaker big in the middle. $N"
PB="Photoreal premium CGI view of a home electrical panel recessed in a living room wall at golden-hour sunset light, the wall cut away in cross-section to show wooden studs and a white electrical cable glowing red-hot inside the wall, and one breaker in the panel pulled forward and cut open to reveal its glowing copper and steel parts. Warm cinematic light, high-tech look. Vertical 9:16 composition. $N"
PC="Photoreal premium CGI extreme close-up of $B, the bimetal strip glowing orange-hot and bending, sparks flying from the contacts, deep blue night background with soft bokeh lights, glowing internals, crisp high-detail render. Vertical 9:16 composition, the breaker filling the frame. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
