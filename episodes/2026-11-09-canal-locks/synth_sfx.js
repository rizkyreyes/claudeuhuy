// Procedural canal-lock foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Wall sink, gate swing, gate clunk, valve lift, culvert rush, fill rumble, outlet gush, motor hum (mules), water lap, deny thud.
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
// wall-sink: the near-wall cover sinking away (heavy concrete grind + low thud)
{ const a = len(1.3), s = svf(noise(a.length, 41), t => 180 + 300 * Math.min(1, t / 1.0), 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * s[i] * Math.sin(Math.PI * Math.min(1, t / 1.05)); }
  thump(a, 0.95, 55, 0.6, 9); write("wall-sink.wav", fades(a, 30, 150), -6); }
// gate-swing: a huge steel leaf turning on its hinge (low creak + water push), 1.4 s
{ const a = len(1.4), w = svf(noise(a.length, 42), 260, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 70 + 25 * Math.sin(2 * Math.PI * 1.3 * t);
    a[i] = 0.25 * Math.sin(2 * Math.PI * f * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 11 * t)) * Math.sin(Math.PI * Math.min(1, t / 1.4)) + 0.35 * w[i]; }
  write("gate-swing.wav", fades(a, 60, 250), -8); }
// gate-clunk: leaves meeting / seating (deep metal hit)
{ const a = len(0.8); thump(a, 0.0, 60, 1, 8); modal(a, 0.0, 140, METAL, 0.3, 9);
  add(a, svf(noise(5000, 43), 900, 0.6), 0.25); write("gate-clunk.wav", fades(a, 0, 150), -5); }
// valve-lift: heavy gate valve starting to move (clank + hydraulic whine)
{ const a = len(1.0); modal(a, 0.0, 210, METAL, 0.5, 14); thump(a, 0.0, 80, 0.5, 12);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.08 * Math.sin(2 * Math.PI * (300 + 120 * t) * t) * Math.min(1, t / 0.2) * Math.exp(-Math.max(0, t - 0.6) * 6); }
  write("valve-lift.wav", fades(a, 0, 150), -7); }
// culvert-rush: water pouring through a big tunnel (low roar, slowly rising), 4 s
{ const a = len(4), lo = svf(noise(a.length, 44), 220, 0.5, "low"), mid = svf(noise(a.length, 45), 900, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.6) * (t < 3.2 ? 1 : Math.max(0, 1 - (t - 3.2) / 0.8));
    a[i] = (0.7 * lo[i] + 0.25 * mid[i]) * env; }
  write("culvert-rush.wav", fades(a, 30, 300), -9); }
// fill-rumble: chamber filling, boiling surface + low rumble, 6 s
{ const a = len(6), lo = svf(noise(a.length, 46), 120, 0.5, "low"), hi = svf(noise(a.length, 47), 1600, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.8) * (t < 5 ? 1 : Math.max(0, 1 - (t - 5)));
    a[i] = (0.6 * lo[i] + 0.15 * hi[i]) * env; }
  blips(a, 40, 0.2, 5.6, 120, 380, 0.15, 48, 20); write("fill-rumble.wav", fades(a, 50, 300), -11); }
// outlet-gush: water bursting out of the culvert into the sea, 3 s
{ const a = len(3), n = svf(noise(a.length, 49), 1100, 0.4), lo = svf(noise(a.length, 50), 300, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.15) * Math.max(0, 1 - t / 3);
    a[i] = (0.45 * n[i] + 0.5 * lo[i]) * env; }
  blips(a, 30, 0.05, 2.6, 200, 700, 0.12, 51, 26); write("outlet-gush.wav", fades(a, 10, 300), -9); }
// motor-hum: electric locomotives (steady electric hum + gear whine), 3.5 s
{ const a = len(3.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.4) * (t < 2.8 ? 1 : Math.max(0, 1 - (t - 2.8) / 0.7));
    a[i] = env * (0.3 * Math.sin(2 * Math.PI * 120 * t) + 0.15 * Math.sin(2 * Math.PI * 240 * t) + 0.06 * Math.sin(2 * Math.PI * (620 + 40 * Math.sin(2 * t)) * t)); }
  add(a, svf(noise(a.length, 52), 400, 0.5), 0.08); write("motor-hum.wav", fades(a, 50, 300), -12); }
// water-lap: small waves against concrete, 4 s
{ const a = len(4), n = svf(noise(a.length, 53), 700, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.3 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.9 * t)) * Math.sin(Math.PI * Math.min(1, t / 4)); }
  blips(a, 14, 0.2, 3.6, 300, 800, 0.1, 54, 30); write("water-lap.wav", fades(a, 80, 400), -14); }
// deny-thud: the strong stinger for "never comes back"
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
