# Shared tool paths for the laptop scripts (Git Bash on Windows). Source it: . pipeline3d/bin/env.sh
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
FFBIN="$(cygpath -u "$LOCALAPPDATA")/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin"
FFMPEG="$FFBIN/ffmpeg.exe"; FFPROBE="$FFBIN/ffprobe.exe"
TSRCT="$(cygpath -u "$LOCALAPPDATA")/Tesseract/bin/tsrct.cmd"
export PATH="/c/Program Files/nodejs:$FFBIN:$PATH"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KIT="$REPO/pipeline3d/assets/sfx-kit"     # ui-* accents, pad-bed, deny-thud (laptop only, gitignored)

ep_dir() {   # ep_dir <episode folder name or path> -> absolute path
  local e="$1"; [ -d "$e" ] || e="$REPO/episodes/$1"
  [ -d "$e" ] || { echo "no episode: $1" >&2; exit 1; }; (cd "$e" && pwd)
}
dur_ms() { "$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$1" | awk '{printf "%d", $1*1000}'; }
loudness() { "$FFMPEG" -hide_banner -i "$1" -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2; }
