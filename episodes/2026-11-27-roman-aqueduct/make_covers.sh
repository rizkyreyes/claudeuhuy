#!/usr/bin/env bash
# Cover heroes for roman-aqueduct (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-27-roman-aqueduct/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no signs, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cutaway of an ancient Roman three-tier stone aqueduct bridge crossing a green river valley at golden-hour sunset: warm limestone arches in three rows, the water channel on the very top shown cut open along its length with glowing cyan water flowing inside, a thin glowing gold line along the water surface, a turquoise river far below, wooded hills. Vertical 9:16 composition, the bridge big and diagonal across the frame, low dramatic angle. $N"
PB="Photoreal premium CGI cross-section close-up of the stone water channel on top of an ancient Roman aqueduct: the channel sliced open showing its thick limestone walls, a pink waterproof mortar lining and clear glowing cyan water flowing through it, cream-white limestone mineral crust built up in layers on the inner walls, cover slabs on top, the stacked dry-laid stone blocks and arches of the bridge dropping away below, soft blue sky. Vertical 9:16 composition, the cut-open channel big in the middle. $N"
PC="Photoreal premium CGI cutaway of an ancient Roman aqueduct at blue-hour dusk with a stormy sky: a tall three-tier stone arch bridge across a deep valley, and on both hillsides the ground shown cut open to reveal the buried stone water channel glowing cyan as it runs underground toward the bridge, warm light on the arches, a river below. Vertical 9:16 composition, the bridge and the glowing channel line in frame from hill to hill. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
