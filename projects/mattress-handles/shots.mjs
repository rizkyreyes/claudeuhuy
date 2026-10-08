export const title = "Mattress Handles";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "t01", null, { focus: "30% 50%" }],                    // Those handles (AI high, punch-in)
  ["side", "t01", null, { zoom: 1.6, focus: "35% 58%" }],       // tighter second angle at 0.9 s
  ["never", "t02"],                                             // never meant for carrying (AI high, frayed)
  ["dragging", "s01", "clip"],                                  // dragging a mattress (stock movers, cropped)
  ["fingers", "t03", "clip"],                                   // fingers hooked through (AI + LTX)
  ["rips", "t02", null, { zoom: 1.5, focus: "55% 45%" }],       // rips right off
  ["Hang", "s02", "clip"],                                      // bedroom (stock)
  ["real", "t04", null, { zoom: 1.2, focus: "35% 40%" }],       // real job
  ["bed.", "s03", "clip"],                                      // make the bed (stock)
  ["problem.", "t05"],                                          // heavy mattress in hallway
  ["heavy", "t05", null, { zoom: 1.5, focus: "70% 50%" }],
  ["stitched", "t06"],                                          // stitched handles
  ["catch.", "t01", null, { zoom: 1.3, focus: "45% 55%" }],
  ["sewn", "t06", null, { zoom: 1.5, focus: "70% 20%" }],       // sewn into the cover
  ["stitching", "t02", null, { zoom: 1.7, focus: "30% 40%" }],  // stitching can't hold
  ["Simmons", "t08"],                                           // foundation
  ["position", "t04", "clip"],                                  // position the mattress (AI + LTX)
  ["carrying", "t02", null, { zoom: 1.3, focus: "50% 50%" }],
  ["Serta", "t08", null, { zoom: 1.6, focus: "72% 35%" }],
  ["handles", "t01", null, { zoom: 1.5, focus: "30% 60%" }],    // handles are designed
  ["that's", "t04", null, { zoom: 1.4, focus: "20% 35%" }],
  ["nudge", "t04", null, { zoom: 1.6, focus: "25% 42%" }],
  ["But", "t09"],                                               // no handles at all
  ["why", "t09", null, { zoom: 1.4, focus: "50% 40%" }],
  ["Here's", "t10"],                                            // no-flip designs
  ["No-flip", "t10", null, { zoom: 1.5, focus: "50% 38%" }],
  ["nobody", "t09", null, { zoom: 1.2, focus: "60% 45%" }],
  ["flimsy", "t06", null, { zoom: 1.8, focus: "55% 22%" }],
  ["So", "t05", null, { zoom: 1.3, focus: "40% 40%" }],         // how do you move one
  ["move", "t11"],                                              // bag it
  ["Simmons", "t11", null, { zoom: 1.4, focus: "50% 45%" }],
  ["bag", "t11", null, { zoom: 1.7, focus: "55% 30%" }],
  ["carry", "t05", null, { zoom: 1.2, focus: "60% 45%" }],
  ["So", "t04", null, { zoom: 1.3, focus: "30% 45%" }],         // slide it
  ["don't", "s03", "clip"],
  ["Tell", "s02", "clip"],
];
