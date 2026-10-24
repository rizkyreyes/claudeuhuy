// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const title = "Rearview Mirror Tab";
export const cues = [
  [null, "a01", null, { focus: "50% 35%" }],
  ["rearview", "a02", null, { zoom: 1.1, focus: "45% 40%" }],
  ["You", "a03", null, { zoom: 1.2, focus: "50% 35%" }],
  ["truck", "t02", "clip"],
  ["blast", "a08", null, { zoom: 1.2, focus: "50% 55%" }],
  ["Stay", "a02", null, { zoom: 1.5, focus: "35% 40%" }],
  ["never", "a06", null, { zoom: 1.3, focus: "60% 60%" }],
  ["Here's", "a09", null, { zoom: 1.2, focus: "50% 40%" }],
  ["Your", "a01", null, { zoom: 1.5, focus: "50% 35%" }],
  ["wedge", "a04", null, { zoom: 1.2, focus: "50% 35%" }],
  ["silver", "a04", null, { zoom: 1.6, focus: "60% 80%" }],
  ["bright", "a07", null, { zoom: 1.2, focus: "50% 40%" }],
  ["But", "a04", null, { zoom: 1.5, focus: "70% 20%" }],
  ["only", "a09", null, { zoom: 1.4, focus: "50% 45%" }],
  ["Now", "s01", "clip"],
  ["Flip", "t01", "clip"],
  ["bright", "a05", null, { zoom: 1.2, focus: "50% 45%" }],
  ["ceiling", "a06", null, { zoom: 1.2, focus: "60% 60%" }],
  ["So", "a08", null, { zoom: 1.2, focus: "50% 55%" }],
  ["glare", "s02", "clip"],
  ["You", "a05", null, { zoom: 1.4, focus: "50% 45%" }],
  ["But", "a07", null, { zoom: 1.3, focus: "50% 40%" }],
  ["Many", "a09", null, { zoom: 1.1, focus: "50% 40%" }],
  ["So", "a01", null, { zoom: 1.3, focus: "50% 40%" }],
  ["reach", "a02", null, { zoom: 1.3, focus: "45% 40%" }],
  ["What's", "a08", null, { zoom: 1.5, focus: "35% 70%" }],
  ["Comment", "a03", null, { zoom: 1.3, focus: "50% 35%" }],
];
export const emphasis = ["night", "wedge", "four", "tilts", "ceiling", "glare", "catch", "darkens", "silver", "tab"];
export const slams = [
  { word: "mode", lines: ["NIGHT", "MODE"], dur: 1.3 },
  { word: "wedge", lines: ["A WEDGE", "OF GLASS"], dur: 1.3 },
  { word: "ceiling", lines: ["POINTS AT", "THE CEILING"], dur: 1.3 },
  { word: "catch", lines: ["THERE'S", "A CATCH"], dur: 1.2 },
];
export const counters = [
  { word: "four", to: 4, unit: "PERCENT REFLECTED", dur: 1.5 },
];
export const payoff = "hack";
