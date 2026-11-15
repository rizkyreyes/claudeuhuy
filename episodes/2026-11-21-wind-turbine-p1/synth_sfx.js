// Procedural wind-turbine build foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// deny thud kept; new: wind-bed, wind-gust, steel-creak, rotor-hum, dig-scoop, rebar-clank, steel-ting, truck-idle, concrete-pour, dirt-dump, ground-thud, steel-clang, crane-winch, impact-wrench.
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
// steel-creak: slow stressed-metal groan, 1.4 s
{ const a = len(1.4), r = rng(1111);
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 90 + 40 * t + 6 * Math.sin(t * 23); a[i] = (Math.sin(2 * Math.PI * f * t) + 0.5 * Math.sin(4 * Math.PI * f * t)) * (0.6 + 0.4 * r()) * Math.sin(Math.PI * t / 1.4); }
  write("steel-creak.wav", fades(svf(a, 600, 0.4, "low"), 30, 200), -7); }
// rotor-hum: low blade whoosh pulses (~13 rpm x 3 blades) + drivetrain hum, 2.4 s
{ const a = len(2.4), n = svf(noise(a.length, 1121), 350, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * (0.4 + 0.6 * Math.pow(Math.sin(Math.PI * t / 1.5), 2)) + 0.15 * Math.sin(2 * Math.PI * 60 * t); }
  write("rotor-hum.wav", fades(a, 300, 400), -10); }
// dig-scoop: bucket into soil (crunch + thud), 0.7 s
{ const a = len(0.7), n = svf(noise(a.length, 1131), 900, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 6); } thump(a, 0.05, 60, 0.7, 10); write("dig-scoop.wav", fades(a, 5, 120), -6); }
// rebar-clank: bars dropped into place, 0.6 s
{ const a = len(0.6); modal(a, 0, 620, METAL, 0.5, 9); modal(a, 0.05, 880, METAL, 0.4, 11); modal(a, 0.12, 540, METAL, 0.3, 10); write("rebar-clank.wav", fades(a, 0, 100), -6); }
// steel-ting: bolts settle, 0.9 s
{ const a = len(0.9); modal(a, 0, 1850, METAL, 0.6, 5); modal(a, 0.07, 2330, METAL, 0.4, 6); write("steel-ting.wav", fades(a, 0, 150), -7); }
// truck-idle: diesel idle + rotating drum, 3 s
{ const a = len(3), lo = svf(noise(a.length, 1141), 140, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.7 + 0.3 * Math.sin(2 * Math.PI * 28 * t)) + 0.1 * Math.sin(2 * Math.PI * 42 * t); }
  write("truck-idle.wav", fades(a, 300, 500), -9); }
// concrete-pour: thick slurry slide (low gloopy noise + blips), 2.4 s
{ const a = len(2.4), n = svf(noise(a.length, 1151), 500, 0.6, "low"); blips(a, 40, 0.1, 2.2, 120, 300, 0.25, 1152, 18);
  add(a, n, 0.8); write("concrete-pour.wav", fades(a, 200, 400), -8); }
// dirt-dump: soil load sliding off + rumble, 1.5 s
{ const a = len(1.5), n = svf(noise(a.length, 1161), t => 1200 - 600 * t, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 2.2); } thump(a, 0.2, 45, 0.6, 6); write("dirt-dump.wav", fades(a, 20, 250), -6); }
// ground-thud: heavy soft impact, 0.8 s
{ const a = len(0.8); thump(a, 0, 40, 1, 6); add(a, svf(noise(a.length, 1171), 300, 0.6, "low"), 0.4); write("ground-thud.wav", fades(a, 0, 150), -5); }
// steel-clang: tower section seats on its flange (deep bell + clank), 1.2 s
{ const a = len(1.2); modal(a, 0, 180, METAL, 0.8, 3); modal(a, 0.01, 410, METAL, 0.5, 5); thump(a, 0, 55, 0.6, 8); write("steel-clang.wav", fades(a, 0, 200), -5); }
// crane-winch: geared motor whine rising, 2.5 s
{ const a = len(2.5), n = svf(noise(a.length, 1181), 160, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 220 + 80 * t; a[i] = 0.25 * Math.sin(2 * Math.PI * f * t) + 0.12 * Math.sin(2 * Math.PI * 2 * f * t) + n[i] * 0.6; }
  write("crane-winch.wav", fades(a, 250, 400), -9); }
// impact-wrench: rattling ratchet bursts, 0.7 s
{ const a = len(0.7), r = rng(1191);
  for (let k = 0; k < 28; k++) modal(a, 0.02 + k * 0.022 + 0.003 * r(), 2600 + 300 * r(), [[1, 1, 1], [1.7, 0.4, 2]], 0.25, 70);
  add(a, svf(noise(a.length, 1192), 1200, 0.4), 0.15); write("impact-wrench.wav", fades(a, 5, 120), -7); }
