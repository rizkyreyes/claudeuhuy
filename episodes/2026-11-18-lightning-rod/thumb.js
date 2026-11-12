// Cover (1080x1920) for Shorts / TikTok / Reels. Usage: OPT=A|B|C node thumb.js  (writes editable-thumb.json). Fallback only: covers are made with Remotion cover.sh.
// Separate Blender hero render of the whole house with its lightning protection (build_cover.py, render.sh <ep> hero), not a video frame:
// A: image asset "thumbA" = cover/hero_A.png (whole house, bolt on the ridge, both cables + ground rods glowing), title "HIT BY LIGHTNING / STILL FINE?!"
// B: image asset "thumbB" = cover/hero_B.png (the ridge rods from the gable end, bolt on a rod, glow along the roof edge), title "IT DOESN'T / PULL IT IN?!"
// C: image asset "thumbC" = cover/hero_C.png (front corner: glowing cable diving into the ground rod in the cut soil), title "WHERE DOES / IT GO?!"
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
const img = { type: "Image", id: 1, name: "Blender frame", blendMode: "normal", activeRange: R, transform: T([540, 960], [540, 960]),
  source: { assetId: "thumb" + OPT, fit: "cover" } };
const SETS = {
  A: [text("HIT BY LIGHTNING", 540, 330, 1000, 170, 112, WHITE), text("STILL FINE?!", 540, 480, 1000, 130, 112, RED),
      rect("Title shade", 540, 405, 1080, 380, SHADE)],
  B: [text("IT DOESN'T", 540, 330, 1000, 170, 140, WHITE), text("PULL IT IN?!", 540, 480, 1000, 130, 112, RED),
      rect("Title shade", 540, 405, 1080, 380, SHADE)],
  C: [text("WHERE DOES", 540, 330, 1000, 170, 132, WHITE), text("IT GO?!", 540, 480, 1000, 130, 124, RED),
      rect("Title shade", 540, 405, 1080, 380, SHADE)],
};
const L = [...SETS[OPT], img];
const f = path.join(__dirname, "editable-thumb.json");
const doc = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : { width: 1080, height: 1920, duration: 1, composition: { id: "main", layers: [] } };
doc.duration = 1; doc.composition.layers = L;
fs.writeFileSync(f, JSON.stringify(doc, null, 1)); console.log("option", OPT, "layers", doc.composition.layers.length);
