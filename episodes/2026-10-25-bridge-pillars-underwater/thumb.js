// Cover thumbnail (1080x1920) for Shorts / TikTok / Reels. Usage: node thumb.js  (writes editable-thumb.json)
// Image asset "thumbA" = Blender frame 1576 at 100 % (dry pit below the river line, see cover.md).
const fs = require("fs"), path = require("path");
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
const WHITE = [1, 1, 1, 1], RED = [1, 0.3, 0.24, 1];
const img = { type: "Image", id: 1, name: "Render", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]), source: { assetId: "thumbA", fit: "contain" } };
const shade = rect("Top shade", 540, 420, 1080, 520, [0, 0, 0, 0.45]);
// everything inside the 3:4 profile-grid crop (y 240-1680)
const L = [
  text("UNDER", 540, 360, 1000, 200, 210, WHITE, "Anton", "Regular", 8),
  text("THE RIVER", 540, 545, 1000, 180, 170, RED, "Anton", "Regular", 8),
  rect("Red ring", 540, 900, 740, 520, [0, 0, 0, 0], { round: 60, stroke: RED, sw: 12, nofill: true }),
];
const f = path.join(__dirname, "editable-thumb.json");
const doc = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : { width: 1080, height: 1920, duration: 1, composition: { id: "main", layers: [] } };
doc.duration = 1; doc.composition.layers = [...L.reverse(), shade, img];
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("layers", doc.composition.layers.length);
