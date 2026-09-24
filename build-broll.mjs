// build-broll.mjs — shared generator: full-bleed b-roll cut on VO cue words + karaoke captions. No center text.
//   node ../_shared/build-broll.mjs <projectDir>      (reads <projectDir>/shots.mjs)
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { fx, makeTA, buildCaptions, buildBroll, renderPage } from "./gen-shared.mjs";

const proj = path.resolve(process.argv[2] || ".");
const meta = JSON.parse(fs.readFileSync(path.join(proj, "assets/vo/audio_meta.json"), "utf8"));
const VO = meta.scenes[0];
const W = 1080, H = 1920;
const BG = "#0B0D12", INK = "#F4F5F7", MUTED = "#8A8F99", ACCENT = "#F5C242", DIM = "#151923";
const VO_START = 0.35;
const TA = makeTA(VO, VO_START);
const TOTAL = fx(VO_START + VO.duration + 1.2);
if (TOTAL > 179) throw new Error(`total ${TOTAL}s exceeds the 2:59 ceiling`);

const { title, cues } = await import(pathToFileURL(path.join(proj, "shots.mjs")).href);
// cues: [[cueWord|null, shotId, "clip"?], ...] — chained: each cue is the next occurrence after the previous one
let t = -1;
const SHOTS = cues.map(([word, id, kind], i) => {
  const at = i === 0 ? 0 : (t = TA(word, t));
  if (i === 0) t = 0;
  const img = `assets/broll/${id}.jpg`;
  if (!fs.existsSync(path.join(proj, img))) throw new Error(`missing still ${img}`);
  return kind === "clip" && fs.existsSync(path.join(proj, `assets/footage/${id}.mp4`))
    ? { at, clip: `assets/footage/${id}.mp4`, fallback: img } : { at, img };
});
for (let i = 1; i < SHOTS.length; i++) if (SHOTS[i].at <= SHOTS[i - 1].at) throw new Error(`cue order broken at shot ${i}`);

const tl = [];
const broll = buildBroll({ SHOTS, TOTAL, proj });
tl.push(...broll.tl);
const { caps, tlLines } = buildCaptions(VO, VO_START);
tl.push(...tlLines);

const rootHTML = [...broll.html, `<div id="topfade"></div>`, `<div id="scrim"></div>`].join("\n  ");
const page = renderPage({ W, H, BG, INK, MUTED, ACCENT, DIM, TOTAL, bodyHTML: "", rootHTML, tl, caps, VO, VO_START, title });
fs.writeFileSync(path.join(proj, "index.html"), page);
const longest = SHOTS.map((s, i) => fx((SHOTS[i + 1]?.at ?? TOTAL) - s.at));
console.log(`wrote index.html  total=${TOTAL}s  shots=${SHOTS.length} (clips ${SHOTS.filter((s) => s.clip).length})  longest hold=${Math.max(...longest)}s  tweens=${tl.length}`);
