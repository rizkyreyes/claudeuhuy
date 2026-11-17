// Wind-Turbine-3D part 1 Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  wind: { file: "wind-bed", ms: 3000, vol: 0.16 }, gust: { file: "wind-gust", ms: 1800, vol: 0.4 }, creak: { file: "steel-creak", ms: 1400, vol: 0.45 },
  hum: { file: "rotor-hum", ms: 2400, vol: 0.35 }, dig: { file: "dig-scoop", ms: 700, vol: 0.5 }, clank: { file: "rebar-clank", ms: 600, vol: 0.45 },
  ting: { file: "steel-ting", ms: 900, vol: 0.45 }, truck: { file: "truck-idle", ms: 3000, vol: 0.35 }, pour: { file: "concrete-pour", ms: 2400, vol: 0.4 },
  dump: { file: "dirt-dump", ms: 1500, vol: 0.5 }, thud: { file: "ground-thud", ms: 800, vol: 0.5 }, clang: { file: "steel-clang", ms: 1200, vol: 0.5 },
  winch: { file: "crane-winch", ms: 2500, vol: 0.4 }, wrench: { file: "impact-wrench", ms: 700, vol: 0.45 },
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
// ambience: open prairie wind outside; machine foley per beat
for (let t = 0; t < TL.duration - 0.5; t += 2.9) sound("wind", t, 0.16);
// B1 hook (claim): a buried slab of concrete and a pile of dirt hold it up. Loop: the last line "...every ton of it rests on" flows into this.
show(text("JUST CONCRETE\n+ DIRT", 540, TOP_Y + 20, 980, 300, 116, WHITE), 0.12, C.thats - 0.1, "slam", "impact");
sound("thud", EV.hook_glow, 0.4);
tracked("CONCRETE SLAB", "slab", C.buried + 0.1, C.thats + 0.6, -150, 120, GOLD, "pop");
tracked("DIRT", "dirt", C.pile, C.thats + 0.6, -140, -110, GOLD, "pop");
show(text("THAT'S ALL\nTHAT HOLDS IT", 540, TOP_Y + 20, 980, 300, 104, GOLD), C.thats - 0.05, C.uptop - 0.1, "rise", "whoosh");
sound("hum", C.holds, 0.35);
// B2 stake: wind shoves on three giant blades, tries to tip the tower
show(text("WIND PUSHES\nTHE BLADES", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.uptop - 0.05, C.tip - 0.1, "slam", "gust");
sound("gust", EV.push + 0.4, 0.4);
show(text("TRYING TO\nTIP IT OVER", 540, TOP_Y + 20, 980, 300, 112, RED), C.tip - 0.05, C.so - 0.1, "slam", "deny");
sound("creak", EV.tip[0] + 0.2, 0.45);
// B3 build: hole, rebar cage (50 tons), 100+ anchor bolts, ~500 cubic yards
show(text("STEP 1:\nDIG A HOLE", 540, TOP_Y + 20, 980, 300, 112, WHITE), C.so - 0.05, C.workers - 0.1, "slam", "whoosh");
sound("dig", EV.dig[0], 0.5); sound("dig", EV.dig[0] + 0.8, 0.45);
show(text("STEEL\nREBAR CAGE", 540, TOP_Y + 20, 980, 300, 112, CYAN), C.workers - 0.05, C.fifty - 0.1, "rise", "whoosh");
EV.cage.forEach(t => sound("clank", t, 0.45));
tracked("REBAR", "rebar", C.cage + 0.3, C.middle - 0.1, -140, 120, CYAN, null);
counter(0, 50, C.fifty - 0.05, C.middle - 0.1, n => `UP TO ${n}\nTONS`, 540, TOP_Y + 20, 980, 300, 120, GOLD, 2, 5);
show(text("100+ ANCHOR\nBOLTS", 540, TOP_Y + 20, 980, 300, 112, GOLD), C.anchor - 0.05, C.then - 0.1, "slam", "ting");
sound("ting", EV.bolts[1] - 0.3, 0.45);
tracked("ANCHOR BOLTS", "bolts", C.ring + 0.6, C.then - 0.1, -130, -120, GOLD, null);
show(text("POUR THE\nCONCRETE", 540, TOP_Y + 20, 980, 300, 116, WHITE), C.then - 0.05, C.five - 0.1, "rise", "whoosh");
sound("truck", EV.truck, 0.4); sound("pour", EV.pour[0], 0.45); sound("pour", EV.pour[0] + 2.0, 0.4);
counter(0, 500, C.five - 0.05, C.once - 0.1, n => `~${n}\nCUBIC YARDS`, 540, TOP_Y + 20, 980, 300, 112, GOLD, 2, 50);
tracked("CONCRETE", "concrete", C.pour + 0.6, C.once - 0.1, -150, 110, WHITE, null);
// B4 backfill: dirt back on top pins the slab, wider = harder to tip
show(text("DIRT GOES\nBACK ON TOP", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.once - 0.05, C.soils - 0.1, "rise", "whoosh");
sound("dump", EV.fill[0] + 0.3, 0.55); sound("thud", EV.fill[0] + 0.9, 0.45);
show(text("ITS WEIGHT\nPINS THE SLAB", 540, TOP_Y + 20, 980, 300, 104, GOLD), C.soils - 0.05, C.wider - 0.1, "slam", "down");
tracked("BACKFILL", "backfill", C.soils, C.wider - 0.1, -150, -110, GOLD, null);
show(text("WIDER =\nHARDER TO TIP", 540, TOP_Y + 20, 980, 300, 104, CYAN), C.wider - 0.05, C.now - 0.1, "slam", "ping");
sound("creak", EV.narrow_tip[0], 0.35);
// B5 tower: steel sections, crane, nuts, stack, 340 ft hub
show(text("GIANT STEEL\nSECTIONS", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.now - 0.05, C.crane - 0.1, "slam", "impact");
sound("clang", EV.sections + 0.2, 0.4);
tracked("TOWER SECTIONS", "sections", C.arrives, C.crane - 0.1, -140, -130, WHITE, null);
show(text("OVER THE\nANCHOR BOLTS", 540, TOP_Y + 20, 980, 300, 104, GOLD), C.crane - 0.05, C.tighten - 0.1, "rise", "whoosh");
sound("winch", EV.s1[0], 0.45); sound("clang", EV.s1[1] - 0.05, 0.55);
tracked("CRANE", "crane", C.crane + 0.2, C.tighten - 0.1, 140, -120, WHITE, null);
show(text("EVERY NUT\nTIGHTENED", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.tighten - 0.05, C.each - 0.1, "slam", "wrench");
sound("wrench", EV.nuts[0] + 0.4, 0.45); sound("wrench", EV.nuts[0] + 0.9, 0.4);
tracked("FLANGE", "flange", C.tighten + 0.1, C.each - 0.1, 150, -120, GOLD, null);
show(text("SECTION\nON SECTION", 540, TOP_Y + 20, 980, 300, 112, WHITE), C.each - 0.05, C.stacked - 0.1, "rise", "whoosh");
EV.stack.forEach(t => sound("clang", t - 0.05, 0.45));
counter(0, 340, C.three - 0.05, C.next - 0.1, n => `HUB ~${n} FT\nIN THE AIR`, 540, TOP_Y + 20, 980, 300, 104, CYAN, 2, 20);
show(text("STACKED UP", 540, TOP_Y, 980, 200, 116, WHITE), C.stacked - 0.05, C.three - 0.1, "slam", "riser");
// B6 nacelle (the machine room, ~50 tons on a smaller turbine)
show(text("THE BIG\nLIFT", 540, TOP_Y + 20, 980, 300, 120, WHITE), C.next - 0.05, C.nacelle - 0.1, "slam", "impact");
sound("winch", EV.nacelle[0], 0.45);
show(text("NACELLE", 540, TOP_Y, 980, 200, 128, WHITE), C.nacelle - 0.05, C.machine - 0.1, "pop", "pop");
show(text("THE MACHINE\nROOM", 540, TOP_Y + 20, 980, 300, 112, GOLD), C.machine - 0.05, C.fifty2 - 0.1, "rise", "whoosh");
sound("clang", EV.nacelle[1] - 0.05, 0.5);
tracked("GEARBOX", "gearbox", C.machine + 0.3, C.last - 0.1, 140, 120, GOLD, "pop");
tracked("GENERATOR", "generator", C.machine + 0.5, C.last - 0.1, 140, -120, CYAN, "pop");
counter(0, 50, C.fifty2 - 0.05, C.last - 0.1, n => `~${n} TONS`, 540, TOP_Y, 980, 200, 128, GOLD, 2, 5);
// B7 blades: 200+ ft each, one at a time OR the whole rotor
show(text("200+ FT\nEACH BLADE", 540, TOP_Y + 20, 980, 300, 112, WHITE), C.two - 0.05, C.some - 0.1, "slam", "whoosh");
show(text("THE BLADES", 540, TOP_Y, 980, 200, 124, GOLD), C.last - 0.05, C.two - 0.1, "rise", "whoosh");
sound("winch", EV.blade[0] + 0.2, 0.4);
tracked("BLADE", "blade", C.blades2, C.some - 0.1, 140, -130, GOLD, null);
show(text("ONE AT\nA TIME", 540, TOP_Y + 20, 980, 300, 120, WHITE), C.some - 0.05, C.others - 0.1, "slam", "pop");
sound("clang", EV.blade[1] - 0.05, 0.45);
show(text("OR THE WHOLE\nROTOR AT ONCE", 540, TOP_Y + 20, 980, 300, 100, GOLD), C.others - 0.05, C.and - 0.1, "slam", "whoosh");
sound("winch", EV.rotor[0] + 0.3, 0.45); sound("clang", EV.rotor[1] - 0.05, 0.5);
tracked("ROTOR", "rotor", C.raise, C.and - 0.1, 140, -120, WHITE, null);
// B8 loop: rotor spins, camera falls back to the buried slab = frame 1; no spoken tease, only small "PART 2 TOMORROW" text (15 Nov rule)
sound("whoosh", EV.loop, 0.5); sound("hum", EV.spin, 0.35);
show(text("EVERY TON\nRESTS ON THIS", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.and - 0.05, 71.8 + VO, "rise", "riser");
{ const p2 = text("PART 2: HOW IT MAKES POWER", 540, 1180, 900, 160, 64, GOLD, BODY, { stroke: 8, tracking: 20, name: "Part 2 tease" });
  const t0 = 71.8 + VO; p2.activeRange = R(ms(t0), DUR - ms(t0)); kf(p2.id, "opacity", [[0, 0], [150, 100]]); layers.push(p2); TITLES.push({ t0, t1: TL.duration, text: p2.sourceText.text }); }

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(concrete|rebar|anchor|bolts|dirt|slab|tower|crane|flange|nacelle|blades?|rotor|hub)/i;
const SYN = { "fifty": "50", "tons": "ton", "hundred": "num", "five": "500", "cubic": "cubic", "yards": "yard", "three": "340", "forty": "340", "feet": "ft", "two": "200", "sections": "section", "bolts": "bolt", "blades": "blade", "tip": "tip", "nut": "nut", "tighten": "tightened" };
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
const video = { type: "Video", id: 1, name: "Blender render - wind turbine build cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
