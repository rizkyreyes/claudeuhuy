// slideshow.mjs: turn carousel frames into a vertical slideshow VIDEO with quiet background music.
//
//   node carousel.mjs  <carousel.json> <workDir> frames          # makes <workDir>/frames/01.jpg, 02a.jpg, 02.jpg ...
//   node slideshow.mjs <carousel.json> <workDir>/frames <out.mp4> [music.mp3]
//
// Why a video: Instagram and TikTok don't let schedulers attach sounds from their own music libraries, so the
// music has to be inside the file. Tracks in pipeline/music/ are royalty-free instrumentals generated with
// ElevenLabs Music for this channel (see pipeline/music/README.md). Never use a commercial song.
// If no music file is given, the track is picked from pipeline/music/ by the carousel number (c01 -> track 1, ...).
//
// Timing: cover 2.6 s; each myth: 2.2 s with the myth alone, then the fact for (words / 4.3 + 1.4) s, clamped
// to 4.5–8.5 s; end card 4.5 s. Music is normalised to about -30 LUFS (very quiet, background only) with a fade in and out.
import fs from "node:fs"; import path from "node:path"; import { execFileSync } from "node:child_process";

const [jsonPath, framesDir, outPath, musicArg] = process.argv.slice(2);
if (!jsonPath || !framesDir || !outPath) { console.log("usage: node slideshow.mjs <carousel.json> <framesDir> <out.mp4> [music.mp3]"); process.exit(1); }
const here = path.dirname(new URL(import.meta.url).pathname);
const cfg = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const ffmpeg = process.env.FFMPEG_PATH || "ffmpeg";
const LUFS = Number(process.env.MUSIC_LUFS || -30);

const words = (t) => String(t || "").trim().split(/\s+/).filter(Boolean).length;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const segs = [];   // { file, dur, trans, tdur }  trans = how this frame ENTERS
cfg.slides.forEach((s, i) => {
  const nn = String(i + 1).padStart(2, "0");
  const f = (n) => { const p = path.join(framesDir, n + ".jpg"); if (!fs.existsSync(p)) throw new Error("missing frame " + p); return p; };
  if (s.type === "cover") segs.push({ file: f(nn), dur: 2.6, trans: "slideleft", tdur: 0.4 });
  else if (s.type === "myth") {
    segs.push({ file: f(nn + "a"), dur: 2.2, trans: "slideleft", tdur: 0.4 });
    segs.push({ file: f(nn), dur: clamp(words(s.fact) / 4.3 + 1.4, 4.5, 8.5), trans: "fade", tdur: 0.25 });
  } else segs.push({ file: f(nn), dur: 4.5, trans: "slideleft", tdur: 0.4 });
});

// music: explicit file, or rotate through pipeline/music by the carousel number in the json's folder name (c07 -> 7)
let music = musicArg;
if (!music) {
  const tracks = fs.readdirSync(path.join(here, "music")).filter((x) => x.endsWith(".mp3")).sort();
  if (!tracks.length) throw new Error("no tracks in pipeline/music/");
  const num = Number((path.resolve(jsonPath).match(/c(\d+)[^/]*\/[^/]*$/) || [])[1] || 1);
  music = path.join(here, "music", tracks[(num - 1) % tracks.length]);
}

const args = ["-loglevel", "error", "-y"];
segs.forEach((s) => args.push("-loop", "1", "-t", (s.dur + 0.5).toFixed(2), "-i", s.file));
args.push("-stream_loop", "-1", "-i", music);
let fc = segs.map((s, k) => `[${k}:v]scale=1080:1920,fps=30,format=yuv420p,setsar=1[v${k}]`).join(";");
let last = "v0", acc = segs[0].dur;
for (let k = 1; k < segs.length; k++) {
  const s = segs[k]; const off = (acc - s.tdur).toFixed(3);
  fc += `;[${last}][v${k}]xfade=transition=${s.trans}:duration=${s.tdur}:offset=${off}[x${k}]`;
  last = `x${k}`; acc = acc + s.dur - s.tdur;
}
const total = acc;
fc += `;[${segs.length}:a]loudnorm=I=${LUFS}:TP=-3:LRA=7,afade=t=in:d=0.6,afade=t=out:st=${(total - 1.6).toFixed(2)}:d=1.6[a]`;
args.push("-filter_complex", fc, "-map", `[${last}]`, "-map", "[a]", "-t", total.toFixed(2),
  "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
  "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", outPath);
fs.mkdirSync(path.dirname(outPath), { recursive: true });
execFileSync(ffmpeg, args, { stdio: "inherit" });
console.log(`${outPath}  ${total.toFixed(2)} s  music: ${path.basename(music)} at ${LUFS} LUFS`);
