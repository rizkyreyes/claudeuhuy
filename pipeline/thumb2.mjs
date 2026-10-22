// thumb2.mjs: the NEW thumbnail style (Rizky, 22 Oct 2026), matching the typography layer in the videos:
// full-bleed photo of the detail, a yellow ring on it, and the hook in big Archivo Black type at the top
// (first line white, last line yellow), like the slams in the video. No arrow, no red tag, no brand line.
//
//   node thumb2.mjs <thumb.json> <out.jpg>
//
// thumb.json (paths relative to the json file):
// {
//   "image": "assets/broll/a01.jpg",   // a clean still WITHOUT captions (b-roll still, not a frame of the final video)
//   "point": [40, 45],                 // where the detail is in that image, % from left and from top
//   "zoom": 1.3,                       // 1 = whole image, 1.2-1.6 normal
//   "ring": [520, 520],                // yellow ring size in px around the detail; [0, 0] for no ring
//   "lines": ["NOT A", "REAL CUP"],    // 1-2 lines, ALL CAPS, max 10 characters a line, true to the video
//                                      // (usually the same words as the first slam in the video)
//   "style": "sticker"                 // sticker = DEFAULT, chosen by Rizky 22 Oct 2026. Others kept: top | number | question | spotlight
//   "number": "180", "unit": "ML"      // style "number" only: a spoken number from the video, shown huge
// }
// Styles: top = big white/yellow type at the top; sticker = black type on tilted yellow boxes;
// number = a huge yellow number with the lines under it; question = small white first line, huge yellow second;
// spotlight = everything dark except a bright circle on the detail, lines under it.
// Layout: text sits in the top block (y 230-640), the detail lands at (540, 1130), nothing important in the right
// 140 px or the bottom 300 px (app buttons and captions cover those).
import fs from "node:fs"; import path from "node:path"; import os from "node:os"; import { execFileSync } from "node:child_process";

const [jsonPath, outPath] = process.argv.slice(2);
if (!jsonPath || !outPath) { console.log("usage: node thumb2.mjs <thumb.json> <out.jpg>"); process.exit(1); }
const here = path.dirname(new URL(import.meta.url).pathname);
const base = path.dirname(path.resolve(jsonPath));
const cfg = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const img = path.resolve(base, cfg.image);
if (!fs.existsSync(img)) throw new Error("missing image " + img);
const lines = (cfg.lines || []).map((l) => String(l).trim().toUpperCase()).filter(Boolean);
if (!lines.length || lines.length > 2) throw new Error("lines: give 1 or 2 lines");
const style = cfg.style || "sticker";   // Rizky picked "sticker" (option B) on 22 Oct 2026
for (const l of lines) if (l.length > (style === "question" ? 14 : 10)) throw new Error(`line "${l}" is too long (max 10 characters, 14 for the question style's first line)`);
const ffmpeg = process.env.FFMPEG_PATH || "ffmpeg", ffprobe = process.env.FFPROBE_PATH || "ffprobe";
const pw = fs.existsSync("/opt/pw-browsers") ? fs.readdirSync("/opt/pw-browsers") : [];
const chrome = process.env.CHROME_PATH || [
  ...pw.filter((d) => d.startsWith("chromium_headless_shell-")).flatMap((d) => ["chrome-linux", "chrome-headless-shell-linux64"].map((sub) => `/opt/pw-browsers/${d}/${sub}/headless_shell`)),
  ...pw.filter((d) => d.startsWith("chromium-")).map((d) => `/opt/pw-browsers/${d}/chrome-linux/chrome`),
].find((p) => fs.existsSync(p));
if (!chrome) throw new Error("Chromium not found (set CHROME_PATH)");
const isShell = /headless_shell$/.test(chrome);

const W = 1080, H = 1920, CX = 540, CY = 1130;
const [iw, ih] = execFileSync(ffprobe, ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", img]).toString().trim().split(",").map(Number);
const zoom = Math.min(Math.max(Number(cfg.zoom) || 1.3, 1), 2.5);
const k = Math.max(W / iw, H / ih) * zoom, dw = iw * k, dh = ih * k;
const [px, py] = cfg.point || [50, 50];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const left = clamp(CX - (px / 100) * dw, W - dw, 0), top = clamp(CY - (py / 100) * dh, H - dh, 0);
const rcx = left + (px / 100) * dw, rcy = top + (py / 100) * dh;
const [rw, rh] = cfg.ring || [520, 520];
const longest = Math.max(...lines.map((l) => l.length));
const size = Math.round(Math.min(190, 860 / (0.74 * longest)));   // fills the 860 px text width without overflowing
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
// 3:4 grid crops (TikTok/Instagram profile) cut about 240 px off the top and bottom: keep text below y 300
const T = lines.length > 1 ? 300 : 360;
const L = (l, i, cls = "") => `<div class="l${i === lines.length - 1 ? " acc" : ""} ${cls}">${esc(l)}</div>`;
let block = "", extraCSS = "";
if (style === "top") block = `<div class="txt" style="top:${T}px">${lines.map((l, i) => L(l, i)).join("")}</div>`;
if (style === "sticker") {
  block = `<div class="stk">${lines.map((l, i) => `<div class="s${i}"><span>${esc(l)}</span></div>`).join("")}</div>`;
  extraCSS = `.stk{position:absolute;left:60px;right:140px;top:${T}px}.stk div{margin-bottom:18px}.stk span{display:inline-block;font:400 ${Math.round(size * 0.82)}px/1 "AB";background:#FFD43B;color:#0B0D12;padding:16px 30px 24px;box-shadow:0 14px 30px rgba(0,0,0,.45)}.stk .s0 span{transform:rotate(-4deg);background:#FFFFFF}.stk .s1 span{transform:rotate(2deg);margin-left:40px}`;
}
if (style === "number") {
  const n = String(cfg.number || ""), u = String(cfg.unit || "");
  if (!n) throw new Error("style number needs \"number\"");
  block = `<div class="num" style="top:${T - 20}px"><span class="big">${esc(n)}</span><span class="unit">${esc(u)}</span><div class="sub">${lines.map(esc).join(" ")}</div></div>`;
  extraCSS = `.num{position:absolute;left:60px;right:140px;transform:rotate(-2deg)}.num .big{font:400 330px/0.9 "AB";color:#FFD43B;letter-spacing:-6px;text-shadow:0 12px 0 rgba(0,0,0,.45),0 0 40px rgba(0,0,0,.6)}.num .unit{font:400 120px/1 "AB";color:#fff;margin-left:18px;text-shadow:0 8px 0 rgba(0,0,0,.45)}.num .sub{font:400 92px/1.02 "AB";color:#fff;margin-top:18px;text-shadow:0 8px 0 rgba(0,0,0,.45),0 0 30px rgba(0,0,0,.6)}`;
}
if (style === "question") {
  block = `<div class="q" style="top:${T}px"><div class="q1">${esc(lines[0])}</div>${lines[1] ? `<div class="q2">${esc(lines[1])}</div>` : ""}</div>`;
  extraCSS = `.q{position:absolute;left:70px;right:140px;transform:rotate(-2deg)}.q1{font:400 96px/1.05 "AB";color:#fff;text-shadow:0 8px 0 rgba(0,0,0,.45),0 0 30px rgba(0,0,0,.6)}.q2{font:400 ${Math.min(200, Math.round(860 / (0.74 * (lines[1] || "").length || 1)))}px/0.95 "AB";color:#FFD43B;letter-spacing:-3px;margin-top:8px;text-shadow:0 10px 0 rgba(0,0,0,.45),0 0 34px rgba(0,0,0,.6)}`;
}
if (style === "spotlight") {
  const R = Math.max(rw, rh, 520) / 2;
  block = `<div class="spot"></div><div class="txt" style="top:${Math.min(1380, rcy + R + 40)}px;text-align:center;right:70px;left:70px;transform:none">${lines.map((l, i) => L(l, i)).join("")}</div>`;
  extraCSS = `.spot{position:absolute;inset:0;background:radial-gradient(circle ${R}px at ${rcx.toFixed(0)}px ${rcy.toFixed(0)}px,rgba(0,0,0,0) 0,rgba(0,0,0,0) 92%,rgba(5,7,10,.82) 100%)}.veil{display:none}`;
}
if (!block) throw new Error(`unknown style "${style}"`);
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:"AB";src:url("file://${path.join(here, "fonts", "ArchivoBlack-Regular.ttf")}")}
*{margin:0;padding:0;box-sizing:border-box}html,body{width:${W}px;height:${H}px;overflow:hidden;background:#05070A}
img{position:absolute;left:${left.toFixed(1)}px;top:${top.toFixed(1)}px;width:${dw.toFixed(1)}px;height:${dh.toFixed(1)}px}
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,7,10,.88) 0%,rgba(5,7,10,.72) 24%,rgba(5,7,10,.15) 42%,rgba(5,7,10,0) 55%,rgba(5,7,10,0) 80%,rgba(5,7,10,.55) 100%)}
.ring{position:absolute;left:${(rcx - rw / 2).toFixed(1)}px;top:${(rcy - rh / 2).toFixed(1)}px;width:${rw}px;height:${rh}px;border:14px solid #FFD43B;border-radius:50%;box-shadow:0 0 0 4px rgba(0,0,0,.35),0 0 40px rgba(255,212,59,.35)}
.txt{position:absolute;left:70px;right:150px;transform:rotate(-2deg);transform-origin:0 50%}
.l{font:400 ${size}px/0.98 "AB";letter-spacing:-2px;color:#fff;text-shadow:0 10px 0 rgba(0,0,0,.45),0 0 34px rgba(0,0,0,.6);white-space:nowrap}
.l.acc{color:#FFD43B}
${extraCSS}
</style></head><body><img src="file://${img}" alt=""><div class="veil"></div>${rw > 0 ? '<div class="ring"></div>' : ""}
${block}</body></html>`;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "thumb2-"));
const htmlFile = path.join(tmp, "t.html"), png = path.join(tmp, "t.png");
fs.writeFileSync(htmlFile, html);
execFileSync(chrome, [...(isShell ? [] : ["--headless=new"]), "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--allow-file-access-from-files", "--virtual-time-budget=4000", `--window-size=${W},${H}`, `--screenshot=${png}`, "file://" + htmlFile], { stdio: "ignore" });
fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
execFileSync(ffmpeg, ["-loglevel", "error", "-y", "-i", png, "-q:v", "2", outPath]);
console.log(`${outPath}  [${style}] "${lines.join(" / ")}"  ${size}px  detail at ${Math.round(rcx)},${Math.round(rcy)}`);
