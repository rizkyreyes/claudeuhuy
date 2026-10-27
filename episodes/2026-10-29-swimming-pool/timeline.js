// Swimming-Pool-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.6 }, slab: { file: "slab-drop", ms: 900, vol: 0.6 },
  excavator: { file: "excavator", ms: 2500, vol: 0.4 }, clank: { file: "rebar-clank", ms: 700, vol: 0.4 }, tie: { file: "tie-tick", ms: 80, vol: 0.35 },
  crack: { file: "concrete-crack", ms: 900, vol: 0.7 }, creak: { file: "squeeze-creak", ms: 800, vol: 0.45 }, pvc: { file: "pvc-click", ms: 250, vol: 0.45 },
  spray: { file: "shotcrete-spray", ms: 6000, vol: 0.32 }, trowel: { file: "trowel", ms: 1000, vol: 0.4 }, mist: { file: "mist", ms: 2000, vol: 0.3 },
  tile: { file: "tile-tap", ms: 200, vol: 0.4 }, stone: { file: "stone-set", ms: 500, vol: 0.5 }, fill: { file: "water-fill", ms: 3000, vol: 0.4 },
  hum: { file: "pump-hum", ms: 6000, vol: 0.25 }, lift: { file: "pool-lift", ms: 1800, vol: 0.65 }, glug: { file: "valve-glug", ms: 1200, vol: 0.5 },
  gun: { file: "cement-gun", ms: 4000, vol: 0.32 },
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
// B1 hook: the question over the finished pool, then the front half drops away
show(text("HOW IS A POOL\nACTUALLY BUILT?", 540, TOP_Y, 980, 300, 84, WHITE), C.how, C.lets - 0.08, "rise", "whoosh");
sound("riser", C.lets, 0.35, 1.05); sound("slab", EV.open + 0.3, 0.55); sound("whoosh", C.open, 0.45, 0.25);
// B2 dig: excavator, the hole bigger than the pool (cyan ghost outline)
show(text("DIG THE HOLE", 540, TOP_Y, 980, 200, 96, WHITE), C.digs - 0.05, C.bigger - 0.1, "slam", "impact");
tracked("EXCAVATOR", "excavator", C.crew, C.bigger - 0.1, -150, -150, GOLD);
sound("excavator", EV.dig[0] - 0.3, 0.4); sound("excavator", EV.dig[0] + 2.0, 0.3);
show(text("A LITTLE BIGGER", 540, TOP_Y, 980, 200, 88, CYAN), C.bigger, C.next - 0.1, "rise", "ping");
// B3 steel cage: floor, walls, steps
show(text("STEEL CAGE", 540, TOP_Y, 980, 200, 104, GOLD), C.cage, C.floor - 0.1, "slam", "impact");
for (let k = 0; k < 8; k++) sound(k % 2 ? "tie" : "clank", C.floor - 0.8 + k * 0.32, k % 2 ? 0.3 : 0.32);
tracked("FLOOR", "cage_floor", C.floor, C.walls - 0.1, -150, 150, GOLD);
tracked("WALLS", "cage_wall", C.walls, C.steps - 0.1, -150, -150, GOLD, "clank");
tracked("STEPS", "steps", C.steps, C.concrete - 0.15, 150, -150, GOLD, "clank");
// B4 beam demo: squeezed is fine, pulled cracks, steel takes the pull
show(text("CONCRETE", 540, TOP_Y, 980, 200, 104, WHITE), C.concrete, C.squeezed - 0.1, "slam", "whoosh");
show(text("SQUEEZED: FINE", 540, TOP_Y, 980, 200, 92, GOLD), C.squeezed, C.cracks - 0.1, "slam", "impact");
sound("creak", EV.squeeze, 0.45);
show(text("PULLED: CRACKS", 540, TOP_Y, 980, 200, 92, RED), C.cracks, C.steel2 - 0.1, "slam", null);
sound("crack", EV.beam_crack, 0.7); sound("deny", EV.beam_crack + 0.05, 0.5);
show(text("STEEL TAKES\nTHE PULL", 540, TOP_Y, 980, 300, 92, GOLD), C.steel2, C.then - 0.1, "slam", "clank");
tracked("STEEL BAR", "beam_bar", C.steel2 + 0.2, C.then - 0.15, -150, -150, GOLD, null);
// B5 plumbing
show(text("PLUMBING", 540, TOP_Y, 980, 200, 110, WHITE), C.plumbing, C.main - 0.05, "slam", "impact");
tracked("MAIN DRAIN", "drain", C.main, C.skimmer - 0.1, 150, -150, GOLD, "pvc");
tracked("SKIMMER", "skimmer", C.skimmer, C.return - 0.1, -150, -150, GOLD, "pvc");
tracked("RETURN JETS", "jet", C.return, C.now - 0.1, 150, -150, CYAN, "pvc");
// B6 the sprayed shell: gunite (dry) / shotcrete (wet), smoothed by hand
show(text("NOW THE FUN PART", 540, TOP_Y, 980, 200, 86, GOLD), C.now, C.hose - 0.1, "rise", "riser");
tracked("CONCRETE HOSE", "nozzle", C.hose, C.dry - 0.1, -150, -150, GOLD);
sound("spray", EV.spray[0], 0.32); sound("spray", EV.spray[0] + 5.6, 0.25);
show(text("GUNITE", 540, TOP_Y - 30, 980, 180, 118, WHITE), C.dry, C.wet - 0.1, "slam", "impact");
show(text("DRY MIX", 540, TOP_Y + 110, 600, 80, 52, GOLD, BODY, { tracking: 60 }), C.dry, C.wet - 0.1, "rise", null);
show(text("SHOTCRETE", 540, TOP_Y - 30, 980, 180, 110, WHITE), C.wet, C.crew2 - 0.1, "slam", "impact");
show(text("WET MIX", 540, TOP_Y + 110, 600, 80, 52, CYAN, BODY, { tracking: 60 }), C.wet, C.crew2 - 0.1, "rise", null);
show(text("SMOOTHED BY HAND", 540, TOP_Y, 980, 200, 84, WHITE), C.smooths, C.then2 - 0.1, "rise", "whoosh");
sound("trowel", C.smooths + 0.1, 0.4);
// B7 curing
show(text("KEPT WET\nWHILE IT CURES", 540, TOP_Y, 980, 300, 84, CYAN), C.wet2 - 0.05, C.tile - 0.1, "rise", "ping");
sound("mist", EV.cure[0], 0.3);
// B8 finishes: tile, coping, plaster; bare concrete seeps
tracked("WATERLINE TILE", "tile", C.tile, C.coping - 0.1, -120, -170, CYAN);
for (let k = 0; k < 5; k++) sound("tile", C.tile + 0.1 + k * 0.18, 0.35);
tracked("COPING", "coping", C.coping, C.plaster - 0.1, 150, -170, GOLD, "stone");
show(text("PLASTER SEALS IT", 540, TOP_Y, 980, 200, 86, WHITE), C.plaster, C.because - 0.1, "slam", "impact");
show(text("BARE CONCRETE\nSEEPS", 540, TOP_Y, 980, 300, 92, RED), C.bare, C.fill - 0.1, "slam", "deny");
tracked("WATER SEEPS OUT", "seep", C.seep - 0.3, C.fill - 0.15, -150, 150, RED, null);
// B9 fill + the loop
show(text("FILL IT UP", 540, TOP_Y, 980, 200, 104, CYAN), C.fill, C.loop - 0.1, "slam", "whoosh");
sound("fill", EV.fill[0], 0.4);
show(text("THE LOOP", 540, TOP_Y, 980, 200, 110, WHITE), C.loop, C.pump - 0.1, "slam", "impact");
sound("hum", C.pump - 0.2, 0.25);
tracked("PUMP", "pump", C.pump, C.pushes + 0.2, -150, -170, GOLD);
tracked("FILTER", "filter", C.pushes + 0.35, C.sends - 0.05, -150, -170, GOLD);   // the camera reaches the filter on "pushes"
show(text("BACK OUT\nTHE JETS", 540, TOP_Y, 980, 300, 92, CYAN), C.sends, C.heres - 0.1, "rise", "whoosh");
// B10 the scary part: empty pool + high groundwater = it floats
show(text("HERE'S THE\nSCARY PART", 540, TOP_Y, 980, 300, 92, RED), C.heres, C.drain3 - 0.1, "rise", "riser");
show(text("DRAIN IT EMPTY", 540, TOP_Y, 980, 200, 88, WHITE), C.drain3, C.groundwater - 0.1, "slam", "down");
show(text("HIGH GROUNDWATER", 540, TOP_Y, 980, 200, 82, CYAN), C.groundwater, C.float - 0.1, "rise", "impact");
show(text("IT FLOATS UP!", 540, TOP_Y, 980, 200, 104, RED), C.float, C.thats - 0.1, "slam", "deny");
sound("lift", EV.float[0], 0.65);
// B11 relief valve
tracked("RELIEF VALVE", "valve", C.relief, C.and - 0.1, -150, -150, GOLD, "ping");
show(text("LETS GROUNDWATER IN", 540, TOP_Y, 980, 200, 76, CYAN), C.lets2, C.and - 0.1, "rise", null);
sound("glug", EV.valve_flow[0] + 0.2, 0.5);
// B12 history: the cement gun, Carl Akeley, a museum in Chicago (name only, no likeness)
sound("whoosh", EV.set_b[0], 0.5, 0.25); sound("gun", EV.gun_spray[0], 0.3); sound("gun", EV.gun_spray[0] + 3.8, 0.25);
show(text("THE CONCRETE GUN", 540, TOP_Y, 980, 200, 84, GOLD), C.and, C.taxidermist - 0.1, "rise", "impact");
tracked("CEMENT GUN", "gun", C.gun, C.carl - 0.1, -150, -170, GOLD);
show(text("A TAXIDERMIST", 540, TOP_Y, 980, 200, 92, WHITE), C.taxidermist, C.carl - 0.1, "slam", "impact");
show(text("CARL AKELEY", 540, TOP_Y, 980, 200, 104, WHITE), C.carl, C.hundred - 0.1, "slam", "impact");
show(text("100+ YEARS AGO", 540, TOP_Y, 980, 200, 96, GOLD), C.hundred, C.museum - 0.1, "slam", "tick");
show(text("A CHICAGO MUSEUM", 540, TOP_Y, 980, 200, 84, WHITE), C.museum, C.would - 0.1, "rise", "whoosh");
tracked("FRESH PLASTER", "patch", C.replaster, C.would - 0.1, 150, 150, GOLD, null);
// B13 CTA: a question to the viewer (comments), no channel name
show(text("CONCRETE POOL OR\nABOVE-GROUND?", 540, TOP_Y, 980, 300, 76, WHITE), C.would, C.end, "slam", "whoosh");
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
const HL = /^(pool|hole|steel|cage|concrete|squeezed|cracks|pulled|plumbing|drain|skimmer|jets|hose|gunite|shotcrete|cures|tile|coping|plaster|seep|pump|filter|groundwater|float|valve|gun|taxidermist|akeley|museum)/i;
const SYN = { "it's": "it", hundred: "100", bars: "bar", jets: "jet", steps: "step", walls: "wall", cures: "cure", seals: "seal", smooths: "smoothed", pools: "pool", floats: "float", lets: "let", "here's": "here" };
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
  sourceIntrinsicDuration: VO_MS, source: { assetId: "vo" }, volume: 0.82, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, Math.min(DUR, 76000)), sourceRange: R(0, Math.min(DUR, 76000)),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.30, captionsEnabled: false });
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - pool cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
