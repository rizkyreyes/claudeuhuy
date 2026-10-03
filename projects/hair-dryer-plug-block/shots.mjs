export const title = "Hair Dryer Plug Block";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "t01", null, { focus: "40% 60%" }],                   // That chunky block (AI high still, punch-in)
  ["hair", "t01", null, { zoom: 1.6, focus: "35% 62%" }],      // second angle: tight on the two buttons
  ["isn't", "t02", "clip"],       // isn't a power brick (LTX: hand turns the block)
  ["It's", "t03"],                // It's a safety device
  ["and", "t04", "clip"],         // and it has saved lives (stock hospital corridor)
  ["Two", "t03", null, { zoom: 1.4, focus: "50% 55%" }],   // Two little buttons
  ["But", "t05", "clip"],         // reloop 1: nobody tells you (stock circuit)
  ["It's", "t06", null, { zoom: 1.1, focus: "50% 55%" }],  // called an appliance leakage circuit interrupter (AI high cutaway)
  ["electricity", "t08", "clip"], // electricity flowing out
  ["Normally,", "t09", "clip"],   // those match
  ["Here's", "t07", "clip"],      // reloop 2: exactly how it protects you
  ["If", "t10", "clip"],          // current starts leaking
  ["and", "t01", null, { zoom: 1.3, focus: "45% 60%" }],   // the block cuts the power
  ["So", "t11", "clip"],          // press reset, then test (LTX)
  ["If", "t12"],                  // if it doesn't, stop using that dryer
  ["Consumer", "t13", "clip"],    // Consumer Product Safety Commission
  ["hand-held", "t12", null, { zoom: 1.5, focus: "30% 40%" }], // hand-held hair dryers once caused
  ["About", "t14", "clip"],       // small children
  ["1987", "t15", "clip"],        // 1987 standard
  ["Since", "t03", null, { zoom: 1.2, focus: "50% 40%" }], // Since 1991
  ["And", "t06", null, { zoom: 1.5, focus: "50% 70%" }],   // reloop 3: the part that got me
  ["After", "t16", "clip"],       // two deaths in 1992
  ["It", "t17"],                  // still doesn't make a dryer safe near water
  ["Keep", "t18"],                // unplug it
  ["Follow", "t01", null, { zoom: 1.2, focus: "50% 55%" }],
];
