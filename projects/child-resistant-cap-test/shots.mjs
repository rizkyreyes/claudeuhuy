// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const title = "Child-Resistant Cap Test";
export const cues = [
  [null, "a01", null, { focus: "50% 45%" }],
  ["cap", "a02", null, { zoom: 1.1, focus: "50% 40%" }],
  ["You", "a03", null, { zoom: 1.3, focus: "60% 50%" }],
  ["won't", "t01", "clip"],
  ["thumb", "a02", null, { zoom: 1.5, focus: "50% 30%" }],
  ["Stay", "a06", null, { zoom: 1.2, focus: "50% 35%" }],
  ["stranger", "a04", null, { zoom: 1.2, focus: "50% 40%" }],
  ["Back", "s01", "clip"],
  ["calls", "a03", null, { zoom: 1.5, focus: "75% 55%" }],
  ["chemicals", "a07", null, { zoom: 1.2, focus: "50% 55%" }],
  ["But", "a08", null, { zoom: 1.2, focus: "50% 40%" }],
  ["actual", "s02", "clip"],
  ["Testers", "a05", null, { zoom: 1.1, focus: "50% 40%" }],
  ["give", "t02", "clip"],
  ["To", "a02", null, { zoom: 1.6, focus: "50% 40%" }],
  ["And", "a04", null, { zoom: 1.5, focus: "40% 55%" }],
  ["Over", "a05", null, { zoom: 1.5, focus: "50% 25%" }],
  ["But", "a09", null, { zoom: 1.1, focus: "50% 35%" }],
  ["Adults", "a06", null, { zoom: 1.1, focus: "50% 35%" }],
  ["So", "a01", null, { zoom: 1.3, focus: "40% 40%" }],
  ["narrow", "a05", null, { zoom: 1.3, focus: "55% 35%" }],
  ["child-resistant", "a07", null, { zoom: 1.2, focus: "50% 45%" }],
  ["What's", "a03", null, { zoom: 1.2, focus: "50% 50%" }],
  ["Tell", "a01", null, { zoom: 1.5, focus: "35% 40%" }],
];
export const emphasis = ["preschoolers", "1970", "Congress", "fifty", "eighty-five", "hardest", "ninety", "Adults", "child-proof", "gap"];
export const slams = [
  { word: "preschoolers", lines: ["TESTED ON", "PRESCHOOLERS"], dur: 1.4 },
  { word: "1970", lines: ["THE LAW", "OF 1970"], dur: 1.3 },
  { word: "gap", lines: ["THE NARROW", "GAP"], dur: 1.3 },
];
export const counters = [
  { word: "eighty-five", to: 85, unit: "PERCENT OF KIDS FAIL", dur: 1.5 },
  { word: "ninety", to: 90, unit: "PERCENT OF ADULTS OPEN IT", dur: 1.5 },
];
export const payoff = "safety";
