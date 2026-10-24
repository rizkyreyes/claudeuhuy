// Cover thumbnails (1080x1920) for Shorts / TikTok / Reels. Usage: node thumb.js A|B  (writes editable-thumb.json)
const fs = require("fs"), path = require("path");
const v = process.argv[2];
const T = (pos, anchor = [0, 0]) => ({ anchorPoint: anchor, position: pos, scale: [100, 100], rotation: 0, opacity: 100 });
const R = { start: 0, duration: 1000 };
let n = 10;
const text = (s, x, y, w, h, size, color, family = "Anton", style = "Regular", stroke = 0, tracking = 10) => ({
  type: "Text", id: n++, name: "T " + s, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2]),
  sourceText: { text: s, fontFamily: family, fontStyle: style, fontSize: size, fillColor: color, applyStroke: stroke > 0, strokeColor: [0, 0, 0, 1],
    strokeWidth: stroke, strokeOverFill: false, justification: "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h], verticalAlign: "center",
    tracking, leading: size * 1.0 } });
const rect = (name, x, y, w, h, fill, opts = {}) => ({ type: "Rect", id: n++, name, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2]),
  rect: { size: [w, h], fillColor: fill, roundness: opts.round || 0, strokeEnabled: !!opts.stroke, strokeColor: opts.stroke || null, strokeWidth: opts.sw || 0, fillEnabled: opts.nofill ? false : true } });
const WHITE = [1, 1, 1, 1], GOLD = [0.98, 0.74, 0.27, 1], CYAN = [0.3, 0.92, 1, 1], RED = [1, 0.28, 0.22, 1];
const img = { type: "Image", id: 1, name: "Render", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]),
  source: { assetId: v === "A" ? "thumbA" : "thumbB2", fit: "contain" } };
const shade = v === "A" ? rect("Top shade", 540, 230, 1080, 460, [0, 0, 0, 0.35]) : rect("Top shade", 540, 420, 1080, 520, [0, 0, 0, 0.45]);
let L;
if (v === "A") L = [
  text("HOW KEYS", 540, 205, 1040, 230, 230, WHITE, "Anton", "Regular", 8),
  text("REALLY WORK", 540, 395, 1040, 180, 168, GOLD, "Anton", "Regular", 8),
  rect("Shear tag", 540, 1625, 560, 92, [0, 0, 0, 0.7], { round: 22 }),
  text("THE SECRET LINE", 540, 1625, 560, 92, 48, CYAN, "Poppins", "ExtraBold", 0, 60),
  text("HIDDEN IN YOUR HOME", 540, 1820, 1000, 60, 36, [1, 1, 1, 0.85], "Poppins", "ExtraBold", 0, 140),
];
else L = [
  // inside the 3:4 profile-grid crop (y 240-1680): title, line and red pin all survive the crop
  text("HOW KEYS", 540, 380, 1000, 200, 200, WHITE, "Anton", "Regular", 8),
  text("REALLY WORK", 540, 560, 1000, 170, 150, RED, "Anton", "Regular", 8),
  rect("Red ring", 540, 980, 230, 560, [0, 0, 0, 0], { round: 115, stroke: RED, sw: 12, nofill: true }),
];
const f = path.join(__dirname, "editable-thumb.json");
const doc = JSON.parse(fs.readFileSync(f, "utf8"));
doc.duration = 1; doc.composition.layers = [...L.reverse(), shade, img];
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("layers", doc.composition.layers.length);
