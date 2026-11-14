// City-Sewers-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  flush: { file: "flush", ms: 2200, vol: 0.6 }, gurgle: { file: "gurgle", ms: 1400, vol: 0.45 }, flow: { file: "pipe-flow", ms: 3000, vol: 0.25 },
  splash: { file: "splash", ms: 700, vol: 0.45 }, clank: { file: "cover-clank", ms: 800, vol: 0.6 }, scrape: { file: "cover-scrape", ms: 700, vol: 0.45 },
  dig: { file: "dig-scoop", ms: 900, vol: 0.55 }, pump: { file: "pump-hum", ms: 3000, vol: 0.4 }, click: { file: "float-click", ms: 250, vol: 0.55 },
  rush: { file: "pressure-rush", ms: 1500, vol: 0.45 }, street: { file: "street-tone", ms: 3000, vol: 0.18 }, cash: { file: "coin-drop", ms: 600, vol: 0.45 },
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
// ambience: street room tone outside the demo studio; flowing water whenever a pipe with flow is on screen
for (let t = 0; t < TL.duration - 0.5; t += 2.9) if (!(t > C.lay - 0.3 && t < C.backup)) sound("street", t, 0.16);
for (let t = C.rolls; t < TL.duration - 0.5; t += 2.9) if (!(t > C.this - 0.3 && t < C.every)) sound("flow", t, 0.18);
// B1 hook: the claim, the answer (gravity, pipes always tilt downhill), the stake (too flat -> backup in your house)
show(text("GRAVITY DOES\nTHE WORK", 540, TOP_Y + 20, 980, 300, 112, WHITE), 0.15, C.rolls - 0.1, "slam", "impact");
sound("flush", EV.flushes[0] - 0.05, 0.4); sound("gurgle", EV.slugs[0][0] + 0.6, 0.35);
tracked("TOILET", "toilet", 0.4, C.gravity - 0.1, 140, -110, WHITE, "pop");
show(text("ALWAYS\nDOWNHILL", 540, TOP_Y + 20, 980, 300, 128, CYAN), C.always - 0.05, C.lay - 0.1, "slam", "whoosh");
sound("whoosh", C.rolls - 0.05, 0.4);
show(text("TOO FLAT?", 540, TOP_Y, 980, 200, 132, RED), C.lay - 0.05, C.stops - 0.1, "slam", "deny");
sound("scrape", EV.demo_flat[0], 0.3);
show(text("IT STOPS", 540, TOP_Y, 980, 200, 132, RED), C.stops - 0.05, C.backup - 0.1, "slam", "impact");
show(text("IT COMES UP\nIN YOUR HOUSE", 540, TOP_Y + 20, 980, 300, 100, RED), C.backup - 0.05, C.this - 0.1, "rise", "down");
sound("gurgle", EV.backup_spurt - 0.3, 0.55); sound("splash", EV.pool[0], 0.45);
tracked("FLOOR DRAIN", "floordrain", C.lowest - 0.1, C.this - 0.1, 140, -140, RED, "pop");
// B3 this is a toilet -> the pipe under the floor
show(text("THIS IS A\nTOILET", 540, TOP_Y + 20, 980, 300, 128, WHITE), C.this - 0.05, C.flushes - 0.1, "rise", "whoosh");
sound("flush", EV.flushes[1] - 0.05, 0.42);
show(text("DOWN THE\nPIPE", 540, TOP_Y + 20, 980, 300, 128, GOLD), C.drops - 0.05, C.that - 0.1, "slam", "impact");
sound("gurgle", C.drops + 0.2, 0.4);
tracked("STACK", "stack", C.pipe, C.that - 0.1, 140, 0, GOLD, "pop");
// B4 it leaves the house tilted: a quarter inch every foot = the lateral
show(text("IT LEAVES\nTILTED", 540, TOP_Y + 20, 980, 300, 128, WHITE), C.that - 0.05, C.quarter - 0.1, "rise", "whoosh");
sound("ping", EV.level_line, 0.35);
show(text("1/4 INCH\nEVERY FOOT", 540, TOP_Y + 20, 980, 300, 120, CYAN), C.quarter - 0.05, C.lateral - 0.1, "slam", "impact");
sound("tick", EV.drop_bar + 0.2, 0.4);
show(text("YOUR\nLATERAL", 540, TOP_Y + 20, 980, 300, 132, GOLD), C.lateral - 0.1, C.runs - 0.1, "slam", "ping");
tracked("LATERAL", "lateral", C.lateral, C.street - 0.1, 0, -150, GOLD, "pop");
// B5 under the yard to the sewer main under the street
show(text("UNDER\nTHE STREET", 540, TOP_Y + 20, 980, 300, 124, WHITE), C.bigger - 0.05, C.sewer - 0.1, "rise", "whoosh");
show(text("THE SEWER\nMAIN", 540, TOP_Y + 20, 980, 300, 132, GOLD), C.sewer - 0.05, C.every - 0.1, "slam", "impact");
sound("splash", EV.slugs[1][1], 0.4);
tracked("SEWER MAIN", "maina", C.sewer, C.every - 0.1, -140, -150, GOLD, "pop");
// B6 every house on the block ties in
show(text("EVERY HOUSE\nTIES IN", 540, TOP_Y + 20, 980, 300, 118, WHITE), C.every - 0.05, C.the - 0.1, "rise", "whoosh");
EV.jets.forEach(t => sound("splash", t, 0.4));
// B7 the main tilts too; fast enough to carry solids
show(text("THE MAIN\nTILTS TOO", 540, TOP_Y + 20, 980, 300, 124, CYAN), C.the - 0.05, C.flow - 0.1, "slam", "whoosh");
show(text("FAST ENOUGH\nTO CARRY SOLIDS", 540, TOP_Y + 20, 980, 300, 96, WHITE), C.flow - 0.05, C.every2 - 0.1, "rise", "riser");
// B8 manholes: a turn, a slope change, a size change; crews reach it
show(text("A TURN", 540, TOP_Y, 980, 200, 132, WHITE), C.turns - 0.1, C.slope - 0.1, "pop", "ping");
tracked("TURN", "m0", C.turns, C.slope - 0.1, 150, -100, CYAN, null);
show(text("A NEW SLOPE", 540, TOP_Y, 980, 200, 118, WHITE), C.slope - 0.1, C.bigger2 - 0.1, "pop", "ping");
show(text("A BIGGER PIPE", 540, TOP_Y, 980, 200, 110, WHITE), C.bigger2 - 0.1, C.manhole - 0.1, "pop", "ping");
show(text("= A MANHOLE", 540, TOP_Y, 980, 200, 124, CYAN), C.manhole - 0.05, C.downhill2 - 0.1, "slam", "impact");
sound("clank", EV.cover_lift[0] + 0.05, 0.42); sound("scrape", EV.cover_lift[0] + 0.3, 0.45);
tracked("MANHOLE", "m1", C.crews, C.downhill2 - 0.1, 150, -60, CYAN, "pop");
// B9 small mains join into bigger ones
show(text("SMALL MAINS\nJOIN BIGGER ONES", 540, TOP_Y + 20, 980, 300, 96, WHITE), C.downhill2 - 0.05, C.but - 0.1, "rise", "whoosh");
sound("splash", EV.side_jet, 0.45); sound("riser", C.bigger3 - 0.2, 0.3);
// B10 the catch: flat ground, the pipe keeps getting deeper; too deep = very expensive to dig
show(text("THE CATCH", 540, TOP_Y, 980, 200, 132, RED), C.but - 0.05, C.flat2 - 0.1, "slam", "deny");
show(text("FLAT\nGROUND", 540, TOP_Y + 20, 980, 300, 132, WHITE), C.flat2 - 0.05, C.tilting - 0.1, "rise", "whoosh");
show(text("DEEPER AND\nDEEPER", 540, TOP_Y + 20, 980, 300, 118, RED), C.tilting - 0.05, C.too - 0.1, "slam", "down");
show(text("TOO DEEP", 540, TOP_Y, 980, 200, 140, RED), C.too - 0.05, C.digging - 0.1, "slam", "deny");
EV.dig && [0, 0.45, 0.9].forEach(d => sound("dig", EV.dig[0] + d, 0.5));
show(text("$$$", 540, TOP_Y, 980, 200, 150, RED), C.expensive - 0.15, C.so - 0.1, "slam", "cash");
// B11 the lift station: wet well, float switch, pump
show(text("A LIFT\nSTATION", 540, TOP_Y + 20, 980, 300, 132, GOLD), C.lift - 0.1, C.sewage - 0.1, "slam", "impact");
sound("impact", EV.lift_drop[1], 0.5);
show(text("THE WET\nWELL", 540, TOP_Y + 20, 980, 300, 132, WHITE), C.wet - 0.1, C.float - 0.1, "rise", "whoosh");
sound("flow", EV.pour, 0.35); sound("splash", EV.pour + 0.1, 0.45);
tracked("WET WELL", "wetwell", C.pit, C.float - 0.1, 160, 0, WHITE, "pop");
show(text("FLOAT\nSWITCH", 540, TOP_Y + 20, 980, 300, 132, GOLD), C.float - 0.05, C.pushes - 0.1, "slam", "click");
tracked("FLOAT", "float", C.float, C.pushes - 0.1, -160, -80, GOLD, null);
tracked("PUMP", "pump", C.starts, C.pushes + 1.5, 160, 60, CYAN, "pop");
sound("pump", EV.pump_start, 0.4); sound("pump", EV.pump_start + 2.9, 0.35);
// B12 force main up to a higher manhole, gravity again
show(text("PUSHED\nUPHILL", 540, TOP_Y + 20, 980, 300, 132, CYAN), C.pushes - 0.05, C.force - 0.1, "slam", "rush");
EV.fm_pulses.slice(1).forEach(t => sound("rush", t, 0.3));
show(text("THE FORCE\nMAIN", 540, TOP_Y + 20, 980, 300, 132, CYAN), C.force - 0.05, C.gravity2 - 0.1, "rise", "whoosh");
tracked("FORCE MAIN", "forcemain", C.force, C.gravity2 - 0.1, 0, -150, CYAN, "pop");
show(text("GRAVITY\nAGAIN", 540, TOP_Y + 20, 980, 300, 132, GOLD), C.gravity2 - 0.05, C.america - 0.1, "slam", "impact");
// B13 800,000 miles of public sewers, all running to treatment plants
counter(0, 800000, C.eight - 0.05, C.treatment - 0.1, n => `${n.toLocaleString("en-US")}\nMILES`, 540, TOP_Y + 20, 980, 300, 124, GOLD, 2, 100000);
show(text("TREATMENT\nPLANT", 540, TOP_Y + 20, 980, 300, 124, WHITE), C.treatment - 0.05, C.would - 0.1, "rise", "whoosh");
tracked("TREATMENT PLANT", "plant", C.treatment, C.would - 0.1, -160, -120, WHITE, null);
// B14 tail (rule 12 Nov): question + next tease spoken in ~3 s; comments + follow only as on-screen text, hard cut
show(text("WOULD YOU\nGO DOWN ONE?", 540, TOP_Y + 20, 980, 300, 110, WHITE), C.would - 0.05, C.nextup - 0.1, "slam", "clank");
show(text("TELL ME IN THE COMMENTS", 540, TOP_Y + 215, 900, 80, 50, GOLD, BODY, { tracking: 60 }), C.would + 0.3, C.nextup - 0.1, "rise", "ping");
show(text("NEXT:\nAIRPORT RUNWAYS", 540, TOP_Y + 20, 980, 300, 100, WHITE), C.nextup - 0.05, C.end, "slam", "pop");
show(text("FOLLOW SO YOU DON'T MISS IT", 540, TOP_Y + 215, 940, 80, 46, GOLD, BODY, { tracking: 40 }), C.nextup + 0.25, C.end, "rise", "ping");

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(gravity|downhill|lateral|sewer|main|manhole|lift|pump|force|tilt)/i;
const SYN = { "eight": "800000", "hundred": "800000", "thousand": "800000", "800,000": "800000", "tilted": "tilt", "tilts": "tilt", "tilting": "tilt", "mains": "main", "plants": "plant", "manholes": "manhole", "deeper": "deep", "1/4": "quarter", "pushes": "pushed", "flat": "flat", "ones": "bigger" };
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
const video = { type: "Video", id: 1, name: "Blender render - city sewer cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([540, 960], [540, 960]), source: { assetId: RENDER_ID, fit: "contain" } };
// slow push-in over the CTA (manhole shot)
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
