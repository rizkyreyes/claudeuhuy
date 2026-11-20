// Procedural hydro-dam foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, steel-clunk, block-thud, elec-hum, gen-whir, line-buzz. New: canyon-wind, water-rush, water-roar, gate-clack, hammer-bang,
// pipe-burst, spray-hiss, elevator-hum.
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
// steel-clunk: beam / strut seated, 0.7 s
// elec-hum: 60 Hz transformer hum with harmonics, 3 s (loops)
{ const a = len(3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * Math.sin(2 * Math.PI * 120 * t) + 0.3 * Math.sin(2 * Math.PI * 240 * t) + 0.15 * Math.sin(2 * Math.PI * 360 * t) + 0.08 * Math.sin(2 * Math.PI * 480 * t); }
  write("elec-hum.wav", fades(a, 200, 200), -10); }
// gen-whir: big rotor spinning (rising whine + low rumble), 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 4031), 120, 0.5, "low"); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 180 + 60 * Math.min(1, t / 1.2); ph += 2 * Math.PI * f / SR; a[i] = 0.35 * Math.sin(ph) + 0.15 * Math.sin(3 * ph) + 0.8 * lo[i]; }
  write("gen-whir.wav", fades(a, 300, 400), -9); }
// line-buzz: high-voltage line corona crackle-buzz, 3 s (loops)
{ const a = len(3), n = svf(noise(a.length, 4071), 6000, 0.6, "high"), r = rng(4072);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.35 * n[i] * (0.6 + 0.4 * Math.sin(2 * Math.PI * 120 * t)) + 0.2 * Math.sin(2 * Math.PI * 120 * t) + (Math.abs(r()) > 0.999 ? 0.5 * r() : 0); }
  write("line-buzz.wav", fades(a, 200, 200), -12); }
// steel-clunk: gate ring seated / hatch, 0.7 s
{ const a = len(0.7); modal(a, 0, 260, METAL, 0.6, 10); thump(a, 0, 65, 0.7, 12); write("steel-clunk.wav", fades(a, 0, 120), -6); }
// block-thud: heavy hit, 0.5 s
{ const a = len(0.5); thump(a, 0, 70, 1, 14); add(a, svf(noise(4000, 4061), 400, 0.6, "low"), 0.4); write("block-thud.wav", fades(a, 0, 100), -6); }
// canyon-wind: open desert air, slow gusts, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6011), t => 380 + 160 * Math.sin(t * 1.3), 0.3), hs = svf(noise(a.length, 6012), 2200, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (lo[i] + 0.15 * hs[i]) * (0.6 + 0.4 * Math.sin(Math.PI * t / 3)); }
  write("canyon-wind.wav", fades(a, 300, 300), -16); }
// water-rush: fast water inside a big steel pipe (low roar + hollow resonance), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6021), 180, 0.35, "low"), mid = svf(noise(a.length, 6022), t => 620 + 90 * Math.sin(t * 2.3), 0.15);
  for (let i = 0; i < a.length; i++) a[i] = 0.9 * lo[i] + 0.35 * mid[i];
  write("water-rush.wav", fades(a, 250, 250), -11); }
// water-roar: water churning out into the river (broadband + bubbles), 3 s (loops)
{ const a = len(3), n = svf(noise(a.length, 6031), 1400, 0.25), lo = svf(noise(a.length, 6032), 140, 0.4, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.5 * n[i] + 0.8 * lo[i];
  blips(a, 40, 0.1, 2.9, 180, 700, 0.18, 6033, 26); write("water-roar.wav", fades(a, 250, 300), -10); }
// gate-clack: the wicket-gate ring turning (servo groan + 20 small clacks), 0.9 s
{ const a = len(0.9), r = rng(6041), g = svf(noise(a.length, 6042), t => 300 + 500 * t, 0.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.25 * g[i] * Math.sin(Math.PI * Math.min(1, t / 0.9)); }
  for (let k = 0; k < 20; k++) modal(a, 0.05 + 0.03 * k + 0.004 * r(), 1300 + 200 * r(), METAL, 0.12, 35);
  write("gate-clack.wav", fades(a, 10, 150), -7); }
// hammer-bang: water hammer, a heavy slam + the steel pipe ringing, 1.6 s
{ const a = len(1.6); thump(a, 0, 42, 1, 5); modal(a, 0, 95, METAL, 0.8, 2.6); modal(a, 0.02, 210, METAL, 0.4, 4);
  add(a, svf(noise(SR * 0.4, 6051), 250, 0.6, "low"), 0.5); write("hammer-bang.wav", fades(a, 0, 300), -3); }
// pipe-burst: steel tearing + water blast, 2.2 s
{ const a = len(2.2), n = svf(noise(a.length, 6061), t => 2800 - 900 * t, 0.3), lo = svf(noise(a.length, 6062), 160, 0.5, "low"), r = rng(6063);
  thump(a, 0, 50, 1, 6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += (0.7 * n[i] + 0.9 * lo[i]) * Math.min(1, t * 20) * Math.exp(-t * 1.1); }
  for (let k = 0; k < 10; k++) modal(a, 0.02 + 0.5 * Math.abs(r()), 500 + 900 * Math.abs(r()), METAL, 0.25, 9);
  write("pipe-burst.wav", fades(a, 0, 400), -3); }
// spray-hiss: water spraying out (high hiss), 1.8 s
{ const a = len(1.8), h = svf(noise(a.length, 6071), 5200, 0.4, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.exp(-t * 1.2); }
  write("spray-hiss.wav", fades(a, 20, 300), -10); }
// elevator-hum: lift motor + car sliding down the shaft, 3 s
{ const a = len(3), lo = svf(noise(a.length, 6081), 220, 0.3, "low"); let ph = 0;
  for (let i = 0; i < a.length; i++) { ph += 2 * Math.PI * 118 / SR; a[i] = 0.7 * lo[i] + 0.12 * Math.sin(ph) + 0.05 * Math.sin(ph * 2.01); }
  write("elevator-hum.wav", fades(a, 300, 600), -14); }
