// Cover thumbnail (1080x1920) for Shorts / TikTok / Reels. Usage: OPT=A|B node thumb.js  (writes editable-thumb.json)
// A: image asset "thumbA" = Blender frame 915 (tank cut open, level line at the outlet), red line on the level, title at the top.
// B: image asset "thumbB" = Blender frame 1150 (layers + arrows into the T outlet), red ring on the tee.
// Everything sits inside the 3:4 profile-grid crop (y 240-1680). No brand line, no caption tag.
const fs = require("fs"), path = require("path");
const T = (pos, anchor = [0, 0], rot = 0) => ({ anchorPoint: anchor, position: pos, scale: [100, 100], rotation: rot, opacity: 100 });
const R = { start: 0, duration: 1000 };
let n = 10;
const text = (s, x, y, w, h, size, color, stroke = 10, tracking = 10) => ({
  type: "Text", id: n++, name: "T " + s, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2]),
  sourceText: { text: s, fontFamily: "Anton", fontStyle: "Regular", fontSize: size, fillColor: color, applyStroke: stroke > 0, strokeColor: [0, 0, 0, 1],
    strokeWidth: stroke, strokeOverFill: false, justification: "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h], verticalAlign: "center",
    tracking, leading: size * 1.0 } });
const rect = (name, x, y, w, h, fill, round = 0, rot = 0) => ({ type: "Rect", id: n++, name, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2], rot),
  rect: { size: [w, h], fillColor: fill, roundness: round } });
const ring = (name, x, y, w, h, col, th = 12) => [rect(name + " top", x, y - h / 2, w, th, col), rect(name + " bottom", x, y + h / 2, w, th, col),
  rect(name + " left", x - w / 2, y, th, h, col), rect(name + " right", x + w / 2, y, th, h, col)];
const WHITE = [1, 1, 1, 1], RED = [1, 0.3, 0.24, 1], INK = [0, 0, 0, 1], SHADE = [0, 0, 0, 0.45];
const OPT = process.env.OPT || "A";
const img = { type: "Image", id: 1, name: "Render", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]),
  source: { assetId: OPT === "A" ? "thumbA" : "thumbB", fit: "contain" } };
// positions from the projected anchors (frame 915: level (858, 852); frame 1150: tee (679, 931))
const SETS = {
  A: [text("ALWAYS", 540, 360, 1000, 220, 220, WHITE), text("FULL?!", 540, 540, 1000, 180, 170, RED),
      rect("Level line", 540, 852, 1000, 12, RED, 0, -0.4), rect("Level line outline", 540, 852, 1008, 20, INK, 0, -0.4),
      rect("Title shade", 540, 450, 1080, 420, SHADE)],
  B: [text("IT NEVER", 540, 350, 1000, 200, 200, WHITE), text("FILLS UP?!", 540, 530, 1000, 160, 150, RED),
      ...ring("Tee ring", 680, 930, 260, 330, RED), rect("Title shade", 540, 440, 1080, 420, SHADE)],
};
const L = [...SETS[OPT], img];
const f = path.join(__dirname, "editable-thumb.json");
const doc = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : { width: 1080, height: 1920, duration: 1, composition: { id: "main", layers: [] } };
doc.duration = 1; doc.composition.layers = L;
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("option", OPT, "layers", doc.composition.layers.length);
