"""cap-pauses.py — shorten long pauses in the EXISTING voice take instead of speeding the voice up.

    python3 ../../pipeline/cap-pauses.py <projectDir> [cap=0.24] [capSentence=0.34]

Every gap between two words longer than the cap is cut down to the cap (after a sentence ends, . ? !,
the cap is capSentence so sentences still breathe). The cut is taken from the middle of the gap, with a
4 ms fade on both sides so there is no click. Word timestamps are shifted by the exact samples removed,
so captions and every cue stay locked to the voice. No new TTS call, no cost.

Backs up assets/vo/<id>.wav and audio_meta.json once (*.orig) and always works from the backup, so it is
safe to run again with a different cap. Then re-run lint-plan.mjs and build-broll.mjs.
"""
import json, os, shutil, sys, wave
import numpy as np

proj = sys.argv[1]
CAP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.24
CAP_SENT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.34
vo = os.path.join(proj, "assets/vo")
meta_p = os.path.join(vo, "audio_meta.json")
if not os.path.exists(meta_p + ".orig"):
    shutil.copy(meta_p, meta_p + ".orig")
meta = json.load(open(meta_p + ".orig"))
sc = meta["scenes"][0]
wav_p = os.path.join(vo, sc["wav"])
if not os.path.exists(wav_p + ".orig"):
    shutil.copy(wav_p, wav_p + ".orig")

w = wave.open(wav_p + ".orig", "rb")
nch, sw, sr, nfr = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
assert sw == 2 and nch == 1, "expected 16-bit mono PCM (tts.mjs output)"
pcm = np.frombuffer(w.readframes(nfr), dtype=np.int16).astype(np.float32)
w.close()

words = sc["words"]
cuts = []  # (startSample, endSample) to remove
for i in range(len(words) - 1):
    a, b = words[i], words[i + 1]
    cap = CAP_SENT if a["text"].rstrip()[-1:] in ".?!" else CAP
    gap = b["start"] - a["end"]
    if gap > cap:
        keep = cap / 2
        cs, ce = int(round((a["end"] + keep) * sr)), int(round((b["start"] - keep) * sr))
        if ce > cs:
            cuts.append((cs, ce))

fade = int(0.004 * sr)
out, pos = [], 0
for cs, ce in cuts:
    seg = pcm[pos:cs].copy()
    if len(seg) > fade:
        seg[-fade:] *= np.linspace(1, 0, fade)
    out.append(seg)
    pos = ce
    if len(pcm) - pos > fade:
        pcm[pos:pos + fade] *= np.linspace(0, 1, fade)
out.append(pcm[pos:])
new = np.concatenate(out).clip(-32768, 32767).astype(np.int16)

def shift(t):
    s = int(round(t * sr))
    removed = sum(min(ce, s) - cs for cs, ce in cuts if cs < s)
    return round((s - removed) / sr, 3)

for wd in words:
    wd["start"], wd["end"] = shift(wd["start"]), shift(wd["end"])
old_dur = sc["duration"]
sc["duration"] = round(len(new) / sr, 3)
sc["speechStart"], sc["speechEnd"] = words[0]["start"], words[-1]["end"]

o = wave.open(wav_p, "wb")
o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(new.tobytes()); o.close()
json.dump(meta, open(meta_p, "w"), indent=1)
print(f"cap-pauses: {len(cuts)} pauses capped (cap {CAP}s, after a sentence {CAP_SENT}s): {old_dur}s -> {sc['duration']}s")
