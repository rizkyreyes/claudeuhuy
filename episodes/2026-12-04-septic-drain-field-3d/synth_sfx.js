// Procedural septic drain-field foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from pipe-lining: deny-thud, water-rush, dust-crumble, sewer-drip, yard-air, set-ping. New: drip-plink, car-thud, mud-squelch, gurgle-rise.
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
// deny-thud: the stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
// water-rush: water/air through a closed pipe, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6021), 180, 0.35, "low"), mid = svf(noise(a.length, 6022), t => 620 + 90 * Math.sin(t * 2.3), 0.15);
  for (let i = 0; i < a.length; i++) a[i] = 0.9 * lo[i] + 0.35 * mid[i];
  write("water-rush.wav", fades(a, 250, 250), -11); }
// dust-crumble: grit and chips falling, 1.0 s
{ const a = len(1.0), h = svf(noise(a.length, 7031), 3500, 0.5), r = rng(7032);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.3 * h[i] * Math.exp(-t * 3); }
  for (let k = 0; k < 26; k++) modal(a, 0.6 * Math.abs(r()), 1500 + 2500 * Math.abs(r()), [[1, 1, 1], [2.3, 0.4, 2]], 0.08, 60);
  write("dust-crumble.wav", fades(a, 5, 200), -9); }
// set-ping: the resin hardening (bright glassy chime), 1.0 s
{ const a = len(1.0); modal(a, 0, 1320, [[1, 1, 1], [2.0, 0.4, 1.4], [3.0, 0.2, 2]], 0.6, 4); write("set-ping.wav", fades(a, 0, 200), -8); }
// sewer-drip: brick sewer ambience (low air + drips), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 8091), 220, 0.4, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.4 * lo[i];
  blips(a, 7, 0.1, 2.8, 900, 1500, 0.4, 8092, 30); write("sewer-drip.wav", fades(a, 250, 250), -15); }
// yard-air: outdoor ambience (soft wind + birds-free), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6011), t => 380 + 160 * Math.sin(t * 1.3), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.6 + 0.4 * Math.sin(Math.PI * t / 3)); }
  write("yard-air.wav", fades(a, 300, 300), -18); }
// drip-plink: single water drop into gravel/soil, 0.3 s
{ const a = len(0.3); blips(a, 1, 0.0, 0.01, 1100, 1300, 0.8, 9101, 40); add(a, svf(noise(2000, 9102), 2600, 0.5), 0.12); write("drip-plink.wav", fades(a, 0, 60), -10); }
// car-thud: a car dropping onto turf (low body + suspension creak + dirt), 1.0 s
{ const a = len(1.0); thump(a, 0, 42, 1, 6); thump(a, 0.12, 60, 0.4, 9); modal(a, 0.02, 260, METAL, 0.18, 14);
  add(a, svf(noise(a.length, 9111), 900, 0.5), 0.15); write("car-thud.wav", fades(a, 0, 200), -4); }
// mud-squelch: wet soil bubbling up, 1.2 s
{ const a = len(1.2), lo = svf(noise(a.length, 9121), 320, 0.35, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * lo[i] * Math.exp(-t * 1.5); }
  blips(a, 9, 0.0, 1.0, 180, 420, 0.45, 9122, 18); write("mud-squelch.wav", fades(a, 10, 250), -8); }
// gurgle-rise: water rising through the trench, 2.0 s
{ const a = len(2.0), lo = svf(noise(a.length, 9131), t => 160 + 220 * t, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * lo[i] * Math.min(1, t * 2); }
  blips(a, 14, 0.1, 1.9, 300, 700, 0.3, 9132, 22); write("gurgle-rise.wav", fades(a, 80, 300), -9); }
