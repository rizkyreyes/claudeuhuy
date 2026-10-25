// Septic-Tank-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  if (!opts.local) { const x0 = Math.max(60, x - w / 2), x1 = Math.min(950, x + w / 2); x = (x0 + x1) / 2; w = x1 - x0; }   // keep inside the platform safe area (labels use group-local coords)
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
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.6 },
  trickle: { file: "pipe-trickle", ms: 6000, vol: 0.2 }, flush: { file: "drain-flush", ms: 1600, vol: 0.45 }, slab: { file: "slab-drop", ms: 900, vol: 0.6 },
  plop: { file: "solid-plop", ms: 250, vol: 0.35 }, bubble: { file: "fat-bubble", ms: 300, vol: 0.3 }, fizz: { file: "bacteria-fizz", ms: 2500, vol: 0.3 },
  glug: { file: "gallon-glug", ms: 900, vol: 0.5 }, lift: { file: "earth-lift", ms: 1000, vol: 0.5 }, drip: { file: "drip", ms: 200, vol: 0.3 },
  truck: { file: "truck-arrive", ms: 2600, vol: 0.45 }, pump: { file: "vac-pump", ms: 1600, vol: 0.5 }, stone: { file: "stone-lid", ms: 1100, vol: 0.55 },
};

// ================= TYPOGRAPHY =================
const SAFE = { top: 200, bottom: 1500, right: 950, left: 60 };
const TOP_Y = 352;            // type band centre (y 202-502 for two-line titles)
function tracked(label, anchorName, t0, t1, dx, dy, color = GOLD, sfx = "pop") {
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
// B1 hook: the question, then the paradox answer; the closed tank shows a glowing level line on "full"
show(text("WHY DOESN'T A SEPTIC\nTANK EVER FILL UP?", 540, TOP_Y, 980, 300, 92, WHITE), C.why, C.because - 0.08, "rise", "whoosh");
show(text("IT'S ALREADY FULL", 540, TOP_Y, 980, 200, 116, CYAN), C.already - 0.05, C.lets - 0.1, "slam", "impact");
// B2 cut open: the front wall drops away
sound("riser", C.lets, 0.35, 1.05); sound("slab", C.open + 0.35, 0.55); sound("whoosh", C.open, 0.45, 0.25);
// B3 inlet + baffle
tracked("FROM THE HOUSE", "inlet", C.house - 0.1, C.baffle - 0.15, 0, -170, WHITE);
show(text("BURIED TANK", 540, TOP_Y, 980, 200, 124, WHITE), C.buried, C.baffle - 0.1, "slam", "impact");
sound("flush", C.wastewater - 0.2, 0.45);
tracked("BAFFLE", "baffle", C.baffle, C.then - 0.15, 150, -150, GOLD);
show(text("FLOW TURNS DOWN", 540, TOP_Y, 980, 200, 112, GOLD), C.turns, C.churn - 0.1, "rise", "whoosh");
show(text("NO CHURNING", 540, TOP_Y, 980, 200, 124, WHITE), C.churn, C.then - 0.1, "slam", "impact");
// B4 gravity sorts it: sludge down, scum up, clear liquid in between
show(text("GRAVITY SORTS IT", 540, TOP_Y, 980, 200, 116, WHITE), C.gravity, C.heavy - 0.1, "slam", "impact");
for (let k = 0; k < 6; k++) sound("plop", C.sink - 0.3 + k * 0.22, 0.3);
show(text("SLUDGE", 540, TOP_Y, 900, 200, 180, GOLD), C.sludge, C.grease - 0.1, "slam", "impact");
tracked("HEAVY SOLIDS", "sludge", C.solids, C.grease - 0.15, 150, 150, GOLD);
for (let k = 0; k < 5; k++) sound("bubble", C.float - 0.2 + k * 0.25, 0.28);
show(text("SCUM", 540, TOP_Y, 900, 200, 180, GOLD), C.scum, C.between - 0.1, "slam", "impact");
tracked("GREASE + OILS", "scum", C.grease, C.between - 0.15, -150, -150, GOLD);
show(text("CLEAR LIQUID", 540, TOP_Y, 980, 200, 130, CYAN), C.clear, C.bacteria - 0.1, "slam", "ping");
// B5 bacteria, no oxygen
show(text("BACTERIA", 540, TOP_Y, 900, 200, 160, WHITE), C.bacteria, C.oxygen - 0.1, "slam", "impact");
show(text("NO OXYGEN", 540, TOP_Y, 900, 200, 150, WHITE), C.oxygen, C.slowly - 0.1, "slam", "impact");
sound("fizz", C.bacteria, 0.3);
tracked("EATING SOLIDS", "bacteria", C.slowly, C.now - 0.15, 150, -150, GOLD);
// B6 the trick: the level sits at the outlet; every gallon in pushes one out
show(text("HERE'S THE TRICK", 540, TOP_Y, 980, 200, 116, GOLD), C.now, C.liquid2 - 0.1, "rise", "riser");
tracked("ALWAYS THIS LEVEL", "level", C.always, C.so - 0.15, 150, -150, CYAN, "ping");
show(text("1 GALLON IN", 540, TOP_Y, 980, 200, 124, GOLD), C.flows, C.pushes - 0.08, "slam", "impact");
show(text("1 GALLON OUT", 540, TOP_Y, 980, 200, 124, CYAN), C.pushes, C.tshaped - 0.1, "slam", "impact");
sound("glug", EV.gallon_in + 0.6, 0.5); sound("glug", EV.gallon_out + 0.3, 0.45);
// B7 T outlet draws from the middle, scum + sludge stay
tracked("T-SHAPED OUTLET", "tee", C.tshaped, C.scum2 - 0.15, -150, 150, GOLD);
show(text("FROM THE MIDDLE", 540, TOP_Y, 980, 200, 112, CYAN), C.draws, C.scum2 - 0.1, "rise", "whoosh");
show(text("SCUM + SLUDGE\nSTAY BEHIND", 540, TOP_Y, 980, 300, 112, RED), C.scum2, C.that - 0.1, "slam", "deny");
// B8 drainfield: lid lifts, pipes in gravel, lid back down
show(text("DRAINFIELD", 540, TOP_Y, 980, 200, 160, WHITE), C.drainfield, C.perforated - 0.1, "slam", "impact");
sound("lift", EV.lid_up, 0.5);
tracked("PERFORATED PIPE", "drainpipe", C.perforated, C.trenches + 0.2, 120, -170, GOLD);
tracked("GRAVEL", "gravel", C.gravel, C.lawn - 0.1, -150, -150, WHITE);
show(text("UNDER THE LAWN", 540, TOP_Y, 980, 200, 116, WHITE), C.lawn, C.trickles - 0.1, "rise", null);
sound("slab", EV.lid_down + 0.5, 0.5);
// B9 soil filters the water, germs stop, clean water reaches the groundwater
show(text("THE SOIL CLEANS IT", 540, TOP_Y, 980, 200, 104, GOLD), C.soil2, C.filtering - 0.1, "slam", "impact");
EV.drips && [0, 0.7, 1.5, 2.1, 3.0, 3.8, 4.6, 5.3].forEach(d => sound("drip", EV.drips[0] + 0.3 + d, 0.22));
show(text("GERMS FILTERED OUT", 540, TOP_Y, 980, 200, 100, RED), C.germs - 0.05, C.groundwater - 0.1, "slam", "deny");
tracked("GROUNDWATER", "groundwater", C.groundwater, C.but - 0.1, 150, -150, CYAN, "ping");
// B10 sludge builds up, 3-5 years, the pump truck
show(text("CAN'T EAT\nEVERYTHING", 540, TOP_Y, 980, 300, 112, RED), C.eat, C.sludge3 - 0.1, "slam", "deny");
show(text("SLUDGE BUILDS UP", 540, TOP_Y, 980, 200, 108, GOLD), C.sludge3, C.three - 0.1, "rise", "riser");
show(text("EVERY 3–5 YEARS", 540, TOP_Y, 980, 200, 108, WHITE), C.three, C.truck - 0.1, "slam", "impact");
sound("truck", EV.truck_in, 0.45);
tracked("PUMP TRUCK", "truck", C.truck, C.around - 0.25, 150, -150, GOLD);
sound("pump", EV.pump[0], 0.55);
// B11 history: 1860, a sealed tank, opened years later, almost no solids
sound("whoosh", EV.set_b[0], 0.5, 0.25);
const y60 = text("1860", 540, TOP_Y - 20, 600, 220, 190, GOLD, DISPLAY, { name: "Year counter 1860" });
show(y60, C.y1860, C.mouras - 0.1, "pop", "tick");
edits.push({ type: "setFxPropertyAnimator", compositionId: "main", property: { layerId: y60.id, propertyType: "textContent" }, dependencies: [],
  animator: { type: "jsScript", layerTimeJsCode: "var p = Math.min(1, input.time.seconds / 0.6); p = 1 - Math.pow(1 - p, 3); return String(Math.round(1830 + 30 * p));" } });
show(text("FRANCE", 540, TOP_Y + 150, 600, 80, 56, WHITE, BODY, { tracking: 60 }), C.frenchman, C.mouras - 0.1, "rise", "pop");
show(text("SEALED TANK", 540, TOP_Y, 980, 200, 124, WHITE), C.sealed, C.years2 - 0.1, "slam", "impact");
tracked("SEALED LID", "old_lid", C.sealed, C.opened - 0.1, 150, -150, GOLD);
show(text("YEARS LATER", 540, TOP_Y, 980, 200, 124, WHITE), C.years2, C.almost - 0.1, "rise", "whoosh");
sound("stone", EV.old_lid, 0.55);
show(text("ALMOST NO SOLIDS", 540, TOP_Y, 980, 200, 108, GOLD), C.almost, C.is - 0.1, "slam", "ping");
tracked("THIN LAYER", "old_solids", C.free, C.is - 0.1, 150, -150, GOLD, null);
// B12 CTA: a question to the viewer (comments), no channel name
show(text("IS YOUR HOME ON SEPTIC\nOR ON THE SEWER?", 540, TOP_Y, 980, 300, 84, WHITE), C.is, C.end, "slam", "whoosh");
show(text("TELL ME IN THE COMMENTS", 540, TOP_Y + 215, 900, 80, 50, GOLD, BODY, { tracking: 60 }), C.tell, C.end, "rise", "ping");

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(septic|tank|full|baffle|gravity|sludge|scum|grease|oils|clear|bacteria|oxygen|trick|outlet|gallon|t-shaped|drainfield|perforated|gravel|soil|germs|groundwater|truck|sealed|solids|sewer)/i;
const SYN = { "it's": "it", one: "1", three: "3", five: "5", "1860": "1860", pipes: "pipe", solids: "solid", trenches: "trench", germs: "germ", oils: "oils", years: "year", builds: "build" };
const STOP = ["the", "and", "you", "your", "its", "for", "are", "this", "they", "from", "with", "into", "that", "can't", "would", "did", "was", "one"];
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
  sourceIntrinsicDuration: VO_MS, source: { assetId: "vo" }, volume: 0.86, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, Math.min(DUR, 76000)), sourceRange: R(0, Math.min(DUR, 76000)),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.30, captionsEnabled: false });
for (const [a, b] of EV.flow_in.concat(EV.flow_out)) for (let t = a; t < Math.min(b, DUR / 1000) - 0.5; t += 6) sound("trickle", t, 0.16);   // water in the pipes while pulses run
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - septic cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([540, 960], [540, 960]), source: { assetId: RENDER_ID, fit: "contain" } };
// slow push-in over the CTA
for (const p of ["scaleX", "scaleY"]) kf(video.id, p, [[ms(C.is), 100, "lin"], [DUR, 106, "lin"]]);
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
