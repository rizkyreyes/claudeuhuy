export const title = "Vacuum Suction Valve";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "t01", null, { focus: "45% 45%" }],                    // That little slider (AI high, punch-in)
  ["vacuum", "t01", null, { zoom: 1.6, focus: "35% 25%" }],     // tighter second angle at 1.2 s
  ["turns", "t01", "clip"],                                     // thumb slides it (AI + LTX)
  ["vacuuming", "t02"],                                         // curtains stuck
  ["panel", "t02", null, { zoom: 1.5, focus: "50% 35%" }],
  ["nozzle", "t02", null, { zoom: 1.7, focus: "55% 30%" }],
  ["Stay", "t05"],
  ["fix", "t03"],
  ["Here's", "t04"],                                            // the problem
  ["vacuum", "s01", "clip"],                                    // stock: red nozzle on rug
  ["hard", "t04", null, { zoom: 1.4, focus: "50% 40%" }],
  ["thin", "t02", null, { zoom: 1.3, focus: "50% 45%" }],
  ["makers", "t05", null, { zoom: 1.4, focus: "50% 35%" }],
  ["hole", "t03", null, { zoom: 1.4, focus: "35% 55%" }],
  ["slider", "t01", null, { zoom: 1.5, focus: "70% 25%" }],
  ["Slide", "t05", "clip"],                                     // slider pushed open (AI + LTX)
  ["But", "t03", null, { zoom: 1.7, focus: "35% 55%" }],
  ["weaken", "t02"],
  ["Here's", "t03", null, { zoom: 1.2, focus: "55% 45%" }],
  ["motor", "t05", null, { zoom: 1.5, focus: "50% 30%" }],
  ["Whatever", "t03", null, { zoom: 1.8, focus: "30% 50%" }],
  ["grip", "t02", null, { zoom: 1.5, focus: "50% 38%" }],
  ["Bissell", "t01", null, { zoom: 1.2, focus: "50% 40%" }],
  ["drapes", "t02", null, { zoom: 1.2, focus: "50% 50%" }],
  ["it's", "s02", "clip"],                                      // stock: top-down carpet
  ["high", "t06"],
  ["So", "t05", null, { zoom: 1.3, focus: "45% 35%" }],
  ["open", "t03", null, { zoom: 1.4, focus: "60% 40%" }],
  ["fabric", "t02", null, { zoom: 1.4, focus: "50% 35%" }],
  ["stuck", "t02", null, { zoom: 1.8, focus: "55% 32%" }],
  ["Tell", "s01", "clip"],
  ["house", "t01", null, { zoom: 1.3, focus: "40% 40%" }],
];
