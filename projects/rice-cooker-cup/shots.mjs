export const title = "Rice Cooker Cup";
// [cue word (next occurrence after previous cue), shot id, kind, { zoom, focus }]
export const cues = [
  [null, "r01", null, { focus: "50% 40%" }],                     // plastic cup of rice on the cooker (AI high, punch-in)
  ["rice", "r01", null, { zoom: 1.6, focus: "35% 30%" }],        // tighter second angle
  ["scoop", "t01", "clip"],                                      // hand scoops rice (AI + LTX)
  ["fill", "r03", null, { zoom: 1.2, focus: "50% 40%" }],
  ["somehow", "s03", "clip"],                                    // stock: rice bowls
  ["Keep", "s01", "clip"],                                       // stock: rice cooker on counter
  ["tonight", "r06", null, { zoom: 1.2, focus: "50% 40%" }],
  ["Here's", "r02", null, { focus: "50% 45%" }],
  ["kitchen", "r02", null, { zoom: 1.5, focus: "72% 35%" }],
  ["plastic", "r01", null, { zoom: 1.3, focus: "35% 30%" }],
  ["three", "t02", "clip"],                                      // small cup beside the glass cup (AI + LTX)
  ["why", "r05", null, { zoom: 1.3, focus: "50% 40%" }],
  ["Nobody", "r03", null, { zoom: 1.5, focus: "30% 25%" }],
  ["Japanese", "r04", null, { zoom: 1.2, focus: "55% 55%" }],
  ["1891", "r01", null, { zoom: 1.2, focus: "50% 50%" }],
  ["But", "r06", null, { zoom: 1.5, focus: "60% 35%" }],
  ["exactly", "r04", null, { zoom: 1.4, focus: "40% 55%" }],
  ["Zojirushi", "r01", null, { zoom: 1.5, focus: "30% 40%" }],
  ["water", "r03", null, { zoom: 1.6, focus: "35% 25%" }],
  ["Grab", "r02", null, { zoom: 1.4, focus: "75% 35%" }],
  ["third", "r02", null, { zoom: 1.7, focus: "72% 25%" }],
  ["soggy", "r05", null, { zoom: 1.2, focus: "50% 40%" }],
  ["fix", "r06", null, { zoom: 1.2, focus: "50% 40%" }],
  ["lost", "r06", null, { zoom: 1.7, focus: "45% 30%" }],
  ["Next", "r01", null, { zoom: 1.2, focus: "50% 45%" }],
  ["Check", "r01", null, { zoom: 1.6, focus: "35% 30%" }],
  ["Got", "s03", "clip"],
  ["Comment", "r06", null, { zoom: 1.4, focus: "55% 40%" }],
];
