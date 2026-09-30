// carousel.mjs: render a "myth vs fact" photo carousel to JPGs with headless Chromium.
//
//   node carousel.mjs <carousel.json> <outDir> [ig|tt|both]      (default: both)
//     ig = 1080x1350 (Instagram 4:5)   tt = 1080x1920 (TikTok photo mode 9:16)
//
// carousel.json (paths are relative to the json file):
// {
//   "slides": [
//     { "type": "cover", "bg": "bg/cover.jpg", "kicker": "Myth vs fact", "title": "5 home energy myths you probably still believe", "sub": "Swipe" },
//     { "type": "myth",  "bg": "bg/thermostat.jpg", "myth": "Crank the thermostat way up and the house heats faster.", "fact": "Your furnace runs at one speed. ...", "source": "Trane, via Popular Science" },
//     { "type": "end",   "bg": "bg/cover.jpg", "title": "Save this for later.", "cta": "Follow for more", "sources": ["...", "..."] }
//   ]
// }
// No @handle on any slide (Rizky, 30 Sep 2026): the footer shows only "Hidden In Your Home".
// Myth slides are numbered automatically (1/5, 2/5 ...). Text on the image is allowed here (the "no text in the
// middle of the screen" rule is for videos only). Keep myth lines under ~90 characters and facts under ~200.
import fs from "node:fs"; import path from "node:path"; import os from "node:os"; import { execFileSync } from "node:child_process";

const [jsonPath, outDir, which = "both"] = process.argv.slice(2);
if (!jsonPath || !outDir) { console.log("usage: node carousel.mjs <carousel.json> <outDir> [ig|tt|both]"); process.exit(1); }
const here = path.dirname(new URL(import.meta.url).pathname);
const base = path.dirname(path.resolve(jsonPath));
const cfg = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
// Prefer chrome-headless-shell: its --window-size is the exact viewport (full Chrome's headless mode can lose ~90px).
const pw = fs.existsSync("/opt/pw-browsers") ? fs.readdirSync("/opt/pw-browsers") : [];
const chrome = process.env.CHROME_PATH || [
  ...pw.filter((d) => d.startsWith("chromium_headless_shell-")).flatMap((d) => ["chrome-linux", "chrome-headless-shell-linux64"].map((sub) => `/opt/pw-browsers/${d}/${sub}/headless_shell`)),
  ...pw.filter((d) => d.startsWith("chromium-")).map((d) => `/opt/pw-browsers/${d}/chrome-linux/chrome`),
].find((p) => fs.existsSync(p));
const isShell = /headless_shell$/.test(chrome || "");
if (!chrome) throw new Error("Chromium not found (set CHROME_PATH)");
const ffmpeg = process.env.FFMPEG_PATH || "ffmpeg";
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const url = (p) => "file://" + path.resolve(base, p);
const font = (f) => "file://" + path.join(here, "fonts", f);
const total = cfg.slides.filter((s) => s.type === "myth").length;

function page(s, i, W, H) {
  const tall = H > 1500;
  const pad = 84;
  let n = 0; for (let k = 0; k <= i; k++) if (cfg.slides[k].type === "myth") n++;
  const top = `<div class="top"><span class="chip">Myth vs fact</span>${s.type === "myth" ? `<span class="count">${n}/${total}</span>` : ""}</div>`;
  let body = "";
  if (s.type === "cover") body = `
    ${s.kicker ? `<div class="kicker">${esc(s.kicker)}</div>` : ""}
    <h1 class="cover">${esc(s.title)}</h1>
    ${s.sub ? `<div class="swipe">${esc(s.sub)} <span>&rarr;</span></div>` : ""}`;
  if (s.type === "myth") body = `
    <div class="label myth-l">Myth</div>
    <p class="myth">${esc(s.myth)}</p>
    <div class="label fact-l">Fact</div>
    <p class="fact">${esc(s.fact)}</p>
    ${s.source ? `<p class="src">Source: ${esc(s.source)}</p>` : ""}`;
  if (s.type === "end") body = `
    <h1 class="end">${esc(s.title)}</h1>
    ${s.cta ? `<div class="cta">${esc(s.cta)}</div>` : ""}
    ${(s.sources || []).length ? `<div class="srclist"><b>Sources</b>${s.sources.map((x) => `<span>${esc(x)}</span>`).join("")}</div>` : ""}`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:"ArchivoBlack";src:url("${font("ArchivoBlack-Regular.ttf")}")}
  @font-face{font-family:"Archivo";src:url("${font("Archivo-Variable.ttf")}");font-weight:100 900;font-stretch:62% 125%}
  :root{--ink:#FFFFFF;--muted:rgba(255,255,255,.72);--yellow:#F5C242;--red:#FF6B5B;--shade:10,12,14}
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{width:${W}px;height:${H}px;overflow:hidden;background:#0a0c0e}
  body{font-family:"Archivo",Arial,sans-serif;color:var(--ink);position:relative}
  .bg{position:absolute;inset:0;background:url("${url(s.bg)}") center/cover no-repeat}
  .veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(var(--shade),.55) 0%,rgba(var(--shade),.15) 22%,rgba(var(--shade),.35) ${tall ? 42 : 36}%,rgba(var(--shade),.88) ${tall ? 62 : 58}%,rgba(var(--shade),.96) 100%)}
  .wrap{position:absolute;inset:0;padding:${pad}px ${pad}px ${pad - 8}px;display:flex;flex-direction:column}
  .top{display:flex;justify-content:space-between;align-items:center}
  .chip{font:800 26px/1 "Archivo";letter-spacing:.14em;text-transform:uppercase;background:var(--yellow);color:#14161a;padding:14px 20px;border-radius:999px}
  .count{font:700 30px/1 "Archivo";letter-spacing:.06em;color:var(--ink);background:rgba(0,0,0,.45);padding:12px 18px;border-radius:999px}
  .main{margin-top:auto;display:flex;flex-direction:column;gap:22px}
  .kicker{font:800 30px/1 "Archivo";letter-spacing:.16em;text-transform:uppercase;color:var(--yellow)}
  h1{font-family:"ArchivoBlack",Arial,sans-serif;font-weight:400;letter-spacing:-.01em}
  h1.cover{font-size:${tall ? 104 : 94}px;line-height:1.02;text-wrap:balance}
  h1.end{font-size:${tall ? 92 : 84}px;line-height:1.04;text-wrap:balance}
  .swipe{font:700 34px/1 "Archivo";color:var(--muted);margin-top:8px}.swipe span{color:var(--yellow)}
  .label{font:800 26px/1 "Archivo";letter-spacing:.18em;text-transform:uppercase;padding:10px 16px;border-radius:8px;align-self:flex-start}
  .myth-l{background:rgba(255,107,91,.18);color:var(--red);border:2px solid var(--red)}
  .fact-l{background:var(--yellow);color:#14161a;margin-top:18px}
  .myth{font:700 ${tall ? 50 : 46}px/1.18 "Archivo";color:rgba(255,255,255,.82);text-decoration:line-through;text-decoration-color:var(--red);text-decoration-thickness:5px;text-wrap:balance}
  .fact{font:600 ${tall ? 44 : 40}px/1.28 "Archivo";color:var(--ink);text-wrap:pretty}
  .src{font:500 24px/1.3 "Archivo";color:var(--muted);margin-top:6px}
  .cta{font:800 38px/1.2 "Archivo";color:var(--yellow)}
  .srclist{display:flex;flex-direction:column;gap:6px;font:500 22px/1.3 "Archivo";color:var(--muted);margin-top:18px}.srclist b{font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:20px;color:var(--ink)}
  .foot{margin-top:34px;display:flex;justify-content:space-between;font:700 26px/1 "Archivo";color:var(--muted)}
  </style></head><body><div class="bg"></div><div class="veil"></div>
  <div class="wrap">${top}<div class="main">${body}</div><div class="foot"><span>Hidden In Your Home</span></div></div></body></html>`;
}

const sizes = { ig: [1080, 1350], tt: [1080, 1920] };
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "carousel-"));
for (const key of which === "both" ? ["ig", "tt"] : [which]) {
  const [W, H] = sizes[key]; const dir = path.join(outDir, key); fs.mkdirSync(dir, { recursive: true });
  cfg.slides.forEach((s, i) => {
    if (!fs.existsSync(path.resolve(base, s.bg))) throw new Error(`missing background ${s.bg}`);
    const html = path.join(tmp, `${key}-${i}.html`); fs.writeFileSync(html, page(s, i, W, H));
    const png = path.join(tmp, `${key}-${i}.png`);
    execFileSync(chrome, [...(isShell ? [] : ["--headless=new"]), "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
      "--allow-file-access-from-files", "--virtual-time-budget=4000", `--window-size=${W},${H}`, `--screenshot=${png}`, "file://" + html], { stdio: "ignore" });
    const out = path.join(dir, `${String(i + 1).padStart(2, "0")}.jpg`);
    execFileSync(ffmpeg, ["-loglevel", "error", "-y", "-i", png, "-q:v", "2", out]);
    console.log(out);
  });
}
