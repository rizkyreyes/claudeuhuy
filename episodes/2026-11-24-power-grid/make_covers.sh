#!/usr/bin/env bash
# Cover heroes for power-grid (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-24-power-grid/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cutaway of a large high-voltage step-up power transformer standing next to a power plant at golden hour, the front of the steel oil tank sliced away to reveal a dark iron core with two glowing copper coils, one coil with few thick turns and one with many thin turns glowing bright gold, tall porcelain bushings on top feeding glowing cyan high-voltage lines that run to a steel lattice transmission tower behind, dramatic orange and violet sunset sky. Vertical 9:16 composition, the transformer big and centered. $N"
PB="Photoreal premium CGI of a giant steel lattice high-voltage transmission tower seen from a low angle against a dramatic stormy blue evening sky, long strings of glass insulator discs, the bare conductors glowing with bright cyan energy pulses racing along them, a line of towers marching over green hills into the distance toward a small town. Vertical 9:16 composition, the tower tall and centered. $N"
PC="Photoreal premium CGI cross-section of a suburban street at dusk: a wooden utility pole with a gray cylindrical pole-mounted transformer cut open to reveal glowing gold and cyan copper coils on an iron core, three glowing service wires running to a cut-away house wall where a white wall outlet glows warmly inside the stud cavity, warm window light, deep blue sky. Vertical 9:16 composition, the pole transformer big in the upper middle. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
