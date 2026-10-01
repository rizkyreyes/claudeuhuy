export const title = "Trash Can Vents";
// [cue word (next occurrence after previous cue), shot id, kind]
export const cues = [
  [null, "t01"],              // Ever fight a full trash bag
  ["trash", "t09"],
  ["Look", "t02"],            // Look near the top for little holes
  ["When", "s01", "clip"],    // When you drop a bag in
  ["Then", "s02", "clip"],    // Then you pull up
  ["So", "t03", "clip"],      // So the can basically sucks the bag back down
  ["That's", "s03", "clip"],  // That's a vacuum seal
  ["Vent", "t04"],            // Vent holes let air slip in
  ["pressure", "t07"],
  ["Some", "t05"],            // Some cans mold narrow channels
  ["Same", "t04"],
  ["Rubbermaid", "s04", "clip"],
  ["commercial", "t05"],
  ["own", "s05", "clip"],     // That's their own number
  ["other", "t07"],           // It works the other way too
  ["settles", "s06", "clip"], // bag settles flat
  ["And", "t02"],
  ["drill", "t08"],           // people drill a few small ones
  ["So", "t09"],              // So next time a bag fights back
  ["Follow", "t04"],
];
