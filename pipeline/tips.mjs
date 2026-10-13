// tips.mjs: render minimal "tip" photos (Facebook, 1080x1350) to JPGs with headless Chromium.
//   node pipeline/tips.mjs <tips.json> <outDir>
// tips.json: { "tips": [ { "slug": "gas-gauge-arrow", "title": "...", "text": "...", "icon": "<svg 600x600 inner markup>" } ] }
// Style chosen by Rizky 13 Oct 2026: cream background, one line icon, headline + one sentence, no brand line, no "TIP 01" label.
// In icon markup use class "a" for the accent (the detail the tip is about) and "af" for accent fills.
import fs from "node:fs"; import path from "node:path"; import os from "node:os"; import { execFileSync } from "node:child_process";

const [jsonPath, outDir] = process.argv.slice(2);
if (!jsonPath || !outDir) { console.log("usage: node tips.mjs <tips.json> <outDir>"); process.exit(1); }
const here = path.dirname(new URL(import.meta.url).pathname);
const cfg = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const pw = fs.existsSync("/opt/pw-browsers") ? fs.readdirSync("/opt/pw-browsers") : [];
const chrome = process.env.CHROME_PATH || [
  ...pw.filter((d) => d.startsWith("chromium_headless_shell-")).flatMap((d) => ["chrome-linux", "chrome-headless-shell-linux64"].map((sub) => `/opt/pw-browsers/${d}/${sub}/headless_shell`)),
  ...pw.filter((d) => d.startsWith("chromium-")).map((d) => `/opt/pw-browsers/${d}/chrome-linux/chrome`),
].find((p) => fs.existsSync(p));
if (!chrome) throw new Error("Chromium not found (set CHROME_PATH)");
const isShell = /headless_shell$/.test(chrome);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const font = (f) => "file://" + path.join(here, "fonts", f);
const W = 1080, H = 1350;
const C = { bg: "#F3EEE6", ink: "#1F1D1A", accent: "#E0522D", muted: "#6B655D" };

fs.mkdirSync(outDir, { recursive: true });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "tips-"));
cfg.tips.forEach((t, i) => {
  const n = String(i + 1).padStart(2, "0");
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:AB;src:url("${font("ArchivoBlack-Regular.ttf")}")}
@font-face{font-family:AV;src:url("${font("Archivo-Variable.ttf")}");font-weight:100 900}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:${W}px;height:${H}px;background:${C.bg};overflow:hidden}
.wrap{position:absolute;inset:0;padding:92px 100px 100px;display:flex;flex-direction:column}
.icon{flex:1;display:flex;align-items:center;justify-content:center;min-height:0}
.icon svg{width:700px;height:700px}
.icon svg *{fill:none;stroke:${C.ink};stroke-width:14;stroke-linecap:round;stroke-linejoin:round}
.icon svg .a{stroke:${C.accent}}
.icon svg .af{fill:${C.accent};stroke:none}
.icon svg .if{fill:${C.ink};stroke:none}
.icon svg .thin{stroke-width:8}
h1{font:400 74px/1.06 AB;color:${C.ink};letter-spacing:-0.5px;margin-bottom:28px}
p{font:500 40px/1.38 AV;color:${C.muted};max-width:860px}
</style></head><body><div class="wrap">
<div class="icon"><svg viewBox="30 40 540 540" xmlns="http://www.w3.org/2000/svg">${t.icon}</svg></div>
<h1>${esc(t.title)}</h1>
<p>${esc(t.text)}</p>
</div></body></html>`;
  const htmlPath = path.join(tmp, `${n}.html`), png = path.join(tmp, `${n}.png`);
  fs.writeFileSync(htmlPath, html);
  execFileSync(chrome, [...(isShell ? [] : ["--headless=new"]), "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
    "--allow-file-access-from-files", "--virtual-time-budget=3000", `--window-size=${W},${H}`, `--screenshot=${png}`, "file://" + htmlPath], { stdio: "ignore" });
  const out = path.join(outDir, `${n}-${t.slug}.jpg`);
  execFileSync(process.env.FFMPEG_PATH || "ffmpeg", ["-loglevel", "error", "-y", "-i", png, "-q:v", "2", out]);
  console.log(out);
});
