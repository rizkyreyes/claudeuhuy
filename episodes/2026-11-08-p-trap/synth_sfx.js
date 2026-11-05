// Procedural P-trap foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Pipe slide, faucet run, drain gurgle, water trickle, gas bubble, siphon slurp, air draw, ring tink, plop, nut creak, pipe clunk, deny thud.
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
// pipe-slide: the PVC front halves sliding off (hollow plastic scrape + knock)
{ const a = len(0.9), s = svf(noise(a.length, 41), t => 500 + 1200 * Math.min(1, t / 0.7), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.45 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  thump(a, 0.7, 210, 0.35, 30); write("pipe-slide.wav", fades(a, 20, 120), -7); }
// faucet-run: tap water falling into a basin, 4 s
{ const a = len(4), n = svf(noise(a.length, 51), 2600, 0.5), lo = svf(noise(a.length, 52), 500, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.12) * (t < 3.3 ? 1 : Math.max(0, 1 - (t - 3.3) / 0.7));
    a[i] = (0.5 * n[i] + 0.35 * lo[i]) * env; }
  blips(a, 40, 0.1, 3.6, 700, 1600, 0.06, 53, 45); write("faucet-run.wav", fades(a, 10, 300), -12); }
// drain-gurgle: water going down a drain, glugs, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 54), 700, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.35 * n[i] * Math.sin(Math.PI * Math.min(1, t / 2.5)); }
  blips(a, 26, 0.05, 2.3, 160, 420, 0.35, 55, 22); write("drain-gurgle.wav", fades(a, 30, 300), -9); }
// water-trickle: light flow through the trap, 2 s
{ const a = len(2), n = svf(noise(a.length, 56), 1900, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.3 * n[i] * Math.sin(Math.PI * Math.min(1, t / 2)); }
  blips(a, 30, 0.05, 1.9, 900, 2200, 0.08, 57, 60); write("water-trickle.wav", fades(a, 30, 300), -13); }
// gas-bubble: slow low bubbling rising up the stack, 3 s
{ const a = len(3), lo = svf(noise(a.length, 58), 120, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * lo[i] * Math.sin(Math.PI * Math.min(1, t / 3)); }
  blips(a, 18, 0.1, 2.8, 90, 220, 0.45, 59, 14); write("gas-bubble.wav", fades(a, 80, 400), -10); }
// siphon-slurp: the seal pulled out (long sucking gurgle)
{ const a = len(1.6), n = svf(noise(a.length, 60), t => 300 + 900 * Math.min(1, t / 1.4), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.min(1, t / 0.1) * Math.exp(-Math.max(0, t - 1.0) * 5); }
  blips(a, 16, 0.0, 1.3, 120, 360, 0.4, 61, 18); write("siphon-slurp.wav", fades(a, 10, 200), -7); }
// air-draw: air pulled down the vent (soft rising breath)
{ const a = len(2), n = svf(noise(a.length, 62), t => 400 + 800 * t, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * n[i] * Math.sin(Math.PI * Math.min(1, t / 2)); }
  write("air-draw.wav", fades(a, 60, 300), -13); }
// ring-tink: a metal ring hitting plastic pipe walls on the way down
{ const a = len(1.4), r = rng(63);
  for (let k = 0; k < 5; k++) modal(a, 0.05 + 0.22 * k + 0.05 * r(), 3100 + 400 * r(), METAL, 0.5 - 0.07 * k, 35);
  write("ring-tink.wav", fades(a, 0, 200), -8); }
// plop: something sinking into water
{ const a = len(0.5); blips(a, 1, 0, 0.001, 380, 380, 0.9, 64, 14); thump(a, 0, 120, 0.3, 30);
  add(a, svf(noise(a.length, 65), 1500, 0.5), 0.05); write("plop.wav", fades(a, 0, 120), -7); }
// nut-creak: plastic slip nut twisted loose
{ const a = len(0.8), r = rng(66);
  for (let k = 0; k < 14; k++) { const i0 = Math.round((0.05 + 0.045 * k) * SR), f = 700 + 300 * Math.abs(r());
    for (let i = 0; i < SR * 0.04; i++) a[i0 + i] += 0.5 * Math.sin(2 * Math.PI * f * i / SR) * Math.exp(-i / (SR * 0.008)); }
  write("nut-creak.wav", fades(a, 0, 120), -8); }
// pipe-clunk: the J-bend dropping free (hollow plastic thud)
{ const a = len(0.7); thump(a, 0, 150, 0.9, 18); modal(a, 0, 520, [[1, 1, 1], [2.3, 0.4, 1.8], [4.1, 0.2, 2.6]], 0.35, 30);
  write("pipe-clunk.wav", fades(a, 0, 150), -5); }
// deny-thud: failure stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
