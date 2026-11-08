// Generic 2-line cover: node thumb-generic.js <editable-thumb.json> <assetId> "<WHITE LINE>" "<RED LINE>"
// Poppins ExtraBold, ALL CAPS, 10 px stroke, shade band at the top, inside the 3:4 crop.
const fs = require("fs");
const [f, asset, l1, l2] = process.argv.slice(2);
const T = (pos, anchor) => ({ anchorPoint: anchor, position: pos, scale: [100, 100], rotation: 0, opacity: 100 });
const R = { start: 0, duration: 1000 }; let n = 10;
const fit = (s, base) => Math.min(base, Math.floor(1000 / (s.length * 0.72)));
const text = (s, y, h, size, color) => ({ type: "Text", id: n++, name: "T " + s, blendMode: "normal", activeRange: R, transform: T([540, y], [500, h / 2]),
  sourceText: { text: s, fontFamily: "Poppins", fontStyle: "ExtraBold", fontSize: size, fillColor: color, applyStroke: true, strokeColor: [0, 0, 0, 1],
    strokeWidth: 10, strokeOverFill: false, justification: "center", boxText: true, boxPosition: [0, 0], boxSize: [1000, h], verticalAlign: "center", tracking: -10, leading: size } });
const shade = { type: "Rect", id: n++, name: "Title shade", blendMode: "normal", activeRange: R, transform: T([540, 405], [540, 190]),
  rect: { size: [1080, 380], fillColor: [0, 0, 0, 0.35], roundness: 0 } };
const img = { type: "Image", id: 1, name: "Blender frame", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]), source: { assetId: asset, fit: "cover" } };
const doc = JSON.parse(fs.readFileSync(f, "utf8"));
doc.duration = 1; doc.composition.layers = [text(l1, 330, 170, fit(l1, 140), [1, 1, 1, 1]), text(l2, 480, 130, fit(l2, 112), [1, 0.3, 0.24, 1]), shade, img];
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("ok", l1, "/", l2);
