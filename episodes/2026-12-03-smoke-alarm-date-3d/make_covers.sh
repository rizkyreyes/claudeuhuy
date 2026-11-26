#!/usr/bin/env bash
# Cover heroes for smoke-alarm-date-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage: bash episodes/2026-12-03-smoke-alarm-date-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
if command -v cygpath >/dev/null 2>&1; then . ../../pipeline3d/bin/env.sh; else FFMPEG=ffmpeg; fi
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no dates, no labels, no signs, no logos, no brand names, no people, no hands. Leave the top fifth of the image calm and simple."
B="a generic round white ceiling smoke alarm with a ring of vent slots, a small test button and a tiny LED"
PA="Photoreal premium CGI 3D cutaway of $B, mounted on a white hallway ceiling, sliced in half to reveal the inside: a black sensing chamber with a maze of angled black walls, a tiny LED shining a thin glowing cyan beam across it, a light sensor off to the side, grey smoke particles drifting into the chamber, a green circuit board, a 9-volt battery and a brass horn disc. The cut faces glow orange. Dark hallway, thin grey smoke layer under the ceiling, warm orange firelight from a doorway behind. Vertical 9:16 composition, the alarm big in the middle. $N"
PB="Photoreal premium CGI of an old yellowed $B being held up close, flipped over to show its plain back with a blank white sticker glowing softly gold, the ceiling mounting plate above it, cool morning daylight in a modern hallway, shallow depth of field, crisp product-shot look. Vertical 9:16 composition, the alarm big in the middle. $N"
PC="Photoreal premium CGI exploded cross-section of $B floating against a deep dark blue studio background: the cover lifted off, the black labyrinth sensing chamber cut open in the middle with a glowing cyan light beam and a few smoke particles scattering light onto a small sensor, the circuit board and horn below, dust and grime coating parts of the chamber, dramatic rim light. High-tech, cinematic. Vertical 9:16 composition. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  "$FFMPEG" -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
