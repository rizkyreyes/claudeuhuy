export const title = "Iron Button Groove";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "t01", null, { focus: "50% 58%" }],                  // That notch... (AI high, fast punch-in)
  ["iron", "t01", null, { zoom: 1.6, focus: "50% 58%" }],     // ...on your iron: tighter second angle at 0.9 s
  ["Yes,", "s01", "clip"],      // button on cardigan (stock)
  ["sticks", "s02", "clip"],    // button sticks up (stock)
  ["hot", "s03", "clip"],       // hot plate: iron on board (stock)
  ["Slide", "t04", "clip"],     // plate across a plastic button (AI + LTX)
  ["melt", "t05"],              // melted button (AI)
  ["Iron", "s04", "clip"],      // iron around buttons (stock hands)
  ["But", "t02", null, { zoom: 1.3, focus: "50% 82%" }],   // trick to using that notch (AI)
  ["Slide", "t03", "clip"],     // tip beside a button (AI high + LTX)
  ["slips", "t03", null, { zoom: 1.5, focus: "47% 50%" }], // button slips into groove
  ["between", "t08"],           // gap between plate and body (AI)
  ["stays", "s07", "clip"],     // button stays out of the heat (stock)
  ["Now", "t09"],               // rest of the tip (AI)
  ["One", "s05", "clip"],       // one maker says (stock)
  ["pointed", "t09", null, { zoom: 1.5, focus: "50% 85%" }],
  ["reach", "s06", "clip"],     // reach around buttons (stock)
  ["Here's", "s09", "clip"],    // how to put it to work (stock)
  ["Flip", "t06"],              // flip shirt, press from the back (AI)
  ["Then", "s08", "clip"],      // switch sides (stock)
  ["Check", "t07"],             // care label (AI)
  ["So", "s10", "clip"],        // next time you press a shirt (stock)
  ["Follow", "t01", null, { zoom: 1.3, focus: "50% 60%" }],
];
