export const title = "Smoke Alarm Date";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "a01", null, { focus: "50% 38%" }],                      // hand flips the alarm, blank label (AI high, punch-in)
  ["over", "a01", null, { zoom: 1.6, focus: "50% 33%" }],   // tighter second angle on the label
  ["back", "t01", "clip"],                                        // hand with alarm back (AI + LTX)
  ["You're", "s01", "clip"],                                      // stock: dark corridor
  ["green", "a02", null, { zoom: 1.3, focus: "50% 55%" }],
  ["years", "s02", "clip"],                                       // stock: clock ticking
  ["why", "a07", null, { zoom: 1.2, focus: "50% 38%" }],
  ["milk", "a06", null, { zoom: 1.2, focus: "50% 25%" }],
  ["Stay", "a05", null, { zoom: 1.2, focus: "50% 45%" }],
  ["Here's", "a03", null, { focus: "50% 45%" }],
  ["Dust", "a03", null, { zoom: 1.6, focus: "35% 40%" }],
  ["battery", "a06", null, { zoom: 1.5, focus: "50% 15%" }],
  ["So", "a07", null, { zoom: 1.5, focus: "60% 40%" }],
  ["different", "a02", null, { zoom: 1.6, focus: "50% 55%" }],
  ["exactly", "a04", null, { focus: "55% 40%" }],
  ["printed", "a04", null, { zoom: 1.6, focus: "65% 38%" }],
  ["made", "a01", null, { zoom: 1.3, focus: "50% 35%" }],
  ["U.S.", "a06", null, { zoom: 1.3, focus: "50% 22%" }],
  ["ten", "s02", "clip"],
  ["But", "t02", "clip"],                                         // thumb on test button (AI + LTX)
  ["old", "a07", null, { zoom: 1.2, focus: "50% 40%" }],
  ["slow", "a03", null, { zoom: 1.4, focus: "55% 50%" }],
  ["Now", "a03", null, { zoom: 1.3, focus: "45% 40%" }],
  ["National", "a02", null, { zoom: 1.2, focus: "50% 55%" }],
  ["Almost", "a05", null, { zoom: 1.5, focus: "50% 40%" }],
  ["So", "a04", null, { zoom: 1.2, focus: "55% 40%" }],
  ["blinking", "a02", null, { zoom: 1.7, focus: "42% 52%" }],
  ["date", "a01", null, { zoom: 1.5, focus: "50% 32%" }],
  ["What's", "s01", "clip"],
  ["Comment", "a06", null, { zoom: 1.3, focus: "50% 22%" }],
];
