// Septic drain field Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
// Run from the episode folder after build_scene.py (it writes timeline.json). Writes editable.json + edits.json + sfx-used.json.
// Env: RENDER_ID (video asset), RENDER_MS (its duration). editable.json = the laptop's Tesseract project template (skeleton made if missing).
const fs = require("fs"), path = require("path");
const D = __dirname;
const TL = JSON.parse(fs.readFileSync(path.join(D, "timeline.json"), "utf8"));
const VOM = JSON.parse(fs.readFileSync(path.join(D, "assets/vo/audio_meta.json"), "utf8"));
const C = TL.cues, EV = TL.events, FPS = TL.fps, DUR = Math.round(TL.duration * 1000), VO = TL.vo_offset;
const VO_MS = Math.round(VOM.scenes[0].duration * 1000);
const ms = s => Math.round(s * 1000);
const A = (name, t) => TL.anchors[name][Math.max(0, Math.min(TL.frames - 1, Math.round(t * FPS)))];
const T = (pos, anchor = [0, 0], s = 100, rot = 0, op = 100) => ({ anchorPoint: anchor, position: pos, scale: [s, s], rotation: rot, opacity: op });
const R = (start, dur) => ({ start: Math.round(start), duration: Math.max(1, Math.round(dur)) });

// ---- palette + type ----
const WHITE = [1, 1, 1, 1], GOLD = [0.98, 0.74, 0.27, 1], CYAN = [0.3, 0.92, 1, 1], RED = [1, 0.3, 0.24, 1], INK = [0, 0, 0, 1];
const DISPLAY = { fontFamily: "Poppins", fontStyle: "ExtraBold" }, BODY = { fontFamily: "Poppins", fontStyle: "ExtraBold" };
let NEXT_ID = 100; const id = () => NEXT_ID++;
const layers = [], edits = [], audio = [];
const kf = (layerId, prop, keys) => edits.push({ type: "setFxPropertyKeyframes", compositionId: "main", property: { layerId, propertyType: prop },
  keyframes: keys.map(([t, v, e], i) => ({ id: `L${layerId}-${prop}-${i}`, layerTime: Math.round(t), value: { type: "float", value: v },
    easing: e === "hold" ? { type: "hold" } : e === "lin" ? { type: "linear" } : { type: "cubicBezier", x1: 0.2, y1: 0, x2: 0.1, y2: 1 } })) });

function text(str, x, y, w, h, size, color, font = DISPLAY, opts = {}) {
  if (!opts.local) { const x0 = Math.max(60, x - w / 2), x1 = Math.min(950, x + w / 2); x = (x0 + x1) / 2; w = x1 - x0; }   // keep inside the platform safe area (labels use group-local coords)
  return { type: "Text", id: id(), name: opts.name || `Type - ${str.replace(/\n/g, " ")}`, blendMode: "normal",
    activeRange: R(0, 1000), transform: T([x, y], [w / 2, h / 2]),
    sourceText: { text: str, ...font, fontSize: size, fillColor: color, applyStroke: !!opts.stroke, strokeColor: INK, strokeWidth: opts.stroke || 0,
      strokeOverFill: false, justification: opts.just || "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h],
      verticalAlign: "center", tracking: opts.tracking ?? (font === DISPLAY ? -10 : 20), leading: opts.leading ?? size * 1.05 } };
}
function rect(name, w, h, color, opts = {}) {
  return { type: "Rect", id: id(), name, blendMode: "normal", activeRange: R(0, 1000),
    transform: T(opts.pos || [0, 0], opts.anchor || [0, h / 2], 100, opts.rot || 0),
    rect: { size: [w, h], fillColor: color, roundness: opts.round || 0 } };
}
const TITLES = [];
function show(layer, t0, t1, style = "pop", sfx = null) {
  layer.activeRange = R(ms(t0), ms(t1 - t0));
  if (!layer.sourceText.applyStroke) Object.assign(layer.sourceText, { applyStroke: true, strokeWidth: layer.sourceText.fontSize < 80 ? 8 : 6 });   // legible over gold steel and pale chalk
  const d = ms(t1 - t0);
  if (style === "pop") { kf(layer.id, "scaleX", [[0, 72], [160, 106], [260, 100]]); kf(layer.id, "scaleY", [[0, 72], [160, 106], [260, 100]]); }
  if (style === "slam") { kf(layer.id, "scaleX", [[0, 165], [150, 96], [240, 100]]); kf(layer.id, "scaleY", [[0, 165], [150, 96], [240, 100]]); }
  if (style === "rise") { const y = layer.transform.position[1]; kf(layer.id, "positionY", [[0, y + 50], [260, y]]); }
  kf(layer.id, "opacity", [[0, 0], [110, 100], [Math.max(120, d - 180), 100], [d, 0]]);
  layers.push(layer); TITLES.push({ t0, t1, text: layer.sourceText.text });
  if (sfx) sound(sfx, t0);
  return layer;
}
// ---- SFX (ui-* = the laptop's existing UI kit; the rest come from synth_sfx.js in this folder) ----
function sound(name, t, vol = null, peak = 0) {        // peak: seconds from file start to the perceptual hit
  const f = SFXF[name]; audio.push({ name, start: Math.max(0, t - peak), vol: vol ?? f.vol, ms: f.ms });
}
const SFXF = {
  pop: { file: "ui-soft-pop", ms: 180, vol: 0.55 }, tick: { file: "ui-dry-click", ms: 65, vol: 0.5 }, ping: { file: "ui-clear-ping", ms: 480, vol: 0.45 },
  whoosh: { file: "ui-air-whoosh", ms: 500, vol: 0.5 }, impact: { file: "ui-soft-impact", ms: 450, vol: 0.75 }, riser: { file: "ui-short-riser", ms: 1100, vol: 0.4 },
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.32 }, rush: { file: "water-rush", ms: 3000, vol: 0.3 },
  crumble: { file: "dust-crumble", ms: 1000, vol: 0.5 }, setping: { file: "set-ping", ms: 1000, vol: 0.4 }, sewer: { file: "sewer-drip", ms: 3000, vol: 0.3 },
  yard: { file: "yard-air", ms: 3000, vol: 0.3 }, drip: { file: "drip-plink", ms: 300, vol: 0.35 }, car: { file: "car-thud", ms: 1000, vol: 0.7 },
  squelch: { file: "mud-squelch", ms: 1200, vol: 0.5 }, gurgle: { file: "gurgle-rise", ms: 2000, vol: 0.5 },
};
// ================= TYPOGRAPHY =================
const SAFE = { top: 200, bottom: 1500, right: 950, left: 60 };
const TOP_Y = 352;            // type band centre (y 202-502 for two-line titles)
function tracked(label, anchorName, t0, t1, dx, dy, color = GOLD, sfx = "pop") {
  // end the label when its 3D anchor leaves the frame (camera moves / cuts); skip it if that leaves too little time
  for (let t = t0; t < t1; t += 1 / FPS) { const p = A(anchorName, t); if (p[0] < 40 || p[0] > 1040 || p[1] < 300 || p[1] > 1400) { t1 = t; break; } }
  if (t1 - t0 < 0.6) { console.log("label skipped (anchor off screen):", label); return null; }
  const g = { type: "Group", id: id(), name: `Label - ${label}`, blendMode: "normal", activeRange: R(ms(t0), ms(t1 - t0)), transform: T([0, 0]), layers: [] };
  const tw = Math.max(220, label.length * 33 + 70), th = 64;
  let minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
  for (let t = t0; t <= t1; t += 0.2) { const p = A(anchorName, t); minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]); minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]); }
  if (dx > 0 && maxX + dx + tw > SAFE.right) dx = -dx; else if (dx < 0 && minX + dx - tw < SAFE.left) dx = -dx;
  if (dy < 0 && minY + dy - th < 520) dy = -dy; else if (dy > 0 && maxY + dy + th > 1300) dy = -dy;
  // left edge of the label relative to the anchor, kept inside the safe box for the whole time the anchor moves
  const lo = SAFE.left + 10 - minX, hi = SAFE.right - 10 - tw - maxX;
  let o = dx < 0 ? dx - tw : dx;
  o = lo <= hi ? Math.max(lo, Math.min(hi, o)) : (lo + hi) / 2;
  const ex = Math.max(o, Math.min(o + tw, 0)) === 0 ? 0 : (o > 0 ? o : o + tw);    // leader ends on the near edge of the pill
  const len = Math.max(1, Math.hypot(ex, dy)), rot = Math.atan2(dy, ex) * 180 / Math.PI;
  const dot = rect(`${label} dot`, 18, 18, color, { anchor: [9, 9], round: 9 });
  const line = rect(`${label} leader`, len, 4, color, { anchor: [0, 2], rot });
  const txt = text(label, o + tw / 2, dy, tw, th, 40, color, BODY, { tracking: 60, name: `${label} text`, local: true });
  const pill = rect(`${label} backing`, tw, th, [0, 0, 0, 0.55], { pos: [o, dy], anchor: [0, th / 2], round: 14 });
  for (const l of [txt, pill, line, dot]) { l.activeRange = R(0, ms(t1 - t0)); g.layers.push(l); }
  const d = ms(t1 - t0);
  kf(dot.id, "scaleX", [[0, 0], [160, 100]]); kf(dot.id, "scaleY", [[0, 0], [160, 100]]);
  kf(line.id, "scaleX", [[60, 0], [300, 100]]);
  for (const l of [txt, pill]) kf(l.id, "opacity", [[180, 0], [330, 100]]);
  kf(g.id, "opacity", [[0, 100], [Math.max(10, d - 200), 100], [d, 0]]);
  const px = [], py = [];
  for (let t = t0; t <= t1 + 1e-6; t += 2 / FPS) { const p = A(anchorName, t); px.push([ms(t - t0), p[0], "lin"]); py.push([ms(t - t0), p[1], "lin"]); }
  kf(g.id, "positionX", px); kf(g.id, "positionY", py);
  layers.push(g); TITLES.push({ t0, t1, text: label }); if (sfx) sound(sfx, t0 + 0.05);
  return g;
}
// counter: a spoken number counting up on its word (one text layer per step)
function counter(n0, n1, t0, t1, fmt, x, y, w, h, size, color, sfxEvery = 2, step = 1) {
  const steps = Math.round((n1 - n0) / step), cd = Math.min(0.5, (t1 - t0) * 0.3);
  for (let k = 0; k <= steps; k++) {
    const a = t0 + cd * k / (steps + 1), b = k === steps ? t1 : t0 + cd * (k + 1) / (steps + 1);
    const l = text(fmt(k === steps ? n1 : n0 + k * step), x, y, w, h, size, color);
    l.activeRange = R(ms(a), ms(b - a));
    Object.assign(l.sourceText, { applyStroke: true, strokeWidth: 6 });
    if (k === steps) { kf(l.id, "scaleX", [[0, 118], [160, 100]]); kf(l.id, "scaleY", [[0, 118], [160, 100]]); kf(l.id, "opacity", [[Math.max(10, ms(b - a) - 180), 100], [ms(b - a), 0]]); }
    layers.push(l);
    if (k < steps && k % sfxEvery === 0) sound("tick", a, 0.35);
  }
  TITLES.push({ t0, t1, text: fmt(n1) }); sound("ping", t0 + cd, 0.4);
}
// ambience per set: room tone + hum indoors, wind outdoors, line buzz near the wires
const bed = (name, a, b, vol, step = 2.9) => { for (let t = a; t < b - 0.4; t += step) sound(name, t, vol); };
const H = TOP_Y + 20;
const small = (str, t0, t1, color = WHITE) => { const l = text(str, 540, 1240, 880, 70, 40, color, BODY, { stroke: 8, tracking: 20, name: "Note - " + str });
  l.activeRange = R(ms(t0), ms(t1 - t0)); kf(l.id, "opacity", [[0, 0], [150, 100], [Math.max(160, ms(t1 - t0) - 150), 100], [ms(t1 - t0), 0]]); layers.push(l); TITLES.push({ t0, t1, text: str }); };
const GREEN = [0.55, 1, 0.35, 1];
// ambience: outdoor air everywhere, soft underground drips while we are below the lawn
bed("yard", 0, TL.duration - 0.8, 0.22);
bed("sewer", C.drips, C.but - 0.2, 0.18);
// flows + mechanical events
bed("rush", EV.flow[0], EV.flow[1] - 0.3, 0.22); bed("rush", C.liquid, C.one2 - 0.2, 0.2); bed("rush", EV.share, C.drips, 0.2);
for (const [a, b] of EV.drips) for (let t = a + 0.2; t < b - 0.2; t += 0.55) sound("drip", t, 0.28);
sound("setping", EV.level, 0.35);
sound("car", EV.car_land, 0.7); sound("crumble", EV.crush, 0.5);
sound("gurgle", EV.rise[0], 0.5); bed("rush", EV.rise[0] + 1.0, EV.rise[1], 0.18);
sound("squelch", EV.mud[0], 0.5); sound("squelch", EV.mud[0] + 1.3, 0.35);
sound("squelch", EV.puddles[0] + 0.2, 0.4);
// B1 hook: the claim on screen from frame 0
show(text("UNDER\nYOUR LAWN", 540, H, 980, 300, 128, WHITE), 0.0, C.leaking - 0.1, "slam", "impact");
tracked("SEPTIC TANK", "tank", 0.6, C.leaking - 0.1, 70, 170, GOLD, null);
show(text("PIPES FULL\nOF HOLES", 540, H, 980, 300, 118, GOLD), C.leaking - 0.05, C.purpose - 0.1, "slam", "impact");
show(text("ON PURPOSE", 540, TOP_Y, 980, 200, 124, CYAN), C.purpose - 0.05, C.if2 - 0.1, "pop", "ping");
// B2 stake
show(text("IF THEY CLOG...", 540, TOP_Y, 980, 200, 104, WHITE), C.if2 - 0.05, C.sewage - 0.1, "rise", "whoosh");
show(text("SEWAGE\nCOMES BACK UP", 540, H, 980, 300, 108, RED), C.sewage - 0.05, C.more - 0.1, "slam", "deny");
// B3 one in five homes
show(text("1 IN 5\nU.S. HOMES", 540, H, 980, 300, 124, GOLD), C.one - 0.05, C.liquid - 0.1, "slam", "impact");
small("U.S. EPA: MORE THAN 1 IN 5 HOMES USE SEPTIC", C.five, C.liquid - 0.1, WHITE);
// B4 tank -> downhill -> distribution box
tracked("SEPTIC TANK", "tank", C.liquid + 0.05, C.downhill - 0.1, 80, -170, GOLD, "pop");
show(text("DOWNHILL", 540, TOP_Y, 980, 200, 124, WHITE), C.downhill - 0.05, C.concrete - 0.1, "rise", "whoosh");
tracked("DISTRIBUTION BOX", "dbox", C.concrete - 0.05, C.one2 - 0.1, 70, -180, GOLD, "pop");
show(text("A SMALL\nCONCRETE BOX", 540, H, 980, 300, 108, WHITE), C.concrete - 0.05, C.one2 - 0.1, "pop", null);
// B5 plan view: one outlet per trench, dead level, equal share
show(text("1 OUTLET\nPER TRENCH", 540, H, 980, 300, 112, WHITE), C.one2 - 0.05, C.dead - 0.1, "pop", "pop");
show(text("DEAD LEVEL", 540, TOP_Y, 980, 200, 128, CYAN), C.dead - 0.05, C.equal - 0.1, "slam", null);
show(text("EQUAL SHARE", 540, TOP_Y, 980, 200, 124, GOLD), C.equal - 0.05, C.then - 0.1, "pop", "pop");
// B6 the pipe: 4 inches, laid flat in gravel, holes down
show(text("4 INCHES WIDE", 540, TOP_Y, 980, 200, 112, GOLD), C.four - 0.05, C.laid - 0.1, "slam", "impact");
show(text("LAID FLAT", 540, TOP_Y, 980, 200, 124, WHITE), C.laid - 0.05, C.trenches - 0.1, "pop", null);
show(text("IN TRENCHES\nOF GRAVEL", 540, H, 980, 300, 108, WHITE), C.trenches - 0.05, C.holes2 - 0.1, "pop", "pop");
tracked("GRAVEL", "gravel", C.trenches + 0.05, C.holes2 - 0.1, 60, 170, WHITE, null);
show(text("HOLES\nPOINTING DOWN", 540, H, 980, 300, 108, GOLD), C.holes2 - 0.05, C.drips - 0.1, "slam", "impact");
// B7 drips into the soil, the real cleaning
show(text("DRIPS INTO\nTHE SOIL", 540, H, 980, 300, 112, CYAN), C.drips - 0.05, C.cleaning - 0.1, "rise", "whoosh");
show(text("THE REAL\nCLEANING", 540, H, 980, 300, 120, WHITE), C.cleaning - 0.05, C.packed - 0.1, "slam", "impact");
// B8 bacteria
show(text("PACKED WITH\nBACTERIA", 540, H, 980, 300, 108, GREEN), C.packed - 0.05, C.within - 0.1, "pop", "ping");
tracked("SOIL BACTERIA", "bacteria", C.bacteria + 0.05, C.within - 0.1, 70, 170, GREEN, null);
// B9 within a few feet, most germs gone before the groundwater
show(text("A FEW FEET", 540, TOP_Y, 980, 200, 124, WHITE), C.within - 0.05, C.germs - 0.1, "pop", null);
show(text("MOST GERMS\nGONE", 540, H, 980, 300, 120, GREEN), C.germs - 0.05, C.groundwater - 0.1, "slam", "down");
tracked("GROUNDWATER", "groundwater", C.groundwater - 0.1, C.but - 0.1, 70, -170, CYAN, "pop");
// B10 bacteria need air: shallow trenches, only grass on top
show(text("THEY NEED AIR", 540, TOP_Y, 980, 200, 116, CYAN), C.bacteria2 - 0.05, C.thats - 0.1, "pop", "whoosh");
show(text("SHALLOW\nTRENCHES", 540, H, 980, 300, 116, WHITE), C.trenches2 - 0.1, C.grass - 0.1, "pop", null);
show(text("ONLY GRASS\nON TOP", 540, H, 980, 300, 116, GOLD), C.grass - 0.05, C.park - 0.1, "pop", "pop");
// B11 park a car on it
show(text("PARK ON IT...", 540, TOP_Y, 980, 200, 110, WHITE), C.park - 0.05, C.crushed - 0.1, "rise", null);
show(text("CRUSHED SOIL", 540, TOP_Y, 980, 200, 116, RED), C.crushed - 0.05, C.chokes - 0.1, "slam", "deny");
show(text("NO AIR", 540, TOP_Y, 980, 200, 140, RED), C.chokes - 0.05, C.over - 0.1, "slam", null);
// B12 the biomat
show(text("OVER THE YEARS", 540, TOP_Y, 980, 200, 104, WHITE), C.over - 0.05, C.black - 0.1, "rise", "riser");
show(text("A BLACK,\nSLIMY LAYER", 540, H, 980, 300, 112, RED), C.black - 0.05, C.slows - 0.1, "slam", "impact");
tracked("BIOMAT", "biomat", C.layer, C.skip - 0.1, 60, -170, RED, "pop");
show(text("SLOWS\nTHE WATER", 540, H, 980, 300, 116, WHITE), C.slows - 0.05, C.skip - 0.1, "pop", "down");
// B13 skip pumping
show(text("SKIP PUMPING", 540, TOP_Y, 980, 200, 112, RED), C.skip - 0.05, C.solids - 0.1, "slam", "impact");
tracked("SLUDGE", "sludge", C.skip + 0.1, C.solids - 0.1, 70, 170, [0.8, 0.55, 0.3, 1], null);
show(text("SOLIDS\nWASH OUT", 540, H, 980, 300, 116, WHITE), C.solids - 0.05, C.clog2 - 0.1, "pop", "whoosh");
show(text("CLOGS FASTER", 540, TOP_Y, 980, 200, 112, RED), C.clog2 - 0.05, C.nowhere - 0.1, "slam", "deny");
// B14 nowhere to go but up
show(text("NOWHERE TO GO\nBUT UP", 540, H, 980, 300, 104, RED), C.nowhere - 0.05, C.grass2 - 0.1, "slam", "impact");
// B15 warning signs
show(text("BRIGHT GREEN,\nSPONGY GRASS", 540, H, 980, 300, 100, GOLD), C.grass2 - 0.05, C.dry - 0.1, "pop", "pop");
show(text("EVEN IN\nDRY WEATHER", 540, H, 980, 300, 108, WHITE), C.dry - 0.05, C.sewage2 - 0.1, "pop", null);
show(text("SEWAGE\nSURFACES", 540, H, 980, 300, 120, RED), C.sewage2 - 0.05, C.do - 0.1, "slam", "deny");
small("WARNING SIGNS: WA DEPT. OF HEALTH, U.S. EPA", C.grass2, C.do - 0.1, WHITE);
// CTA: spoken question as the closing title, NEXT small over the last 2 s, fade out
show(text("DO YOU KNOW WHERE\nYOUR DRAIN FIELD IS?", 540, H, 980, 300, 84, WHITE), C.do - 0.05, TL.duration, "slam", "impact");
tracked("DRAIN FIELD", "field", C.drain, TL.duration - 2.1, 60, 170, CYAN, "ping");
show(text("TELL ME IN THE COMMENTS", 540, H + 230, 980, 110, 56, GOLD, BODY, { tracking: 10 }), C.tell - 0.05, TL.duration, "pop", "ping");
{ const nx = text("NEXT: THE NOTCH ON YOUR IRON", 540, 1240, 880, 70, 40, WHITE, BODY, { stroke: 8, tracking: 20, name: "Next tease" });
  const t0 = TL.duration - 2.0; nx.activeRange = R(ms(t0), DUR - ms(t0)); kf(nx.id, "opacity", [[0, 0], [150, 100]]); layers.push(nx); TITLES.push({ t0, t1: TL.duration, text: nx.sourceText.text }); }
{ const fo = rect("Fade out", 1080, 1920, [0, 0, 0, 1], { pos: [540, 960], anchor: [540, 960] }); const t0 = TL.duration - 0.8;
  fo.activeRange = R(ms(t0), DUR - ms(t0)); kf(fo.id, "opacity", [[0, 0], [ms(0.8), 100]]); layers.push(fo); }
// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(septic|sewage|lawn|holes|tank|box|trench|level|gravel|soil|bacteria|germs|groundwater|air|grass|black|slimy|solids|clog|drain|field)/i;
const SYN = { "one": "1", "five": "5", "four": "4", "outlet": "outlet", "trench,": "trench" };
const STOP = ["about", "so", "it's", "isn't", "can", "that's", "the", "and", "you", "your", "its", "for", "are", "this", "they", "from", "with", "into", "that", "would", "did", "was", "one", "there's", "it", "but", "how", "yours"];
const toks = str => str.toLowerCase().replace(/,/g, "").split(/[^a-z0-9']+/).filter(w => w.length > 2 || /^\d+$/.test(w))
  .map(w => SYN[w] || w).filter(w => !STOP.includes(w));
// drop when most of the caption's words are already on screen in a title or label
const dupOfTitle = (str, s, e) => { const c = toks(str); if (!c.length) return false;
  return TITLES.some(T => T.t0 < e && T.t1 > s + 0.05 && c.filter(w => toks(T.text).includes(w)).length * 2 >= c.length + (c.length > 2 ? 1 : 0)); };
let dropped = 0;
groups.forEach((g, i) => {
  const s = g[0].s, next = groups[i + 1] ? groups[i + 1][0].s : C.end, e = Math.min(next, g.at(-1).e + 0.35);
  const str = g.map(x => x.t).join(" ");
  const hl = g.some(x => HL.test(x.t.replace(/[^a-z]/gi, "")));
  if (dupOfTitle(str, s, e)) { dropped++; if (process.env.SHOW_DROPPED) console.log("drop:", str); return; }
  const cap = text(str, 510, 1395, 880, 150, 62, hl ? GOLD : WHITE, BODY, { stroke: 10, tracking: 0, name: `Caption - ${str}` });
  cap.activeRange = R(ms(s), ms(e - s));
  kf(cap.id, "scaleX", [[0, 88], [110, 100]]); kf(cap.id, "scaleY", [[0, 88], [110, 100]]); kf(cap.id, "opacity", [[0, 0], [60, 100]]);
  layers.push(cap);
});

// ================= DOCUMENT =================
const RENDER_ID = process.env.RENDER_ID || "proxy", RENDER_MS = +(process.env.RENDER_MS || DUR);
const audioLayers = [];
let aid = 2000;
audioLayers.push({ type: "Audio", id: aid++, name: "VO - Liam (Eleven v4 Turbo)", windowMs: VO_MS,
  activeRange: R(ms(VO), Math.min(DUR - ms(VO), VO_MS)), sourceRange: R(0, Math.min(DUR - ms(VO), VO_MS)),
  sourceIntrinsicDuration: VO_MS, source: { assetId: "vo" }, volume: 0.85, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, Math.min(DUR, 76000)), sourceRange: R(0, Math.min(DUR, 76000)),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.40, captionsEnabled: false });
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - septic drain field cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([540, 960], [540, 960]), source: { assetId: RENDER_ID, fit: "contain" } };
const docPath = path.join(D, "editable.json");
const doc = fs.existsSync(docPath) ? JSON.parse(fs.readFileSync(docPath, "utf8"))
  : { width: 1080, height: 1920, fps: FPS, duration: 0, composition: { id: "main", layers: [] } };   // skeleton: copy the laptop template over it
doc.duration = DUR / 1000;
doc.composition.layers = [...layers.slice().reverse(), video, ...audioLayers];
fs.writeFileSync(docPath, JSON.stringify(doc, null, 1));
fs.writeFileSync(path.join(D, "edits.json"), JSON.stringify(edits, null, 1));
fs.writeFileSync(path.join(D, "sfx-used.json"), JSON.stringify([...used].sort(), null, 1));
// safe-area report for every text layer
const off = layers.filter(l => l.type === "Text").filter(l => { const [x, y] = l.transform.position, [w, h] = l.sourceText.boxSize; return x - w / 2 < 59 || x + w / 2 > 951 || y - h / 2 < 199 || y + h / 2 > 1501; });
console.log("captions dropped as title duplicates", dropped, "| text layers outside the safe box", off.map(l => l.name));
console.log("type/caption layers", layers.length, "captions", groups.length, "audio layers", audioLayers.length, "edits", edits.length, "duration", DUR);
