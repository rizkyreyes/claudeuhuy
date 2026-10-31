// Cover (1080x1920) for Shorts / TikTok / Reels. Usage: OPT=A|B node thumb.js  (writes editable-thumb.json)
// Real stock photos (Pexels licence, credited in sources.txt), already cropped to 1080x1920 in cover/:
// A: image asset "thumbA" = cover/photo_A.jpg (worm's-eye view of a glass tower over a brick corner, blue sky + cloud), title in the sky: "WHY DOESN'T / IT SINK?!"
// B: image asset "thumbB" = cover/photo_B_inset.jpg (slim residential tower on a deep blue sky + our Blender cutaway of the raft and piles
//    in a gold-bordered inset on the left sky, x 34-390 y 600-1100), title in the sky above it: "WHAT'S / UNDER IT?!"
// Poppins ExtraBold, ALL CAPS, tracking -10, 10 px black stroke. Everything sits inside the 3:4 profile-grid crop (y 240-1680).
const fs = require("fs"), path = require("path");
const T = (pos, anchor = [0, 0], rot = 0) => ({ anchorPoint: anchor, position: pos, scale: [100, 100], rotation: rot, opacity: 100 });
const R = { start: 0, duration: 1000 };
let n = 10;
const text = (s, x, y, w, h, size, color, stroke = 10, tracking = -10) => ({
  type: "Text", id: n++, name: "T " + s, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2]),
  sourceText: { text: s, fontFamily: "Poppins", fontStyle: "ExtraBold", fontSize: size, fillColor: color, applyStroke: stroke > 0, strokeColor: [0, 0, 0, 1],
    strokeWidth: stroke, strokeOverFill: false, justification: "center", boxText: true, boxPosition: [0, 0], boxSize: [w, h], verticalAlign: "center",
    tracking, leading: size * 1.0 } });
const rect = (name, x, y, w, h, fill, round = 0, rot = 0) => ({ type: "Rect", id: n++, name, blendMode: "normal", activeRange: R, transform: T([x, y], [w / 2, h / 2], rot),
  rect: { size: [w, h], fillColor: fill, roundness: round } });
const WHITE = [1, 1, 1, 1], RED = [1, 0.3, 0.24, 1], SHADE = [0, 0, 0, 0.35];
const OPT = process.env.OPT || "A";
const img = { type: "Image", id: 1, name: "Photo", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]),
  source: { assetId: OPT === "A" ? "thumbA" : "thumbB", fit: "cover" } };
const SETS = {
  A: [text("WHY DOESN'T", 540, 330, 1000, 170, 140, WHITE), text("IT SINK?!", 540, 480, 1000, 130, 112, RED),
      rect("Title shade", 540, 405, 1080, 380, SHADE)],
  B: [text("WHAT'S", 540, 330, 1000, 170, 150, WHITE), text("UNDER IT?!", 540, 480, 1000, 130, 112, RED),
      rect("Title shade", 540, 405, 1080, 380, SHADE)],
};
const L = [...SETS[OPT], img];
const f = path.join(__dirname, "editable-thumb.json");
const doc = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : { width: 1080, height: 1920, duration: 1, composition: { id: "main", layers: [] } };
doc.duration = 1; doc.composition.layers = L;
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("option", OPT, "layers", doc.composition.layers.length);
