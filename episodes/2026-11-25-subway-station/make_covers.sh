#!/usr/bin/env bash
# Cover heroes for subway-station (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-25-subway-station/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no signs, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cross-section of a busy city street while a subway station is built underneath it: cars driving on a temporary road deck at street level, and below the cut-open ground a deep rectangular excavation between two thick concrete walls, braced by rows of big yellow steel struts, an excavator working at the bottom, warm work lights glowing, clearly visible soil layers in the cut face, golden-hour sky with city towers behind. Vertical 9:16 composition, the deep braced hole big and centered under the cars. $N"
PB="Photoreal premium CGI cutaway of a normal city avenue at blue-hour dusk with light rain, cars with glowing headlights on wet asphalt, and directly beneath the street the ground sliced open to reveal a finished, brightly lit subway station: island platform, two tracks, a silver train at the platform, concrete columns and a mezzanine, under a thin layer of soil and pavement. Vertical 9:16 composition, the glowing station big in the middle third, the street on top. $N"
PC="Photoreal premium CGI cross-section close-up of slurry wall construction beside a city street on an overcast morning: a yellow crawler crane holding a heavy steel clamshell bucket above a narrow deep trench, the trench filled with glossy brown bentonite slurry shown in the cut face, a tall steel reinforcement cage being lowered into it, layered soil from dark topsoil to gray rock, a tremie pipe and hose. Vertical 9:16 composition, the trench and bucket big and centered. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
