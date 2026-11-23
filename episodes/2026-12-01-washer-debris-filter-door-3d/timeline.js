// Washer debris filter door Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.6 }, rush: { file: "water-rush", ms: 3000, vol: 0.3 },
  splash: { file: "splash", ms: 1200, vol: 0.7 }, spark: { file: "spark-crackle", ms: 500, vol: 0.5 }, click: { file: "button-click", ms: 250, vol: 0.6 },
  pull: { file: "plug-pull", ms: 600, vol: 0.6 }, room: { file: "room-tone", ms: 3000, vol: 0.25 }, whir: { file: "pump-whir", ms: 2000, vol: 0.22 },
  clink: { file: "coin-clink", ms: 500, vol: 0.45 }, clank: { file: "pan-clank", ms: 600, vol: 0.6 }, twist: { file: "filter-twist", ms: 1000, vol: 0.6 },
  drip: { file: "drip", ms: 300, vol: 0.5 }, beep: { file: "error-beep", ms: 350, vol: 0.35 },
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
// ambience: laundry-room tone everywhere, pump whir while it runs, water rush while the drain flows
bed("room", 0, TL.duration - 0.8, 0.2);
bed("whir", EV.pump_on, EV.pump_off, 0.22, 1.95);
bed("rush", C.pushes, C.slows, 0.18, 2.9);
// mechanical events
sound("ping", C.door, 0.4); sound("whoosh", C.hides - 0.05, 0.45); sound("deny", C.stop, 0.5);
EV.arrive.forEach((t, i) => sound(i < 7 ? "clink" : "pop", t - 0.05, i < 7 ? 0.45 : 0.25));
sound("spark", EV.sparks, 0.55); sound("deny", EV.sparks + 0.05, 0.45);
sound("whoosh", EV.towel, 0.35); sound("clank", EV.pan_land, 0.6);
sound("click", EV.door_open, 0.6); sound("click", EV.door_close, 0.55); sound("pop", EV.hose_pop, 0.4);
sound("rush", EV.stream[0], 0.3); sound("splash", EV.stream[0] + 0.1, 0.3);
sound("twist", EV.ccw[0], 0.6); sound("pull", EV.pull[0], 0.55); sound("rush", EV.rinse[0], 0.3);
for (let k = 0; k < 5; k++) sound("clink", EV.junk_fall + 0.12 + 0.09 * k, 0.4);
sound("pull", EV.back[0], 0.4); sound("twist", EV.cw[0], 0.55);
for (let k = 0; k < 4; k++) sound("drip", EV.leak + 0.18 * k + 0.25, 0.5);
for (let k = 0; k < 4; k++) sound("beep", EV.led + 0.5 * k, 0.35);
for (let k = 0; k < 12; k++) sound("tick", C.every + 0.06 * k, 0.3);
for (let k = 0; k < 6; k++) sound("tick", C.five + 0.24 * k, 0.35);
// B1 hook: the claim on screen from frame 0
show(text("A TRAP FOR\nPOCKET JUNK", 540, H, 980, 300, 112, GOLD), 0.0, C.ignore - 0.1, "slam", "impact");
tracked("TINY DOOR", "kickdoor", 0.5, C.hides - 0.1, 120, -140, WHITE, null);
// B2 stake
show(text("STOPS DRAINING", 540, TOP_Y, 980, 200, 100, RED), C.stop - 0.05, C.leaving - 0.1, "slam", null);
show(text("CLOTHES IN\nDIRTY WATER", 540, H, 980, 300, 104, RED), C.leaving - 0.05, C.at - 0.1, "rise", "whoosh");
// B3 the pump
show(text("END OF EVERY\nWASH + RINSE", 540, H, 980, 300, 96, WHITE), C.end - 0.1, C.electric - 0.1, "pop", "pop");
tracked("DRAIN PUMP", "motor", C.electric, C.pushes - 0.1, -110, -110, GOLD, "pop");
show(text("PUMP ON", 540, TOP_Y, 980, 200, 128, GOLD), C.switches - 0.05, C.its - 0.1, "slam", "impact");
tracked("IMPELLER", "imp", C.spinning - 0.05, C.pushes - 0.05, 110, 120, CYAN, "pop");
// B4 the route
show(text("OUT OF\nTHE DRUM", 540, H, 980, 300, 110, CYAN), C.pushes - 0.05, C.up - 0.1, "slam", "whoosh");
show(text("UP THE\nDRAIN HOSE", 540, H, 980, 300, 110, WHITE), C.up - 0.05, C.into - 0.1, "rise", "whoosh");
show(text("INTO YOUR\nDRAIN PIPE", 540, H, 980, 300, 110, CYAN), C.into - 0.05, C.but - 0.1, "rise", "pop");
tracked("STANDPIPE", "stand", C.into + 0.1, C.but - 0.1, -120, 90, WHITE, null);
// B5 passengers
show(text("PASSENGERS", 540, TOP_Y, 980, 200, 116, GOLD), C.passengers - 0.05, C.coins - 0.1, "slam", "impact");
show(text("COINS", 540, TOP_Y, 980, 200, 128, GOLD), C.coins - 0.05, C.buttons - 0.1, "pop", "pop");
show(text("BUTTONS", 540, TOP_Y, 980, 200, 128, WHITE), C.buttons - 0.05, C.bits - 0.1, "pop", "pop");
show(text("PLASTIC", 540, TOP_Y, 980, 200, 128, GOLD), C.bits - 0.05, C.loads - 0.1, "pop", "pop");
show(text("LOADS OF LINT", 540, TOP_Y, 980, 200, 104, WHITE), C.loads - 0.05, C.junk - 0.1, "pop", "pop");
tracked("SUMP HOSE", "sump", C.loads, C.chew - 0.1, -120, 110, WHITE, null);
show(text("CAN CHEW UP\nTHE IMPELLER", 540, H, 980, 300, 100, RED), C.chew - 0.05, C.so - 0.1, "slam", null);
// B6 the strainer
show(text("IN FRONT\nOF THE PUMP", 540, H, 980, 300, 104, WHITE), C.so - 0.05, C.plastic2 - 0.1, "rise", "whoosh");
tracked("PLASTIC STRAINER", "cart", C.plastic2 - 0.05, C.water2 - 0.1, 100, -150, GOLD, "pop");
show(text("WATER SLIPS\nTHROUGH", 540, H, 980, 300, 104, CYAN), C.water2 - 0.05, C.junk2 - 0.1, "rise", "whoosh");
show(text("JUNK DOESN'T", 540, TOP_Y, 980, 200, 110, RED), C.junk2 - 0.05, C.also - 0.1, "slam", "deny");
show(text("ALSO THE\nLINT FILTER", 540, H, 980, 300, 108, GOLD), C.also - 0.05, C.over - 0.1, "rise", "pop");
// B7 months later
show(text("OVER MONTHS", 540, TOP_Y, 980, 200, 110, WHITE), C.over - 0.05, C.packs - 0.1, "pop", "whoosh");
show(text("PACKED TIGHT", 540, TOP_Y, 980, 200, 110, RED), C.packs - 0.05, C.slows - 0.1, "slam", "deny");
show(text("A TRICKLE", 540, TOP_Y, 980, 200, 128, RED), C.slows - 0.05, C.drain3 - 0.1, "slam", "down");
show(text("DRAIN TAKES\nTOO LONG", 540, H, 980, 300, 104, RED), C.drain3 - 0.05, C.some - 0.2, "rise", null);
// B8 error code
small("SOME WHIRLPOOL WASHERS", C.some, C.eight - 0.1, GOLD);
counter(0, 8, C.eight - 0.05, C.throws - 0.1, n => `${n} MIN`, 540, TOP_Y, 980, 200, 140, GOLD, 1);
show(text("ERROR CODE", 540, TOP_Y, 980, 200, 124, RED), C.error - 0.05, C.before - 0.1, "slam", "deny");
// B9-B11 before opening it
show(text("TOWELS +\nSHALLOW PAN", 540, H, 980, 300, 104, WHITE), C.lay - 0.05, C.water4 - 0.1, "pop", "pop");
show(text("WATER WAITS\nDOWN THERE", 540, H, 980, 300, 104, CYAN), C.water4 - 0.05, C.hot - 0.1, "rise", "whoosh");
show(text("HOT WATER\nCAN BURN", 540, H, 980, 300, 110, RED), C.hot - 0.05, C.many - 0.1, "slam", "deny");
tracked("EMERGENCY HOSE", "ehose", C.hose2 - 0.05, C.twist - 0.1, -100, -170, GOLD, "pop");
show(text("DRAIN IT", 540, TOP_Y, 980, 200, 128, CYAN), C.drain5 - 0.05, C.twist - 0.1, "slam", null);
// B12 twist, pull, rinse
show(text("TWIST\nCOUNTERCLOCKWISE", 540, H, 980, 300, 76, GOLD), C.twist - 0.05, C.pull - 0.1, "pop", "whoosh");
show(text("PULL IT OUT", 540, TOP_Y, 980, 200, 116, WHITE), C.pull - 0.05, C.rinse2 - 0.1, "slam", "impact");
tracked("LINT + COINS", "cart_pulled", C.out - 0.05, C.rinse2 + 0.2, 110, -150, RED, "pop");
show(text("RINSE IN\nWARM WATER", 540, H, 980, 300, 104, CYAN), C.rinse2 - 0.05, C.check - 0.1, "rise", "pop");
// B13 impeller check
show(text("SPINS FREELY?", 540, TOP_Y, 980, 200, 104, CYAN), C.check - 0.05, C.screw - 0.1, "pop", "ping");
tracked("IMPELLER", "imp", C.check + 0.1, C.screw - 0.1, -110, 140, WHITE, null);
// B14 back in tight
show(text("SCREW IT\nBACK TIGHT", 540, H, 980, 300, 108, WHITE), C.screw - 0.05, C.leak - 0.1, "slam", "impact");
show(text("OR IT LEAKS", 540, TOP_Y, 980, 200, 116, RED), C.leak - 0.05, C.lg - 0.1, "slam", "deny");
// B15 how often (calendar)
show(text("LG:\nEVERY MONTH", 540, H, 980, 300, 108, GOLD), C.lg - 0.05, C.samsung - 0.1, "slam", "impact");
show(text("SAMSUNG:\n5-6× A YEAR", 540, H, 980, 300, 108, CYAN), C.samsung - 0.05, C.when - 0.1, "slam", "impact");
// B16 CTA: spoken question as the closing title, NEXT small over the last 2 s, fade out
show(text("WHEN DID YOU LAST\nOPEN YOURS?", 540, H, 980, 300, 84, WHITE), C.when - 0.05, TL.duration, "slam", "impact");
show(text("TELL ME IN THE COMMENTS", 540, H + 230, 980, 110, 56, GOLD, BODY, { tracking: 10 }), C.tell - 0.05, TL.duration, "pop", "ping");
{ const nx = text("NEXT: YOUR DISPOSAL HAS NO BLADES", 540, 1240, 880, 70, 40, WHITE, BODY, { stroke: 8, tracking: 20, name: "Next tease" });
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
const HL = /^(trap|pump|impeller|coins|buttons|plastic|lint|strainer|filter|counterclockwise|burn|leak|error)/i;
const SYN = { "eight": "8", "five": "5", "six": "6", "minutes": "min", "packs": "packed" };
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
const video = { type: "Video", id: 1, name: "Blender render - washer debris filter cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
