// Procedural lightning-rod foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny thud, wind; new: thunder-crack, thunder-rumble, zap, sizzle, fire-crackle, rain, rod-clank, drive-hit, hum.
// new: pile-blow (diesel hammer stroke), stake-tap, metal-crunch, weight-thud, winch, steel-slide, air-squeeze, fuel-spray, ignite, crawler.
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
// wind-gust: soft outdoor air, 3 s
{ const a = len(3), n = svf(noise(a.length, 105), t => 500 + 350 * Math.sin(2 * Math.PI * 0.4 * t), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.33 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  write("wind-gust.wav", fades(a, 200, 500), -14); }
// thunder-crack: a close strike (sharp white crack, then a ripping tail), 1.5 s
{ const a = len(1.5), n = noise(a.length, 701), hi = svf(n, 3000, 0.4, "high"), lo = svf(noise(a.length, 702), 120, 0.5, "low"), r = rng(703);
  for (let i = 0; i < a.length; i++) { const t = i / SR;
    a[i] += hi[i] * Math.exp(-t * 18) * 1.2 + lo[i] * 2.5 * Math.min(1, t * 80) * Math.exp(-t * 2.5) + (r() > 0.997 ? r() * 0.6 * Math.exp(-t * 4) : 0); }
  thump(a, 0.0, 45, 0.8, 4); write("thunder-crack.wav", fades(a, 0, 300), -2); }
// thunder-rumble: rolling low rumble, 4 s
{ const a = len(4), lo = svf(noise(a.length, 711), t => 60 + 40 * Math.sin(t * 2.1), 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * Math.min(1, t * 3) * Math.exp(-t * 0.7) * (0.7 + 0.3 * Math.sin(2 * Math.PI * 1.3 * t) ** 2); }
  write("thunder-rumble.wav", fades(a, 50, 800), -6); }
// zap: electric arc (buzzy 120 Hz harmonics + crackle), 0.6 s
{ const a = len(0.6), r = rng(721);
  for (let i = 0; i < a.length; i++) { const t = i / SR; let v = 0;
    for (let h = 1; h < 14; h++) v += Math.sin(2 * Math.PI * 120 * h * t + h) / h;
    a[i] = (0.5 * Math.sign(v) * Math.abs(v) ** 0.5 + (r() > 0.99 ? r() : 0)) * Math.exp(-t * 5); }
  write("zap.wav", fades(a, 5, 120), -6); }
// sizzle: crackling hiss, 1.5 s
{ const a = len(1.5), n = svf(noise(a.length, 731), 4500, 0.5, "high"), r = rng(732);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * 0.4 * Math.exp(-t * 1.5) + (r() > 0.996 ? r() * 0.7 : 0) * Math.exp(-t * 2); }
  write("sizzle.wav", fades(a, 20, 300), -10); }
// fire-crackle: low roar + pops, 3 s
{ const a = len(3), lo = svf(noise(a.length, 741), 300, 0.5, "low"), r = rng(742);
  for (let i = 0; i < a.length; i++) a[i] = lo[i] * 0.6;
  blips(a, 40, 0, 2.9, 1500, 4000, 0.4, 743, 120); write("fire-crackle.wav", fades(a, 300, 400), -10); }
// rain: steady patter, 3 s
{ const a = len(3), n = svf(noise(a.length, 751), 2500, 0.3), r = rng(752);
  for (let i = 0; i < a.length; i++) a[i] = n[i] * 0.5 + (r() > 0.995 ? r() * 0.25 : 0);
  write("rain.wav", fades(a, 300, 300), -14); }
// rod-clank: small metal part set down, 0.7 s
{ const a = len(0.7); modal(a, 0, 1400, METAL, 0.6, 9); modal(a, 0.05, 2100, METAL, 0.2, 14); write("rod-clank.wav", fades(a, 0, 120), -6); }
// drive-hit: sledge on a ground rod (thud + ring), 0.6 s
{ const a = len(0.6); thump(a, 0, 70, 0.9, 14); modal(a, 0, 900, METAL, 0.35, 10); write("drive-hit.wav", fades(a, 0, 100), -4); }
// hum: electrical hum swell, 1.5 s
{ const a = len(1.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (Math.sin(2 * Math.PI * 120 * t) + 0.4 * Math.sin(2 * Math.PI * 240 * t) + 0.2 * Math.sin(2 * Math.PI * 360 * t)) * Math.sin(Math.PI * t / 1.5); }
  write("hum.wav", fades(a, 50, 200), -12); }
