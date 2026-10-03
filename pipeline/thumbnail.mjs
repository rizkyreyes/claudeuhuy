// thumbnail.mjs: make the 1080x1920 thumbnail for a video (style chosen by Rizky, 3 Oct 2026:
// tight photo, red circle on the detail, red arrow, 2-3 word label on a red tag).
//
//   node thumbnail.mjs <thumb.json> <out.jpg>
//
// thumb.json (paths relative to the json file):
// {
//   "image": "assets/broll/t01.jpg",   // a clean still WITHOUT captions (a b-roll still, not a frame of the final video)
//   "point": [50, 31],                 // where the detail is in that image, in % from the left and from the top
//   "zoom": 1.4,                       // 1 = whole image, 1.2-1.6 is normal. The detail must be easy to see on a phone
//   "ring": [560, 480],                // width and height of the red circle in pixels (fits the detail with a little air)
//   "label": "NOT BROKEN"              // 2-3 words, max 20 characters, upper case, true to the video.
//                                      // Over 11 characters it is split into two lines at the space nearest the middle.
// }
// The detail always lands in the middle of the frame (540, 860) and the label sits right under it, so everything
// important stays inside the centre of the image, which is the part YouTube, Instagram and TikTok show when they crop.
import fs from "node:fs"; import path from "node:path"; import os from "node:os"; import { execFileSync } from "node:child_process";

const [jsonPath, outPath] = process.argv.slice(2);
if (!jsonPath || !outPath) { console.log("usage: node thumbnail.mjs <thumb.json> <out.jpg>"); process.exit(1); }
const here = path.dirname(new URL(import.meta.url).pathname);
const base = path.dirname(path.resolve(jsonPath));
const cfg = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const img = path.resolve(base, cfg.image);
if (!fs.existsSync(img)) throw new Error("missing image " + img);
const label = String(cfg.label || "").trim().toUpperCase();
if (!label) throw new Error("label is required");
if (label.length > 20) throw new Error(`label "${label}" is ${label.length} characters, max 20`);
// one line up to 11 characters, otherwise two lines split at the space nearest the middle
let lines = [label];
if (label.length > 11 && label.includes(" ")) {
  const sp = [...label].map((c, i) => (c === " " ? i : -1)).filter((i) => i > 0);
  const cut = sp.reduce((a, b) => (Math.abs(b - label.length / 2) < Math.abs(a - label.length / 2) ? b : a));
  lines = [label.slice(0, cut), label.slice(cut + 1)];
}
const longest = Math.max(...lines.map((l) => l.length));
if (longest > 12) throw new Error(`label line "${lines.find((l) => l.length === longest)}" is too long, use shorter words`);
const ffmpeg = process.env.FFMPEG_PATH || "ffmpeg", ffprobe = process.env.FFPROBE_PATH || "ffprobe";
const pw = fs.existsSync("/opt/pw-browsers") ? fs.readdirSync("/opt/pw-browsers") : [];
const chrome = process.env.CHROME_PATH || [
  ...pw.filter((d) => d.startsWith("chromium_headless_shell-")).flatMap((d) => ["chrome-linux", "chrome-headless-shell-linux64"].map((sub) => `/opt/pw-browsers/${d}/${sub}/headless_shell`)),
  ...pw.filter((d) => d.startsWith("chromium-")).map((d) => `/opt/pw-browsers/${d}/chrome-linux/chrome`),
].find((p) => fs.existsSync(p));
if (!chrome) throw new Error("Chromium not found (set CHROME_PATH)");
const isShell = /headless_shell$/.test(chrome);

const W = 1080, H = 1920, CX = 540, CY = 860;
const [iw, ih] = execFileSync(ffprobe, ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", img]).toString().trim().split(",").map(Number);
const zoom = Math.min(Math.max(Number(cfg.zoom) || 1.3, 1), 2.5);
const k = Math.max(W / iw, H / ih) * zoom;            // displayed scale of the source image
const dw = iw * k, dh = ih * k;
const [px, py] = cfg.point || [50, 40];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const left = clamp(CX - (px / 100) * dw, W - dw, 0), top = clamp(CY - (py / 100) * dh, H - dh, 0);
const rcx = left + (px / 100) * dw, rcy = top + (py / 100) * dh;   // where the detail really ends up (after clamping)
const [rw, rh] = cfg.ring || [460, 420];
const size = Math.round(Math.min(lines.length > 1 ? 112 : 138, 860 / (0.76 * longest)));
const tagTop = Math.min(rcy + rh / 2 + 150, lines.length > 1 ? 1230 : 1330);
// arrow: from just above the right end of the tag up to the lower right edge of the ring
const tagW = longest * 0.76 * size + 80;
const ax1 = clamp(Math.max(W / 2 + tagW / 2 - 70, rcx + rw / 2 + 60), 120, W - 90), ay1 = tagTop - 2;
const ax2 = rcx + (rw / 2) * 0.80 + 14, ay2 = rcy + (rh / 2) * 0.66 + 14;
const ang = Math.atan2(ay2 - ay1, ax2 - ax1), hx = ax2 + Math.cos(ang) * -6, hy = ay2 + Math.sin(ang) * -6;
const head = [[0, 0], [-62, -34], [-62, 34]].map(([x, y]) => `${(hx + x * Math.cos(ang) - y * Math.sin(ang)).toFixed(1)},${(hy + x * Math.sin(ang) + y * Math.cos(ang)).toFixed(1)}`).join(" ");
const cxq = (ax1 + ax2) / 2 + 70, cyq = (ay1 + ay2) / 2 + 10;
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:"AB";src:url("file://${path.join(here, "fonts", "ArchivoBlack-Regular.ttf")}")}
@font-face{font-family:"A";src:url("file://${path.join(here, "fonts", "Archivo-Variable.ttf")}");font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}html,body{width:${W}px;height:${H}px;overflow:hidden;background:#0a0c0e}
body{position:relative;color:#fff}
img{position:absolute;left:${left.toFixed(1)}px;top:${top.toFixed(1)}px;width:${dw.toFixed(1)}px;height:${dh.toFixed(1)}px}
.veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(8,10,14,.45) 0%,rgba(8,10,14,0) 22%,rgba(8,10,14,0) 58%,rgba(8,10,14,.6) 70%,rgba(8,10,14,1) 79%,rgba(8,10,14,1) 100%)}
.ring{position:absolute;left:${(rcx - rw / 2).toFixed(1)}px;top:${(rcy - rh / 2).toFixed(1)}px;width:${rw}px;height:${rh}px;border:16px solid #FF3B30;border-radius:50%;box-shadow:0 0 0 5px rgba(0,0,0,.35),inset 0 0 0 5px rgba(0,0,0,.25)}
svg{position:absolute;inset:0;width:${W}px;height:${H}px;filter:drop-shadow(0 4px 6px rgba(0,0,0,.6))}
.tag{position:absolute;left:0;right:0;top:${tagTop.toFixed(1)}px;text-align:center}
.tag span{display:inline-block;font:400 ${size}px/1.02 "AB";background:#FF3B30;color:#fff;padding:18px 40px 26px;transform:rotate(-3deg);box-shadow:0 12px 30px rgba(0,0,0,.5);white-space:nowrap}
.brand{position:absolute;left:0;right:0;top:1660px;text-align:center;font:800 30px/1 "A";letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.8)}
</style></head><body><img src="file://${img}" alt=""><div class="veil"></div><div class="ring"></div>
<svg viewBox="0 0 ${W} ${H}"><path d="M${ax1.toFixed(1)} ${ay1.toFixed(1)} Q ${cxq.toFixed(1)} ${cyq.toFixed(1)}, ${(ax2 - Math.cos(ang) * 40).toFixed(1)} ${(ay2 - Math.sin(ang) * 40).toFixed(1)}" stroke="#FF3B30" stroke-width="22" fill="none" stroke-linecap="round"/><polygon points="${head}" fill="#FF3B30"/></svg>
<div class="tag"><span>${lines.map(esc).join("<br>")}</span></div><div class="brand">Hidden In Your Home</div></body></html>`;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "thumb-"));
const htmlFile = path.join(tmp, "t.html"), png = path.join(tmp, "t.png");
fs.writeFileSync(htmlFile, html);
execFileSync(chrome, [...(isShell ? [] : ["--headless=new"]), "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--allow-file-access-from-files", "--virtual-time-budget=4000", `--window-size=${W},${H}`, `--screenshot=${png}`, "file://" + htmlFile], { stdio: "ignore" });
fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
execFileSync(ffmpeg, ["-loglevel", "error", "-y", "-i", png, "-q:v", "2", outPath]);
console.log(`${outPath}  label "${label}"  detail at ${Math.round(rcx)},${Math.round(rcy)}`);
