// Procedural skyscraper-damper foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, wind-bed, wind-gust, steel-creak, storm-rain, steel-clunk. New: plate-clank, cable-creak, hydraulic-hiss, heat-sizzle, sway-tick, lamp-creak, box-slide, thunder, tower-groan.
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
// storm-rain: dense rain hiss + low wind roar, 3 s
{ const a = len(3), hi = svf(noise(a.length, 2011), 4500, 0.7, "high"), lo = svf(noise(a.length, 2012), t => 180 + 60 * Math.sin(t * 2.3), 0.4, "low"), r = rng(2013);
  for (let i = 0; i < a.length; i++) a[i] = 0.35 * hi[i] + lo[i] + (Math.abs(r()) > 0.9993 ? r() * 0.6 : 0); write("storm-rain.wav", fades(a, 300, 300), -9); }
// steel-clunk: yaw brake / gear engage, 0.7 s
{ const a = len(0.7); modal(a, 0, 260, METAL, 0.6, 10); thump(a, 0, 65, 0.7, 12); write("steel-clunk.wav", fades(a, 0, 120), -6); }
// plate-clank: heavy steel plate landing on the stack, 0.5 s
{ const a = len(0.5); modal(a, 0, 180, METAL, 0.5, 14); thump(a, 0, 55, 0.6, 16); write("plate-clank.wav", fades(a, 0, 100), -7); }
// cable-creak: taut steel cable under load, 1.2 s
{ const a = len(1.2), r = rng(3011);
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 140 + 30 * Math.sin(t * 5); a[i] = (Math.sin(2 * Math.PI * f * t) + 0.4 * Math.sin(2 * Math.PI * 2.7 * f * t)) * (0.5 + 0.5 * Math.abs(r())) * Math.sin(Math.PI * t / 1.2); }
  write("cable-creak.wav", fades(svf(a, 900, 0.4, "low"), 40, 200), -10); }
// hydraulic-hiss: piston push + oil hiss, 1.5 s
{ const a = len(1.5), n = svf(noise(a.length, 3021), t => 900 + 600 * Math.sin(Math.PI * t / 1.5), 0.3), lo = svf(noise(a.length, 3022), 90, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, e = Math.sin(Math.PI * t / 1.5); a[i] = e * (0.5 * n[i] + lo[i]); }
  write("hydraulic-hiss.wav", fades(a, 60, 250), -8); }
// heat-sizzle: crackling hiss (energy turned into heat), 2 s
{ const a = len(2), n = svf(noise(a.length, 3031), 5000, 0.6, "high"), r = rng(3032);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.4 * n[i] + (Math.abs(r()) > 0.997 ? r() * 0.8 : 0)) * Math.min(1, t * 3) * (1 - t / 2.2); }
  write("heat-sizzle.wav", fades(a, 50, 300), -10); }
// sway-tick: metronome-like woody tick (the tower's rhythm), 0.25 s
{ const a = len(0.25); modal(a, 0, 1250, [[1, 1, 1], [2.3, 0.4, 2]], 0.6, 45); write("sway-tick.wav", fades(a, 0, 40), -8); }
// lamp-creak: small squeaky swing, 0.8 s
{ const a = len(0.8); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 700 + 250 * Math.sin(Math.PI * t / 0.8); ph += 2 * Math.PI * f / SR; a[i] = Math.sin(ph) * Math.pow(Math.sin(Math.PI * t / 0.8), 2) * (0.7 + 0.3 * Math.sin(t * 90)); }
  write("lamp-creak.wav", fades(a, 30, 120), -14); }
// box-slide: cardboard scraping across a floor, 1.2 s
{ const a = len(1.2), n = svf(noise(a.length, 3041), 1500, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * (0.6 + 0.4 * Math.sin(t * 40)) * Math.sin(Math.PI * t / 1.2); } thump(a, 1.0, 90, 0.3, 20);
  write("box-slide.wav", fades(a, 40, 150), -9); }
// thunder: rumble roll, 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 3051), 70, 0.6, "low"), mid = svf(noise(a.length, 3052), 300, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (lo[i] + 0.3 * mid[i] * Math.exp(-t * 3)) * Math.exp(-t * 1.2) * Math.min(1, t * 20); }
  write("thunder.wav", fades(a, 0, 400), -5); }
// tower-groan: deep slow structural groan, 2 s
{ const a = len(2), r = rng(3061);
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 48 + 8 * Math.sin(t * 2.2); a[i] = (Math.sin(2 * Math.PI * f * t) + 0.35 * Math.sin(2 * Math.PI * 2.1 * f * t)) * (0.7 + 0.3 * r()) * Math.sin(Math.PI * t / 2); }
  write("tower-groan.wav", fades(svf(a, 400, 0.5, "low"), 80, 300), -8); }
