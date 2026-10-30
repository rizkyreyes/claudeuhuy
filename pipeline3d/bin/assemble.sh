#!/usr/bin/env bash
# Tesseract assembly for one episode, after render.sh final.
#   assemble.sh <episode> [Name]      Name = project/output base name (default: from the slug, e.g. Septic)
# Does: synth_sfx.js, SFX kit, project create (first run only: fonts, VO, SFX), import render.mp4,
# timeline.js -> commit -> apply, filmstrip previews/filmstrip.png, export <Name>.mp4, loudness.
# Re-run after editing timeline.js: it reuses the project and only rebuilds the timeline + export.
set -euo pipefail
. "$(dirname "$0")/env.sh"
EP="$(ep_dir "$1")"; cd "$EP"
SLUG="$(basename "$EP" | cut -d- -f4-)"
NAME="${2:-$(echo "${SLUG%%-*}" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')}"
P="$NAME.tsrct"
[ -f render.mp4 ] || { echo "render.mp4 missing: run render.sh $1 final first" >&2; exit 1; }

if [ ! -f "$P" ]; then
  node synth_sfx.js >/dev/null
  for f in $(grep -o 'file: "[^"]*"' timeline.js | cut -d'"' -f2 | sort -u) pad-bed; do
    [ -f "sfx/$f.wav" ] || cp "$KIT/$f.wav" sfx/ 2>/dev/null || echo "WARN missing sfx $f" >&2
  done
  "$TSRCT" project create --project "$P" >/dev/null
  "$TSRCT" project import-font --project "$P" --file "$REPO/pipeline3d/fonts/Poppins-ExtraBold.ttf" >/dev/null 2>&1
  "$TSRCT" project import-asset --project "$P" --file assets/vo/vo.wav --asset-id vo --kind audio >/dev/null
  for f in sfx/*.wav; do "$TSRCT" project import-asset --project "$P" --file "$f" --asset-id "sfx-$(basename "$f" .wav)" --kind audio >/dev/null; done
fi
RMS=$(dur_ms render.mp4); RID="render$(stat -c %Y render.mp4)"     # new asset id whenever the render changes
"$TSRCT" project import-video --project "$P" --file render.mp4 --asset-id "$RID" >/dev/null 2>&1 || true
"$TSRCT" project checkout --project "$P" --output editable.json >/dev/null
RENDER_ID="$RID" RENDER_MS="$RMS" node timeline.js
"$TSRCT" project commit --project "$P" --file editable.json >/dev/null
"$TSRCT" project apply --project "$P" --actions edits.json >/dev/null
mkdir -p previews
TS=$(node -e 'const d=Math.round(require("./timeline.json").duration*1000);console.log(Array.from({length:12},(_,i)=>Math.round(800+i*(d-1300)/11)).join(","))')
"$TSRCT" filmstrip --project "$P" --timestamps-ms "$TS" --tile-width 180 --tile-height 320 --items-per-row 12 --output previews/filmstrip.png >/dev/null
"$TSRCT" export --project "$P" --resolution 1080p --fps 30 --output "$NAME.mp4" >/dev/null 2>&1
echo "$EP/$NAME.mp4  $(dur_ms "$NAME.mp4") ms"; loudness "$NAME.mp4"
echo "filmstrip: $EP/previews/filmstrip.png"
