// Procedural dam-build foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Blast boom, rock rumble, truck dump, splash, water rush, trickle, dig scoop, drill whirr, grout pump, heat hiss, concrete crack, block clunk, deny thud.
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
// porcelain-slide: the front half sliding off (ceramic scrape, light knock)
{ const a = len(0.9), s = svf(noise(a.length, 41), t => 900 + 1500 * Math.min(1, t / 0.7), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.45 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  modal(a, 0.7, 1300, [[1, 1, 1], [2.3, 0.4, 1.8]], 0.25, 30); write("porcelain-slide.wav", fades(a, 20, 120), -7); }
// blast-boom: tunnel blast in rock (low thump + crackle + debris)
{ const a = len(1.6); thump(a, 0, 42, 1, 4.5); add(a, svf(noise(a.length, 61), 180, 0.5, "low"), 0.8);
  const r = rng(62); for (let k = 0; k < 30; k++) modal(a, 0.05 + 1.1 * Math.abs(r()) ** 2, 700 + 1600 * Math.abs(r()), [[1, 1, 1], [2.2, 0.4, 1.8]], 0.06, 60);
  write("blast-boom.wav", fades(a, 0, 300), -3); }
// rock-rumble: a cut slab of canyon dropping away (long low rumble)
{ const a = len(1.8), lo = svf(noise(a.length, 63), t => 140 - 60 * Math.min(1, t / 1.6), 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * Math.min(1, t / 0.15) * Math.max(0, 1 - t / 1.8); }
  thump(a, 0.75, 38, 0.6, 5); write("rock-rumble.wav", fades(a, 10, 300), -4); }
// truck-dump: diesel idle + gravel sliding off a tipped bed, 3 s
{ const a = len(3.0), g = svf(noise(a.length, 64), 1200, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.35 * Math.sin(2 * Math.PI * 38 * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 9 * t)) + 0.45 * g[i] * Math.min(1, Math.max(0, (t - 0.6) / 0.6)); }
  const r = rng(65); for (let k = 0; k < 22; k++) thump(a, 0.8 + 2.0 * Math.abs(r()), 70 + 60 * Math.abs(r()), 0.18, 22);
  write("truck-dump.wav", fades(a, 80, 400), -8); }
// splash: a boulder hitting the river
{ const a = len(0.7), n = svf(noise(a.length, 66), 1400, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * n[i] * Math.exp(-t * 7); }
  thump(a, 0, 95, 0.5, 18); blips(a, 8, 0.05, 0.5, 400, 1000, 0.12, 67, 35); write("splash.wav", fades(a, 0, 120), -7); }
// water-rush: the river pouring into the tunnel, 4 s
{ const a = len(4), n = svf(noise(a.length, 46), 800, 0.35), lo = svf(noise(a.length, 47), 160, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.4) * (t < 3 ? 1 : Math.max(0, 1 - (t - 3)));
    a[i] = (0.5 * n[i] + 0.7 * lo[i]) * env * (0.85 + 0.15 * Math.sin(2 * Math.PI * 4 * t)); }
  write("water-rush.wav", fades(a, 10, 300), -9); }
// trickle: the riverbed draining
{ const a = len(2.5); blips(a, 60, 0.0, 2.4, 500, 1300, 0.2, 56, 45); add(a, svf(noise(a.length, 57), 2000, 0.5), 0.12); write("trickle.wav", fades(a, 100, 400), -11); }
// dig-scoop: an excavator bucket biting sediment
{ const a = len(0.6), n = svf(noise(a.length, 68), 500, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * n[i] * Math.sin(Math.PI * Math.min(1, t / 0.5)); }
  modal(a, 0.02, 900, METAL, 0.2, 40); write("dig-scoop.wav", fades(a, 10, 120), -7); }
// drill-whirr: rock drill boring down, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 69), 2400, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.35 * Math.sin(2 * Math.PI * 110 * t) * (0.5 + 0.5 * Math.sin(2 * Math.PI * 28 * t)) + 0.3 * n[i]) * Math.min(1, t / 0.2); }
  write("drill-whirr.wav", fades(a, 30, 300), -10); }
// grout-pump: piston pump pushing liquid cement (rhythmic slosh), 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 70), 260, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.4 + 0.6 * Math.max(0, Math.sin(2 * Math.PI * 2.4 * t))); }
  for (let k = 0; k < 6; k++) thump(a, 0.1 + k / 2.4, 70, 0.3, 20); write("grout-pump.wav", fades(a, 40, 300), -9); }
// heat-hiss: curing concrete giving off heat (airy hiss + low warmth), 3 s
{ const a = len(3), n = svf(noise(a.length, 71), 3000, 0.6), lo = svf(noise(a.length, 72), 90, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.35 * n[i] + 0.4 * lo[i]) * Math.sin(Math.PI * t / 3); }
  write("heat-hiss.wav", fades(a, 60, 400), -12); }
// concrete-crack: a dam cracking (sharp snap + splintering)
{ const a = len(1.2); thump(a, 0, 60, 0.8, 9); modal(a, 0, 1800, [[1, 1, 1], [2.6, 0.6, 1.5], [4.9, 0.3, 2.2]], 0.5, 45);
  const r = rng(73); for (let k = 0; k < 16; k++) modal(a, 0.04 + 0.7 * Math.abs(r()), 1500 + 2500 * Math.abs(r()), METAL, 0.08, 70);
  write("concrete-crack.wav", fades(a, 0, 200), -4); }
// block-clunk: a concrete block landing in place
{ const a = len(0.5); thump(a, 0, 70, 0.9, 14); add(a, svf(noise(6000, 74), 600, 0.5), 0.25); write("block-clunk.wav", fades(a, 0, 100), -7); }
// deny-thud: failure stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
