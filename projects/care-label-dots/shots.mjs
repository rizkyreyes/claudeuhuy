export const title = "Care Label Dots";
// [cue word (next occurrence after previous cue), shot id, kind]
export const cues = [
  [null, "d01", "clip"],        // Those little dots inside your laundry tag
  ["They're", "d02", "clip"],   // They're a temperature code
  ["Every", "d03"],             // Every dot is a heat limit
  ["Start", "d04", "clip"],     // Start with the washtub
  ["one", "d05"],               // one dot means cold
  ["Two", "d06"],               // Two dots is warm
  ["Three", "d07"],             // Three dots is hot
  ["sanitizing", "d08"],        // five dots is the sanitizing setting
  ["Now", "d09", "clip"],       // Now look at the iron symbol
  ["One", "d10", "clip"],       // One dot is low
  ["Two", "d11"],               // Two dots is medium
  ["Three", "d12", "clip"],     // Three dots is high
  ["cotton", "d13"],            // cotton and linen
  ["The", "d14", "clip"],       // The dryer symbol
  ["Every", "d15", "clip"],     // Every one of these is a maximum
  ["shrinks", "d16"],           // shrinks and damages fabric
  ["Care", "d17"],              // The Care Labeling Rule
  ["So", "d18"],                // So before you toss something in on hot
  ["Follow", "d01", "clip"],
];
