// Procedural water-tower foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// stone slide (cutaway), tower rise, deny thud, wind gust (kept from the bridge set) + water rush, pump hum, pump start / power-down,
// glass clink (water discs), gauge tick, shower spray, night crickets, morning birds, splash spill, ladder clank, siren-free hydrant hiss.
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
// stone-slide: the near half of the anchorage sliding off (concrete scrape), 0.9 s
{ const a = len(0.9), s = svf(noise(a.length, 103), t => 300 + 400 * t, 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.9)); }
  thump(a, 0.0, 60, 0.4, 12); write("stone-slide.wav", fades(a, 10, 200), -7); }
// tower-rise: steel sections stacking up (rising rumble + 5 clanks), 1.6 s
{ const a = len(1.6), lo = svf(noise(a.length, 104), t => 80 + 60 * t, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * lo[i] * Math.sin(Math.PI * Math.min(1, t / 1.6)); }
  for (let k = 0; k < 5; k++) modal(a, 0.1 + k * 0.28, 140 + k * 18, METAL, 0.3, 10);
  write("tower-rise.wav", fades(a, 20, 200), -6); }
// wind-gust: high wind for the kite and the catwalk shots, 3 s
{ const a = len(3), n = svf(noise(a.length, 105), t => 500 + 350 * Math.sin(2 * Math.PI * 0.4 * t), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.33 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  write("wind-gust.wav", fades(a, 200, 500), -12); }
// deny-thud: the stinger ("nothing can slip", "still no road")
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
// glass-clink: a disc of water landing in the tube, 0.35 s
{ const a = len(0.35); modal(a, 0, 1400, [[1, 1, 1], [2.6, 0.4, 1.8], [4.1, 0.2, 2.5]], 0.4, 22); add(a, svf(noise(5000, 305), 2200, 0.5), 0.15);
  write("glass-clink.wav", fades(a, 0, 60), -11); }
// gauge-tick: needle clicking up, 0.08 s
{ const a = len(0.08); modal(a, 0, 2400, [[1, 1, 1]], 0.4, 120); write("gauge-tick.wav", fades(a, 0, 20), -12); }
// shower-spray: hiss of a running shower, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 306), 4200, 0.7);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.min(1, t / 0.15) * (0.85 + 0.15 * Math.sin(2 * Math.PI * 9 * t)); }
  write("shower-spray.wav", fades(a, 10, 400), -13); }
// crickets: night ambience, 5 s
{ const a = len(5), r = rng(307);
  for (let k = 0; k < 60; k++) { const t0 = 5 * Math.abs(r()), f = 4200 + 400 * r();
    for (let j = 0; j < 3; j++) { const i0 = Math.round((t0 + j * 0.035) * SR);
      for (let i = i0; i < a.length && i < i0 + SR * 0.025; i++) { const t = (i - i0) / SR; a[i] += 0.12 * Math.sin(2 * Math.PI * f * t) * Math.sin(Math.PI * t / 0.025); } } }
  write("crickets.wav", fades(a, 300, 600), -16); }
// birds: morning chirps, 3 s
{ const a = len(3), r = rng(308);
  for (let k = 0; k < 12; k++) { const t0 = 2.7 * Math.abs(r()), f0 = 2600 + 900 * Math.abs(r()), i0 = Math.round(t0 * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.12; i++) { const t = (i - i0) / SR; a[i] += 0.2 * Math.sin(2 * Math.PI * (f0 + 2500 * t) * t) * Math.sin(Math.PI * t / 0.12); } }
  write("birds.wav", fades(a, 50, 300), -15); }
// splash-spill: overflow water falling onto the drain, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 309), 1800, 0.5), lo = svf(noise(a.length, 310), 300, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.35 * n[i] + 0.3 * lo[i]) * Math.min(1, t / 0.08); }
  blips(a, 40, 0.0, 2.4, 500, 1400, 0.06, 311); thump(a, 0, 90, 0.3, 14); write("splash-spill.wav", fades(a, 0, 500), -10); }
// ladder-clank: hand on a steel rung, 0.4 s
{ const a = len(0.4); modal(a, 0, 520, METAL, 0.5, 16); thump(a, 0, 110, 0.3, 25); write("ladder-clank.wav", fades(a, 0, 80), -9); }
// hydrant-hiss: pressurised water burst, 1.5 s
{ const a = len(1.5), n = svf(noise(a.length, 312), 2500, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.55 * n[i] * Math.min(1, t / 0.05) * Math.max(0, 1 - t / 1.5); }
  write("hydrant-hiss.wav", fades(a, 0, 200), -10); }
