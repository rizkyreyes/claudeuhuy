// Suspension-Bridge-P1-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  slide: { file: "stone-slide", ms: 900, vol: 0.5 }, rumble: { file: "concrete-rumble", ms: 1200, vol: 0.6 }, towerrise: { file: "tower-rise", ms: 1600, vol: 0.55 },
  clunk: { file: "saddle-clunk", ms: 700, vol: 0.6 }, wind: { file: "wind-gust", ms: 3000, vol: 0.3 }, zip: { file: "rope-zip", ms: 1000, vol: 0.4 },
  clack: { file: "plank-clack", ms: 250, vol: 0.35 }, wheelroll: { file: "wheel-roll", ms: 5000, vol: 0.45 }, latch: { file: "latch-clunk", ms: 500, vol: 0.6 },
  click: { file: "strand-click", ms: 200, vol: 0.4 }, press: { file: "squeeze-press", ms: 1400, vol: 0.55 }, waves: { file: "waves", ms: 4000, vol: 0.25 },
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
// B1 hook: the claim on the cable's cut face, then the whole bridge + the stake
show(text("ONE CABLE =", 540, TOP_Y - 20, 980, 160, 104, WHITE), 0.15, C.n27572 - 0.08, "rise", "whoosh");
sound("wind", 0.0, 0.25);
counter(0, 27572, C.n27572 - 0.05, C.spun - 0.1, n => `${Math.round(n).toLocaleString("en-US")}\nSTEEL WIRES`, 540, TOP_Y + 20, 980, 300, 108, CYAN, 2, 2757.2);
show(text("SPUN IN PLACE", 540, TOP_Y, 980, 200, 104, GOLD), C.spun - 0.05, C.every - 0.1, "slam", "impact");
tracked("MAIN CABLE", "cable", C.spun + 0.3, C.every - 0.1, 150, 170, WHITE, null);
show(text("EVERY CAR\nHANGS FROM THEM", 540, TOP_Y + 20, 980, 300, 96, WHITE), C.every - 0.05, C.slip - 0.75, "rise", "whoosh");
show(text("NOTHING CAN SLIP", 540, TOP_Y, 980, 200, 96, RED), C.slip - 0.7, C.lets - 0.1, "slam", "impact");
sound("deny", C.slip - 0.05, 0.6);
// B2 cut it open (the left anchorage's near half slides off)
show(text("LET'S CUT IT OPEN", 540, TOP_Y, 980, 200, 92, WHITE), C.lets - 0.05, C.first - 0.1, "pop", null);
sound("riser", C.cut - 0.6, 0.3, 0.9); sound("slide", EV.cut[0], 0.5, 0.05);
// B3 anchorages
show(text("1. ANCHORAGES", 540, TOP_Y, 980, 200, 110, GOLD), C.first - 0.05, C.cables - 0.1, "rise", "whoosh");
sound("rumble", EV.anch_rise[0], 0.6);
show(text("A HUGE PULL", 540, TOP_Y, 980, 200, 112, RED), C.pull - 0.05, C.giant - 0.1, "slam", "impact");
show(text("A GIANT\nCONCRETE BLOCK", 540, TOP_Y + 20, 980, 300, 100, WHITE), C.giant - 0.05, C.eyebars - 0.1, "rise", "pop");
tracked("ANCHORAGE", "anchorage", C.giant + 0.2, C.eyebars - 0.4, 120, -150, GOLD, null);
show(text("STEEL EYEBARS\nCAST INSIDE", 540, TOP_Y + 20, 980, 300, 100, GOLD), C.eyebars - 0.05, C.next - 0.1, "slam", "impact");
sound("slide", EV.eyecut[0], 0.45, 0.05);
tracked("EYEBARS", "eyebars", C.eyebars + 0.5, C.next - 0.1, 140, 170, GOLD, "ping");
// B4 towers + saddles
show(text("2. TOWERS RISE", 540, TOP_Y, 980, 200, 110, GOLD), C.next - 0.05, C.saddle - 0.1, "rise", "whoosh");
sound("towerrise", EV.tower_rise[0], 0.6);
show(text("A STEEL SADDLE", 540, TOP_Y, 980, 200, 104, WHITE), C.saddle - 0.05, C.so - 0.1, "pop", null);
sound("clunk", EV.saddle + 0.15, 0.6);
tracked("SADDLE", "saddle", C.cradle, C.so - 0.1, -140, 170, GOLD, "ping");
// B5 the first line: a kite (Niagara, 1848)
show(text("THE FIRST LINE?", 540, TOP_Y, 980, 200, 104, WHITE), C.first2 - 0.4, C.niagara - 0.1, "rise", "whoosh");
sound("wind", C.so + 0.2, 0.35);
show(text("NIAGARA, 1848", 540, TOP_Y, 980, 200, 104, WHITE), C.niagara - 0.05, C.kite - 0.1, "pop", "pop");
show(text("ON A KITE", 540, TOP_Y, 980, 200, 128, GOLD), C.kite - 0.05, C.thin - 0.1, "slam", "impact");
sound("zip", EV.kite[0] + 0.2, 0.35);
// B6 heavier ropes, then the catwalk
show(text("HEAVIER ROPES", 540, TOP_Y, 980, 200, 104, WHITE), C.heavier - 0.05, C.catwalk - 0.1, "rise", "whoosh");
sound("zip", EV.ropes[0], 0.4);
show(text("A CATWALK\nIN THE SKY", 540, TOP_Y + 20, 980, 300, 108, GOLD), C.catwalk - 0.05, C.spinning - 0.1, "slam", "impact");
for (let k = 0; k < 8; k++) sound("clack", EV.walk[0] + k * (EV.walk[1] - EV.walk[0]) / 8, 0.35);
sound("wind", C.catwalk + 0.3, 0.3);
// B7 spinning: wheel runs anchorage to anchorage with a loop of wire, hooked on, back for more
show(text("3. SPINNING", 540, TOP_Y, 980, 200, 116, GOLD), C.spinning - 0.05, C.loop - 0.1, "rise", "whoosh");
sound("wheelroll", EV.trip1[0], 0.5);
tracked("SPINNING WHEEL", "wheel", C.wheel + 0.1, C.loop - 0.15, 120, -170, GOLD, "pop");
show(text("A LOOP OF WIRE", 540, TOP_Y, 980, 200, 100, CYAN), C.loop - 0.05, C.loop2 - 0.1, "pop", "ping");
show(text("HOOKED ON", 540, TOP_Y, 980, 200, 116, WHITE), C.hooked - 0.05, C.back - 0.1, "slam", null);
sound("latch", EV.hook, 0.6);
show(text("BACK FOR MORE", 540, TOP_Y, 980, 200, 104, WHITE), C.back - 0.05, C.golden2 - 0.1, "rise", "whoosh");
sound("wheelroll", EV.trip2[0], 0.4); sound("wheelroll", EV.montage[0], 0.35);
for (const t of EV.passes) sound("clack", t, 0.25);
// B8 six months, 80,000 miles
counter(1, 6, C.six - 0.05, C.eighty - 0.1, n => `${n} MONTHS`, 540, TOP_Y, 980, 200, 116, WHITE, 1, 1);
counter(0, 80000, C.eighty - 0.05, C.wires2 - 0.1, n => `${n.toLocaleString("en-US")}\nMILES OF WIRE`, 540, TOP_Y + 20, 980, 300, 104, GOLD, 2, 8000);
// B9 61 strands, squeezed round, about 3 feet thick
counter(1, 61, C.n61 - 0.05, C.squeezed - 0.1, n => `${n} STRANDS`, 540, TOP_Y, 980, 200, 116, WHITE, 2, 6);
for (const t of EV.rings) sound("click", t, 0.4);
show(text("SQUEEZED\nINTO ONE CABLE", 540, TOP_Y + 20, 980, 300, 100, WHITE), C.squeezed - 0.05, C.about - 0.1, "rise", null);
sound("press", EV.squeeze[0], 0.55);
show(text("ABOUT 3 FEET THICK", 540, TOP_Y, 980, 200, 92, GOLD), C.about - 0.05, C.but - 0.1, "slam", "impact");
// B10 still no road (cliffhanger)
show(text("STILL NO ROAD", 540, TOP_Y, 980, 200, 124, RED), C.but - 0.05, C.would - 0.1, "slam", "impact");
sound("deny", C.road - 0.05, 0.6); sound("wind", C.but + 0.1, 0.25);
// B11 CTA: a question to the viewer, then the Part 2 follow line (playbook Follower growth 6)
show(text("WOULD YOU WALK\nTHAT CATWALK?", 540, TOP_Y + 20, 980, 300, 92, WHITE), C.would, C.part - 0.1, "slam", "whoosh");
show(text("TELL ME IN THE COMMENTS", 540, TOP_Y + 220, 900, 80, 50, GOLD, BODY, { tracking: 60 }), C.tell, C.part - 0.1, "rise", "ping");
show(text("PART 2 TOMORROW:\nHANGING THE ROAD", 540, TOP_Y, 980, 300, 88, WHITE), C.part, C.end, "slam", "pop");
show(text("FOLLOW SO YOU DON'T MISS IT", 540, TOP_Y + 215, 940, 80, 46, GOLD, BODY, { tracking: 40 }), C.follow, C.end, "rise", "ping");
sound("wind", C.would + 0.3, 0.3); sound("wind", C.would + 3.2, 0.25); sound("waves", C.would + 1.0, 0.2);

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(cable|cables|wires?|anchorages?|eyebars|towers|saddle|kite|catwalk|spinning|wheel|strands)/i;
const SYN = { six: "6", eighty: "80000", "80000": "80000", three: "3", "27572": "27572", "61": "61", "1848": "1848", two: "2" };
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
  sourceIntrinsicDuration: VO_MS, source: { assetId: "vo" }, volume: 0.87, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, Math.min(DUR, 76000)), sourceRange: R(0, Math.min(DUR, 76000)),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.30, captionsEnabled: false });
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - suspension bridge part 1 cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
