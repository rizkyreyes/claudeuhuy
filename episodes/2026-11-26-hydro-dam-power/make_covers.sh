#!/usr/bin/env bash
# Cover heroes for hydro-dam-power (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Usage (from anywhere): bash episodes/2026-11-26-hydro-dam-power/make_covers.sh [A B C]
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no numbers, no signs, no logos, no brand names, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cross-section of a tall concrete gravity dam in a red desert canyon at golden-hour sunset: deep blue reservoir on the left, the dam sliced open, a big steel penstock pipe glowing with cyan light running down through the rock to a powerhouse at the foot of the dam, where a cut-open turbine and a large red generator glow warmly, water churning out into the river below. Vertical 9:16 composition, the dam and the glowing penstock big and centered. $N"
PB="Photoreal premium CGI cutaway close-up inside a hydroelectric powerhouse: a huge steel spiral casing cut open in half with glowing cyan water swirling through it, a ring of golden wicket gates around a polished stainless steel Francis turbine runner, a thick vertical shaft rising to a giant generator with red and blue rotor poles and copper stator coils glowing above, dramatic cool and warm studio light, dark industrial hall. Vertical 9:16 composition, turbine low, generator high, both big. $N"
PC="Photoreal premium CGI cross-section of a hydroelectric dam during a stormy dusk with lightning far in the sky: the reservoir held back by the curved concrete wall, the dam and the rock beneath shown cut open, a glowing cyan stream of water falling through a steel pipe deep inside to a turbine and generator glowing gold at the bottom, power lines climbing the canyon wall. Vertical 9:16 composition, the full height of the dam from the lake to the turbine in frame. $N"
for X in ${@:-A B C}; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
