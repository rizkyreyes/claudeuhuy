// Power grid (3d-31) Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  wind: { file: "wind-bed", ms: 3000, vol: 0.14 }, gust: { file: "wind-gust", ms: 1800, vol: 0.35 }, clunk: { file: "steel-clunk", ms: 700, vol: 0.45 },
  sizzle: { file: "heat-sizzle", ms: 2000, vol: 0.35 }, hum: { file: "elec-hum", ms: 3000, vol: 0.22 }, zap: { file: "elec-zap", ms: 600, vol: 0.55 },
  crackle: { file: "spark-crackle", ms: 1500, vol: 0.45 }, whir: { file: "gen-whir", ms: 2500, vol: 0.4 }, oil: { file: "oil-pour", ms: 3000, vol: 0.35 },
  coil: { file: "coil-tick", ms: 120, vol: 0.3 }, crumble: { file: "drywall-crumble", ms: 1200, vol: 0.45 }, thud: { file: "block-thud", ms: 500, vol: 0.45 },
  buzz: { file: "line-buzz", ms: 3000, vol: 0.2 }, street: { file: "street-amb", ms: 3000, vol: 0.2 }, clack: { file: "breaker-clack", ms: 400, vol: 0.45 },
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
bed("hum", 0, EV.fail[1], 0.14); bed("hum", EV.room[0], EV.room[1], 0.14); bed("hum", EV.back[0] + 1.5, TL.duration, 0.12);
bed("wind", EV.aerial1[0], EV.aerial1[1], 0.14); bed("wind", EV.plant[0], EV.plant[1], 0.12); bed("hum", EV.stepup[0], EV.stepup[1], 0.2);
bed("buzz", EV.demo[0], EV.flyover[1], 0.18); bed("wind", EV.flyover[0], EV.flyover[1], 0.14); bed("buzz", EV.insulator[0], EV.insulator[1], 0.2);
bed("hum", EV.substation[0], EV.street[0], 0.2); bed("street", EV.street[0], EV.can[1], 0.2); bed("hum", EV.can[0], EV.can[1], 0.16);
bed("wind", EV.aerial2[0], EV.back[0] + 1.5, 0.14);
const H = TOP_Y + 20;
const small = (str, t0, t1, color = WHITE) => { const l = text(str, 540, 1240, 880, 70, 40, color, BODY, { stroke: 8, tracking: 20, name: "Note - " + str });
  l.activeRange = R(ms(t0), ms(t1 - t0)); kf(l.id, "opacity", [[0, 0], [150, 100], [Math.max(160, ms(t1 - t0) - 150), 100], [ms(t1 - t0), 0]]); layers.push(l); TITLES.push({ t0, t1, text: str }); };
// B1 hook (claim). Loop: "...even though" flows into this.
show(text("HUNDREDS OF\nTHOUSANDS OF VOLTS", 540, H, 980, 300, 92, GOLD), 0.12, C.let - 0.1, "slam", "impact");
sound("zap", 0.3, 0.35); for (let t = 0.9; t < C.let - 0.3; t += 1.1) sound("tick", t, 0.25);
tracked("YOUR OUTLET", "outlet", C.outlet, C.let - 0.1, 130, -120, WHITE, "pop");
// B2 stake: what if it came in at that voltage
show(text("LET THAT IN...", 540, TOP_Y, 980, 200, 104, RED), C.let - 0.05, C.wire - 0.1, "rise", "deny");
sound("zap", EV.plate_pop, 0.6); sound("crackle", EV.plate_pop + 0.1, 0.5); sound("crumble", EV.plate_pop + 0.2, 0.45);
show(text("YOUR WIRING\nWOULD FAIL", 540, H, 980, 300, 116, RED), C.wire - 0.05, C.so - 0.1, "slam", "zap");
sound("crackle", C.wire + 0.2, 0.45); sound("deny", C.fail, 0.6);
// B3 the route: 3 voltage changes
show(text("VOLTAGE CHANGES\n3+ TIMES", 540, H, 980, 300, 100, WHITE), C.so - 0.05, C.starts - 0.1, "rise", "whoosh");
["STEP-UP", "SUBSTATION", "POLE CAN"].forEach((lb, j) => tracked(lb, ["m_stepup", "m_sub", "m_can"][j], EV.markers[j], C.starts - 0.1, j === 0 ? 110 : -110, -90, GOLD, "ping"));
// B4 plant + generator
show(text("POWER PLANT", 540, TOP_Y, 980, 200, 112, WHITE), C.starts - 0.05, C.generator - 0.1, "slam", "impact");
show(text("MUCH LOWER\nVOLTAGE", 540, H, 980, 300, 116, CYAN), C.generator - 0.05, C.next - 0.1, "rise", "whoosh");
tracked("GENERATOR", "generator", C.generator + 0.1, C.next - 0.1, 120, -120, GOLD, "pop");
sound("whir", C.generator, 0.45);
// B5 step-up transformer
show(text("STEP-UP\nTRANSFORMER", 540, H, 980, 300, 112, GOLD), C.next - 0.05, C.inside - 0.1, "slam", "impact");
sound("clack", C.next + 0.1, 0.4);
// B6 inside: two coils, one iron core (oil fills)
show(text("2 COPPER COILS\n1 IRON CORE", 540, H, 980, 300, 96, WHITE), C.inside - 0.05, C.output - 0.1, "rise", "whoosh");
sound("oil", EV.oil_fill[0], 0.35);
tracked("INPUT COIL", "primary", C.copper, C.output - 0.1, -120, 110, CYAN, "pop");
tracked("OUTPUT COIL", "secondary", C.coils, C.output - 0.1, 120, -110, GOLD, "pop");
tracked("IRON CORE", "core", C.iron, C.output - 0.1, -120, -110, WHITE, "pop");
// B7 more turns -> 765,000 V
show(text("MORE TURNS\n= MORE VOLTAGE", 540, H, 980, 300, 96, GOLD), C.output - 0.05, C.seven - 0.1, "slam", "ping");
for (let k = 0; k < 22; k++) sound("coil", EV.turns_light[0] + (EV.turns_light[1] - EV.turns_light[0]) * k / 22, 0.25);
counter(0, 765000, C.seven - 0.05, C.why - 0.1, n => `${n.toLocaleString("en-US")}\nVOLTS`, 540, H, 980, 300, 124, GOLD, 2, 85000);
// B8 why so high: less current, heat = current squared, double V -> 1/4 heat
show(text("WHY SO HIGH?", 540, TOP_Y, 980, 200, 112, WHITE), C.why - 0.05, C.same - 0.1, "rise", "whoosh");
sound("sizzle", C.why + 0.3, 0.35);
show(text("SAME POWER", 540, TOP_Y, 980, 200, 112, WHITE), C.same - 0.05, C.higher - 0.1, "pop", "pop");
show(text("HIGHER VOLTAGE\n= LESS CURRENT", 540, H, 980, 300, 96, CYAN), C.higher - 0.05, C.wires - 0.1, "slam", "impact");
show(text("WIRES WASTE\nIT AS HEAT", 540, H, 980, 300, 108, RED), C.wires - 0.05, C.square - 0.1, "rise", "sizzle");
show(text("BY THE SQUARE\nOF THE CURRENT", 540, H, 980, 300, 96, RED), C.square - 0.05, C.double - 0.1, "slam", null);
for (const t of EV.heat_blocks) sound("pop", t, 0.45);
show(text("DOUBLE\nTHE VOLTAGE", 540, H, 980, 300, 112, GOLD), C.double - 0.05, C.quarter - 0.1, "slam", "impact");
show(text("1/4 THE HEAT", 540, H, 980, 300, 128, CYAN), C.quarter - 0.05, C.now - 0.1, "slam", "ping");
for (let j = 1; j < 4; j++) sound("thud", EV.heat_drop + 0.35 + 0.05 * j, 0.4);
// B9 flyover
show(text("HUNDREDS\nOF MILES", 540, H, 980, 300, 124, WHITE), C.now - 0.05, C.the2 - 0.1, "rise", "whoosh");
// B10 bare conductor: aluminum around a steel core
show(text("BARE WIRES", 540, TOP_Y, 980, 200, 116, WHITE), C.the2 - 0.05, C.air - 0.1, "slam", "impact");
tracked("ALUMINUM", "aluminum", C.aluminum, C.air - 0.1, -120, -120, WHITE, "pop");
tracked("STEEL CORE", "steel", C.steel, C.air - 0.1, 110, 120, CYAN, "pop");
// B11 air insulates, discs keep it off the tower
show(text("AIR IS THE\nINSULATION", 540, H, 980, 300, 112, CYAN), C.air - 0.05, C.insulator - 0.1, "rise", "gust");
show(text("INSULATOR\nDISCS", 540, H, 980, 300, 120, GOLD), C.insulator - 0.05, C.near - 0.1, "slam", "ping");
for (const t of EV.disc_ripple) sound("coil", t, 0.22);
// B12 substation -> under 34,000 V -> down your street
show(text("SUBSTATION", 540, TOP_Y, 980, 200, 116, WHITE), C.near - 0.05, C.under - 0.1, "slam", "impact");
sound("clack", C.substation, 0.45);
counter(0, 34000, C.under - 0.05, C.sends - 0.1, n => `UNDER\n${n.toLocaleString("en-US")} V`, 540, H, 980, 300, 116, CYAN, 2, 34000 / 10);
show(text("DOWN YOUR\nSTREET", 540, H, 980, 300, 116, WHITE), C.sends - 0.05, C.then - 0.1, "rise", "whoosh");
// B13 pole can: 240 V split into two 120 V halves
show(text("THE GRAY CAN", 540, TOP_Y, 980, 200, 112, WHITE), C.then - 0.05, C.two - 0.1, "slam", "impact");
tracked("TRANSFORMER", "polecan", C.gray + 0.1, C.two - 0.1, -120, -110, GOLD, "pop");
sound("hum", C.gray + 0.3, 0.25);
counter(0, 240, C.two - 0.05, C.split - 0.1, n => `${n} VOLTS`, 540, TOP_Y, 980, 200, 124, GOLD, 2, 40);
show(text("2 HALVES\nOF 120", 540, H, 980, 300, 120, WHITE), C.split - 0.05, C.your - 0.1, "slam", "ping");
tracked("120 V", "sec_upper", C.halves, C.your - 0.1, -120, -100, GOLD, "pop");
tracked("120 V", "sec_lower", C.halves + 0.15, C.your - 0.1, -120, 100, CYAN, "pop");
// B14 inside the house: outlet = one half, dryer = both
show(text("OUTLET:\n120 V", 540, H, 980, 300, 120, GOLD), C.your - 0.05, C.your2 - 0.1, "slam", "pop");
show(text("DRYER:\n240 V", 540, H, 980, 300, 120, CYAN), C.your2 - 0.05, C.only - 0.1, "slam", "pop");
sound("clack", EV.outlet_on, 0.35); sound("whir", EV.dryer_on + 0.2, 0.25);
// B15 about 5% lost
counter(0, 5, C.five - 0.05, C.and - 0.1, n => `ONLY ~${n}%\nLOST`, 540, H, 980, 300, 124, GOLD, 1, 1);
show(text("THE WHOLE TRIP", 540, TOP_Y - 40, 980, 120, 72, WHITE), C.only - 0.05, C.five - 0.1, "rise", "whoosh");
small("U.S. AVERAGE (EIA)", C.five, C.and - 0.1);
// B16 loop: fly back into the house, then frame 1. No spoken tease; small NEXT text only (15 Nov rule).
show(text("NONE OF IT\nREACHES YOU", 540, H, 980, 300, 112, WHITE), C.and - 0.05, C.even - 0.1, "rise", "whoosh");
show(text("EVEN\nTHOUGH...", 540, H, 980, 300, 124, GOLD), C.even - 0.05, C.end, "rise", "riser");
sound("whoosh", C.and + 0.1, 0.45); sound("whoosh", C.even - 0.2, 0.4);
{ const nx = text("NEXT: BUILDING A SUBWAY STATION", 540, 1240, 880, 70, 40, WHITE, BODY, { stroke: 8, tracking: 20, name: "Next tease" });
  const t0 = Math.max(C.even, TL.duration - 1.5); nx.activeRange = R(ms(t0), DUR - ms(t0)); kf(nx.id, "opacity", [[0, 0], [150, 100]]); layers.push(nx); TITLES.push({ t0, t1: TL.duration, text: nx.sourceText.text }); }
// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(volts?|voltage|transformer|substation|generator|coils?|core|current|heat|insulat|aluminum|steel|outlet|dryer|halves)/i;
const SYN = { "seven": "765,000", "sixty-five": "765,000", "hundred": "765,000", "thirty-four": "34,000", "thousand": "34,000", "five": "5", "percent": "5", "forty": "240", "two": "2", "twenty": "120", "one": "1", "three": "3", "times": "times", "coils": "coils", "volts": "volts", "voltage": "voltage", "wires": "wires", "towers": "tower", "discs": "discs", "miles": "miles" };
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
const video = { type: "Video", id: 1, name: "Blender render - power grid cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([540, 960], [540, 960]), source: { assetId: RENDER_ID, fit: "contain" } };
// no push-in at the end: the last frame must match frame 1 (loop)
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
