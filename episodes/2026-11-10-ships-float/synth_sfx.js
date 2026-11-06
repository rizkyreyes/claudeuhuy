// Procedural ship foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Hull slide, splash, sink bubbles, bed thud, plate clang, hull creak, container clank, waves, pump hum, prop churn, flood rush, breach crunch, hull groan, deny thud.
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
// hull-slide: the near-half cover (hull + sea) pulled away on "cut" (big steel scrape + whoosh of water)
{ const a = len(1.2), s = svf(noise(a.length, 61), t => 250 + 500 * Math.min(1, t / 0.9), 0.3), w = svf(noise(a.length, 62), 600, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.sin(Math.PI * Math.min(1, t / 1.1)); a[i] = env * (0.45 * s[i] + 0.35 * w[i]); }
  modal(a, 0.05, 95, METAL, 0.25, 6); write("hull-slide.wav", fades(a, 20, 200), -6); }
// splash: the steel block hits the water
{ const a = len(1.6), n = svf(noise(a.length, 63), 1400, 0.4), lo = svf(noise(a.length, 64), 260, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.exp(-t * 3.2); a[i] = env * (0.55 * n[i] + 0.6 * lo[i]); }
  thump(a, 0.0, 70, 0.5, 10); blips(a, 26, 0.05, 1.3, 260, 900, 0.12, 65, 22); write("splash.wav", fades(a, 2, 250), -5); }
// sink-bubbles: muffled underwater descent (low drone + rising bubbles), 6 s
{ const a = len(6), lo = svf(noise(a.length, 66), 90, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.6) * (t < 5 ? 1 : Math.max(0, 1 - (t - 5))); a[i] = 0.7 * lo[i] * env; }
  blips(a, 34, 0.1, 5.6, 180, 520, 0.14, 67, 18); write("sink-bubbles.wav", fades(a, 60, 400), -12); }
// bed-thud: the block landing on the sea bed (deep, muffled)
{ const a = len(0.9); thump(a, 0, 42, 1, 6); add(a, svf(noise(9000, 68), 160, 0.6, "low"), 0.5); write("bed-thud.wav", fades(a, 0, 200), -4); }
// plate-clang: a hull plate snapping into place (bright metal hit)
{ const a = len(0.7); modal(a, 0, 180, METAL, 0.6, 9); thump(a, 0, 90, 0.4, 14); add(a, svf(noise(3000, 69), 2400, 0.6), 0.15); write("plate-clang.wav", fades(a, 0, 150), -6); }
// hull-creak: the hull settling into the water (low steel creak + water push), 2.2 s
{ const a = len(2.2), w = svf(noise(a.length, 70), 300, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 58 + 18 * Math.sin(2 * Math.PI * 0.8 * t);
    a[i] = 0.28 * Math.sin(2 * Math.PI * f * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 9 * t)) * Math.sin(Math.PI * Math.min(1, t / 2.2)) + 0.4 * w[i] * Math.sin(Math.PI * Math.min(1, t / 2.2)); }
  write("hull-creak.wav", fades(a, 60, 300), -8); }
// container-clank: one box landing on the stack (hollow steel box)
{ const a = len(0.5); modal(a, 0, 120, [[1, 1, 1], [1.9, 0.6, 1.4], [3.1, 0.3, 2]], 0.6, 12); thump(a, 0, 70, 0.6, 16); write("container-clank.wav", fades(a, 0, 120), -7); }
// waves: open-sea wash against the hull, 4 s
{ const a = len(4), n = svf(noise(a.length, 71), 650, 0.5), lo = svf(noise(a.length, 72), 180, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.3 * n[i] + 0.3 * lo[i]) * (0.45 + 0.55 * Math.sin(2 * Math.PI * 0.35 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 4)); }
  write("waves.wav", fades(a, 100, 400), -14); }
// pump-hum: ballast pumps running + water filling the tanks, 3 s
{ const a = len(3), w = svf(noise(a.length, 73), 380, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.3) * (t < 2.4 ? 1 : Math.max(0, 1 - (t - 2.4) / 0.6));
    a[i] = env * (0.28 * Math.sin(2 * Math.PI * 100 * t) + 0.12 * Math.sin(2 * Math.PI * 200 * t) + 0.3 * w[i]); }
  blips(a, 20, 0.3, 2.6, 150, 420, 0.1, 74, 24); write("pump-hum.wav", fades(a, 40, 300), -10); }
// prop-churn: a half-out propeller thrashing air and water, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 75), 900, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.4 + 0.6 * Math.abs(Math.sin(2 * Math.PI * 4.5 * t))) * Math.sin(Math.PI * Math.min(1, t / 2.5)); }
  add(a, svf(noise(a.length, 76), 120, 0.5, "low"), 0.4); write("prop-churn.wav", fades(a, 60, 300), -9); }
// flood-rush: sea water pouring through a hole into a compartment, 3 s
{ const a = len(3), lo = svf(noise(a.length, 77), 240, 0.5, "low"), mid = svf(noise(a.length, 78), 1100, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.1) * (t < 2.3 ? 1 : Math.max(0, 1 - (t - 2.3) / 0.7)); a[i] = env * (0.65 * lo[i] + 0.3 * mid[i]); }
  blips(a, 30, 0.05, 2.6, 160, 600, 0.12, 79, 20); write("flood-rush.wav", fades(a, 5, 300), -8); }
// breach-crunch: the hull tearing open (metal crunch + thud)
{ const a = len(0.9); thump(a, 0, 55, 1, 8); modal(a, 0, 150, METAL, 0.45, 8); add(a, svf(noise(12000, 80), 1800, 0.5), 0.35);
  write("breach-crunch.wav", fades(a, 0, 200), -4); }
// hull-groan: a ship going down by the bow (long, deep steel groan), 2 s
{ const a = len(2.0);
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 46 - 10 * t / 2; a[i] = 0.5 * Math.sin(2 * Math.PI * f * t) * (0.5 + 0.5 * Math.sin(2 * Math.PI * 5 * t)) * Math.sin(Math.PI * Math.min(1, t / 2)); }
  add(a, svf(noise(a.length, 81), 200, 0.5, "low"), 0.35); write("hull-groan.wav", fades(a, 60, 300), -6); }
// deny-thud: the strong stinger ("goes down fast", "opened more")
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
