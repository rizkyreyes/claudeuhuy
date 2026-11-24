// Procedural garbage-disposal foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, water-rush, splash, spark-crackle, button-click, room-tone. New: disposal-grind, motor-hum, motor-spinup, switch-click, ice-clatter, wrench-turn, pit-knock.
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
// deny-thud: the stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
// water-rush: water/air through a closed pipe, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6021), 180, 0.35, "low"), mid = svf(noise(a.length, 6022), t => 620 + 90 * Math.sin(t * 2.3), 0.15);
  for (let i = 0; i < a.length; i++) a[i] = 0.9 * lo[i] + 0.35 * mid[i];
  write("water-rush.wav", fades(a, 250, 250), -11); }
// splash: a dryer hitting water (thump + spray), 1.2 s
{ const a = len(1.2); thump(a, 0, 70, 0.8, 9); const s = svf(noise(a.length, 9001), t => 2500 - 1500 * t, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.7 * s[i] * Math.exp(-t * 4) * Math.min(1, t * 80); }
  blips(a, 18, 0.15, 1.0, 500, 1400, 0.25, 9002, 25); write("splash.wav", fades(a, 0, 200), -4); }
// spark-crackle: a short electric spark, 0.5 s
{ const a = len(0.5), r = rng(9021), h = svf(noise(a.length, 9022), 6000, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (Math.abs(r()) > 0.93 ? 1 : 0.08) * Math.exp(-t * 9); }
  write("spark-crackle.wav", fades(a, 0, 120), -6); }
// button-click: plastic push button, 0.25 s
{ const a = len(0.25); add(a, svf(noise(300, 9031), 3000, 0.5), 0.8); modal(a, 0.002, 1800, [[1, 1, 1], [2.4, 0.4, 2]], 0.3, 60); write("button-click.wav", fades(a, 0, 60), -6); }
// room-tone: small tiled bathroom (low air + faint hum), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 9051), 300, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] + 0.05 * Math.sin(2 * Math.PI * 120 * t); }
  write("room-tone.wav", fades(a, 300, 300), -20); }
// ---- new for the garbage disposal (3d-45a) ----
// disposal-grind: induction motor whine + food being torn against the ring (gritty, uneven), 2 s (loops)
{ const a = len(2.0), r = rng(9201), g = svf(noise(a.length, 9202), t => 1800 + 600 * Math.sin(t * 11), 0.35), lo = svf(noise(a.length, 9203), 260, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; const grit = Math.abs(r()) > 0.82 ? 1 : 0.25;
    a[i] = 0.35 * Math.sin(2 * Math.PI * 115 * t) + 0.18 * Math.sin(2 * Math.PI * 230 * t) + 0.6 * g[i] * grit * (0.6 + 0.4 * Math.sin(t * 17)) + 0.5 * lo[i]; }
  write("disposal-grind.wav", fades(a, 150, 150), -12); }
// motor-hum: stalled motor, 60 Hz hum with a strained buzz, 2 s (loops)
{ const a = len(2.0); for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(2 * Math.PI * 60 * t) + 0.6 * Math.sin(2 * Math.PI * 120 * t) + 0.3 * Math.sign(Math.sin(2 * Math.PI * 120 * t)) * (0.7 + 0.3 * Math.sin(t * 6)); }
  write("motor-hum.wav", fades(a, 120, 120), -14); }
// motor-spinup: rising whine as the plate comes up to speed, 1.2 s
{ const a = len(1.2); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 40 + 75 * (1 - Math.exp(-t * 4)); ph += 2 * Math.PI * f / SR; a[i] = (Math.sin(ph) + 0.4 * Math.sin(2 * ph) + 0.2 * Math.sin(3 * ph)) * Math.min(1, t * 8); }
  add(a, svf(noise(a.length, 9211), t => 300 + 900 * t, 0.4), 0.25); write("motor-spinup.wav", fades(a, 5, 200), -8); }
// switch-click: wall toggle switch, 0.3 s
{ const a = len(0.3); add(a, svf(noise(400, 9221), 3500, 0.4), 0.9); modal(a, 0.003, 1300, [[1, 1, 1], [2.7, 0.5, 2]], 0.4, 70); thump(a, 0.0, 180, 0.3, 50); write("switch-click.wav", fades(a, 0, 60), -4); }
// ice-clatter: cubes hitting a steel sink, 1 s
{ const a = len(1.0), r = rng(9231);
  for (let k = 0; k < 9; k++) { const t0 = 0.02 + 0.6 * Math.abs(r()) * (k / 9 + 0.3); modal(a, t0, 1700 + 900 * Math.abs(r()), METAL, 0.35, 30); add(a, svf(noise(700, 9232 + k), 4200, 0.4), 0.25, t0); }
  write("ice-clatter.wav", fades(a, 0, 150), -5); }
// wrench-turn: hex key forcing the stuck plate back and forth (creak + clunks), 0.7 s
{ const a = len(0.7), s = svf(noise(a.length, 9241), t => 500 + 300 * Math.sin(t * 20), 0.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * (0.5 + 0.5 * Math.sin(t * 30)); }
  modal(a, 0.12, 700, METAL, 0.35, 30); modal(a, 0.45, 640, METAL, 0.35, 30); write("wrench-turn.wav", fades(a, 10, 120), -6); }
// pit-knock: a hard pit rattling against the ring, 0.4 s
{ const a = len(0.4); thump(a, 0, 220, 0.6, 40); modal(a, 0.004, 1150, METAL, 0.4, 35); modal(a, 0.09, 1250, METAL, 0.25, 40); write("pit-knock.wav", fades(a, 0, 80), -5); }
