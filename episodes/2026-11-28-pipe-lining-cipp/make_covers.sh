#!/usr/bin/env bash
# Cover heroes for pipe-lining-cipp (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-28-pipe-lining-cipp/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no signs, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cross-section of a modern single-story house on a concrete slab at golden-hour sunset: the ground below the house cut open like a cake, showing dark soil layers and an old rusty cracked cast-iron drain pipe running under the kitchen floor, and inside it a new smooth pipe liner glowing cyan, the tiled floor above completely intact. Warm sky, dramatic light. Vertical 9:16 composition, the glowing pipe big and diagonal across the lower middle. $N"
PB="Photoreal premium CGI cutaway close-up inside an old rusty cast-iron sewer pipe buried in soil: a soft resin-soaked felt liner turning itself inside out as it travels down the pipe, the rolling front glowing gold, the inverted liner pressed against the corroded walls, cyan air-pressure glow behind it, tree roots poking through a cracked joint. Moody blue backlight. Vertical 9:16 composition, the rolling liner front big in the middle. $N"
PC="Photoreal premium CGI cutaway of a drain pipe under a house in a rainy blue-hour storm: the soil cut open, a small yellow robotic cutter with a camera inside a smooth newly lined pipe, its spinning cutter head grinding open a side branch, sparks of resin dust, the old cracked cast-iron pipe around the liner. Vertical 9:16 composition, the robot and the branch opening big in the middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
