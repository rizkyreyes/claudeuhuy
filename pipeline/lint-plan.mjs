// lint-plan.mjs — beat-plan gates for the beat-plan method (docs/beat-plan-method.md). Exit 1 on any error.
//   node ../../pipeline/lint-plan.mjs <projectDir>
// Reads <projectDir>/plan.json, shots.mjs, script.json, assets/vo/audio_meta.json and thumb.json (if present).
// Run it after shots.mjs is written and BEFORE build/render. Every error is a reason to fix the plan or the
// shot list, not to skip the gate.
//
// plan.json format:
// { "beats": [
//   { "beat": "B1 hook", "from": null,      "job": "event",  "register": "photoreal", "hero": "cap flying off a bottle",
//     "framing": "macro", "shots": ["t01", "a01"], "onscreen": [] },
//   { "beat": "B2 count", "from": "Count", "job": "recognition", "register": "still", "hero": "the 21 teeth",
//     "framing": "close", "shots": ["a02"], "onscreen": ["21"] }, ... ] }
//  from      = the word that starts the beat (next occurrence after the previous beat's word, like shots.mjs cues)
//  register  = photoreal (generated clip/still of an event) | document (a REAL record: patent drawing, label, manual
//              page; never generated) | stock | still (AI still of the object) | drawn
//  framing   = macro | close | medium | wide | hands | document | archive
//  shots     = the shots.mjs ids used inside this beat (for a document beat, list the real document first)
//  onscreen  = every number that appears on screen in this beat (inside an image or a label). Captions don't count.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { fx, makeTA } from "./gen-shared.mjs";

const proj = path.resolve(process.argv[2] || ".");
const errors = [], warns = [];
const err = (m) => errors.push(m), warn = (m) => warns.push(m);
const read = (f) => JSON.parse(fs.readFileSync(path.join(proj, f), "utf8"));

const meta = read("assets/vo/audio_meta.json");
const VO = meta.scenes[0];
const VO_START = 0.35;                       // same as build-broll.mjs
const TA = makeTA(VO, VO_START);
const TOTAL = fx(VO_START + VO.duration + 1.2);
const plan = read("plan.json");
const beats = plan.beats || [];
const { cues } = await import(pathToFileURL(path.join(proj, "shots.mjs")).href);
const script = read("script.json");

// ---- resolve times (same chaining as build-broll.mjs)
let t = -1;
const shots = cues.map(([word, id, kind, opts = {}], i) => {
  const at = i === 0 ? 0 : (t = TA(word, t)); if (i === 0) t = 0;
  return { at, id, kind, zoom: opts.zoom ?? 1, focus: opts.focus ?? "" };
});
shots.forEach((s, i) => (s.end = shots[i + 1]?.at ?? TOTAL));
let bt = -1;
beats.forEach((b, i) => { b.at = i === 0 ? 0 : (bt = TA(b.from, bt)); if (i === 0) bt = 0; });
beats.forEach((b, i) => (b.end = beats[i + 1]?.at ?? TOTAL));

// ---- 1. the plan exists and every beat is complete
if (beats.length < 6) err(`plan has ${beats.length} beats; a 60–75 s video needs about 8–12`);
const REG = ["photoreal", "document", "stock", "still", "drawn"];
for (const b of beats) {
  const name = `${b.beat} (${b.at.toFixed(1)}s)`;
  if (!b.job) err(`${name}: no job`);
  if (!b.hero || typeof b.hero !== "string") err(`${name}: no hero — a beat with no hero is where people skip`);
  else if (/\b(and|\+|&)\b/.test(b.hero)) warn(`${name}: hero "${b.hero}" looks like two heroes — split the beat`);
  if (!REG.includes(b.register)) err(`${name}: register "${b.register}" must be one of ${REG.join(", ")}`);
  if (!b.framing) err(`${name}: no framing`);
  if (!Array.isArray(b.shots) || !b.shots.length) err(`${name}: no shots listed`);
  if (b.end - b.at > 12) warn(`${name}: lasts ${(b.end - b.at).toFixed(1)}s — a beat over 12 s usually outstays its job; split it`);
}

// ---- 2. two beats in a row with the same framing
for (let i = 1; i < beats.length; i++)
  if (beats[i].framing === beats[i - 1].framing) err(`${beats[i - 1].beat} → ${beats[i].beat}: same framing "${beats[i].framing}" twice in a row — change one`);

// ---- 3. the hook is photoreal and moves
const b1 = beats[0];
if (b1 && b1.register !== "photoreal") err(`hook beat register is "${b1.register}" — the hook is the event, it must be photoreal (a generated clip or real footage)`);
if (shots[0] && shots[0].kind !== "clip") warn(`first shot ${shots[0].id} is a still — the method wants a moving photoreal plate in the hook`);

// ---- 4. the shot list follows the plan (nothing outstays its beat)
for (const s of shots) {
  const b = beats.find((x) => s.at >= x.at - 0.01 && s.at < x.end - 0.01);
  if (!b) { err(`shot ${s.id} at ${s.at}s falls outside every beat`); continue; }
  if (!b.shots.includes(s.id)) err(`shot ${s.id} at ${s.at}s plays inside ${b.beat}, but that beat lists [${b.shots}] — a visual from another step outstaying it, or a plan that is out of date`);
}
for (const b of beats) for (const id of b.shots || []) if (!shots.some((s) => s.id === id)) warn(`${b.beat}: lists shot ${id} that no cue uses`);

// ---- 5. dead air (our b-roll is always full-bleed, so "dead" = one picture held too long)
for (const s of shots) {
  const hold = s.end - s.at;
  if (hold > 4.5) err(`dead air: shot ${s.id} holds ${hold.toFixed(1)}s (${s.at}–${fx(s.end)}s) — max 4.5 s; add a cue (tighter crop, second angle, hands)`);
}
for (let i = 1; i < shots.length; i++) {
  const a = shots[i - 1], b = shots[i];
  if (a.id === b.id && a.zoom === b.zoom && a.focus === b.focus) err(`cue ${i}: ${b.id} cuts to the identical picture (same zoom and focus) — change the crop or the shot`);
}
if (shots[1] && shots[1].at > 2.0) err(`opening holds ${shots[1].at}s — second angle must land inside 2 s`);

// ---- 6. every number on screen is spoken
const ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(" ");
const TENS_ = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];
const two = (n) => n < 20 ? ONES[n] : TENS_[Math.floor(n / 10)] + (n % 10 ? " " + ONES[n % 10] : "");
const words = (n) => {
  if (n < 100) return two(n);
  if (n < 1000) return ONES[Math.floor(n / 100)] + " hundred" + (n % 100 ? " " + two(n % 100) : "");
  if (n < 1e6) return words(Math.floor(n / 1000)) + " thousand" + (n % 1000 ? " " + words(n % 1000) : "");
  return null;
};
const yearWords = (n) => (n >= 1100 && n <= 1999) ? two(Math.floor(n / 100)) + " " + (n % 100 === 0 ? "hundred" : n % 100 < 10 ? "oh " + ONES[n % 100] : two(n % 100)) : null;
const spokenText = " " + VO.words.map((w) => w.text).join(" ").toLowerCase().replace(/[-–]/g, " ").replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ") + " ";
const isSpoken = (raw) => {
  const n = Number(String(raw).replace(/[^0-9]/g, ""));
  if (!Number.isFinite(n) || String(raw).replace(/[^0-9]/g, "") === "") return true;
  const cands = [String(n), words(n), yearWords(n)].filter(Boolean);
  return cands.some((c) => spokenText.includes(" " + c + " ") || spokenText.includes(" " + c));
};
for (const b of beats) for (const n of b.onscreen || []) if (!isSpoken(n)) err(`${b.beat}: number ${n} is on screen but never spoken — say it or remove it`);
if (fs.existsSync(path.join(proj, "thumb.json"))) {
  const label = read("thumb.json").label || "";
  for (const n of label.match(/\d[\d,]*/g) || []) if (!isSpoken(n)) err(`thumbnail label number ${n} is never spoken in the video`);
}

// ---- 7. length, pauses, voice speed
const speechLen = VO.speechEnd - VO.speechStart;
if (TOTAL > 179) err(`total ${TOTAL}s is over the 2:59 ceiling`);
else if (speechLen < 58 || speechLen > 80) warn(`speech runs ${speechLen.toFixed(1)}s — playbook target is 60–75 s`);
const longGaps = VO.words.slice(1).map((w, i) => w.start - VO.words[i].end).filter((g) => g > 0.4).length;
if (longGaps) warn(`${longGaps} pauses longer than 0.4 s — run: python3 ../../pipeline/cap-pauses.py .`);
const speed = script.voiceSettings?.speed ?? 1.08;
if (speed > 1.0) warn(`voice speed ${speed} — the method keeps speed 1.0 and caps the pauses instead`);

// ---- 8. document shots must be real and sourced
const sources = fs.existsSync(path.join(proj, "publish/sources.txt")) ? fs.readFileSync(path.join(proj, "publish/sources.txt"), "utf8") : "";
for (const b of beats.filter((x) => x.register === "document")) {
  const id = (b.shots || [])[0];  // the hero shot of a document beat is listed first
  if (id && !new RegExp(`\\b${id}\\b[^\\n]*https?://`).test(sources)) err(`${b.beat}: document shot ${id} has no source line with a URL in publish/sources.txt — a document must be real, never generated`);
}

// ---- report
console.log(`lint-plan  ${beats.length} beats  ${shots.length} shots  total ${TOTAL}s  speech ${speechLen.toFixed(1)}s`);
for (const b of beats) console.log(`  ${b.at.toFixed(1).padStart(5)}s  ${b.beat.padEnd(18)} ${String(b.register).padEnd(9)} ${String(b.framing).padEnd(8)} ${b.hero}`);
for (const w of warns) console.log(`  ! ${w}`);
for (const e of errors) console.log(`  ✗ ${e}`);
if (errors.length) { console.log(`FAIL: ${errors.length} error(s)`); process.exit(1); }
console.log(`PASS${warns.length ? ` with ${warns.length} warning(s)` : ""}`);
