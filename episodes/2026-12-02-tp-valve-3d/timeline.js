// T&P valve Tesseract timeline: render + VO + captions + kinetic typography + labels tracked to the 3D parts + SFX.
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
  down: { file: "ui-downlifter", ms: 900, vol: 0.5 }, deny: { file: "deny-thud", ms: 600, vol: 0.32 }, rush: { file: "water-rush", ms: 3000, vol: 0.3 },
  splash: { file: "splash", ms: 1200, vol: 0.5 }, click: { file: "button-click", ms: 250, vol: 0.6 }, room: { file: "room-tone", ms: 3000, vol: 0.25 },
  rumble: { file: "heater-rumble", ms: 1500, vol: 0.5 }, burst: { file: "tank-burst", ms: 2000, vol: 0.55 }, crash: { file: "debris-crash", ms: 1400, vol: 0.5 },
  hiss: { file: "steam-hiss", ms: 2000, vol: 0.3 }, burner: { file: "burner-whoosh", ms: 1200, vol: 0.45 }, vpop: { file: "valve-pop", ms: 500, vol: 0.55 },
  spring: { file: "spring-creak", ms: 600, vol: 0.45 }, drip: { file: "drip", ms: 350, vol: 0.5 }, gush: { file: "water-gush", ms: 2000, vol: 0.35 },
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
// ambience: utility-room tone everywhere, burner roar while the flames run, water through the valve while it is open
bed("room", 0, TL.duration - 0.8, 0.2);
for (const t of EV.flames_on) sound("burner", t, 0.4);
bed("rush", EV.flames_on[1] + 0.8, EV.super[1], 0.1, 2.9);
for (const [a, b] of EV.flow) { bed("rush", a, b, 0.2, 2.9); sound("hiss", a, 0.22); }
// mechanical events
sound("click", EV.cap_on, 0.5);
bed("rumble", EV.rumble[0], EV.launch + 0.1, 0.5, 1.4);
sound("burst", EV.launch - 0.05, 0.55); sound("crash", EV.ceiling_hit + 0.25, 0.45);
sound("deny", EV.crack, 0.3); sound("hiss", EV.crack + 0.1, 0.2);
sound("burst", EV.flash - 0.03, 0.35); bed("hiss", EV.flash + 0.3, EV.steam[1] - 0.3, 0.25, 1.95);
for (const t of EV.disc_open) sound("vpop", t, 0.5);
for (const t of EV.disc_close) sound("click", t, 0.35);
sound("spring", C.spring + 0.05, 0.45); sound("spring", C.shoves, 0.35);
sound("click", C.lift, 0.5);
bed("gush", EV.gush[0], EV.gush[1], 0.35, 1.95); sound("splash", EV.gush[0] + 0.15, 0.3);
for (let t = EV.drips[0] + 0.3; t < EV.drips[1] - 0.3; t += 0.75) sound("drip", t, 0.45);
// B1 hook: the claim on screen from frame 0
show(text("THIS VALVE", 540, TOP_Y, 980, 200, 132, GOLD), 0.0, C.water - 0.1, "slam", "impact");
tracked("T&P RELIEF VALVE", "valve_full", 0.5, C.water - 0.1, -60, 160, GOLD, null);
show(text("OR YOUR HEATER\nBECOMES A ROCKET", 540, H, 980, 300, 96, RED), C.water - 0.05, C.if - 0.1, "slam", "deny");
// B2 stake: capped / stuck -> through the roof (what-if)
show(text("CAPPED?", 540, TOP_Y, 980, 200, 128, RED), C.capped - 0.05, C.stuck - 0.1, "slam", "pop");
show(text("STUCK?", 540, TOP_Y, 980, 200, 128, RED), C.stuck - 0.05, C.tank - 0.1, "slam", "pop");
show(text("THROUGH\nTHE ROOF", 540, H, 980, 300, 128, RED), C.blast - 0.05, C.inside - 0.1, "slam", "impact");
// B3 inside: heat under pressure, the thermostat
show(text("INSIDE THE TANK", 540, TOP_Y, 980, 200, 96, WHITE), C.inside - 0.05, C.heats - 0.1, "rise", "whoosh");
show(text("UNDER PRESSURE", 540, TOP_Y, 980, 200, 96, RED), C.pressure - 0.4, C.normally - 0.1, "pop", null);
tracked("THERMOSTAT", "thermostat", C.thermostat - 0.05, C.but - 0.1, 150, -120, GOLD, "pop");
show(text("CUTS THE HEAT", 540, TOP_Y, 980, 200, 100, WHITE), C.cuts - 0.05, C.but - 0.1, "pop", null);
// B4 the thermostat fails: heat and pressure climb
show(text("IF IT FAILS", 540, TOP_Y, 980, 200, 120, RED), C.but - 0.05, C.keeps - 0.1, "slam", "deny");
show(text("HEAT KEEPS\nCLIMBING", 540, H, 980, 300, 110, RED), C.keeps - 0.05, C.hot - 0.1, "pop", "riser");
show(text("WATER EXPANDS", 540, TOP_Y, 980, 200, 100, WHITE), C.hot - 0.05, C.climbs - 0.1, "pop", "whoosh");
show(text("PRESSURE CLIMBS", 540, TOP_Y, 980, 200, 100, RED), C.climbs - 0.05, C.under - 0.1, "slam", "impact");
// B5 superheated
counter(150, 212, C.two - 0.05, C.boil - 0.7, n => `${n}°F`, 540, TOP_Y, 980, 200, 140, GOLD, 2, 2);
show(text("AND STILL\nNOT BOILING", 540, H, 980, 300, 104, WHITE), C.boil - 0.7, C.thats - 0.1, "pop", "pop");
show(text("SUPERHEATED", 540, TOP_Y, 980, 200, 124, RED), C.superheated - 0.05, C.if2 - 0.1, "slam", "impact");
// B6 the tank splits: flash to steam, 1,000x
show(text("IF THE TANK SPLITS", 540, TOP_Y, 980, 200, 92, RED), C.if2 - 0.05, C.flashes - 0.1, "pop", null);
show(text("FLASH TO STEAM", 540, TOP_Y, 980, 200, 110, WHITE), C.flashes - 0.05, C.thousand - 0.1, "slam", null);
counter(0, 1000, C.thousand - 0.05, C.all - 0.1, n => `${n.toLocaleString("en-US")}x BIGGER`, 540, TOP_Y, 980, 200, 104, GOLD, 2, 100);
show(text("ALL AT ONCE", 540, TOP_Y, 980, 200, 124, RED), C.all - 0.05, C.so - 0.1, "slam", "deny");
// B7 the valve watches both: probe in the top 6 inches
show(text("IT WATCHES\nHEAT + PRESSURE", 540, H, 980, 300, 96, GOLD), C.so - 0.05, C.probe - 0.1, "pop", "whoosh");
tracked("PROBE", "probe", C.probe - 0.05, C.top - 0.1, -40, 150, GOLD, "pop");
show(text("TOP 6 INCHES", 540, TOP_Y, 980, 200, 120, CYAN), C.top - 0.05, C.at - 0.1, "slam", "impact");
tracked("HOTTEST WATER", "top6", C.hottest - 0.1, C.at - 0.1, 60, 160, RED, "pop");
// B8 temperature trip: ~210 F, the element expands, the disc lifts
counter(200, 210, C.two2 - 0.05, C.element - 0.1, n => `${n}°F`, 540, TOP_Y, 980, 200, 140, GOLD, 2, 1);
small("ABOUT", C.at, C.element - 0.1, GOLD);
tracked("ELEMENT EXPANDS", "element", C.element + 0.05, C.lifts - 0.1, 30, 150, RED, "pop");
show(text("LIFTS THE DISC", 540, TOP_Y, 980, 200, 104, WHITE), C.lifts - 0.05, C.hot2 - 0.1, "pop", null);
tracked("DISC", "disc", C.disc - 0.05, C.hot2 - 0.1, -80, -130, CYAN, "pop");
show(text("HOT WATER OUT", 540, TOP_Y, 980, 200, 110, GOLD), C.hot2 - 0.05, C.superheat - 0.1, "pop", "whoosh");
show(text("BEFORE IT\nSUPERHEATS", 540, H, 980, 300, 104, WHITE), C.superheat - 0.05, C.spring - 0.1, "pop", null);
// B9 pressure trip: spring holds it shut until ~150 psi
tracked("SPRING", "spring", C.spring - 0.05, C.pressure3 - 0.1, 40, -140, GOLD, "pop");
show(text("HOLDS IT SHUT", 540, TOP_Y, 980, 200, 110, WHITE), C.holds - 0.05, C.pressure3 - 0.1, "pop", null);
counter(0, 150, C.one - 0.05, C.then - 0.1, n => `${n} PSI`, 540, TOP_Y, 980, 200, 140, RED, 2, 10);
small("ABOUT", C.one - 0.05, C.then - 0.1, GOLD);
show(text("WATER SHOVES\nIT OPEN", 540, H, 980, 300, 104, CYAN), C.shoves - 0.05, C.either - 0.1, "slam", "impact");
// B10 drains to the floor
show(text("DRAINS TO\nTHE FLOOR", 540, H, 980, 300, 110, WHITE), C.drains - 0.05, C.once2 - 0.1, "pop", "down");
tracked("DISCHARGE PIPE", "pipe", C.pipe - 0.05, C.floor - 0.1, 70, -120, GOLD, "pop");
// B11 test it once a year
show(text("ONCE A YEAR", 540, TOP_Y, 980, 200, 120, GOLD), C.once2 - 0.05, C.gush - 0.1, "slam", "impact");
tracked("TEST LEVER", "lever", C.test - 0.05, C.gush - 0.1, -60, 150, GOLD, "pop");
show(text("HOT WATER\nSHOULD GUSH OUT", 540, H, 980, 300, 96, WHITE), C.gush - 0.05, C.never - 0.1, "pop", null);
// B12 never cap it
show(text("NEVER CAP IT", 540, TOP_Y, 980, 200, 124, RED), C.never - 0.05, C.drips - 0.1, "slam", "deny");
show(text("EVEN IF IT DRIPS", 540, TOP_Y, 980, 200, 96, WHITE), C.drips - 0.3, C.drip - 0.1, "pop", null);
show(text("A DRIP =\nCALL A PLUMBER", 540, H, 980, 300, 100, GOLD), C.drip - 0.05, C.have - 0.1, "pop", "impact");
// B13 CTA: spoken question as the closing title, NEXT small over the last 2 s, fade out
show(text("HAVE YOU EVER\nTESTED YOURS?", 540, H, 980, 300, 96, WHITE), C.have - 0.05, TL.duration, "slam", "impact");
show(text("TELL ME IN THE COMMENTS", 540, H + 230, 980, 110, 56, GOLD, BODY, { tracking: 10 }), C.tell - 0.05, TL.duration, "pop", "ping");
{ const nx = text("NEXT: DRYER LINT FIRES", 540, 1240, 880, 70, 40, WHITE, BODY, { stroke: 8, tracking: 20, name: "Next tease" });
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
const HL = /^(valve|rocket|roof|thermostat|superheated|steam|probe|disc|spring|psi|degrees|cap|plumber|lever)/i;
const SYN = { "two": "212", "hundred": "212", "twelve": "212", "ten": "210", "fifty": "150", "thousand": "1000", "superheat": "superheats", "heats": "heat", "boil": "boiling", "lifts": "lifts", "pressure.": "pressure" };
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
const video = { type: "Video", id: 1, name: "Blender render - T&P valve cutaway", blendMode: "normal", activeRange: R(0, DUR), sourceRange: R(0, Math.min(DUR, RENDER_MS)),
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
