// Procedural nuclear-plant foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from the water-tower set: stone slide (cutaway), deny thud, wind gust, water rush, pump hum (generator hum), birds
// new: pellet clink (ceramic), cap click, rod slide (control rods), rod rise (assembly rows), fission boom, boiling bubbles,
// steam hiss, turbine whine (spin-up), electric zap, condense drip.
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
// stone-slide: the near half of the containment sliding off (concrete scrape), 0.9 s
{ const a = len(0.9), s = svf(noise(a.length, 103), t => 300 + 400 * t, 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.9)); }
  thump(a, 0.0, 60, 0.4, 12); write("stone-slide.wav", fades(a, 10, 200), -7); }
// wind-gust: wind over the plant, 3 s
{ const a = len(3), n = svf(noise(a.length, 105), t => 500 + 350 * Math.sin(2 * Math.PI * 0.4 * t), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.33 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  write("wind-gust.wav", fades(a, 200, 500), -12); }
// deny-thud: the stinger ("melt", "stops it")
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
// water-rush: water running through a pipe (filtered noise with slow swirl), 3 s
{ const a = len(3), n = svf(noise(a.length, 301), t => 700 + 250 * Math.sin(2 * Math.PI * 0.8 * t), 0.3), lo = svf(noise(a.length, 302), 160, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.35 * n[i] + 0.35 * lo[i]) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  blips(a, 30, 0.2, 2.8, 300, 900, 0.05, 303); write("water-rush.wav", fades(a, 150, 400), -12); }
// pump-hum: electric motor hum with a spin-up, 4 s
{ const a = len(4), n = svf(noise(a.length, 304), 900, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR, sp = Math.min(1, t / 0.6);
    a[i] = Math.sin(Math.PI * Math.min(1, t / 4)) ** 0.3 * (0.35 * Math.sin(2 * Math.PI * 120 * sp * t) + 0.15 * Math.sin(2 * Math.PI * 240 * sp * t) + 0.08 * n[i]); }
  write("pump-hum.wav", fades(a, 60, 500), -11); }
// power-down: motor winding down + relay clack, 1.4 s
{ const a = len(1.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 120 * Math.max(0.15, 1 - t / 1.2); a[i] = 0.5 * Math.sin(2 * Math.PI * f * t) * Math.max(0, 1 - t / 1.3); }
  modal(a, 0, 900, [[1, 1, 1], [2.4, 0.5, 2]], 0.4, 50); thump(a, 0, 70, 0.4, 20); write("power-down.wav", fades(a, 0, 150), -7); }
// birds: morning chirps, 3 s
{ const a = len(3), r = rng(308);
  for (let k = 0; k < 12; k++) { const t0 = 2.7 * Math.abs(r()), f0 = 2600 + 900 * Math.abs(r()), i0 = Math.round(t0 * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.12; i++) { const t = (i - i0) / SR; a[i] += 0.2 * Math.sin(2 * Math.PI * (f0 + 2500 * t) * t) * Math.sin(Math.PI * t / 0.12); } }
  write("birds.wav", fades(a, 50, 300), -15); }
// pellet-clink: ceramic pellet landing on a pellet in the tube, 0.25 s
{ const a = len(0.25); modal(a, 0, 2100, [[1, 1, 1], [2.3, 0.5, 1.6], [3.9, 0.25, 2.4]], 0.4, 40); add(a, svf(noise(3000, 401), 3000, 0.5), 0.12);
  write("pellet-clink.wav", fades(a, 0, 40), -12); }
// cap-click: end cap seated and welded shut (click + short zip), 0.5 s
{ const a = len(0.5); modal(a, 0, 1500, METAL, 0.5, 30); const z = svf(noise(a.length, 402), 5000, 0.4);
  for (let i = Math.round(0.08 * SR); i < a.length; i++) { const t = i / SR; a[i] += 0.25 * z[i] * Math.max(0, 1 - (t - 0.08) / 0.4); }
  write("cap-click.wav", fades(a, 0, 60), -8); }
// rod-slide: control rods gliding in or out (metal-on-metal slide + latch), 0.7 s
{ const a = len(0.7), s = svf(noise(a.length, 403), t => 900 - 500 * t, 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.6)); }
  modal(a, 0.58, 620, METAL, 0.35, 18); write("rod-slide.wav", fades(a, 20, 80), -9); }
// rod-rise: a row of fuel rods sliding up into the assembly, 0.35 s
{ const a = len(0.35), s = svf(noise(a.length, 404), t => 1200 + 3000 * t, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.3 * s[i] * Math.sin(Math.PI * t / 0.35); }
  modal(a, 0.28, 1800, [[1, 1, 1], [2.7, 0.4, 2]], 0.15, 40); write("rod-rise.wav", fades(a, 5, 40), -14); }
// fission-boom: the nucleus split (bright crack + low boom + air), 1.4 s
{ const a = len(1.4); thump(a, 0, 55, 1.0, 4.5); add(a, svf(noise(SR * 0.3, 405), 3500, 0.3), 0.5);
  const air = svf(noise(a.length, 406), t => 1800 - 1200 * t, 0.4); for (let i = 0; i < a.length; i++) a[i] += 0.25 * air[i] * Math.exp(-i / SR * 2.5);
  write("fission-boom.wav", fades(a, 0, 300), -4); }
// boil-bubbles: water boiling in the steam generator, 3 s
{ const a = len(3), lo = svf(noise(a.length, 407), 400, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.2 * lo[i] * Math.sin(Math.PI * Math.min(1, t / 3)); }
  blips(a, 160, 0.05, 2.9, 250, 900, 0.07, 408, 40); write("boil-bubbles.wav", fades(a, 200, 500), -12); }
// steam-hiss: high-pressure steam rushing through the line, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 409), 3200, 0.5), lo = svf(noise(a.length, 410), 500, 0.6, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.45 * n[i] + 0.3 * lo[i]) * Math.min(1, t / 0.12) * (0.9 + 0.1 * Math.sin(2 * Math.PI * 6 * t)); }
  write("steam-hiss.wav", fades(a, 0, 600), -11); }
// turbine-whine: rotor spinning up (rising tone + harmonics + air), 4 s
{ const a = len(4), air = svf(noise(a.length, 411), 1500, 0.5); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 140 + 520 * Math.min(1, t / 2.2) ** 0.7; ph += 2 * Math.PI * f / SR;
    a[i] = Math.sin(Math.PI * Math.min(1, t / 4)) ** 0.4 * (0.3 * Math.sin(ph) + 0.12 * Math.sin(2 * ph) + 0.06 * Math.sin(3.01 * ph) + 0.12 * air[i]); }
  write("turbine-whine.wav", fades(a, 80, 500), -10); }
// electric-zap: power hitting the lines (crackle + 60 Hz buzz), 1.2 s
{ const a = len(1.2), r = rng(412);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.25 * Math.sign(Math.sin(2 * Math.PI * 60 * t)) * Math.exp(-t * 2.2) * 0.6; }
  for (let k = 0; k < 50; k++) { const i0 = Math.round(Math.abs(r()) * 0.5 * SR); for (let i = i0; i < i0 + 250 && i < a.length; i++) a[i] += 0.5 * r() * Math.exp(-(i - i0) / 60); }
  write("electric-zap.wav", fades(a, 0, 200), -8); }
// condense-drip: steam turning back into water (soft drips), 2 s
{ const a = len(2), lo = svf(noise(a.length, 413), 700, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.08 * lo[i] * Math.sin(Math.PI * t / 2); }
  blips(a, 14, 0.05, 1.8, 900, 1600, 0.25, 414, 30); write("condense-drip.wav", fades(a, 50, 300), -12); }
