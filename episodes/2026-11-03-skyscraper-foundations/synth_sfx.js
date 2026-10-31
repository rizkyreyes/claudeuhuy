// Procedural foundation foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Slab slide, heavy thud, soil squish, stone creak, auger drill, slurry slosh + plop, steel clank, concrete pour, ground rumble, deny thud.
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
// slab-slide: the front slab of ground dropping away (rising scrape, soft thud)
{ const a = len(0.9), s = svf(noise(a.length, 41), t => 300 + 700 * Math.min(1, t / 0.7), 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  thump(a, 0.72, 50, 0.6, 9); write("slab-slide.wav", fades(a, 20, 120), -6); }
// heavy-thud: a weight / the raft landing (deep body + dirt)
{ const a = len(0.6); thump(a, 0, 45, 1, 6); add(a, svf(noise(9000, 51), 400, 0.5, "low"), 0.5); write("heavy-thud.wav", fades(a, 0, 120), -4); }
// soil-squish: wet grains pressed together (low band noise, wobbling)
{ const a = len(0.9), n = svf(noise(a.length, 52), t => 260 + 200 * Math.sin(2 * Math.PI * 9 * t), 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.sin(Math.PI * t / 0.9); }
  write("soil-squish.wav", fades(a, 30, 150), -8); }
// stone-creak: masonry settling (slow resonant groan + grit)
{ const a = len(1.6), g = svf(noise(a.length, 53), t => 140 + 60 * t, 0.08), grit = svf(noise(a.length, 54), 2500, 0.6), r = rng(55);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.8 * g[i] + 0.15 * grit[i] * Math.max(0, r())) * Math.sin(Math.PI * t / 1.6); }
  write("stone-creak.wav", fades(a, 80, 300), -8); }
// auger-drill: diesel rig + grinding auger, 2.4 s
{ const a = len(2.4), grind = svf(noise(a.length, 56), 700, 0.5); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * 38 / SR;
    a[i] = 0.35 * Math.sin(ph) + 0.15 * Math.sin(3 * ph) + 0.5 * grind[i] * (0.7 + 0.3 * Math.sin(2 * Math.PI * 4.5 * t)); }
  write("auger-drill.wav", fades(a, 150, 500), -12); }
// slurry-slosh: thick liquid filling the hole (gurgles)
{ const a = len(1.8), r = rng(57);
  for (let k = 0; k < 16; k++) { const t0 = 0.05 + 1.6 * Math.abs(r()), f = 180 + 220 * Math.abs(r()), i0 = Math.round(t0 * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.15; i++) { const t = (i - i0) / SR; a[i] += 0.5 * Math.sin(2 * Math.PI * f * (1 + 0.8 * t) * t) * Math.exp(-t * 30); } }
  add(a, svf(noise(a.length, 58), 300, 0.5, "low"), 0.4); write("slurry-slosh.wav", fades(a, 50, 300), -9); }
// slurry-plop: one blob landing in the tank
{ const a = len(0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(2 * Math.PI * (220 + 300 * Math.exp(-t * 35)) * t) * Math.exp(-t * 18); }
  write("slurry-plop.wav", fades(a, 0, 60), -8); }
// steel-clank: rebar cage / pipe touching down (metal partials + knock)
{ const a = len(0.7); modal(a, 0, 420, METAL, 0.6, 9); modal(a, 0.04, 610, METAL, 0.3, 12); thump(a, 0, 90, 0.4, 25); write("steel-clank.wav", fades(a, 0, 120), -5); }
// concrete-pour: wet concrete rushing down a pipe, 4 s
{ const a = len(4), n = svf(noise(a.length, 59), 450, 0.4), r2 = svf(noise(a.length, 60), 90, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.6 * n[i] + 0.8 * r2[i]) * Math.min(1, t / 0.4) * (0.85 + 0.15 * Math.sin(2 * Math.PI * 3 * t)); }
  write("concrete-pour.wav", fades(a, 200, 600), -12); }
// ground-rumble: rock dropping away / the tower settling
{ const a = len(1.5), n = svf(noise(a.length, 61), 70, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.sin(Math.PI * t / 1.5); }
  thump(a, 0.05, 38, 0.4, 4); write("ground-rumble.wav", fades(a, 60, 300), -6); }
// deny-thud: failure stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
