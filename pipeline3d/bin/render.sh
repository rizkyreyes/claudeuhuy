#!/usr/bin/env bash
# GPU renders for one episode.
#   render.sh <episode> stills [f1,f2,...]   -> checks_local/still_*.png + checks_local/sheet.png (50 %, 24 samples)
#   render.sh <episode> final                -> frames_final/f_####.png, then render.mp4 (crf 14)
#   render.sh <episode> cover <frame>        -> cover/still_<frame>.png (100 %, 64 samples)
set -euo pipefail
. "$(dirname "$0")/env.sh"
EP="$(ep_dir "$1")"; MODE="$2"; cd "$EP"
blend() { "$BLENDER" -b -y -P build_scene.py -- "$@" --cycles-device OPTIX; }
case "$MODE" in
  stills)
    FR="${3:-$(node -e 'const t=require("./timeline.json");const n=t.frames;console.log(Array.from({length:10},(_,i)=>Math.round(30+i*(n-60)/9)).join(","))')}"
    rm -rf checks_local; mkdir -p checks_local
    blend --save scene.blend --stills "$FR" --pct 50 --samples 24 --out "$(cygpath -w "$EP/checks_local")" > checks_local.log 2>&1
    grep -E "Traceback|Error:" checks_local.log && exit 1
    cd checks_local; IN=(); FL=""; i=0
    for f in still_*.png; do IN+=(-i "$f"); FL="$FL[$i:v]scale=216:384[s$i];"; i=$((i+1)); done
    H=$(( (i+1)/2 )); A=""; B=""; for ((k=0;k<i;k++)); do if [ $k -lt $H ]; then A="$A[s$k]"; else B="$B[s$k]"; fi; done
    if [ $((i-H)) -lt $H ]; then FL="${FL}color=black:216x384[pad];"; B="$B[pad]"; fi
    "$FFMPEG" -v error -y "${IN[@]}" -filter_complex "${FL}${A}hstack=$H[a];${B}hstack=$H[b];[a][b]vstack" -frames:v 1 sheet.png
    echo "sheet: $EP/checks_local/sheet.png" ;;
  final)
    mkdir -p frames_final
    blend --anim --pct 100 --samples 24 --out "$(cygpath -w "$EP/frames_final")" > render_final.log 2>&1
    "$FFMPEG" -v error -y -framerate 30 -i frames_final/f_%04d.png -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p render.mp4
    echo "render.mp4 $(dur_ms render.mp4) ms, $(ls frames_final | wc -l) frames" ;;
  cover)
    mkdir -p cover
    blend --stills "$3" --pct 100 --samples 64 --out "$(cygpath -w "$EP/cover")" > cover.log 2>&1
    echo "cover/still_$(printf %04d "$3").png" ;;
  *) echo "usage: render.sh <episode> stills|final|cover" >&2; exit 2 ;;
esac
