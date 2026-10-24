// Cover thumbnail (1080x1920) for Shorts / TikTok / Reels. Usage: OPT=A|B node thumb.js  (writes editable-thumb.json)
// Image asset "thumbZ" = Blender frame 1620 cropped 1.5x on the drained pit (previews/zA.png): crew on dry concrete, river higher outside.
// Red = the river level line + a depth bracket showing the crew stands below it. Everything inside the 3:4 crop (y 240-1680).
const fs = require("fs"), path = require("path");
const T = (pos, anchor = [0, 0]) => ({ anchorPoint: anchor, position: pos, scale: [100, 100], rotation: 0, opacity: 100 });
const R = { start: 0, duration: 1000 };
let n = 10;
const text = (s, x, y, w, h, size, color, stroke = 10, tracking = 10) => ({
  type: "Text", id: n++, name: "T " + s, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2]),
  sourceText: { text: s, fontFamily: "Anton", fontStyle: "Regular", fontSize: size, fillColor: color, applyStroke: stroke > 0, strokeColor: [0, 0, 0, 1],
    strokeWidth: stroke, strokeOverFill: false, justification: "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h], verticalAlign: "center",
    tracking, leading: size * 1.0 } });
const rect = (name, x, y, w, h, fill) => ({ type: "Rect", id: n++, name, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2]),
  rect: { size: [w, h], fillColor: fill, roundness: 0 } });
const WHITE = [1, 1, 1, 1], RED = [1, 0.3, 0.24, 1], INK = [0, 0, 0, 1];
const img = { type: "Image", id: 1, name: "Render", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]), source: { assetId: "thumbZ", fit: "contain" } };
const RIVER_Y = 822, FLOOR_Y = 1300, BX = 975;
const marks = [
  // layers listed first draw on top: red marks above their dark outlines
  rect("River line", 540, RIVER_Y, 1080, 12, RED), rect("Depth bar", BX, (RIVER_Y + FLOOR_Y) / 2, 12, FLOOR_Y - RIVER_Y, RED), rect("Depth cap", BX - 20, FLOOR_Y, 52, 12, RED),
  rect("River line outline", 540, RIVER_Y, 1080, 20, INK), rect("Depth bar outline", BX, (RIVER_Y + FLOOR_Y) / 2, 20, FLOOR_Y - RIVER_Y + 8, INK), rect("Depth cap outline", BX - 20, FLOOR_Y, 60, 20, INK),
];
const TITLES = {
  A: [text("WORKING", 540, 360, 1000, 200, 200, WHITE), text("UNDER A RIVER", 540, 540, 1000, 160, 140, RED)],
  B: [text("BONE DRY", 540, 360, 1000, 200, 210, WHITE), text("UNDERWATER?!", 540, 545, 1000, 160, 150, RED)],
};
const L = [...TITLES[process.env.OPT || "A"], ...marks];
const f = path.join(__dirname, "editable-thumb.json");
const doc = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : { width: 1080, height: 1920, duration: 1, composition: { id: "main", layers: [] } };
doc.duration = 1; doc.composition.layers = [...L, img];
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("layers", doc.composition.layers.length);
