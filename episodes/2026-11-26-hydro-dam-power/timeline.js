// Hydro dam power (3d-33) Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  clunk: { file: "steel-clunk", ms: 700, vol: 0.45 }, thud: { file: "block-thud", ms: 500, vol: 0.45 },
  hum: { file: "elec-hum", ms: 3000, vol: 0.25 }, whir: { file: "gen-whir", ms: 2500, vol: 0.45 }, buzz: { file: "line-buzz", ms: 3000, vol: 0.22 },
  wind: { file: "canyon-wind", ms: 3000, vol: 0.22 }, rush: { file: "water-rush", ms: 3000, vol: 0.32 }, roar: { file: "water-roar", ms: 3000, vol: 0.34 },
  gate: { file: "gate-clack", ms: 900, vol: 0.5 }, hammer: { file: "hammer-bang", ms: 1600, vol: 0.75 }, burst: { file: "pipe-burst", ms: 2200, vol: 0.8 },
  spray: { file: "spray-hiss", ms: 1800, vol: 0.4 }, lift: { file: "elevator-hum", ms: 3000, vol: 0.3 },
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
// ambience: canyon wind outside, water rushing in the pipe while the gates are open, hum + whir at the generator
bed("wind", 0, EV.drop[0], 0.2); bed("rush", C.fall, EV.slam, 0.3); bed("rush", EV.gates_reopen, EV.gates_close_slow[1], 0.26);
bed("rush", C.shaft + 0.5, EV.draft[0], 0.16); bed("hum", EV.gen[0], EV.xf[1], 0.22); bed("buzz", EV.xf[0], EV.wide[0], 0.2);
bed("roar", EV.draft[0], EV.wide[0] + 0.5, 0.34); bed("wind", EV.wide[0], TL.duration, 0.2); bed("wind", EV.y1950[0], EV.y1950[1], 0.16);
// mechanical events
sound("gate", EV.gates_open, 0.5); sound("whir", C.runner - 0.1, 0.35);
sound("gate", EV.slam, 0.55); sound("hammer", EV.slam + 0.12, 0.7); sound("hammer", C.hammers, 0.75);
sound("burst", EV.burst, 0.8); sound("spray", EV.burst + 0.2, 0.45);
sound("clunk", EV.gates_reopen, 0.35); sound("gate", EV.gates_close_slow[0], 0.3); sound("clunk", EV.gates_close_slow[1], 0.3);
sound("whir", C.spins2 - 0.2, 0.5); sound("lift", EV.elevator_down - 0.2, 0.32); sound("lift", EV.elevator_down + 2.6, 0.26);
// B1 hook (claim) + stake
show(text("NOTHING\nBURNS", 540, H, 980, 300, 128, GOLD), 0.12, C.lets - 0.1, "slam", "impact");
show(text("JUST FALLING\nWATER", 540, H, 980, 300, 116, CYAN), C.lets - 0.05, C.pipes - 0.1, "rise", "whoosh");
show(text("SHUT IT TOO FAST\nAND IT BURSTS", 540, H, 980, 300, 96, RED), C.pipes - 0.05, C.lake - 0.1, "rise", "deny");
sound("hammer", C.burst0, 0.55);
// B2 stored energy
show(text("STORED\nENERGY", 540, H, 980, 300, 124, GOLD), C.stored - 0.05, C.at - 0.1, "slam", "impact");
tracked("LAKE", "lake", C.lake + 0.1, C.at - 0.1, 120, 110, CYAN, "pop");
// B3 intake + penstock
small("HOOVER DAM", C.hoover, C.drops - 0.1);
tracked("INTAKE TOWER", "intake", C.intake, C.penstocks - 0.1, 120, -100, WHITE, "pop");
show(text("PENSTOCKS", 540, TOP_Y, 980, 200, 124, WHITE), C.penstocks - 0.05, C.thirty - 0.1, "slam", "impact");
counter(0, 30, C.thirty - 0.05, C.drops - 0.1, n => `${n} FT WIDE`, 540, TOP_Y, 980, 200, 124, GOLD, 1, 5);
tracked("PENSTOCK", "penstock_up", C.thirty + 0.2, C.drops - 0.1, 120, 110, CYAN, null);
// B4 the drop
show(text("THE DROP", 540, TOP_Y, 980, 200, 124, WHITE), C.drops - 0.05, C.five - 0.15, "slam", "down");
counter(0, 500, C.five - 0.1, C.then - 0.1, n => `~${n} FT`, 540, TOP_Y, 980, 200, 132, GOLD, 2, 50);
// B5 spiral casing
show(text("SPIRAL\nCASING", 540, H, 980, 300, 124, CYAN), C.spiral - 0.05, C.ring - 0.1, "rise", "whoosh");
tracked("TURBINE", "runner", C.turbine - 0.1, C.ring - 0.1, 120, 120, WHITE, "pop");
// B6 wicket gates + runner
show(text("WICKET\nGATES", 540, H, 980, 300, 124, GOLD), C.wicket - 0.05, C.runner - 0.3, "slam", "impact");
tracked("GATES", "gates", C.aims + 0.1, C.good - 0.1, 120, 110, GOLD, null);
show(text("RUNNER\nSPINS", 540, H, 980, 300, 124, WHITE), C.runner - 0.25, C.good - 0.1, "pop", "pop");
// B7 efficiency
counter(0, 90, C.ninety - 0.1, C.but - 0.1, n => `OVER ${n}%`, 540, TOP_Y, 980, 200, 132, CYAN, 2, 10);
small("OF THE WATER'S ENERGY CAPTURED", C.percent, C.but - 0.1);
// B8 water hammer
show(text("CAN'T SLAM\nSHUT", 540, H, 980, 300, 124, RED), C.but - 0.05, C.stop - 0.1, "slam", "deny");
show(text("ALL THAT WATER\nSTOPS AT ONCE", 540, H, 980, 300, 96, WHITE), C.stop - 0.05, C.hammers - 0.1, "rise", "whoosh");
show(text("WATER\nHAMMER", 540, H, 980, 300, 128, RED), C.hammers - 0.05, C.japan - 0.1, "slam", "impact");
// B9 1950 what-if
small("JAPAN", C.japan, C.so - 0.1);
counter(1946, 1950, C.y1950 - 0.1, C.burst - 0.1, n => `${n}`, 540, TOP_Y, 980, 200, 150, WHITE, 1, 1);
show(text("PENSTOCK\nBURST", 540, H, 980, 300, 128, RED), C.burst - 0.05, C.so - 0.1, "slam", "deny");
// B10 close gradually
show(text("CLOSE\nGRADUALLY", 540, H, 980, 300, 120, GOLD), C.close - 0.05, C.shaft - 0.1, "rise", "whoosh");
// B11 shaft -> generator
tracked("SHAFT", "shaft", C.shaft + 0.45, C.generator - 0.1, 120, 100, WHITE, "pop");
show(text("GENERATOR", 540, TOP_Y, 980, 200, 124, WHITE), C.generator - 0.05, C.rotor - 0.1, "slam", "impact");
// B12 rotor + 300 tons + copper coils
show(text("ELECTRO-\nMAGNETS", 540, H, 980, 300, 120, WHITE), C.electromagnets - 0.05, C.three - 0.15, "pop", "pop");
tracked("ROTOR", "rotor", C.rotor + 0.1, C.coils - 0.1, 120, 120, RED, "pop");
counter(0, 300, C.three - 0.1, C.coils - 0.1, n => `${n}+ TONS`, 540, TOP_Y, 980, 200, 132, GOLD, 2, 50);
tracked("COPPER COILS", "coils", C.coils - 0.05, C.moving - 0.1, -120, 110, GOLD, "ping");
tracked("STATOR", "stator", C.coils + 0.2, C.moving - 0.1, -120, -110, WHITE, null);
// B13 electricity
show(text("MOVING\nMAGNETS", 540, H, 980, 300, 124, WHITE), C.moving - 0.05, C.electrons - 0.1, "rise", "whoosh");
show(text("PUSH\nELECTRONS", 540, H, 980, 300, 124, CYAN), C.electrons - 0.05, C.electricity - 0.15, "pop", "pop");
show(text("ELECTRICITY", 540, TOP_Y, 980, 200, 120, GOLD), C.electricity - 0.1, C.transformer - 0.1, "slam", "impact");
// B14 transformer
show(text("STEPPED UP", 540, TOP_Y, 980, 200, 124, WHITE), C.transformer - 0.05, C.water2 - 0.1, "slam", "impact");
tracked("TRANSFORMER", "transformer", C.transformer + 0.1, C.water2 - 0.1, -120, 110, CYAN, "pop");
// B15 draft tube -> river
tracked("DRAFT TUBE", "draft", C.draft - 0.1, C.river, 120, -110, WHITE, "pop");
show(text("SLOWS\nDOWN", 540, H, 980, 300, 124, CYAN), C.slows - 0.05, C.returns - 0.1, "rise", "whoosh");
show(text("SAME WATER,\nJUST LOWER", 540, H, 980, 300, 108, GOLD), C.lower - 0.9, C.hoover2 - 0.1, "slam", "impact");
// B16 17 turbines
small("HOOVER DAM", C.hoover2, C.would - 0.1);
counter(0, 17, C.seventeen - 0.1, C.would - 0.1, n => `${n} TURBINES`, 540, TOP_Y, 980, 200, 124, GOLD, 2, 1);
// B17 CTA: spoken question as the closing title, NEXT small over the last 2 s, fade out
show(text("RIDE THE ELEVATOR\nDOWN INSIDE?", 540, H, 980, 300, 96, WHITE), C.would - 0.05, TL.duration, "slam", "impact");
tracked("ELEVATOR", "elevator", C.elevator + 0.1, C.tell - 0.1, 120, 100, GOLD, null);
show(text("TELL ME IN THE COMMENTS", 540, H + 230, 980, 110, 56, GOLD, BODY, { tracking: 10 }), C.tell - 0.05, TL.duration, "pop", "ping");
{ const nx = text("NEXT: ROMAN AQUEDUCTS", 540, 1240, 880, 70, 40, WHITE, BODY, { stroke: 8, tracking: 20, name: "Next tease" });
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
const HL = /^(penstocks?|turbines?|gates?|wicket|runner|spiral|casing|generator|rotor|electromagnets|copper|electrons|electricity|transformer|draft|energy|hammers?)/i;
const SYN = { "thirty": "30", "feet": "ft", "ninety": "90", "seventeen": "17", "penstocks": "penstock", "gates": "gates", "electromagnets": "electro", "magnets": "magnets" };
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
const video = { type: "Video", id: 1, name: "Blender render - hydro dam cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
