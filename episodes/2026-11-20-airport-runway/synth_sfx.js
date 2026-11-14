// Procedural airport-runway foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny thud; new: jet-roar, tire-screech, slab-crack, gear-thud, roller-rumble, layer-thud, steel-ting, rain, saw-whine, water-hiss, water-spray, wind-bed.
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
// jet-roar: airliner engines (low rumble + whine), 3 s
{ const a = len(3), lo = svf(noise(a.length, 901), 120, 0.5, "low"), hi = svf(noise(a.length, 902), 2400, 0.15);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * 1.0 + hi[i] * 0.12 + 0.05 * Math.sin(2 * Math.PI * (1800 + 60 * t) * t); }
  write("jet-roar.wav", fades(a, 400, 600), -8); }
// tire-screech: touchdown chirp + smoke hiss, 0.9 s
{ const a = len(0.9), n = svf(noise(a.length, 911), t => 1500 - 600 * t, 0.08);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 4) + 0.3 * Math.sin(2 * Math.PI * 1100 * t) * Math.exp(-t * 9); }
  thump(a, 0, 70, 0.6, 9); write("tire-screech.wav", fades(a, 5, 200), -6); }
// slab-crack: concrete snapping (sharp transients + crumble), 1.2 s
{ const a = len(1.2); const r = rng(921);
  for (let k = 0; k < 14; k++) { const t0 = 0.02 + 0.5 * Math.abs(r()) * Math.abs(r()); add(a, svf(noise(1800, 930 + k), 2500 + 2000 * Math.abs(r()), 0.3), 0.8 * Math.exp(-t0 * 3), t0); }
  thump(a, 0, 55, 0.9, 6); add(a, svf(noise(SR, 940), 600, 0.4, "low"), 0.35, 0.15);
  write("slab-crack.wav", fades(a, 0, 250), -4); }
// gear-thud: heavy gear settles / wheels hit, 0.7 s
{ const a = len(0.7); thump(a, 0, 42, 1, 6); modal(a, 0.01, 420, METAL, 0.25, 14); write("gear-thud.wav", fades(a, 0, 120), -4); }
// roller-rumble: vibratory roller pass, 2.4 s
{ const a = len(2.4), lo = svf(noise(a.length, 951), 90, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.7 + 0.3 * Math.sin(2 * Math.PI * 30 * t)) + 0.25 * Math.sin(2 * Math.PI * 55 * t); }
  write("roller-rumble.wav", fades(a, 200, 400), -9); }
// layer-thud: a layer lands (soft heavy thud + grit), 0.8 s
{ const a = len(0.8); thump(a, 0, 50, 1, 7); add(a, svf(noise(SR * 0.5, 961), 1800, 0.3), 0.25, 0.02); write("layer-thud.wav", fades(a, 0, 150), -4); }
// steel-ting: dowels glow, 0.9 s
{ const a = len(0.9); modal(a, 0, 1850, METAL, 0.6, 5); modal(a, 0.07, 2330, METAL, 0.4, 6); write("steel-ting.wav", fades(a, 0, 150), -7); }
// rain: 3 s loop-ish
{ const a = len(3), n = svf(noise(a.length, 971), 3000, 0.25); blips(a, 120, 0, 2.9, 2500, 5000, 0.12, 972, 60);
  for (let i = 0; i < a.length; i++) a[i] += n[i] * 0.5; write("rain.wav", fades(a, 300, 300), -12); }
// saw-whine: diamond saw cutting wet concrete, 3.6 s
{ const a = len(3.6), n = svf(noise(a.length, 981), 1600, 0.12);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * Math.sin(2 * Math.PI * (2200 + 40 * Math.sin(t * 7)) * t) + n[i] * 0.4 + 0.2 * Math.sin(2 * Math.PI * 110 * t); }
  write("saw-whine.wav", fades(a, 150, 300), -10); }
// water-hiss: tire on a wet film, 2 s
{ const a = len(2), n = svf(noise(a.length, 991), t => 900 + 500 * t, 0.2);
  for (let i = 0; i < a.length; i++) a[i] = n[i]; write("water-hiss.wav", fades(a, 150, 300), -9); }
// water-spray: high-pressure jets, 1.6 s
{ const a = len(1.6), n = svf(noise(a.length, 1001), 4200, 0.2), lo = svf(noise(a.length, 1002), 400, 0.4, "low");
  for (let i = 0; i < a.length; i++) a[i] = n[i] + lo[i] * 0.3; write("water-spray.wav", fades(a, 60, 250), -8); }
// wind-bed: open airfield room tone, 3 s
{ const a = len(3), lo = svf(noise(a.length, 1011), t => 200 + 60 * Math.sin(t * 1.1), 0.4, "low");
  for (let i = 0; i < a.length; i++) a[i] = lo[i]; write("wind-bed.wav", fades(a, 300, 300), -16); }
