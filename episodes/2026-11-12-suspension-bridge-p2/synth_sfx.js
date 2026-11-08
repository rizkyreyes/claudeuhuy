// Procedural bridge-building foley for part 2 (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Part-1 set (concrete rumble, stone slide, tower rise, saddle clunk, wind gust, rope zip, plank clack, wheel roll, latch clunk,
// strand click, squeeze press, waves, deny thud) + band clamp, bolt tick, winch whine, deck thud, barge horn-free hull wash, closure ring.
const fs = require("fs"), path = require("path");
const SR = 48000, OUT = path.join(__dirname, "sfx");
fs.mkdirSync(OUT, { recursive: true });
const rng = s => () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296) * 2 - 1;
const db = x => Math.pow(10, x / 20);
function write(name, a, peakDb) {
  let pk = 0; for (const v of a) pk = Math.max(pk, Math.abs(v));
  const g = pk ? db(peakDb) / pk : 1, b = Buffer.alloc(44 + a.length * 2);
  b.write("RIFF", 0); b.writeUInt32LE(36 + a.length * 2, 4); b.write("WAVEfmt ", 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20);
  b.writeUInt16LE(1, 22); b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34);
  b.write("data", 36); b.writeUInt32LE(a.length * 2, 40);
  a.forEach((v, i) => b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, v * g)) * 32767), 44 + i * 2));
  fs.writeFileSync(path.join(OUT, name), b); console.log(name, (a.length / SR).toFixed(2) + "s");
}
function svf(x, fc, q, mode = "band") {
  let lo = 0, bd = 0; const y = new Float32Array(x.length);
  for (let i = 0; i < x.length; i++) {
    const f = 2 * Math.sin(Math.PI * Math.min(typeof fc === "function" ? fc(i / SR) : fc, SR / 6) / SR);
    const hi = x[i] - lo - q * bd; bd += f * hi; lo += f * bd; y[i] = mode === "low" ? lo : mode === "high" ? hi : bd;
  }
  return y;
}
const noise = (n, s) => { const r = rng(s), a = new Float32Array(n); for (let i = 0; i < n; i++) a[i] = r(); return a; };
const len = s => new Float32Array(Math.round(SR * s));
const fades = (a, inMs, outMs) => { const ni = SR * inMs / 1000, no = SR * outMs / 1000;
  for (let i = 0; i < ni; i++) a[i] *= i / ni; for (let i = 0; i < no; i++) a[a.length - 1 - i] *= i / no; return a; };
function modal(a, t0, f0, partials, amp, decay) {
  const i0 = Math.round(t0 * SR);
  for (let i = i0; i < a.length; i++) {
    const t = (i - i0) / SR; let v = 0;
    for (const [ratio, g, d] of partials) v += g * Math.sin(2 * Math.PI * f0 * ratio * t) * Math.exp(-t * decay * d);
    a[i] += amp * v; if (t > 6 / decay) break;
  }
}
function thump(a, t0, f0, amp, decay) {          // pitched-down sine hit (body of a heavy impact)
  const i0 = Math.round(t0 * SR);
  for (let i = i0; i < a.length; i++) { const t = (i - i0) / SR; a[i] += amp * Math.sin(2 * Math.PI * f0 * (1 + 1.5 * Math.exp(-t * 30)) * t) * Math.exp(-t * decay); }
}
const add = (a, b, g = 1, off = 0) => { const o = Math.round(off * SR); for (let i = 0; i < b.length && i + o < a.length; i++) a[i + o] += g * b[i]; return a; };
const METAL = [[1, 1, 1], [2.76, 0.5, 1.6], [5.4, 0.3, 2.4], [8.9, 0.15, 3.2]];
// gurgle-ish bubbles: n short rising blips scattered over dur
function blips(a, n, t0, t1, f0, f1, amp, seed, decay = 28) {
  const r = rng(seed);
  for (let k = 0; k < n; k++) { const ts = t0 + (t1 - t0) * Math.abs(r()), f = f0 + (f1 - f0) * Math.abs(r()), i0 = Math.round(ts * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.12; i++) { const t = (i - i0) / SR; a[i] += amp * Math.sin(2 * Math.PI * f * (1 + 2.2 * t) * t) * Math.exp(-t * decay); } }
}
// waves: open-sea wash against the hull, 4 s
{ const a = len(4), n = svf(noise(a.length, 71), 650, 0.5), lo = svf(noise(a.length, 72), 180, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.3 * n[i] + 0.3 * lo[i]) * (0.45 + 0.55 * Math.sin(2 * Math.PI * 0.35 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 4)); }
  write("waves.wav", fades(a, 100, 400), -14); }
// concrete-rumble: a giant block rising out of the ground (low rumble + grit), 1.2 s
{ const a = len(1.2), lo = svf(noise(a.length, 101), 90, 0.5, "low"), g = svf(noise(a.length, 102), 1400, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR, e = Math.sin(Math.PI * Math.min(1, t / 1.2)); a[i] = e * (0.8 * lo[i] + 0.12 * g[i]); }
  thump(a, 1.0, 50, 0.6, 9); write("concrete-rumble.wav", fades(a, 30, 150), -5); }
// stone-slide: the near half of the anchorage sliding off (concrete scrape), 0.9 s
{ const a = len(0.9), s = svf(noise(a.length, 103), t => 300 + 400 * t, 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.9)); }
  thump(a, 0.0, 60, 0.4, 12); write("stone-slide.wav", fades(a, 10, 200), -7); }
// tower-rise: steel sections stacking up (rising rumble + 5 clanks), 1.6 s
{ const a = len(1.6), lo = svf(noise(a.length, 104), t => 80 + 60 * t, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * lo[i] * Math.sin(Math.PI * Math.min(1, t / 1.6)); }
  for (let k = 0; k < 5; k++) modal(a, 0.1 + k * 0.28, 140 + k * 18, METAL, 0.3, 10);
  write("tower-rise.wav", fades(a, 20, 200), -6); }
// saddle-clunk: a heavy cast saddle seated on the tower top
{ const a = len(0.7); thump(a, 0, 58, 1, 9); modal(a, 0.005, 210, METAL, 0.4, 10); write("saddle-clunk.wav", fades(a, 0, 150), -5); }
// wind-gust: high wind for the kite and the catwalk shots, 3 s
{ const a = len(3), n = svf(noise(a.length, 105), t => 500 + 350 * Math.sin(2 * Math.PI * 0.4 * t), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.33 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  write("wind-gust.wav", fades(a, 200, 500), -12); }
// rope-zip: a line pulled fast across (rising whizz), 1 s
{ const a = len(1.0), n = svf(noise(a.length, 106), t => 700 + 2200 * t, 0.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.sin(Math.PI * Math.min(1, t / 1.0)); }
  write("rope-zip.wav", fades(a, 20, 150), -9); }
// plank-clack: one catwalk section clicking in place
{ const a = len(0.25); modal(a, 0, 420, [[1, 1, 1], [2.3, 0.5, 1.5]], 0.6, 30); add(a, svf(noise(3000, 107), 2600, 0.6), 0.2); write("plank-clack.wav", fades(a, 0, 60), -9); }
// wheel-roll: the spinning wheel running along the catwalk (pulley whir + rhythmic sheave ticks), 5 s
{ const a = len(5), n = svf(noise(a.length, 108), 900, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(Math.PI * Math.min(1, t / 5)) * (0.25 * n[i] + 0.2 * Math.sin(2 * Math.PI * 160 * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 7 * t))); }
  for (let k = 0; k < 25; k++) modal(a, 0.1 + k * 0.19, 900, [[1, 1, 1]], 0.06, 60);
  write("wheel-roll.wav", fades(a, 80, 300), -10); }
// latch-clunk: the wire loop hooked on at the far anchorage
{ const a = len(0.5); modal(a, 0, 320, METAL, 0.5, 14); thump(a, 0, 80, 0.5, 18); write("latch-clunk.wav", fades(a, 0, 100), -6); }
// strand-click: a strand dropping into the bundle
{ const a = len(0.2); modal(a, 0, 650, [[1, 1, 1], [2.7, 0.4, 2]], 0.5, 40); write("strand-click.wav", fades(a, 0, 40), -10); }
// squeeze-press: hydraulic compaction (whine down + creak + clunk), 1.4 s
{ const a = len(1.4), n = svf(noise(a.length, 109), 300, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(Math.PI * Math.min(1, t / 1.4)) * (0.35 * Math.sin(2 * Math.PI * (220 - 70 * t) * t) + 0.3 * n[i]); }
  thump(a, 1.15, 60, 0.6, 10); write("squeeze-press.wav", fades(a, 40, 150), -6); }
// deny-thud: the stinger ("nothing can slip", "still no road")
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
// band-clamp: two steel half shells slamming shut round the cable, 0.7 s
{ const a = len(0.7); thump(a, 0, 70, 0.9, 11); modal(a, 0.004, 260, METAL, 0.55, 9); modal(a, 0.02, 390, METAL, 0.25, 12); write("band-clamp.wav", fades(a, 0, 150), -5); }
// bolt-tick: a bolt run home (short ratchet), 0.3 s
{ const a = len(0.3);
  for (let k = 0; k < 4; k++) modal(a, k * 0.045, 900 + 60 * k, [[1, 1, 1], [2.4, 0.5, 2]], 0.35, 45);
  write("bolt-tick.wav", fades(a, 0, 60), -10); }
// winch-whine: hoist winch lifting a deck section (motor hum rising in pitch + cable creak), 1.6 s
{ const a = len(1.6), cr = svf(noise(a.length, 211), 1800, 0.3);
  let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 90 + 70 * Math.min(1, t / 1.2); ph += 2 * Math.PI * f / SR;
    const e = Math.min(1, t / 0.15) * Math.min(1, (1.6 - t) / 0.3);
    a[i] = e * (0.5 * Math.sin(ph) + 0.25 * Math.sin(2 * ph) + 0.12 * Math.sin(3.01 * ph) + 0.05 * cr[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 7 * t))); }
  write("winch-whine.wav", fades(a, 30, 200), -9); }
// deck-thud: a steel deck section seating against its neighbour, 0.8 s
{ const a = len(0.8); thump(a, 0, 52, 1, 7); modal(a, 0.01, 140, METAL, 0.35, 6); add(a, svf(noise(6000, 212), 400, 0.6), 0.25); write("deck-thud.wav", fades(a, 0, 200), -4); }
// closure-ring: the last joint closes, a long bright steel ring, 1.6 s
{ const a = len(1.6); modal(a, 0, 520, METAL, 0.6, 2.2); modal(a, 0.0, 780, [[1, 1, 1], [2.1, 0.4, 1.5]], 0.3, 3); thump(a, 0, 60, 0.6, 10); write("closure-ring.wav", fades(a, 0, 400), -6); }
