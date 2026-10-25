// Procedural septic / yard foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Water uses filtered noise with bubbly resonances; concrete and stone use low thumps; the truck and vac pump are modulated tones + noise.
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
const STEEL = [[1, 1, 1], [2.32, 0.6, 1.4], [4.25, 0.35, 2.0], [6.63, 0.2, 2.8]];
const add = (a, b, g = 1, at = 0) => { const i0 = Math.round(at * SR); for (let i = 0; i < b.length && i0 + i < a.length; i++) a[i0 + i] += g * b[i]; return a; };
function bubble(a, t0, f0, amp, dur = 0.06) {    // rising-pitch sine blip = a single bubble / drop
  const i0 = Math.round(t0 * SR), n = Math.round(dur * SR); let ph = 0;
  for (let i = 0; i < n && i0 + i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * f0 * (1 + 2.2 * t / dur) / SR; a[i0 + i] += amp * Math.sin(ph) * Math.exp(-t * 4 / dur) * Math.min(1, t * 2000); }
}

// pipe-trickle: 6 s of water running in a pipe (bandpassed noise + sparse bubbles)
{ const a = len(6), n = svf(noise(a.length, 61), t => 900 + 250 * Math.sin(t * 3.1), 0.5), r = rng(62);
  for (let i = 0; i < a.length; i++) a[i] = 0.35 * n[i];
  for (let k = 0; k < 70; k++) bubble(a, 5.9 * (k / 70) + 0.04 * r(), 500 + 500 * Math.abs(r()), 0.25, 0.04 + 0.03 * Math.abs(r()));
  write("pipe-trickle.wav", fades(a, 500, 600), -14); }
// drain-flush: 1.6 s rush of water down the house pipe
{ const a = len(1.6), n = svf(noise(a.length, 63), t => 1600 - 900 * Math.min(1, t / 1.2), 0.45), lo = svf(noise(a.length, 64), 220, 0.7, "low"), r = rng(65);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.6 * n[i] + 0.4 * lo[i]) * Math.min(1, t / 0.08) * Math.exp(-t * 1.2); }
  for (let k = 0; k < 25; k++) bubble(a, 0.1 + 1.2 * (k / 25), 350 + 400 * Math.abs(r()), 0.2);
  write("drain-flush.wav", fades(a, 10, 300), -9); }
// slab-drop: the concrete front wall dropping away (scrape + heavy thud)
{ const a = len(0.9), s = svf(noise(a.length, 66), 700, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * Math.exp(-t * 5); }
  thump(a, 0.12, 52, 1, 7); write("slab-drop.wav", fades(a, 5, 150), -5); }
// solid-plop / fat-bubble: one settling solid, one rising grease bubble
{ const a = len(0.25); bubble(a, 0.0, 180, 1, 0.09); add(a, svf(noise(3000, 67), 400, 0.6, "low"), 0.3); write("solid-plop.wav", fades(a, 0, 60), -10); }
{ const a = len(0.3); bubble(a, 0.0, 420, 1, 0.07); bubble(a, 0.08, 640, 0.6, 0.05); write("fat-bubble.wav", fades(a, 0, 60), -11); }
// bacteria-fizz: 2.5 s soft fizz (tiny bubbles)
{ const a = len(2.5), r = rng(68), h = svf(noise(a.length, 69), 5000, 0.7);
  for (let i = 0; i < a.length; i++) a[i] = 0.08 * h[i];
  for (let k = 0; k < 160; k++) bubble(a, 2.4 * Math.abs(r()), 1500 + 1500 * Math.abs(r()), 0.12, 0.015);
  write("bacteria-fizz.wav", fades(a, 400, 600), -15); }
// gallon-glug: a big slug of water (low glug pair)
{ const a = len(0.9); bubble(a, 0.0, 140, 1, 0.16); bubble(a, 0.18, 190, 0.8, 0.14); bubble(a, 0.36, 160, 0.5, 0.12);
  add(a, svf(noise(a.length, 70), 500, 0.7), 0.15); write("gallon-glug.wav", fades(a, 0, 200), -8); }
// earth-lift: soil lid lifting (low rumble swell + crumble)
{ const a = len(1.0), lo = svf(noise(a.length, 71), 160, 0.7, "low"), r = rng(72);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * Math.sin(Math.PI * Math.min(1, t / 1.0)); }
  for (let k = 0; k < 20; k++) modal(a, 0.1 + 0.8 * Math.abs(r()), 700 + 500 * Math.abs(r()), [[1, 1, 1], [2.7, 0.4, 1.8]], 0.08, 90);
  write("earth-lift.wav", fades(a, 30, 200), -8); }
// drip: one drop into gravel
{ const a = len(0.2); bubble(a, 0.0, 900, 1, 0.03); add(a, svf(noise(1500, 73), 3000, 0.6), 0.15); write("drip.wav", fades(a, 0, 40), -12); }
// truck-arrive: 2.6 s diesel truck rolling in and braking (engine harmonics + air brake hiss)
{ const a = len(2.6), hs = svf(noise(a.length, 74), 4500, 0.7); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 38 + 10 * Math.exp(-Math.pow(t - 1.0, 2) * 2), g = Math.min(1, t / 0.6);
    ph += 2 * Math.PI * f / SR; a[i] = g * (0.5 * Math.sin(ph) + 0.25 * Math.sin(2 * ph) + 0.15 * Math.sign(Math.sin(3 * ph)) * 0.4);
    if (t > 1.9) a[i] += 0.3 * hs[i] * Math.exp(-(t - 1.9) * 4); }
  write("truck-arrive.wav", fades(a, 300, 300), -9); }
// vac-pump: 1.6 s vacuum pump sucking (rising whine + gurgle)
{ const a = len(1.6), gur = svf(noise(a.length, 75), t => 300 + 200 * Math.sin(2 * Math.PI * 6 * t), 0.35); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (180 + 160 * Math.min(1, t / 0.8)) / SR;
    a[i] = 0.25 * Math.sin(ph) * Math.min(1, t / 0.15) + 0.5 * gur[i]; }
  write("vac-pump.wav", fades(a, 50, 400), -9); }
// stone-lid: heavy stone lid grinding open
{ const a = len(1.1), s = svf(noise(a.length, 76), t => 400 + 300 * Math.min(1, t / 0.8), 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * s[i] * Math.sin(Math.PI * Math.min(1, t / 1.0)); }
  thump(a, 0.0, 60, 0.6, 9); write("stone-lid.wav", fades(a, 5, 200), -7); }
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 16), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
