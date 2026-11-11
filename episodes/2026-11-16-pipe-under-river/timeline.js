// Pipe-Under-River-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  splash: { file: "splash", ms: 1200, vol: 0.5 }, birds: { file: "birds", ms: 3000, vol: 0.25 }, drill: { file: "drill-rumble", ms: 3000, vol: 0.5 },
  crumble: { file: "crumble", ms: 1400, vol: 0.6 }, slide: { file: "pipe-slide", ms: 1800, vol: 0.5 }, slurry: { file: "slurry", ms: 1400, vol: 0.5 },
  clank: { file: "rod-clank", ms: 700, vol: 0.5 }, whir: { file: "spin-whir", ms: 2000, vol: 0.45 }, beep: { file: "signal-beep", ms: 1600, vol: 0.4 },
  bubble: { file: "mud-bubble", ms: 2000, vol: 0.5 }, zap: { file: "weld-zap", ms: 400, vol: 0.35 }, boat: { file: "boat-motor", ms: 3000, vol: 0.3 },
  scoop: { file: "scoop", ms: 1200, vol: 0.55 },
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
// B1 hook: the claim (drilled under the river, steered), the stake (a trench tears up the riverbed)
show(text("THEY DRILL\nUNDER IT", 540, TOP_Y + 20, 980, 300, 120, WHITE), 0.15, C.steer - 0.1, "slam", "impact");
sound("whir", 0.2, 0.35); sound("drill", 0.4, 0.4); sound("boat", 1.5, 0.2);
show(text("STEERED THE\nWHOLE WAY", 540, TOP_Y + 20, 980, 300, 108, CYAN), C.steer - 0.05, C.dig2 - 0.1, "rise", "whoosh");
show(text("DIG A TRENCH?", 540, TOP_Y, 980, 200, 112, RED), C.dig2 - 0.05, C.tear - 0.1, "slam", "impact");
sound("scoop", EV.trench, 0.55); sound("scoop", EV.trench + 1.0, 0.45);
show(text("MUD\nDOWNSTREAM", 540, TOP_Y + 20, 980, 300, 112, RED), C.tear - 0.05, C.lets - 0.1, "slam", "deny");
sound("rush", C.mud1 - 0.3, 0.35);
// B2 build it up: a garden hose, then a gas main under the river
show(text("LET'S BUILD ONE", 540, TOP_Y, 980, 200, 104, WHITE), C.lets - 0.05, C.this - 0.1, "pop", "pop");
show(text("THIS IS A\nGARDEN HOSE", 540, TOP_Y + 20, 980, 300, 108, WHITE), C.this - 0.05, C.now - 0.1, "rise", "whoosh");
sound("birds", C.this, 0.25);
show(text("NOW: A GAS MAIN", 540, TOP_Y, 980, 200, 100, GOLD), C.now - 0.05, C.river2 - 0.1, "slam", "impact");
show(text("UNDER\nTHIS RIVER", 540, TOP_Y + 20, 980, 300, 112, WHITE), C.river2 - 0.2, C.so - 0.1, "rise", "pop");
// B3 the rig pushes a rod in at an angle; straight, it keeps going down
show(text("1. THE RIG", 540, TOP_Y, 980, 200, 116, WHITE), C.so - 0.05, C.pushes - 0.1, "rise", "whoosh");
tracked("DRILL RIG", "rig", C.rig, C.straight - 0.1, 130, -170, GOLD, "pop");
sound("clank", EV.push[0], 0.5); sound("whir", EV.push[0] + 0.1, 0.4); sound("drill", EV.push[0] + 0.2, 0.4);
show(text("A STEEL ROD,\nAT AN ANGLE", 540, TOP_Y + 20, 980, 300, 100, WHITE), C.pushes - 0.05, C.straight - 0.1, "pop", "pop");
show(text("STRAIGHT, IT\nKEEPS DIVING", 540, TOP_Y + 20, 980, 300, 100, RED), C.straight - 0.05, C.so2 - 0.1, "slam", "deny");
// B4 the slanted tip: spin = straight, push = it turns
show(text("2. A SLANTED TIP", 540, TOP_Y, 980, 200, 96, WHITE), C.so2 - 0.05, C.spin - 0.1, "rise", "whoosh");
tracked("SLANTED FACE", "slant", C.slanted, C.spin - 0.1, 130, -170, GOLD, "ping");
show(text("SPIN =\nSTRAIGHT", 540, TOP_Y + 20, 980, 300, 120, CYAN), C.spin - 0.05, C.stop - 0.1, "slam", "impact");
sound("whir", EV.spin[0], 0.5);
show(text("PUSH =\nIT TURNS", 540, TOP_Y + 20, 980, 300, 120, GOLD), C.stop - 0.05, C.a - 0.1, "slam", "impact");
sound("clank", C.stop, 0.4); sound("slide", EV.bend[0], 0.45);
// B5 transmitter: the crew knows where it is; pilot hole out on the far bank
show(text("3. TRANSMITTER", 540, TOP_Y, 980, 200, 100, CYAN), C.a - 0.05, C.tells - 0.1, "rise", "whoosh");
tracked("TRANSMITTER", "sonde", C.transmitter + 0.2, C.the - 0.1, 130, -170, CYAN, null);
sound("beep", C.transmitter, 0.4); sound("beep", C.tells + 0.3, 0.35);
show(text("CREW KNOWS\nWHERE IT IS", 540, TOP_Y + 20, 980, 300, 104, WHITE), C.tells - 0.05, C.the - 0.1, "pop", "pop");
show(text("UNDER THE\nRIVERBED", 540, TOP_Y + 20, 980, 300, 112, WHITE), C.the - 0.05, C.climbs - 0.1, "rise", "whoosh");
sound("drill", EV.dive[0], 0.45); sound("whir", EV.dive[0] + 1.5, 0.35);
show(text("OUT ON THE\nFAR BANK", 540, TOP_Y + 20, 980, 300, 112, GOLD), C.climbs - 0.05, C.but - 0.1, "slam", "impact");
sound("splash", EV.exit, 0.35);
// B6 the reamer
show(text("BARELY WIDER\nTHAN THE ROD", 540, TOP_Y + 20, 980, 300, 100, RED), C.but - 0.05, C.so3 - 0.1, "slam", "deny");
show(text("4. THE REAMER", 540, TOP_Y, 980, 200, 112, WHITE), C.so3 - 0.05, C.sometimes - 0.1, "rise", "whoosh");
tracked("REAMER", "reamer", C.reamer, C.pulled + 0.4, -130, -170, GOLD, "pop");
sound("whir", EV.ream1[0], 0.5); sound("drill", EV.ream1[0] + 0.1, 0.5);
show(text("SOMETIMES\nTWICE OR MORE", 540, TOP_Y + 20, 980, 300, 100, GOLD), C.sometimes - 0.05, C.now2 - 0.1, "pop", "pop");
sound("drill", EV.ream2[0], 0.4);
// B7 cave-in -> drilling mud (water + clay): holds the walls, carries cuttings out
show(text("WALLS CAVE IN", 540, TOP_Y, 980, 200, 108, RED), C.now2 - 0.05, C.so4 - 0.1, "slam", "deny");
sound("crumble", EV.cave, 0.6);
show(text("5. DRILLING MUD", 540, TOP_Y, 980, 200, 100, WHITE), C.so4 - 0.05, C.water - 0.1, "rise", "whoosh");
sound("slurry", EV.mud, 0.5); sound("hum", C.pump, 0.35);
show(text("WATER + CLAY", 540, TOP_Y, 980, 200, 112, GOLD), C.water - 0.05, C.it - 0.1, "slam", "impact");
tracked("DRILLING MUD", "mud", C.water, C.it - 0.1, 130, -170, GOLD, null);
show(text("HOLDS\nTHE WALLS", 540, TOP_Y + 20, 980, 300, 116, GOLD), C.it - 0.05, C.carries - 0.1, "slam", "impact");
show(text("CARRIES THE\nCUTTINGS OUT", 540, TOP_Y + 20, 980, 300, 100, WHITE), C.carries - 0.05, C.push2 - 0.1, "rise", "whoosh");
sound("slurry", C.carries + 0.2, 0.4);
// B8 the danger: too much pressure, mud bubbles up into the river
show(text("PUSH TOO HARD?", 540, TOP_Y, 980, 200, 104, RED), C.push2 - 0.05, C.bubbles - 0.1, "slam", "impact");
tracked("CRACK", "crack", C.hard, C.bubbles - 0.1, 130, -170, RED, null);
show(text("MUD IN\nTHE RIVER", 540, TOP_Y + 20, 980, 300, 120, RED), C.bubbles - 0.05, C.on - 0.1, "slam", "deny");
sound("bubble", EV.frac, 0.55);
// B9 the pipe: welded into one string, pulled back in one piece
show(text("6. ONE LONG PIPE", 540, TOP_Y, 980, 200, 96, GOLD), C.on - 0.05, C.then - 0.1, "rise", "whoosh");
EV.welds.forEach((t, k) => sound("zap", t, 0.3 - 0.015 * k));
tracked("WELDED STRING", "pipe", C.welded, C.then - 0.1, -130, -170, GOLD, "pop");
show(text("PULLED BACK\nIN ONE PIECE", 540, TOP_Y + 20, 980, 300, 100, WHITE), C.then - 0.05, C.the2 - 0.1, "slam", "impact");
sound("slide", EV.pull[0], 0.55); sound("drill", EV.pull[0] + 0.2, 0.4); sound("impact", EV.pull[1] - 0.1, 0.5);
show(text("BOATS NEVER\nNOTICE", 540, TOP_Y + 20, 980, 300, 112, GOLD), C.the2 - 0.05, C.how - 0.1, "rise", "ping");
sound("boat", C.the2, 0.3); sound("birds", C.boats, 0.2);
// B10 CTA: a question to the viewer, then the follow line naming the next episode (3d-24 lightning-rod)
show(text("HOW MANY PIPES\nUNDER YOUR\nNEAREST RIVER?", 540, TOP_Y + 40, 980, 330, 80, WHITE), C.how, C.next - 0.1, "slam", "whoosh");
EV.others.forEach(t => sound("ping", t, 0.35));
show(text("TELL ME IN THE COMMENTS", 540, TOP_Y + 250, 900, 80, 50, GOLD, BODY, { tracking: 60 }), C.tell, C.next - 0.1, "rise", "ping");
show(text("NEXT:\nLIGHTNING RODS", 540, TOP_Y + 20, 980, 300, 96, WHITE), C.next, C.end, "slam", "pop");
show(text("FOLLOW SO YOU DON'T MISS IT", 540, TOP_Y + 215, 940, 80, 46, GOLD, BODY, { tracking: 40 }), C.follow, C.end, "rise", "ping");
sound("birds", C.how + 1.0, 0.2); sound("boat", C.how + 3.0, 0.15);

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(drill|steer|trench|rig|rod|slant|transmitter|reamer|mud|pipe|welded|riverbed)/i;
const SYN = { "riverbed,": "riverbed", "it'd": "it", "doesn't": "doesn't" };
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
const video = { type: "Video", id: 1, name: "Blender render - pipe under river cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([540, 960], [540, 960]), source: { assetId: RENDER_ID, fit: "contain" } };
// slow push-in over the CTA
for (const p of ["scaleX", "scaleY"]) kf(video.id, p, [[ms(C.how), 100, "lin"], [DUR, 106, "lin"]]);
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
