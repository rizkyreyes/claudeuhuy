// Tower-Crane-Climb-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  strain: { file: "rope-strain", ms: 1200, vol: 0.4 }, motor: { file: "motor-hum", ms: 4000, vol: 0.3 }, clamp: { file: "brake-clamp", ms: 600, vol: 0.6 },
  release: { file: "magnet-release", ms: 300, vol: 0.45 }, powerdown: { file: "power-down", ms: 900, vol: 0.45 }, snap: { file: "rope-snap", ms: 900, vol: 0.75 },
  cwland: { file: "cw-land", ms: 700, vol: 0.35 }, whirr: { file: "governor-whirr", ms: 3500, vol: 0.35 }, clack: { file: "pawl-clack", ms: 250, vol: 0.55 },
  lock: { file: "governor-lock", ms: 500, vol: 0.6 }, yank: { file: "lever-yank", ms: 400, vol: 0.5 }, bite: { file: "wedge-bite", ms: 700, vol: 0.6 },
  grind: { file: "rail-grind", ms: 7000, vol: 0.32 }, boing: { file: "buffer-spring", ms: 900, vol: 0.5 }, hiss: { file: "oil-hiss", ms: 800, vol: 0.35 },
  creak: { file: "wood-creak", ms: 4000, vol: 0.35 }, twang: { file: "rope-cut", ms: 600, vol: 0.65 }, ratchet: { file: "ratchet-catch", ms: 500, vol: 0.6 },
  hyd: { file: "hydraulic-whine", ms: 3000, vol: 0.30 }, wind: { file: "wind-gust", ms: 1500, vol: 0.40 },
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
// B1 hook
show(text("HOW DOES A CRANE\nBUILD ITSELF?", 540, TOP_Y, 980, 300, 80, WHITE), C.how, C.lets - 0.08, "rise", "whoosh");
sound("riser", C.lets, 0.35, 1.05); sound("whoosh", C.cut, 0.45, 0.25);
// B2 it starts small: a mobile crane stands up the first pieces
show(text("IT STARTS SMALL", 540, TOP_Y, 980, 200, 96, WHITE), C.starts, C.mobile - 0.1, "slam", "impact");
tracked("MOBILE CRANE", "mobile", C.mobile, C.stands + 0.6, 150, -150, GOLD);
for (const k of ["drop_base", "drop_m1", "drop_m2", "drop_slew", "drop_jib", "drop_cw"]) sound("slab", EV[k] + 0.55, 0.5, 0.12);
sound("motor", EV.mobile[0] + 0.2, 0.22);
tracked("MAST SECTIONS", "mast", C.mast - 0.1, C.cab - 0.2, 150, 150, GOLD);
tracked("COUNTERWEIGHTS", "cweights", C.counterweights, C.after + 0.1, 150, -150, WHITE, "pop");
show(text("IT GROWS WITH\nTHE BUILDING", 540, TOP_Y, 980, 300, 84, GOLD), C.grows - 0.1, C.heres - 0.1, "rise", "pop");
sound("hyd", EV.timelapse[0] + 0.1, 0.22);
// B3 the trick: a climbing frame around the mast
show(text("THE TRICK", 540, TOP_Y, 980, 200, 110, GOLD), C.heres, C.under + 0.2, "slam", "impact");
tracked("CLIMBING FRAME", "frame", C.climbing, C.operator - 0.1, 150, -170, CYAN);
show(text("WRAPS AROUND\nTHE MAST", 540, TOP_Y, 980, 300, 88, WHITE), C.wraps - 0.1, C.operator - 0.1, "rise", "pop");
// B4 balance the crane first
show(text("STEP 1:\nBALANCE IT", 540, TOP_Y, 980, 300, 100, WHITE), C.operator, C.then - 0.1, "slam", "impact");
tracked("TROLLEY", "trolley", C.trolley, C.balanced - 0.1, 150, -160, GOLD);
sound("motor", EV.trolley[0], 0.2);
tracked("COUNTERWEIGHTS", "cweights", C.balanced, C.then - 0.1, 150, 150, GOLD, null);
// B5 hook a new section
show(text("STEP 2:\nHOOK A SECTION", 540, TOP_Y, 980, 300, 88, WHITE), C.then, C.now - 0.1, "slam", "impact");
tracked("NEW SECTION", "section", C.new, C.now - 0.1, 150, -150, GOLD);
sound("strain", EV.pick[0] + 0.9, 0.3); sound("slab", EV.pick[1], 0.45, 0.1);
// B6 lift the whole top with hydraulic rams
show(text("STEP 3:\nLIFT THE TOP", 540, TOP_Y, 980, 300, 100, WHITE), C.now, C.hydraulic - 0.1, "slam", "impact");
show(text("HYDRAULIC RAMS", 540, TOP_Y, 980, 200, 88, CYAN), C.hydraulic, C.lift - 0.1, "slam", "pop");
tracked("RAM", "ram", C.rams, C.entire - 0.1, -150, -150, CYAN);
sound("hyd", EV.lift[0] + 0.0, 0.33);
show(text("THE ENTIRE TOP\nGOES UP", 540, TOP_Y, 980, 300, 84, WHITE), C.entire, C.that - 0.1, "rise", "pop");
// B7 the gap
show(text("A ONE-SECTION GAP", 540, TOP_Y, 980, 200, 84, GOLD), C.opens, C.crane2 - 0.1, "slam", "impact");
tracked("GAP", "gap", C.opens + 0.3, C.crane2 + 0.2, 150, -120, CYAN, null);
// B8 slide it in, lock it
show(text("SLIDE IT IN", 540, TOP_Y, 980, 200, 104, WHITE), C.slides2, C.crew - 0.1, "slam", "whoosh");
sound("strain", EV.slide[0] + 0.0, 0.3);
show(text("LOCKED", 540, TOP_Y, 980, 200, 128, CYAN), C.locks, C.then2 - 0.1, "slam", "clamp");
// B9 rams let go, the crane is taller
show(text("RAMS LET GO", 540, TOP_Y, 980, 200, 100, WHITE), C.then2, C.weight - 0.1, "slam", "release");
show(text("WEIGHT SETTLES", 540, TOP_Y, 980, 200, 92, GOLD), C.weight, C.longer - 0.1, "slam", "impact");
sound("cwland", EV.settle[1] - 0.35, 0.3);
show(text("TALLER!", 540, TOP_Y, 980, 200, 150, GOLD), C.taller2 - 0.1, C.repeats - 0.1, "slam", "ping");
// B10 repeat
show(text("REPEAT", 540, TOP_Y, 980, 200, 128, WHITE), C.repeats, C.climbs - 0.1, "slam", "impact");
sound("hyd", EV.repeat1[0], 0.3); sound("hyd", EV.repeat2[0], 0.3);
show(text("AS THE BUILDING\nCLIMBS", 540, TOP_Y, 980, 300, 88, GOLD), C.climbs, C.one - 0.1, "rise", "pop");
// B11 one strict rule
show(text("ONE STRICT RULE", 540, TOP_Y, 980, 200, 92, GOLD), C.one, C.jib4 - 0.1, "slam", "impact");
show(text("NO SWINGING", 540, TOP_Y, 980, 200, 110, RED), C.swing - 0.2, C.twisting - 0.1, "slam", "riser");
sound("strain", EV.swing[0], 0.35);
show(text("TWISTING CAN\nDAMAGE THE MAST", 540, TOP_Y, 980, 300, 84, RED), C.twisting, C.as - 0.1, "rise", "deny");
// B12 ties and wind
show(text("STEEL TIES", 540, TOP_Y, 980, 200, 120, GOLD), C.steel, C.building2 - 0.1, "slam", "impact");
tracked("TIE", "tie", C.ties, C.wind - 0.1, 150, -150, WHITE, null);
tracked("TIE", "tie_lo", C.ties + 0.4, C.wind - 0.1, 150, 150, WHITE, null);
sound("bite", EV.ties[0] + 0.2, 0.5); sound("bite", EV.ties[0] + 0.65, 0.5); sound("bite", EV.ties[0] + 1.1, 0.5);
show(text("WIND CAN'T\nTIP IT", 540, TOP_Y, 980, 300, 96, CYAN), C.wind, C.some - 0.1, "slam", null);
sound("wind", EV.wind - 0.1, 0.4);
// B13 inside the elevator shaft
show(text("SOME CLIMB INSIDE", 540, TOP_Y, 980, 200, 84, WHITE), C.some, C.elevator - 0.1, "slam", "whoosh");
show(text("THE ELEVATOR\nSHAFT", 540, TOP_Y, 980, 300, 92, GOLD), C.elevator, C.so - 0.1, "slam", "impact");
tracked("COLLAR", "b_collar", C.inside, C.so - 0.1, 150, -150, GOLD);
sound("hyd", EV.climb_b[0], 0.3); sound("hyd", EV.climb_b[2], 0.3);
// B14 it builds itself
show(text("THE MACHINE THAT\nBUILDS THE CITY", 540, TOP_Y, 980, 300, 80, WHITE), C.machine, C.also - 0.1, "rise", "whoosh");
sound("hyd", EV.final_climb[0], 0.28);
show(text("ALSO BUILDS\nITSELF", 540, TOP_Y, 980, 300, 108, GOLD), C.also, C.would - 0.1, "slam", "impact");
// B15 CTA: a question to the viewer (comments), no channel name
show(text("WOULD YOU WORK\nIN THAT CAB?", 540, TOP_Y, 980, 300, 92, WHITE), C.would, C["if"] - 0.1, "slam", "whoosh");
show(text("TELL ME IN THE COMMENTS", 540, TOP_Y + 215, 900, 80, 50, GOLD, BODY, { tracking: 60 }), C.tell, C["if"] - 0.1, "rise", "ping");
// fixed closing follow line (playbook, 28 Oct)
show(text("FOUND THIS\nUSEFUL?", 540, TOP_Y, 980, 300, 100, WHITE), C["if"], C.end, "slam", "pop");
show(text("FOLLOW FOR MORE", 540, TOP_Y + 215, 900, 80, 56, GOLD, BODY, { tracking: 60 }), C.follow, C.end, "rise", "ping");

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(crane|tower|mast|jib|trolley|frame|hydraulic|rams|counterweights?|section|gap|ties|wind|elevator|shaft|cab|climbing)/i;
const SYN = { cranes: "crane", sections: "section", locks: "locked", rises: "rise", climbs: "climb", climbing: "climb", rams: "ram", ties: "tie", counterweights: "counterweight", "one-section": "section" };
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
const video = { type: "Video", id: 1, name: "Blender render - tower crane cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
