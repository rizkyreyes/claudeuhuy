export const title = "Zipper Lock Tab";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "t01", null, { focus: "50% 45%" }],                    // If your zipper... (AI high, fast punch-in)
  ["sliding", "t01", null, { zoom: 1.6, focus: "45% 58%" }],    // tighter second angle at 1.0 s
  ["unlocked.", "t02"],                                         // unlocked (AI)
  ["walking", "s06", "clip"],                                   // walking across a parking lot (stock)
  ["creeping", "t02", null, { zoom: 1.5, focus: "42% 50%" }],   // creeping open
  ["So", "s04", "clip"],                                        // zip it up (stock, cropped)
  ["slides", "s01", "clip"],                                    // slides back down (stock feet)
  ["Stay", "t01", null, { zoom: 1.3, focus: "50% 50%" }],
  ["built", "s05", "clip"],                                     // built into the zipper (stock denim)
  ["Look", "t03"],                                              // pull tab (AI high)
  ["stands", "t03", null, { zoom: 1.5, focus: "36% 32%" }],
  ["fold", "t01", null, { zoom: 1.7, focus: "45% 60%" }],       // fold the tab down flat
  ["something", "s03", "clip"],                                 // something clicks into place (stock)
  ["Inside", "t04", "clip"],                                    // tiny pin (AI + LTX)
  ["Here's", "t04", null, { zoom: 1.4, focus: "50% 45%" }],
  ["lies", "t01", null, { zoom: 1.8, focus: "48% 62%" }],
  ["pin", "t04", null, { zoom: 1.3, focus: "50% 62%" }],
  ["Lift", "t06", null, { zoom: 1.2, focus: "22% 22%" }],       // lift the tab (AI)
  ["Pull", "s04", "clip"],
  ["That's", "t03", null, { zoom: 1.3, focus: "40% 45%" }],
  ["most", "s05", "clip"],
  ["Now", "t05"],                                               // worn pin (AI)
  ["wear", "t05", null, { zoom: 1.5, focus: "50% 32%" }],
  ["grind", "t04", null, { zoom: 1.7, focus: "50% 72%" }],
  ["So", "s01", "clip"],
  ["Lay", "t01", null, { zoom: 1.4, focus: "47% 58%" }],
  ["What's", "t03", null, { zoom: 1.2, focus: "45% 40%" }],
  ["Comment", "t06", null, { zoom: 1.25, focus: "25% 25%" }],
];
