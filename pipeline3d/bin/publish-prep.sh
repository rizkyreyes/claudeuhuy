#!/usr/bin/env bash
# After Rizky's "setuju A|B": build the upload file, push it, print the Buffer plan.
#   publish-prep.sh <episode> A|B [video.mp4]
# Appends the chosen cover as the last 2 frames (= thumbnail), audio limiter, crf 21 (raised until < 48 MB),
# copies the cover to thumbnails/, commits + pushes media/<slug>.mp4, checks the raw URL,
# then prints the three create_post payloads (buffer-plan.mjs). It never posts anything itself.
set -euo pipefail
. "$(dirname "$0")/env.sh"
EP="$(ep_dir "$1")"; OPT="$2"; cd "$EP"
BASE="$(basename "$EP")"; SLUG="$(echo "$BASE" | cut -d- -f4-)"
VID="${3:-$(ls -S *.mp4 | grep -v -i 'render\|upload' | head -1)}"
COVER="$(ls cover/cover_$OPT.png previews/cover-$OPT.png 2>/dev/null | head -1 || true)"
[ -n "$COVER" ] || { echo "no cover $OPT" >&2; exit 1; }
D=$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$VID"); W=$(awk "BEGIN{print $D+2/30}")
OUT="$REPO/media/$SLUG.mp4"
for CRF in 21 23 25 27; do
  "$FFMPEG" -v error -y -i "$VID" -loop 1 -framerate 30 -i "$COVER" -filter_complex \
    "[1:v]scale=1080:1920,format=yuv420p,trim=end_frame=2,setpts=PTS-STARTPTS[c];[0:v]format=yuv420p[v];[v][c]concat=n=2:v=1:a=0[o];[0:a]alimiter=limit=0.85,apad=whole_dur=$W[a]" \
    -map "[o]" -map "[a]" -c:v libx264 -crf $CRF -preset slow -c:a aac -b:a 192k -movflags +faststart "$OUT"
  [ "$(stat -c %s "$OUT")" -lt 48000000 ] && break
done
cp "$COVER" "$REPO/thumbnails/$BASE.png"
cd "$REPO"; git pull -q
git add "media/$SLUG.mp4" "thumbnails/$BASE.png"
git commit -q -m "$SLUG: upload file with cover $OPT

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q origin main
sleep 5
curl -sI "https://raw.githubusercontent.com/rizkyreyes/claudeuhuy/main/media/$SLUG.mp4" | grep -i "^HTTP"
node "$REPO/pipeline3d/bin/buffer-plan.mjs" "$EP" "$(awk "BEGIN{printf \"%d\", $D*1000+10}")"
