export const title = "Padlock Bottom Hole";
// [cue word (next occurrence after previous cue), shot id, kind]
export const cues = [
  [null, "t01", "clip"],          // Every padlock has a second hole
  ["Look", "t02"],                // Look underneath...tiny opening drilled through the metal
  ["Padlocks", "t03", "clip"],    // Padlocks live outside, bolted to gates, sheds, and fences
  ["rain", "t04", "clip"],        // exposed to rain and every temperature swing
  ["shackle", "t05"],             // Water gets into that shackle mechanism
  ["exit", "t06", "clip"],        // without an exit it sits against bare steel
  ["rusts.", "t07"],              // until the lock rusts
  ["crack", "t08", "clip"],       // trapped water expands and can crack the housing
  ["drain", "t09"],               // that hole lets gravity drain the case first
  ["sticks,", "t10"],             // when a padlock sticks
  ["lubricant,", "t11", "clip"],  // that same opening is where you drop lubricant
  ["household", "t12"],           // skip the household oil
  ["paste", "t13"],               // turns into paste inside a lock
  ["graphite", "t14"],            // locksmiths reach for dry graphite or PTFE
  ["gumming", "t15"],             // sheds water without gumming up the parts
  ["bottom;", "t16"],             // not every padlock puts this hole on the bottom
  ["down", "t17"],                // now you know exactly what it's for
  ["Follow", "t18", "clip"],
];
