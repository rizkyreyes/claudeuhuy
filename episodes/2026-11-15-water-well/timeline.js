// Water-Well-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.6 },
  wind: { file: "wind-gust", ms: 3000, vol: 0.3 }, rush: { file: "water-rush", ms: 3000, vol: 0.4 }, hum: { file: "pump-hum", ms: 4000, vol: 0.4 },
  blip: { file: "pump-blip", ms: 450, vol: 0.5 }, powerdown: { file: "power-down", ms: 1400, vol: 0.5 }, splash: { file: "splash", ms: 1200, vol: 0.5 },
  rope: { file: "rope-creak", ms: 1200, vol: 0.35 }, birds: { file: "birds", ms: 3000, vol: 0.25 }, squeak: { file: "pump-squeak", ms: 700, vol: 0.45 },
  slurp: { file: "slurp", ms: 1600, vol: 0.45 }, drill: { file: "drill-rumble", ms: 3000, vol: 0.5 }, crumble: { file: "crumble", ms: 1400, vol: 0.6 },
  slide: { file: "pipe-slide", ms: 1800, vol: 0.5 }, rain: { file: "rain", ms: 4500, vol: 0.35 }, slurry: { file: "slurry", ms: 1400, vol: 0.5 },
  click: { file: "switch-click", ms: 120, vol: 0.5 }, spigot: { file: "spigot-stream", ms: 3000, vol: 0.4 },
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
// B1 hook: "This is a bucket" over the first shot, the claim (suction stops at 33 ft), the stake (rain down the pipe into your water)
show(text("THIS IS A BUCKET", 540, TOP_Y, 980, 200, 104, WHITE), 0.15, C.getting - 0.1, "slam", "impact");
sound("birds", 0.0, 0.2); sound("rope", 0.6, 0.35); sound("splash", EV.dip1, 0.5, 0.02);
show(text("THE HARD PART", 540, TOP_Y, 980, 200, 112, GOLD), C.getting - 0.05, C.suction - 0.1, "rise", "whoosh");
show(text("SUCTION STOPS\nAT 33 FEET", 540, TOP_Y + 20, 980, 300, 104, RED), C.suction - 0.05, C.and - 0.1, "slam", "impact");
sound("squeak", EV.col1[0] - 0.4, 0.45); sound("slurp", EV.col1[0], 0.45); sound("deny", C.feet, 0.55);
show(text("BUILT WRONG?", 540, TOP_Y, 980, 200, 116, RED), C.and - 0.05, C.rainwater - 0.1, "slam", "impact");
sound("rain", EV.rain[0][0], 0.35);
show(text("RAIN IN YOUR\nDRINKING WATER", 540, TOP_Y + 20, 980, 300, 96, RED), C.rainwater - 0.05, C.lets - 0.1, "slam", "deny");
// B2 build it up: the bucket, then the real depth
show(text("LET'S BUILD ONE", 540, TOP_Y, 980, 200, 104, WHITE), C.lets - 0.05, C.this - 0.1, "pop", "pop");
show(text("1. A BUCKET", 540, TOP_Y, 980, 200, 116, WHITE), C.this - 0.05, C.fine - 0.1, "rise", "whoosh");
sound("rope", C.this + 0.1, 0.35); sound("splash", EV.dip2, 0.5, 0.02);
tracked("BUCKET", "bucket", C.bucket + 0.1, C.fine - 0.1, 130, -170, GOLD, "pop");
show(text("FINE IF IT'S\nSHALLOW", 540, TOP_Y + 20, 980, 300, 112, GOLD), C.fine - 0.05, C.typical - 0.1, "rise", "pop");
show(text("A TYPICAL\nHOME WELL", 540, TOP_Y + 20, 980, 300, 112, WHITE), C.typical - 0.05, C.hundred - 0.1, "pop", "pop");
sound("drill", EV.deep[0], 0.5);
counter(0, 140, C.hundred - 0.05, C.so - 0.1, n => `${Math.round(n)} FEET`, 540, TOP_Y, 980, 200, 128, GOLD, 2, 10);
// B3 suction pump: it doesn't pull, air pushes, and air runs out at 33 ft
show(text("2. SUCTION PUMP", 540, TOP_Y, 980, 200, 100, WHITE), C.so - 0.05, C.doesnt - 0.1, "rise", "whoosh");
sound("squeak", C.suction2, 0.45); sound("squeak", C.suction2 + 0.75, 0.4);
show(text("IT DOESN'T PULL", 540, TOP_Y, 980, 200, 100, WHITE), C.doesnt - 0.05, C.air - 0.1, "slam", "impact");
tracked("LOW PRESSURE", "spipe", C.lowers + 0.1, C.air - 0.1, 120, -170, CYAN, "pop");
sound("slurp", EV.col2[0] + 0.1, 0.45);
show(text("AIR PUSHES\nIT UP", 540, TOP_Y + 20, 980, 300, 116, GOLD), C.air - 0.05, C.but - 0.1, "slam", "impact");
sound("wind", C.air, 0.3);
show(text("BUT AIR HAS\nA LIMIT", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.but - 0.05, C.thirtythree2 - 0.1, "rise", "whoosh");
counter(0, 33, C.thirtythree2 - 0.05, C.so2 - 0.1, n => `${Math.round(n)} FEET MAX`, 540, TOP_Y, 980, 200, 116, RED, 3, 1);
sound("deny", C.thirtythree2 + 0.5, 0.55);
// B4 electric pump at the bottom: push instead of pull
show(text("3. PUMP AT\nTHE BOTTOM", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.so2 - 0.05, C.push - 0.1, "rise", "whoosh");
sound("slide", EV.pumpdrop[0], 0.4); sound("splash", EV.pumpdrop[0] + 0.9, 0.3);
tracked("ELECTRIC PUMP", "pump", C.bottom, C.push - 0.1, 130, -170, GOLD, "pop");
show(text("PUSH,\nDON'T PULL", 540, TOP_Y + 20, 980, 300, 120, CYAN), C.push - 0.05, C.now - 0.1, "slam", "impact");
sound("hum", C.push - 0.2, 0.4); sound("rush", C.push, 0.35);
// B5 walls cave in -> casing
show(text("WALLS CAVE IN", 540, TOP_Y, 980, 200, 108, RED), C.now - 0.05, C.line - 0.1, "slam", "deny");
sound("crumble", EV.cave, 0.6);
show(text("4. THE CASING", 540, TOP_Y, 980, 200, 112, WHITE), C.line - 0.05, C.at - 0.1, "rise", "whoosh");
sound("slide", EV.casing[0], 0.5);
tracked("CASING", "casing", C.casing, C.at - 0.1, 130, -170, WHITE, "ping");
// B6 the screen: water in, sand out
show(text("5. THE SCREEN", 540, TOP_Y, 980, 200, 112, WHITE), C.at - 0.05, C.lets2 - 0.1, "rise", "whoosh");
tracked("SLOTTED SCREEN", "screen", C.screen, C.but2 - 0.1, 130, -170, CYAN, "ping");
show(text("WATER IN,\nSAND OUT", 540, TOP_Y + 20, 980, 300, 120, CYAN), C.lets2 - 0.05, C.but2 - 0.1, "slam", "impact");
sound("rush", C.lets2, 0.3);
// B7 rain down the outside -> grout seal
show(text("RAIN SEEPS\nDOWN THE SIDE", 540, TOP_Y + 20, 980, 300, 100, RED), C.but2 - 0.05, C.bacteria - 0.1, "rise", "whoosh");
sound("rain", EV.rain[1][0], 0.35);
show(text("BACTERIA", 540, TOP_Y, 980, 200, 128, RED), C.bacteria - 0.05, C.gap - 0.1, "slam", "deny");
show(text("6. GROUT SEAL", 540, TOP_Y, 980, 200, 112, GOLD), C.gap - 0.05, C.last - 0.1, "slam", "impact");
sound("slurry", EV.grout[0], 0.5);
tracked("GROUT", "grout", C.grout, C.last - 0.1, -130, 170, GOLD, "ping");
// B8 the last problem: the pump would start with every tap
show(text("LAST PROBLEM", 540, TOP_Y, 980, 200, 112, WHITE), C.last - 0.05, C.start - 0.1, "rise", "whoosh");
show(text("ON. OFF.\nON. OFF.", 540, TOP_Y + 20, 980, 300, 124, RED), C.start - 0.05, C.wear - 0.1, "pop", null);
EV.taps.slice(0, 3).forEach(([a, b]) => { sound("click", a, 0.5); sound("blip", a + 0.03, 0.5); sound("click", b, 0.4); });
show(text("WEARS IT OUT", 540, TOP_Y, 980, 200, 112, RED), C.wear - 0.05, C.so3 - 0.1, "slam", "deny");
sound("blip", C.wear, 0.55); sound("powerdown", C.out, 0.4);
// B9 pressure tank: a cushion of air
show(text("7. PRESSURE\nTANK", 540, TOP_Y + 20, 980, 300, 116, CYAN), C.so3 - 0.05, C.cushion - 0.1, "rise", "whoosh");
tracked("PRESSURE TANK", "tank", C.tank, C.cushion - 0.1, 130, -170, CYAN, "pop");
show(text("A CUSHION\nOF AIR", 540, TOP_Y + 20, 980, 300, 120, GOLD), C.cushion - 0.05, C.fills - 0.1, "slam", "impact");
tracked("AIR", "air", C.cushion + 0.2, C.more - 0.1, -130, -170, GOLD, "ping");
show(text("PUMP FILLS IT", 540, TOP_Y, 980, 200, 108, CYAN), C.fills - 0.05, C.shuts - 0.1, "rise", "whoosh");
sound("click", C.fills - 0.1, 0.5); sound("hum", C.fills - 0.1, 0.35); sound("rush", C.fills, 0.3);
show(text("PUMP OFF", 540, TOP_Y, 980, 200, 124, WHITE), C.shuts - 0.05, C.air4 - 0.1, "slam", "impact");
sound("click", C.shuts, 0.5); sound("powerdown", C.shuts + 0.05, 0.35);
show(text("AIR DOES\nTHE PUSHING", 540, TOP_Y + 20, 980, 300, 112, GOLD), C.air4 - 0.05, C.more - 0.1, "slam", "ping");
sound("spigot", EV.taps[4][0], 0.4);
// B10 pull-out: 23 million households
counter(0, 23, C.more - 0.05, C.would - 0.1, n => `${Math.round(n)} MILLION`, 540, TOP_Y - 20, 980, 200, 128, GOLD, 3, 1);
show(text("US HOUSEHOLDS", 540, TOP_Y + 150, 900, 100, 64, WHITE, BODY, { tracking: 20 }), C.households - 0.05, C.would - 0.1, "rise", "pop");
sound("whoosh", C.more, 0.4); sound("birds", C.more + 0.5, 0.25);
// B11 CTA: a question to the viewer, then the follow line naming the next episode (3d-23 pipe-under-river)
show(text("WOULD YOU DRINK\nWATER STRAIGHT\nFROM THE GROUND?", 540, TOP_Y + 40, 980, 330, 80, WHITE), C.would, C.next - 0.1, "slam", "whoosh");
show(text("TELL ME IN THE COMMENTS", 540, TOP_Y + 250, 900, 80, 50, GOLD, BODY, { tracking: 60 }), C.tell, C.next - 0.1, "rise", "ping");
show(text("NEXT:\nPIPES UNDER RIVERS", 540, TOP_Y + 20, 980, 300, 84, WHITE), C.next, C.end, "slam", "pop");
show(text("FOLLOW SO YOU DON'T MISS IT", 540, TOP_Y + 215, 940, 80, 46, GOLD, BODY, { tracking: 40 }), C.follow, C.end, "rise", "ping");
sound("spigot", EV.cta + 0.3, 0.4); sound("spigot", EV.cta + 3.2, 0.3); sound("spigot", EV.cta + 6.1, 0.25); sound("birds", C.would + 2.0, 0.2);

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(suction|pump|casing|screen|grout|bacteria|air|tank|pressure|bucket|water)/i;
const SYN = { hundred: "140", forty: "140", "140": "140", "thirty-three": "33", thirty: "33", three: "33", "33": "33", "twenty-three": "23", twenty: "23", "23": "23", feet: "feet", foot: "feet", "rainwater": "rain", "doesn't": "doesn't" };
const STOP = ["about", "so", "it's", "isn't", "can", "that's", "the", "and", "you", "your", "its", "for", "are", "this", "they", "from", "with", "into", "that", "can't", "would", "did", "was", "one"];
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
  sourceIntrinsicDuration: VO_MS, source: { assetId: "vo" }, volume: 0.80, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, Math.min(DUR, 76000)), sourceRange: R(0, Math.min(DUR, 76000)),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.40, captionsEnabled: false });
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - water well cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([540, 960], [540, 960]), source: { assetId: RENDER_ID, fit: "contain" } };
// slow push-in over the CTA
for (const p of ["scaleX", "scaleY"]) kf(video.id, p, [[ms(C.would), 100, "lin"], [DUR, 106, "lin"]]);
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
