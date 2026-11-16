// Procedural wind-turbine power foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from part 1: deny-thud, wind-bed, wind-gust, steel-creak, rotor-hum. New: storm-rain, blade-crack, air-flow, gear-grind, gear-whine, elec-hum, elec-zap, zip-down, servo-whir, steel-clunk, rotor-wind-down.
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
// storm-rain: dense rain hiss + low wind roar, 3 s
{ const a = len(3), hi = svf(noise(a.length, 2011), 4500, 0.7, "high"), lo = svf(noise(a.length, 2012), t => 180 + 60 * Math.sin(t * 2.3), 0.4, "low"), r = rng(2013);
  for (let i = 0; i < a.length; i++) a[i] = 0.35 * hi[i] + lo[i] + (Math.abs(r()) > 0.9993 ? r() * 0.6 : 0); write("storm-rain.wav", fades(a, 300, 300), -9); }
// blade-crack: composite snap + splinter + debris, 0.9 s
{ const a = len(0.9), n = svf(noise(a.length, 2021), 2500, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 9); } thump(a, 0, 70, 0.8, 9); blips(a, 18, 0.05, 0.7, 900, 2600, 0.15, 2022, 60); write("blade-crack.wav", fades(a, 0, 150), -4); }
// air-flow: smooth rushing air, 2 s
{ const a = len(2), n = svf(noise(a.length, 2031), t => 700 + 500 * Math.sin(Math.PI * t / 2), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.sin(Math.PI * t / 2); } write("air-flow.wav", fades(a, 100, 200), -10); }
// gear-grind: slow heavy gear mesh (low tooth clicks + rumble), 1.6 s
{ const a = len(1.6), lo = svf(noise(a.length, 2041), 120, 0.5, "low");
  for (let i = 0; i < a.length; i++) a[i] = lo[i] * 0.8; for (let k = 0; k < 22; k++) modal(a, 0.03 + k * 0.07, 340, METAL, 0.18, 30); write("gear-grind.wav", fades(a, 150, 300), -8); }
// gear-whine: tooth-mesh whine rising in pitch (the speed-up), 2.4 s
{ const a = len(2.4), n = svf(noise(a.length, 2051), 600, 0.4); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 180 + 520 * Math.pow(t / 2.4, 1.5); ph += 2 * Math.PI * f / SR; a[i] = 0.3 * Math.sin(ph) + 0.12 * Math.sin(3 * ph) + 0.25 * n[i]; }
  write("gear-whine.wav", fades(a, 200, 400), -10); }
// elec-hum: 60 Hz hum with harmonics + crackle, 2.4 s
{ const a = len(2.4), r = rng(2061);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * Math.sin(2 * Math.PI * 60 * t) + 0.3 * Math.sin(2 * Math.PI * 120 * t) + 0.15 * Math.sin(2 * Math.PI * 180 * t) + (Math.abs(r()) > 0.998 ? r() * 0.4 : 0); }
  write("elec-hum.wav", fades(a, 250, 400), -11); }
// elec-zap: short bright electric zap, 0.5 s
{ const a = len(0.5), n = svf(noise(a.length, 2071), 3200, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (n[i] + 0.3 * Math.sign(Math.sin(2 * Math.PI * 240 * t))) * Math.exp(-t * 9); } write("elec-zap.wav", fades(a, 2, 100), -7); }
// zip-down: falling electric sweep (power running down the tower), 1.8 s
{ const a = len(1.8); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 1400 * Math.exp(-t * 1.6) + 90; ph += 2 * Math.PI * f / SR; a[i] = (0.5 * Math.sin(ph) + 0.2 * Math.sign(Math.sin(ph * 0.5))) * Math.sin(Math.PI * Math.min(1, t / 1.8)); }
  write("zip-down.wav", fades(svf(a, 3000, 0.5, "low"), 30, 300), -9); }
// servo-whir: electric motor spin up/down, 1.5 s
{ const a = len(1.5), n = svf(noise(a.length, 2081), 900, 0.5); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.sin(Math.PI * t / 1.5), f = 300 + 500 * env; ph += 2 * Math.PI * f / SR; a[i] = env * (0.4 * Math.sin(ph) + 0.15 * Math.sin(2 * ph) + 0.2 * n[i]); }
  write("servo-whir.wav", fades(a, 50, 150), -9); }
// steel-clunk: yaw brake / gear engage, 0.7 s
{ const a = len(0.7); modal(a, 0, 260, METAL, 0.6, 10); thump(a, 0, 65, 0.7, 12); write("steel-clunk.wav", fades(a, 0, 120), -6); }
// rotor-wind-down: blade whoosh pulses slowing + falling hum, 2.6 s
{ const a = len(2.6), n = svf(noise(a.length, 2091), 350, 0.3); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, rate = 0.9 * Math.exp(-t * 0.9); ph += 2 * Math.PI * rate / SR; a[i] = n[i] * (0.3 + 0.7 * Math.pow(Math.sin(ph * 1.0), 2)) * (1 - t / 2.8) + 0.12 * Math.sin(2 * Math.PI * (60 - 15 * t) * t); }
  write("rotor-wind-down.wav", fades(a, 50, 500), -10); }
