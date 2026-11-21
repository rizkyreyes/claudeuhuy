#!/usr/bin/env bash
# Cover heroes for jeans-rivets-3d (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-29-jeans-rivets-3d/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no signs, no logos, no brand names, no leather patch, no stamped lettering on the rivets, no people, no hands. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D close-up of the front pocket of a pair of dark indigo blue jeans lying on a sunlit wooden workbench at golden hour: the curved pocket opening with gold-orange double stitching, a shiny copper rivet at the pocket corner, and next to it the same rivet shown as a glowing cutaway cross-section through three layers of denim, the copper post mushroomed inside the cap, soft cyan glow around the metal. Warm window light, dramatic. Vertical 9:16 composition, the rivet and pocket corner big in the lower middle. $N"
PB="Photoreal premium CGI macro of a single copper jeans rivet sliced in half, floating above dark indigo denim layers that are also cut open showing their woven threads, the copper post crushed into the dome cap, tiny sparks, cool blue studio light with a cyan rim glow, deep blue-black gradient background. Vertical 9:16 composition, the cut rivet big in the middle. $N"
PC="Photoreal premium CGI 3D of the front of a pair of vintage indigo work jeans standing on an old 1870s tailor's wooden workbench in a dusty workshop with warm lamp light: copper rivets glowing at both pocket corners, the tiny watch pocket inside the right front pocket with a gold pocket watch peeking out and its chain hanging, a spool of thread and a pair of shears nearby. Vertical 9:16 composition, the pocket area big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
