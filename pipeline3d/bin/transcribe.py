# Transcribe audio/video with faster-whisper on the RTX 4060 (CPU fallback).
#   python transcribe.py <file|url> [--model medium] [--words]
# A URL is downloaded first with yt-dlp (audio only) into ./_dl/.
import os, sys, glob, site, subprocess, argparse, json
for p in glob.glob(os.path.join(site.getsitepackages()[-1], "nvidia", "*", "bin")):
    os.add_dll_directory(p); os.environ["PATH"] = p + ";" + os.environ["PATH"]
from faster_whisper import WhisperModel

a = argparse.ArgumentParser(); a.add_argument("src"); a.add_argument("--model", default="medium"); a.add_argument("--words", action="store_true")
a = a.parse_args()
src = a.src
if src.startswith("http"):
    os.makedirs("_dl", exist_ok=True)
    out = subprocess.check_output([sys.executable, "-m", "yt_dlp", "-x", "--audio-format", "mp3", "-o", "_dl/%(id)s.%(ext)s", "--print", "after_move:filepath", src], text=True)
    src = out.strip().splitlines()[-1]
try: m = WhisperModel(a.model, device="cuda", compute_type="float16")
except Exception: m = WhisperModel(a.model, device="cpu", compute_type="int8")
segs, info = m.transcribe(src, word_timestamps=a.words, vad_filter=True)
res = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
        **({"words": [[w.word, round(w.start, 2), round(w.end, 2)] for w in s.words]} if a.words else {})} for s in segs]
for r in res: print(f"[{r['start']:7.2f}] {r['text']}")
json.dump({"language": info.language, "segments": res}, open(os.path.splitext(src)[0] + ".transcript.json", "w", encoding="utf-8"), indent=1)
