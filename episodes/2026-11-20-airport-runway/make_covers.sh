#!/usr/bin/env bash
# Cover heroes for airport-runway (playbook Cover section, 14 Nov 2026): fal.ai openai/gpt-image-2, MEDIUM, 1088x1920, one image per option.
# Cloud run 14 Nov: fal returned 401 "credential has been revoked" -> run this on the laptop once the fal key is renewed.
# Usage (from the repo root): bash episodes/2026-11-20-airport-runway/make_covers.sh
set -e
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY=1
N="No text, no letters, no logos, no airline livery, no people. Leave the top fifth of the image calm and simple."
PA="Photoreal premium CGI 3D cutaway of an airport runway, a giant cross-section slice cut out of the ground in the foreground showing the layers: a thick grey concrete slab on top, a cement-treated base, crushed stone subbase, compacted brown soil below, steel dowel bars glowing cyan at a joint between slabs. A plain white twin-engine airliner is landing on the runway behind, landing gear down, tire smoke. Golden sunset sky, dramatic warm light, runway edge lights glowing, high-tech engineering visualization, vertical 9:16 composition, the cutaway big and centered. $N"
PB="Photoreal premium CGI close-up of a plain white airliner's six-wheel main landing gear resting on a runway that is cut open beneath it like a cross-section, revealing a thick concrete slab, cement base, crushed stone and compacted soil layers, a glowing cyan cone showing the weight spreading down through the layers. Stormy dark blue sky with rain, wet reflective runway with saw-cut grooves, dramatic rim light, vertical 9:16 composition, the gear and the layers big and centered. $N"
PC="Photoreal premium CGI aerial three-quarter view of a long airport runway at blue hour, the near end of the runway lifted out as an exploded cutaway showing its stacked layers floating apart: grooved concrete slabs on top, cement base, crushed stone subbase, compacted soil, with glowing gold outlines on each layer. A plain white airliner taking off in the distance, city lights on the horizon, vertical 9:16 composition, the layer stack big in the middle. $N"
for X in A B C; do
  eval P=\$P$X
  node ../../pipeline/falsync.mjs image cover/hero_$X.jpg 1088x1920 medium "$P"
  ffmpeg -v error -y -i cover/hero_$X.jpg cover/hero_$X.png
done
