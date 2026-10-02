// crop.mjs: crop in tighter on the subject of a still or a clip, output 1080x1920.
//
//   node crop.mjs <in.jpg|in.mp4> <out.jpg|out.mp4> <zoom> [focusX% focusY%]
//     zoom 1.5 = keep the middle 1/1.5 of the frame.  focus = where the crop closes in (default 50 40).
//   For a clip it also rewrites <out>.json ({"duration": s}) and <out>_last.jpg, which build-broll.mjs needs.
//
// Why: Rizky, 3 Oct 2026: shots had too much empty space around the object. On a phone the subject should
// fill most of the frame width. Use this on stock clips and AI clips that came out loose.
import fs from "node:fs"; import { execFileSync } from "node:child_process";
const [inp, out, zArg, fxArg = "50", fyArg = "40"] = process.argv.slice(2);
if (!inp || !out || !zArg) { console.log("usage: node crop.mjs <in> <out> <zoom> [focusX% focusY%]"); process.exit(1); }
const Z = Math.min(Math.max(Number(zArg), 1), 3), fx = Math.min(Math.max(parseFloat(fxArg) / 100, 0), 1), fy = Math.min(Math.max(parseFloat(fyArg) / 100, 0), 1);
const ffmpeg = process.env.FFMPEG_PATH || "ffmpeg", ffprobe = process.env.FFPROBE_PATH || "ffprobe";
const vf = `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,crop=trunc(iw/${Z}/2)*2:trunc(ih/${Z}/2)*2:(iw-ow)*${fx}:(ih-oh)*${fy},scale=1080:1920:flags=lanczos`;
const tmp = out.replace(/(\.\w+)$/, ".tmp$1");
if (/\.mp4$/i.test(out)) {
  execFileSync(ffmpeg, ["-loglevel", "error", "-y", "-i", inp, "-vf", vf + ",fps=30", "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", tmp], { stdio: "inherit" });
  fs.renameSync(tmp, out);
  const d = Number(execFileSync(ffprobe, ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]).toString().trim());
  fs.writeFileSync(out.replace(/\.mp4$/i, ".json"), JSON.stringify({ duration: +d.toFixed(3) }));
  execFileSync(ffmpeg, ["-loglevel", "error", "-y", "-sseof", "-0.1", "-i", out, "-frames:v", "1", "-update", "1", "-q:v", "2", out.replace(/\.mp4$/i, "_last.jpg")], { stdio: "inherit" });
} else {
  execFileSync(ffmpeg, ["-loglevel", "error", "-y", "-i", inp, "-vf", vf, "-frames:v", "1", "-update", "1", "-q:v", "2", tmp], { stdio: "inherit" });
  fs.renameSync(tmp, out);
}
console.log(`${out}  zoom ${Z}  focus ${Math.round(fx * 100)}% ${Math.round(fy * 100)}%`);
