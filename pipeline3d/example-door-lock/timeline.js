// Door-Lock-3D Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
// Cues come from blender/timeline.json (resolved from the voice-over words). Writes editable.json + edits.json.
// Env: RENDER_ID (video asset), RENDER_MS (its duration).
const fs = require("fs"), path = require("path");
const D = __dirname;
const TL = JSON.parse(fs.readFileSync(path.join(D, "blender/timeline.json"), "utf8"));
const VOM = JSON.parse(fs.readFileSync(path.join(D, "../assets/vo/audio_meta.json"), "utf8"));
const C = TL.cues, FPS = TL.fps, DUR = Math.round(TL.duration * 1000), VO = TL.vo_offset;
const ms = s => Math.round(s * 1000);
const A = (name, t) => TL.anchors[name][Math.max(0, Math.min(TL.frames - 1, Math.round(t * FPS)))];
const T = (pos, anchor = [0, 0], s = 100, rot = 0, op = 100) => ({ anchorPoint: anchor, position: pos, scale: [s, s], rotation: rot, opacity: op });
const R = (start, dur) => ({ start: Math.round(start), duration: Math.max(1, Math.round(dur)) });

// ---- palette + type ----
const WHITE = [1, 1, 1, 1], GOLD = [0.98, 0.74, 0.27, 1], CYAN = [0.3, 0.92, 1, 1], RED = [1, 0.3, 0.24, 1], INK = [0, 0, 0, 1];
const DISPLAY = { fontFamily: "Anton", fontStyle: "Regular" }, BODY = { fontFamily: "Poppins", fontStyle: "ExtraBold" };
let NEXT_ID = 100; const id = () => NEXT_ID++;
const layers = [], edits = [], audio = [];
const kf = (layerId, prop, keys) => edits.push({ type: "setFxPropertyKeyframes", compositionId: "main", property: { layerId, propertyType: prop },
  keyframes: keys.map(([t, v, e], i) => ({ id: `L${layerId}-${prop}-${i}`, layerTime: Math.round(t), value: { type: "float", value: v },
    easing: e === "hold" ? { type: "hold" } : e === "lin" ? { type: "linear" } : { type: "cubicBezier", x1: 0.2, y1: 0, x2: 0.1, y2: 1 } })) });

function text(str, x, y, w, h, size, color, font = DISPLAY, opts = {}) {
  return { type: "Text", id: id(), name: opts.name || `Type - ${str.replace(/\n/g, " ")}`, blendMode: "normal",
    activeRange: R(0, 1000), transform: T([x, y], [w / 2, h / 2]),
    sourceText: { text: str, ...font, fontSize: size, fillColor: color, applyStroke: !!opts.stroke, strokeColor: INK, strokeWidth: opts.stroke || 0,
      strokeOverFill: false, justification: opts.just || "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h],
      verticalAlign: "center", tracking: opts.tracking ?? 20, leading: opts.leading ?? size * 1.05 } };
}
function rect(name, w, h, color, opts = {}) {
  return { type: "Rect", id: id(), name, blendMode: "normal", activeRange: R(0, 1000),
    transform: T(opts.pos || [0, 0], opts.anchor || [0, h / 2], 100, opts.rot || 0),
    rect: { size: [w, h], fillColor: color, roundness: opts.round || 0 } };
}
// place a layer in time with a pop / slide entrance and a fade exit
const TITLES = [];
function show(layer, t0, t1, style = "pop", sfx = null) {
  layer.activeRange = R(ms(t0), ms(t1 - t0));
  const d = ms(t1 - t0);
  if (style === "pop") { kf(layer.id, "scaleX", [[0, 72], [160, 106], [260, 100]]); kf(layer.id, "scaleY", [[0, 72], [160, 106], [260, 100]]); }
  if (style === "slam") { kf(layer.id, "scaleX", [[0, 165], [150, 96], [240, 100]]); kf(layer.id, "scaleY", [[0, 165], [150, 96], [240, 100]]); }
  if (style === "rise") { const y = layer.transform.position[1]; kf(layer.id, "positionY", [[0, y + 50], [260, y]]); }
  kf(layer.id, "opacity", [[0, 0], [110, 100], [Math.max(120, d - 180), 100], [d, 0]]);
  layers.push(layer); TITLES.push({ t0, t1, text: layer.sourceText.text });
  if (sfx) sound(sfx, t0);
  return layer;
}
// ---- SFX ----
const SFX = {};
function sound(name, t, vol = null, peak = 0) {        // peak: seconds from file start to the perceptual hit
  const f = SFXF[name]; audio.push({ name, start: Math.max(0, t - peak), vol: vol ?? f.vol, ms: f.ms });
}
const SFXF = {
  pop: { file: "ui-soft-pop", ms: 180, vol: 0.55 }, tick: { file: "ui-dry-click", ms: 65, vol: 0.5 }, ping: { file: "ui-clear-ping", ms: 480, vol: 0.45 },
  whoosh: { file: "ui-air-whoosh", ms: 500, vol: 0.5 }, impact: { file: "ui-soft-impact", ms: 450, vol: 0.75 }, riser: { file: "ui-short-riser", ms: 1100, vol: 0.4 },
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, click1: { file: "pin-click-1", ms: 120, vol: 0.5 }, click2: { file: "pin-click-2", ms: 120, vol: 0.5 },
  click3: { file: "pin-click-3", ms: 120, vol: 0.5 }, click4: { file: "pin-click-4", ms: 120, vol: 0.5 }, mtick: { file: "metal-tick", ms: 250, vol: 0.6 },
  shing: { file: "slice-shing", ms: 1400, vol: 0.6 }, boing: { file: "spring-boing", ms: 700, vol: 0.45 }, scrape: { file: "key-scrape", ms: 4600, vol: 0.5 },
  turn: { file: "plug-turn", ms: 900, vol: 0.6 }, clunk: { file: "bolt-clunk", ms: 700, vol: 0.7 }, deny: { file: "deny-thud", ms: 600, vol: 0.6 },
  knock: { file: "wood-knock", ms: 400, vol: 0.6 },
};

// ================= TYPOGRAPHY =================
// platform safe area (TikTok / Reels / Shorts UI): top ~200 px, bottom ~420 px, right ~130 px are covered
const SAFE = { top: 200, bottom: 1500, right: 950, left: 60 };
const TOP_Y = 345;            // type band centre (y 150-430)
// B1 hook
show(text("HOW DOES\nYOUR KEY KNOW?", 540, TOP_Y, 980, 300, 118, WHITE), C.how, C.lets + 0.1, "rise", "whoosh");
// B3 parts: labels tracked to the 3D (group = dot + leader + label, positioned at the anchor every 2 frames)
function tracked(label, anchorName, t0, t1, dx, dy, color = GOLD, sfx = "pop") {
  const g = { type: "Group", id: id(), name: `Label - ${label}`, blendMode: "normal", activeRange: R(ms(t0), ms(t1 - t0)), transform: T([0, 0]), layers: [] };
  const tw = Math.max(220, label.length * 30 + 60), th = 64;
  // keep the label on screen: flip to the other side of its anchor if the box would leave the safe area
  let minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
  for (let t = t0; t <= t1; t += 0.2) { const p = A(anchorName, t); minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]); minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]); }
  if (dx > 0 && maxX + dx + tw > SAFE.right) dx = -dx; else if (dx < 0 && minX + dx - tw < SAFE.left) dx = -dx;
  if (dy < 0 && minY + dy - th < 520) dy = -dy; else if (dy > 0 && maxY + dy + th > 1300) dy = -dy;
  const len = Math.hypot(dx, dy), rot = Math.atan2(dy, dx) * 180 / Math.PI;
  const dot = rect(`${label} dot`, 18, 18, color, { anchor: [9, 9], round: 9 });
  const line = rect(`${label} leader`, len, 4, color, { anchor: [0, 2], rot });
  const txt = text(label, dx + (dx < 0 ? -tw / 2 : tw / 2), dy, tw, th, 40, color, BODY, { tracking: 60, name: `${label} text` });
  const pill = rect(`${label} backing`, tw, th, [0, 0, 0, 0.55], { pos: [dx + (dx < 0 ? -tw : 0), dy], anchor: [0, th / 2], round: 14 });
  for (const l of [txt, pill, line, dot]) { l.activeRange = R(0, ms(t1 - t0)); g.layers.push(l); }
  const d = ms(t1 - t0);
  kf(dot.id, "scaleX", [[0, 0], [160, 100]]); kf(dot.id, "scaleY", [[0, 0], [160, 100]]);
  kf(line.id, "scaleX", [[60, 0], [300, 100]]);
  for (const l of [txt, pill]) kf(l.id, "opacity", [[180, 0], [330, 100]]);
  kf(g.id, "opacity", [[0, 100], [Math.max(10, d - 200), 100], [d, 0]]);
  // follow the anchor
  const px = [], py = [];
  for (let t = t0; t <= t1 + 1e-6; t += 2 / FPS) { const p = A(anchorName, t); px.push([ms(t - t0), p[0], "lin"]); py.push([ms(t - t0), p[1], "lin"]); }
  kf(g.id, "positionX", px); kf(g.id, "positionY", py);
  layers.push(g); if (sfx) sound(sfx, t0 + 0.05);
  return g;
}
show(text("CYLINDER", 540, TOP_Y, 900, 160, 150, GOLD), C.this, C.shell - 0.1, "slam", "impact");
tracked("SHELL", "shell", C.shell, C.drilled - 0.35, -170, -150);
tracked("PLUG", "plug", C.plug, C.drilled - 0.35, -150, 170);
// B4 chambers: counter 1 -> 5 synced with the chambers lighting up
const step = (C.chambers - C.drilled) / 5;
const cnt = text("1", 540, TOP_Y - 20, 400, 220, 200, GOLD, DISPLAY, { name: "Chamber counter" });
show(cnt, C.drilled + 0.2, C.each - 0.2, "pop");
edits.push({ type: "setFxPropertyAnimator", compositionId: "main", property: { layerId: cnt.id, propertyType: "textContent" }, dependencies: [],
  animator: { type: "jsScript", layerTimeJsCode: `var n = Math.floor(input.time.seconds / ${step.toFixed(3)}) + 1; return String(Math.max(1, Math.min(5, n)));` } });
for (let i = 0; i < 5; i++) sound(i % 2 ? "tick" : "click1", C.drilled + 0.2 + i * step);
show(text("TINY CHAMBERS", 540, TOP_Y + 120, 900, 90, 64, WHITE, BODY, { tracking: 80 }), C.five, C.each - 0.2, "rise");
// B5 stack
tracked("SPRING", "spring", C.spring, C.springs - 0.35, 210, -60, WHITE);
tracked("TOP PIN", "top_pin", C.top, C.springs - 0.35, 230, 0, [0.65, 0.85, 1, 1]);
tracked("BOTTOM PIN", "bottom_pin", C.bottom, C.springs - 0.35, 230, 50, GOLD);
// B6 springs push down
sound("boing", C.springs + 0.05);
// B7 shear line
tracked("SHEAR LINE", "shear", C.shear, C.slide - 0.3, 60, -230, CYAN, "ping");
// B8 jam
sound("deny", C.jammed, 0.85); sound("clunk", C.jammed, 0.75); sound("mtick", C.jammed + 0.18, 0.5);   // jammed: metal hits the block
sound("deny", C.high, 0.5);                                                                            // too high: stinger
show(text("NOTHING\nTURNS", 540, TOP_Y, 900, 300, 150, RED), C.nothing, C.slide - 0.1, "slam", "impact");
// B9 key in
show(text("EACH CUT =\nONE HEIGHT", 540, TOP_Y, 980, 300, 120, WHITE), C.cut, C.watch - 0.15, "rise", "whoosh");
sound("scrape", C.slide + 0.15, 0.45);
// B10 align
show(text("ALL 5", 540, TOP_Y, 700, 220, 190, CYAN), C.all, C.plug2 - 0.15, "slam", "impact");
sound("ping", C.lands, 0.5);
const all5step = (C.same - C.all) / 5;
for (let i = 0; i < 5; i++) sound("tick", C.all + 0.1 + i * all5step);
// B11 turn + bolt
sound("turn", C.plug2 + 0.1); sound("clunk", C.plug2 + 0.95);
tracked("CAM", "cam", C.cam, C.opens + 0.6, -200, 120, GOLD);
tracked("BOLT", "bolt", C.bolt, C.opens + 0.6, 140, 150, WHITE);
show(text("OPEN", 540, TOP_Y, 700, 220, 190, [0.4, 1, 0.55, 1]), C.opens, C.turn - 0.1, "slam", "ping");
// B12 relock
sound("turn", C.turn + 0.1, 0.5); sound("boing", C.snap, 0.35);
show(text("LOCKED", 540, TOP_Y, 760, 220, 170, WHITE), C.locked, C.try - 0.15, "slam", "impact");
// B13 wrong key
show(text("WRONG KEY", 540, TOP_Y, 900, 220, 150, RED), C.wrong, C.high - 0.2, "slam", "impact");
sound("scrape", C.wrong, 0.4);
tracked("TOO HIGH", "top_pin", C.high, C.shut - 0.1, 230, -40, RED);
sound("deny", C.crosses2, 0.55); sound("deny", C.shut - 0.25, 0.7);
show(text("STILL\nLOCKED", 540, TOP_Y, 900, 300, 150, RED), C.shut, C.idea - 0.1, "slam", "impact");
// B14 history
sound("whoosh", C.idea);
const yrs = text("4,000", 540, TOP_Y - 30, 900, 230, 210, GOLD, DISPLAY, { name: "Years counter" });
show(yrs, C.four, C.eighteen - 0.15, "pop", "impact");
edits.push({ type: "setFxPropertyAnimator", compositionId: "main", property: { layerId: yrs.id, propertyType: "textContent" }, dependencies: [],
  animator: { type: "jsScript", layerTimeJsCode: "var p = Math.min(1, input.time.seconds / 0.9); p = 1 - Math.pow(1 - p, 3); var n = Math.round(4000 * p / 50) * 50; return n.toLocaleString ? String(n).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') : String(n);" } });
show(text("YEARS AGO", 540, TOP_Y + 120, 900, 90, 64, WHITE, BODY, { tracking: 80 }), C.four + 0.4, C.eighteen - 0.15, "rise");
show(text("ANCIENT EGYPT · WOOD", 540, TOP_Y + 200, 900, 70, 46, GOLD, BODY, { tracking: 60 }), C.ancient, C.eighteen - 0.15, "rise", "knock");
// B15 Yale
show(text("1800s", 540, TOP_Y - 20, 800, 230, 200, GOLD), C.eighteen, C.so - 0.15, "slam", "impact");
show(text("THE YALES MADE IT\nPOCKET-SIZED", 540, TOP_Y + 160, 980, 140, 54, WHITE, BODY, { tracking: 40, leading: 62 }), C.yale, C.so - 0.15, "rise", "pop");
sound("down", C.shrank);
// B16 recap: three slams on the words
const rec = [["5 PINS", C.five2, GOLD], ["1 LINE", C.line, CYAN], ["1 KEY", C.key3, WHITE]];
rec.forEach(([s, t, col], i) => show(text(s, 520, 300 + i * 140, 840, 140, 132, col), t, C.follow - 0.1, "slam", "impact"));
// B17 CTA
show(text("FOLLOW", 520, 330, 800, 200, 160, GOLD), C.follow, C.end, "slam", "ping");
show(text("HIDDEN IN YOUR HOME", 520, 470, 860, 80, 46, WHITE, BODY, { tracking: 110 }), C.follow + 0.25, C.end, "rise", "pop");

// key-pin clicks from the physics of the bitting (merge clicks closer than 45 ms)
const clickList = [...TL.clicks.right, ...TL.clicks.wrong, ...TL.clicks.snap].sort((a, b) => a - b);
let lastClick = -1, ci = 0;
for (const t of clickList) { if (t - lastClick < 0.045) continue; lastClick = t; sound(["click1", "click2", "click3", "click4"][ci++ % 4], t, 0.42); }
// split
sound("riser", C.half, 0.35, 1.05); sound("shing", C.half, 0.6, 0.32); sound("mtick", C.door, 0.6); sound("whoosh", C.door, 0.45, 0.25);

// ================= CAPTIONS (word groups, bottom zone) =================
const W = VOM.scenes[0].words.map(w => ({ t: w.text, s: w.start + VO, e: w.end + VO }));
const groups = []; let cur = [];
for (const w of W) {
  cur.push(w);
  const endSentence = /[.?!,]$/.test(w.t), long = cur.map(x => x.t).join(" ").length > 16;
  if (endSentence || long || cur.length >= 3) { groups.push(cur); cur = []; }
}
if (cur.length) groups.push(cur);
const HL = /^(shell|plug|spring|top|bottom|shear|line|key|cut|jammed|wrong|wood|yale|five|pins)/i;
// a caption is dropped while a title on screen already shows the same words (numbers and spelled-out forms count as the same)
const SYN = { five: "5", one: "1", four: "4000", thousand: "4000", eighteen: "1800s", hundreds: "1800s", opens: "open", turns: "turns" };
const toks = str => str.toLowerCase().replace(/,/g, "").split(/[^a-z0-9]+/).filter(w => w.length > 2 || /^d/.test(w) || ["1", "5"].includes(w))
  .map(w => SYN[w] || w).filter(w => !["the", "and", "you", "your", "its", "for", "are", "about"].includes(w));
const dupOfTitle = (str, s, e) => TITLES.some(T => T.t0 < e && T.t1 > s + 0.05 && toks(str).some(w => toks(T.text).includes(w)));
let dropped = 0;
groups.forEach((g, i) => {
  const s = g[0].s, next = groups[i + 1] ? groups[i + 1][0].s : C.end, e = Math.min(next, g.at(-1).e + 0.35);
  const str = g.map(x => x.t).join(" ");
  const hl = g.some(x => HL.test(x.t.replace(/[^a-z]/gi, "")));
  if (dupOfTitle(str, s, e)) { dropped++; return; }
  const cap = text(str, 510, 1395, 880, 150, 62, hl ? GOLD : WHITE, BODY, { stroke: 10, tracking: 0, name: `Caption - ${str}` });
  cap.activeRange = R(ms(s), ms(e - s));
  kf(cap.id, "scaleX", [[0, 88], [110, 100]]); kf(cap.id, "scaleY", [[0, 88], [110, 100]]); kf(cap.id, "opacity", [[0, 0], [60, 100]]);
  layers.push(cap);
});

// ================= DOCUMENT =================
const RENDER_ID = process.env.RENDER_ID || "proxy", RENDER_MS = +(process.env.RENDER_MS || DUR);
const audioLayers = [];
let aid = 2000;
audioLayers.push({ type: "Audio", id: aid++, name: "VO - Liam (Eleven v4 Turbo)", windowMs: ms(VOM.scenes[0].words.at(-1).end + 0.4),
  activeRange: R(ms(VO), Math.min(DUR - ms(VO), ms(74.080000))), sourceRange: R(0, Math.min(DUR - ms(VO), ms(74.080000))),
  sourceIntrinsicDuration: ms(74.080000), source: { assetId: "vo" }, volume: 0.86, captionsEnabled: false });
audioLayers.push({ type: "Audio", id: aid++, name: "Bed - ambient pad", windowMs: 76000, activeRange: R(0, DUR), sourceRange: R(0, DUR),
  sourceIntrinsicDuration: 76000, source: { assetId: "sfx-pad-bed" }, volume: 0.32, captionsEnabled: false });
const used = new Set();
for (const a of audio.sort((x, y) => x.start - y.start)) {
  const f = SFXF[a.name]; used.add(f.file);
  const start = ms(a.start), dur = Math.min(f.ms, DUR - start); if (dur <= 0) continue;
  audioLayers.push({ type: "Audio", id: aid++, name: `SFX - ${a.name} @${a.start.toFixed(2)}`, windowMs: f.ms, activeRange: R(start, dur),
    sourceRange: R(0, dur), sourceIntrinsicDuration: f.ms, source: { assetId: "sfx-" + f.file }, volume: +(a.vol * (+process.env.SFX_GAIN || 1)).toFixed(3), captionsEnabled: false });
}
const video = { type: "Video", id: 1, name: "Blender render - lock cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
  sourceIntrinsicDuration: RENDER_MS, volume: 0, transform: T([0, 0]), source: { assetId: RENDER_ID, fit: "contain" } };
// top-of-stack order: captions & type above the video; groups after text so labels sit under titles
const doc = JSON.parse(fs.readFileSync(path.join(D, "editable.json"), "utf8"));
doc.duration = DUR / 1000;
doc.composition.layers = [...layers.slice().reverse(), video, ...audioLayers];
fs.writeFileSync(path.join(D, "editable.json"), JSON.stringify(doc, null, 1));
fs.writeFileSync(path.join(D, "edits.json"), JSON.stringify(edits, null, 1));
fs.writeFileSync(path.join(D, "sfx-used.json"), JSON.stringify([...used].sort(), null, 1));
console.log("captions dropped as title duplicates", dropped); console.log("type/caption layers", layers.length, "captions", groups.length, "audio layers", audioLayers.length, "edits", edits.length, "duration", DUR);
