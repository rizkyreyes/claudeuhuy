// Procedural roman-aqueduct foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, block-thud, canyon-wind (as valley-wind), water-rush. New: water-trickle, stone-rumble, dust-crumble, crust-creak, chisel-tap, pressure-hiss, splash.
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
// block-thud: heavy stone set down, 0.5 s
{ const a = len(0.5); thump(a, 0, 70, 1, 14); add(a, svf(noise(4000, 4061), 400, 0.6, "low"), 0.4); write("block-thud.wav", fades(a, 0, 100), -6); }
// valley-wind: open air over the valley, slow gusts, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6011), t => 380 + 160 * Math.sin(t * 1.3), 0.3), hs = svf(noise(a.length, 6012), 2200, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (lo[i] + 0.15 * hs[i]) * (0.6 + 0.4 * Math.sin(Math.PI * t / 3)); }
  write("valley-wind.wav", fades(a, 300, 300), -16); }
// water-rush: water pushed through a closed pipe (low roar + hollow resonance), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6021), 180, 0.35, "low"), mid = svf(noise(a.length, 6022), t => 620 + 90 * Math.sin(t * 2.3), 0.15);
  for (let i = 0; i < a.length; i++) a[i] = 0.9 * lo[i] + 0.35 * mid[i];
  write("water-rush.wav", fades(a, 250, 250), -11); }
// water-trickle: shallow water running in a stone channel (bright babble + small bubbles), 3 s (loops)
{ const a = len(3), n = svf(noise(a.length, 7011), t => 1800 + 500 * Math.sin(t * 3.1), 0.2), lo = svf(noise(a.length, 7012), 500, 0.3, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.35 * n[i] + 0.3 * lo[i];
  blips(a, 70, 0.05, 2.95, 600, 1800, 0.12, 7013, 40); write("water-trickle.wav", fades(a, 250, 250), -14); }
// stone-rumble: a tier of the bridge rising (grinding stone + low rumble), 1.2 s
{ const a = len(1.2), g = svf(noise(a.length, 7021), t => 260 + 200 * t, 0.25), lo = svf(noise(a.length, 7022), 90, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.5 * g[i] + 0.9 * lo[i]) * Math.sin(Math.PI * Math.min(1, t / 1.2)); }
  thump(a, 0.95, 55, 0.8, 9); write("stone-rumble.wav", fades(a, 30, 150), -5); }
// dust-crumble: grit and pebbles after a heavy landing / chips falling, 1.0 s
{ const a = len(1.0), h = svf(noise(a.length, 7031), 3500, 0.5), r = rng(7032);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.3 * h[i] * Math.exp(-t * 3); }
  for (let k = 0; k < 26; k++) modal(a, 0.6 * Math.abs(r()), 1500 + 2500 * Math.abs(r()), [[1, 1, 1], [2.3, 0.4, 2]], 0.08, 60);
  write("dust-crumble.wav", fades(a, 5, 200), -9); }
// crust-creak: limestone crust growing (slow mineral creak + tiny crackle), 0.8 s
{ const a = len(0.8), c = svf(noise(a.length, 7041), t => 700 + 900 * t, 0.08), r = rng(7042);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * c[i] * Math.sin(Math.PI * t / 0.8); }
  for (let k = 0; k < 12; k++) modal(a, 0.7 * Math.abs(r()), 3000 + 2000 * Math.abs(r()), [[1, 1, 1]], 0.05, 80);
  write("crust-creak.wav", fades(a, 20, 150), -10); }
// chisel-tap: iron on stone crust, 0.35 s
{ const a = len(0.35); modal(a, 0, 1900, [[1, 1, 1], [2.7, 0.5, 1.6], [4.9, 0.3, 2.3]], 0.6, 30); add(a, svf(noise(SR * 0.05, 7051), 4000, 0.5), 0.5);
  write("chisel-tap.wav", fades(a, 0, 80), -6); }
// pressure-hiss: water under pressure in a sealed pipe (narrow hiss + groan), 1.5 s
{ const a = len(1.5), h = svf(noise(a.length, 7061), 4200, 0.12), g = svf(noise(a.length, 7062), 160, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.4 * h[i] + 0.7 * g[i]) * Math.min(1, t * 6); }
  write("pressure-hiss.wav", fades(a, 10, 300), -9); }
// splash: water dropping into the round tank, 1.2 s
{ const a = len(1.2), n = svf(noise(a.length, 7071), 1600, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * n[i] * Math.exp(-t * 2.5); }
  blips(a, 30, 0.02, 1.0, 300, 1200, 0.2, 7072, 24); write("splash.wav", fades(a, 5, 250), -9); }
