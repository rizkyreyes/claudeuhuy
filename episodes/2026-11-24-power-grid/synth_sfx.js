// Procedural power-grid foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, wind-bed, wind-gust, steel-clunk, heat-sizzle. New: elec-hum, elec-zap, spark-crackle, gen-whir, oil-pour, coil-tick, drywall-crumble, block-thud, line-buzz, street-amb, breaker-clack.
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
// wind-bed: open prairie room tone, 3 s
{ const a = len(3), lo = svf(noise(a.length, 1011), t => 200 + 60 * Math.sin(t * 1.1), 0.4, "low");
  for (let i = 0; i < a.length; i++) a[i] = lo[i]; write("wind-bed.wav", fades(a, 300, 300), -16); }
// wind-gust: swelling band-passed whoosh, 1.8 s
{ const a = len(1.8), n = svf(noise(a.length, 1101), t => 300 + 900 * Math.sin(Math.PI * t / 1.8), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.sin(Math.PI * t / 1.8); } write("wind-gust.wav", fades(a, 50, 200), -6); }
// steel-clunk: yaw brake / gear engage, 0.7 s
{ const a = len(0.7); modal(a, 0, 260, METAL, 0.6, 10); thump(a, 0, 65, 0.7, 12); write("steel-clunk.wav", fades(a, 0, 120), -6); }
// heat-sizzle: crackling hiss (energy turned into heat), 2 s
{ const a = len(2), n = svf(noise(a.length, 3031), 5000, 0.6, "high"), r = rng(3032);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.4 * n[i] + (Math.abs(r()) > 0.997 ? r() * 0.8 : 0)) * Math.min(1, t * 3) * (1 - t / 2.2); }
  write("heat-sizzle.wav", fades(a, 50, 300), -10); }
// elec-hum: 60 Hz transformer hum with harmonics, 3 s (loops)
{ const a = len(3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * Math.sin(2 * Math.PI * 120 * t) + 0.3 * Math.sin(2 * Math.PI * 240 * t) + 0.15 * Math.sin(2 * Math.PI * 360 * t) + 0.08 * Math.sin(2 * Math.PI * 480 * t); }
  write("elec-hum.wav", fades(a, 200, 200), -10); }
// elec-zap: sharp arc crack + buzzy tail, 0.6 s
{ const a = len(0.6), n = svf(noise(a.length, 4011), 3500, 0.4), r = rng(4012);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 9) * (0.6 + 0.4 * Math.sign(Math.sin(2 * Math.PI * 120 * t))) + (Math.abs(r()) > 0.995 ? r() : 0) * Math.exp(-t * 4); }
  thump(a, 0, 80, 0.5, 25); write("elec-zap.wav", fades(a, 0, 120), -4); }
// spark-crackle: random crackles, 1.5 s
{ const a = len(1.5), r = rng(4021);
  for (let i = 0; i < a.length; i++) { const t = i / SR; if (Math.abs(r()) > 0.9985) { const amp = 0.4 + 0.6 * Math.abs(r()); for (let k = 0; k < 300 && i + k < a.length; k++) a[i + k] += amp * r() * Math.exp(-k / 60); } }
  write("spark-crackle.wav", fades(svf(a, 2500, 0.5, "high"), 20, 200), -7); }
// gen-whir: big rotor spinning (rising whine + low rumble), 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 4031), 120, 0.5, "low"); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 180 + 60 * Math.min(1, t / 1.2); ph += 2 * Math.PI * f / SR; a[i] = 0.35 * Math.sin(ph) + 0.15 * Math.sin(3 * ph) + 0.8 * lo[i]; }
  write("gen-whir.wav", fades(a, 300, 400), -9); }
// oil-pour: thick liquid filling a tank, 3 s
{ const a = len(3), n = svf(noise(a.length, 4041), t => 500 - 120 * t, 0.25), lo = svf(noise(a.length, 4042), 150, 0.5, "low"), r = rng(4043);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.6 * n[i] + 0.6 * lo[i]) * Math.min(1, t * 4) * (1 - t / 3.3); }
  for (let k = 0; k < 18; k++) { const t0 = 0.1 + 2.7 * Math.abs(r()), i0 = Math.round(t0 * SR); for (let j = 0; j < 2400 && i0 + j < a.length; j++) a[i0 + j] += 0.3 * Math.sin(2 * Math.PI * (300 + 500 * j / 2400) * j / SR) * Math.exp(-j / 700); }
  write("oil-pour.wav", fades(a, 100, 400), -9); }
// coil-tick: small bright tick (one coil turn lights up), 0.12 s
{ const a = len(0.12); modal(a, 0, 2200, [[1, 1, 1], [2.7, 0.3, 2]], 0.6, 60); write("coil-tick.wav", fades(a, 0, 30), -9); }
// drywall-crumble: gypsum chunks breaking + falling, 1.2 s
{ const a = len(1.2), n = svf(noise(a.length, 4051), 1800, 0.5), r = rng(4052);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 3) * (Math.abs(r()) > 0.6 ? 1 : 0.3); }
  for (const t0 of [0.35, 0.5, 0.62, 0.8, 0.95]) thump(a, t0, 140, 0.25, 30);
  write("drywall-crumble.wav", fades(a, 0, 200), -8); }
// block-thud: soft heavy block hitting the ground, 0.5 s
{ const a = len(0.5); thump(a, 0, 70, 1, 14); add(a, svf(noise(4000, 4061), 400, 0.6, "low"), 0.4); write("block-thud.wav", fades(a, 0, 100), -6); }
// line-buzz: high-voltage line corona crackle-buzz, 3 s (loops)
{ const a = len(3), n = svf(noise(a.length, 4071), 6000, 0.6, "high"), r = rng(4072);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.35 * n[i] * (0.6 + 0.4 * Math.sin(2 * Math.PI * 120 * t)) + 0.2 * Math.sin(2 * Math.PI * 120 * t) + (Math.abs(r()) > 0.999 ? 0.5 * r() : 0); }
  write("line-buzz.wav", fades(a, 200, 200), -12); }
// street-amb: quiet suburban air + far traffic, 3 s
{ const a = len(3), lo = svf(noise(a.length, 4081), t => 260 + 80 * Math.sin(t * 0.9), 0.4, "low"), mid = svf(noise(a.length, 4082), 900, 0.3);
  for (let i = 0; i < a.length; i++) a[i] = lo[i] + 0.08 * mid[i];
  write("street-amb.wav", fades(a, 300, 300), -16); }
// breaker-clack: switchgear clack, 0.4 s
{ const a = len(0.4); modal(a, 0, 900, [[1, 1, 1], [2.4, 0.5, 1.6], [3.9, 0.3, 2.4]], 0.6, 30); thump(a, 0, 110, 0.6, 30); write("breaker-clack.wav", fades(a, 0, 60), -6); }
