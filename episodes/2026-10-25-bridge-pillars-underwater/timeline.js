// Bridge-Pillar-Cofferdam-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
const DISPLAY = { fontFamily: "Anton", fontStyle: "Regular" }, BODY = { fontFamily: "Poppins", fontStyle: "ExtraBold" };
let NEXT_ID = 100; const id = () => NEXT_ID++;
const layers = [], edits = [], audio = [];
const kf = (layerId, prop, keys) => edits.push({ type: "setFxPropertyKeyframes", compositionId: "main", property: { layerId, propertyType: prop },
  keyframes: keys.map(([t, v, e], i) => ({ id: `L${layerId}-${prop}-${i}`, layerTime: Math.round(t), value: { type: "float", value: v },
    easing: e === "hold" ? { type: "hold" } : e === "lin" ? { type: "linear" } : { type: "cubicBezier", x1: 0.2, y1: 0, x2: 0.1, y2: 1 } })) });

function text(str, x, y, w, h, size, color, font = DISPLAY, opts = {}) {
  const x0 = Math.max(60, x - w / 2), x1 = Math.min(950, x + w / 2); x = (x0 + x1) / 2; w = x1 - x0;   // keep inside the platform safe area
  return { type: "Text", id: id(), name: opts.name || `Type - ${str.replace(/\n/g, " ")}`, blendMode: "normal",
    activeRange: R(0, 1000), transform: T([x, y], [w / 2, h / 2]),
    sourceText: { text: str, ...font, fontSize: size, fillColor: color, applyStroke: !!opts.stroke, strokeColor: INK, strokeWidth: opts.stroke || 0,
      strokeOverFill: false, justification: opts.just || "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h],
      verticalAlign: "center", tracking: opts.tracking ?? 20, leading: opts.leading ?? size * 1.05 } };
}
function rect(name, w, h, color, opts = {}) {
  return { type: "Rect", id: id(), name, blendMode: "normal", activeRange: R(0, 1000),
    transform: T(opts.pos || [0, 0], opts.anchor || [0, h / 2], 100, opts.rot || 0),
    rect: { size: [w, h], fillColor: color, roundness: opts.round || 0 } };
}
const TITLES = [];
function show(layer, t0, t1, style = "pop", sfx = null) {
  layer.activeRange = R(ms(t0), ms(t1 - t0));
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
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.6 },
  river: { file: "river-flow", ms: 6000, vol: 0.35 }, clank: { file: "steel-clank", ms: 500, vol: 0.55 }, sheet: { file: "sheet-drop", ms: 400, vol: 0.45 },
  vibro: { file: "vibro-hammer", ms: 3200, vol: 0.45 }, thud: { file: "pile-thud", ms: 600, vol: 0.7 }, slurp: { file: "mud-slurp", ms: 700, vol: 0.5 },
  pour: { file: "concrete-pour", ms: 7600, vol: 0.4 }, pump: { file: "pump-drone", ms: 4000, vol: 0.4 }, drain: { file: "water-drain", ms: 2600, vol: 0.45 },
  rush: { file: "water-rush", ms: 1800, vol: 0.5 }, creak: { file: "steel-creak", ms: 1400, vol: 0.45 }, knock: { file: "wood-knock", ms: 400, vol: 0.6 },
  splash: { file: "splash", ms: 900, vol: 0.45 },
};

// ================= TYPOGRAPHY =================
const SAFE = { top: 200, bottom: 1500, right: 950, left: 60 };
const TOP_Y = 352;            // type band centre (y 202-502 for two-line titles)
function tracked(label, anchorName, t0, t1, dx, dy, color = GOLD, sfx = "pop") {
  const g = { type: "Group", id: id(), name: `Label - ${label}`, blendMode: "normal", activeRange: R(ms(t0), ms(t1 - t0)), transform: T([0, 0]), layers: [] };
  const tw = Math.max(220, label.length * 30 + 60), th = 64;
  let minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
  for (let t = t0; t <= t1; t += 0.2) { const p = A(anchorName, t); minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]); minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]); }
  if (dx > 0 && maxX + dx + tw > SAFE.right) dx = -dx; else if (dx < 0 && minX + dx - tw < SAFE.left) dx = -dx;
  if (dy < 0 && minY + dy - th < 520) dy = -dy; else if (dy > 0 && maxY + dy + th > 1300) dy = -dy;
  const len = Math.hypot(dx, dy), rot = Math.atan2(dy, dx) * 180 / Math.PI;
  const dot = rect(`${label} dot`, 18, 18, color, { anchor: [9, 9], round: 9 });
  const line = rect(`${label} leader`, len, 4, color, { anchor: [0, 2], rot });
  const txt = text(label, dx + (dx < 0 ? -tw / 2 : tw / 2), dy, tw, th, 40, color, BODY, { tracking: 60, name: `${label} text` });
  const pill = rect(`${label} backing`, tw, th, [0, 0, 0, 0.55], { pos: [dx + (dx < 0 ? -tw : 0), dy], anchor: [0, th / 2], round: 14 });
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
// B1 hook
show(text("HOW DO YOU BUILD\nIN A RIVER?", 540, TOP_Y, 980, 300, 112, WHITE), C.how, C.leave - 0.75, "rise", "whoosh");
tracked("NEW PILLAR HERE", "marker", C.pillar, C.lets - 0.1, 120, -170, GOLD);
show(text("MAKE THE RIVER\nLEAVE", 540, TOP_Y, 980, 300, 128, GOLD), C.leave - 0.72, C.open + 0.3, "slam", "impact");
// B2 cut open
sound("riser", C.lets, 0.35, 1.05); sound("splash", C.open, 0.55); sound("whoosh", C.open, 0.45, 0.25);
// B3 frame
tracked("STEEL FRAME", "frame", C.frame, C.around - 0.2, -160, -150, GOLD);
sound("clank", EV.frame_land, 0.6);
// B4 sheets from the corners
show(text("STEEL SHEETS", 540, TOP_Y, 900, 180, 140, WHITE), C.sheets, C.edges - 0.15, "slam", "impact");
show(text("CORNERS FIRST", 540, TOP_Y + 120, 900, 90, 60, GOLD, BODY, { tracking: 80 }), C.corners, C.edges - 0.15, "rise");
EV.sheet_set.slice().sort((a, b) => a - b).forEach((t, i) => sound("sheet", t, 0.32 + 0.04 * (i % 3)));
// B5 interlock + vibro hammer
tracked("EDGES LOCK", "sheet", C.edges, C.vibrating - 0.1, 180, -120, CYAN, "tick");
sound("clank", C.lock, 0.5);
tracked("VIBRATING HAMMER", "hammer", C.hammer, C.this - 0.25, 160, 120, GOLD);
sound("vibro", C.drives - 0.1, 0.45);
// B6 cofferdam
show(text("COFFERDAM", 540, TOP_Y, 900, 200, 170, GOLD), C.cofferdam, C.water - 0.1, "slam", "impact");
// B7 pressure
show(text("WATER PUSHES IN", 540, TOP_Y, 980, 160, 110, CYAN), C.pushes, C.frame2 - 0.1, "rise", "whoosh");
sound("creak", C.every, 0.45);
show(text("THE FRAME\nHOLDS IT", 540, TOP_Y, 980, 300, 128, GOLD), C.frame2, C.next - 0.15, "slam", "impact");
// B8 dig + piles
tracked("SOFT MUD", "mud", C.next + 0.2, C.dig + 0.4, 150, 130, [0.85, 0.65, 0.45, 1]);
EV.mud_lift.forEach(t => sound("slurp", t, 0.4));
tracked("FOUNDATION PILES", "piles", C.piles, C.but - 0.15, 150, -130, GOLD);
EV.pile_land.forEach(t => sound("splash", t - 0.15, 0.25));
EV.pile_blow.forEach(t => sound("thud", t, 0.6));
// B9 not yet
show(text("NOT YET", 540, TOP_Y, 900, 200, 180, RED), C.pump, C.so - 0.15, "slam", "deny");
sound("drain", C.pump - 0.1, 0.3);
show(text("WATER COMES UP\nFROM BELOW", 540, TOP_Y + 190, 980, 140, 56, RED, BODY, { tracking: 40, leading: 64 }), C.water2, C.so - 0.15, "rise");
sound("rush", C.water2, 0.45); sound("deny", C.below, 0.55);
// B10 tremie
show(text("CONCRETE\nUNDERWATER", 540, TOP_Y, 980, 300, 124, WHITE), C.pour, C.end - 0.15, "rise", "whoosh");
sound("clank", C.pour, 0.4); sound("pour", C.concrete, 0.4);
tracked("PIPE END STAYS BURIED", "pipe_end", C.end, C.this2 - 0.2, 140, 140, GOLD);
show(text("CONCRETE RISES,\nWATER GOES UP", 540, TOP_Y, 980, 300, 104, CYAN), C.rises, C.this2 - 0.15, "rise", "pop");
// B11 seal + 15 ft
show(text("THE SEAL", 540, TOP_Y, 900, 200, 170, CYAN), C.seal, C.kentucky - 0.1, "slam", "impact");
tracked("SEAL", "seal", C.seal, C.weight - 0.1, 140, -150, CYAN);
const ft = text("15", 540, TOP_Y - 30, 600, 230, 210, GOLD, DISPLAY, { name: "Feet counter" });
show(ft, C.fifteen, C.weight - 0.15, "pop", "impact");
edits.push({ type: "setFxPropertyAnimator", compositionId: "main", property: { layerId: ft.id, propertyType: "textContent" }, dependencies: [],
  animator: { type: "jsScript", layerTimeJsCode: "var p = Math.min(1, input.time.seconds / 0.7); p = 1 - Math.pow(1 - p, 3); return String(Math.max(1, Math.round(15 * p)));" } });
for (let i = 0; i < 6; i++) sound("tick", C.fifteen + 0.05 + i * 0.11, 0.35);
show(text("FEET THICK", 540, TOP_Y + 120, 900, 90, 64, WHITE, BODY, { tracking: 80 }), C.thick, C.weight - 0.15, "rise");
show(text("ONE KENTUCKY BRIDGE", 540, TOP_Y + 200, 900, 70, 44, GOLD, BODY, { tracking: 60 }), C.kentucky, C.weight - 0.15, "rise", "pop");
// dimension bar on the seal (seal_top -> seal_bottom anchors, drawn just left of the right wall)
{
  const t0 = C.fifteen, t1 = C.weight - 0.1, top = A("seal_top", t0 + 0.3), bot = A("seal_bottom", t0 + 0.3);
  const x = Math.min(SAFE.right - 30, top[0] - 40), h = Math.max(20, bot[1] - top[1]);
  const bar = rect("Seal dimension bar", 8, h, GOLD, { pos: [x, top[1]], anchor: [4, 0] });
  const capT = rect("Seal dim cap top", 44, 8, GOLD, { pos: [x - 22, top[1]], anchor: [0, 4] });
  const capB = rect("Seal dim cap bottom", 44, 8, GOLD, { pos: [x - 22, bot[1]], anchor: [0, 4] });
  for (const l of [bar, capT, capB]) { l.activeRange = R(ms(t0), ms(t1 - t0)); kf(l.id, "opacity", [[0, 0], [150, 100], [ms(t1 - t0) - 180, 100], [ms(t1 - t0), 0]]); layers.push(l); }
  kf(bar.id, "scaleY", [[0, 0], [350, 100]]);
}
// B12 weight
show(text("ITS WEIGHT\nHOLDS IT DOWN", 540, TOP_Y, 980, 300, 118, GOLD), C.weight, C.once - 0.15, "slam", "impact");
// B13 pumps
tracked("PUMP", "pump", C.pumps, C.crew - 0.2, -160, -120, WHITE);
sound("pump", C.switch, 0.4); sound("drain", C.switch + 0.3, 0.5);
show(text("PUMP IT DRY", 540, TOP_Y, 900, 200, 150, CYAN), C.switch, C.crew - 0.15, "slam", "impact");
// B14 dry below the river
show(text("DRY,\nBELOW THE RIVER", 540, TOP_Y, 980, 300, 112, WHITE), C.dry2, C.pour2 - 0.15, "rise", "whoosh");
tracked("RIVER LEVEL", "water_out", C.below2, C.pour2 - 0.15, 150, -130, CYAN, "ping");
// B15 footing + pillar
tracked("FOOTING", "footing", C.footing, C.then - 0.15, -150, 130, GOLD);
sound("pour", C.footing - 0.1, 0.3); sound("riser", C.pillar2 - 0.2, 0.3);
show(text("PILLAR", 540, TOP_Y, 800, 200, 180, GOLD), C.pillar2, C.then - 0.15, "slam", "impact");
// B16 removal
show(text("PULL THE SHEETS", 540, TOP_Y, 980, 180, 120, WHITE), C.sheets2, C.river3 - 0.1, "rise", "whoosh");
sound("creak", C.pulled, 0.5); sound("clank", C.pulled + 0.4, 0.4);
sound("rush", C.river3, 0.6);
show(text("RIVER BACK IN", 540, TOP_Y, 980, 180, 130, CYAN), C.closes, C.romans - 0.15, "slam", "impact");
// B17 Romans
show(text("THE ROMANS", 540, TOP_Y, 900, 200, 160, GOLD), C.romans, C.same - 0.15, "slam", "impact");
show(text("2 RINGS · WOOD · CLAY", 540, TOP_Y + 130, 980, 90, 58, WHITE, BODY, { tracking: 50 }), C.rings, C.same - 0.15, "rise", "pop");
for (let i = 0; i < 8; i++) sound("knock", C.two + 0.08 + i * 0.16, 0.4);
sound("slurp", C.clay, 0.5);
// B18 recap
const rec = [["WATER OUT", C.keep, CYAN], ["BUILD DRY", C.build, GOLD]];
rec.forEach(([s, t, col], i) => show(text(s, 540, 300 + i * 150, 900, 150, 140, col), t, C.follow - 0.1, "slam", "impact"));
sound("clank", EV.deck_land, 0.7); sound("down", C.build - 0.2, 0.4);
// B19 CTA
show(text("FOLLOW", 540, 330, 800, 200, 160, GOLD), C.follow, C.end_t, "slam", "ping");
show(text("HIDDEN IN YOUR HOME", 540, 470, 860, 80, 46, WHITE, BODY, { tracking: 110 }), C.follow + 0.25, C.end_t, "rise", "pop");

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(cofferdam|frame|sheets|corners|edges|lock|hammer|mud|piles|seal|pipe|concrete|weight|pumps|dry|footing|pillar|romans|clay|fifteen)/i;
const SYN = { fifteen: "15", two: "2", pumps: "pump", sheets: "sheets", rings: "rings" };
const STOP = ["the", "and", "you", "your", "its", "for", "are", "this", "they", "from", "with", "into", "that", "can't", "would", "did", "was", "one"];
const toks = str => str.toLowerCase().replace(/,/g, "").split(/[^a-z0-9']+/).filter(w => w.length > 2 || /^\d+$/.test(w))
  .map(w => SYN[w] || w).filter(w => !STOP.includes(w));
// drop when most of the caption's words are already on screen in a title or label
const dupOfTitle = (str, s, e) => { const c = toks(str); if (!c.length) return false;
  return TITLES.some(T => T.t0 < e && T.t1 > s + 0.05 && c.filter(w => toks(T.text).includes(w)).length * 2 >= c.length + (c.length > 2 ? 1 : 0)); };
let dropped = 0;
groups.forEach((g, i) => {
  const s = g[0].s, next = groups[i + 1] ? groups[i + 1][0].s : C.end_t, e = Math.min(next, g.at(-1).e + 0.35);
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
  sourceIntrinsicDuration: VO_MS, source: { assetId: "vo" }, volume: 0.86, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, DUR), sourceRange: R(0, DUR),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.30, captionsEnabled: false });
sound("river", 0.0, 0.32);                                    // river ambience under the hook
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - cofferdam cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([0, 0]), source: { assetId: RENDER_ID, fit: "contain" } };
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
