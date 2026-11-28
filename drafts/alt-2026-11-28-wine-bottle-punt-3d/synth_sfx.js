// Procedural glass foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, spark-crackle, button-click, room-tone, drip. New: glass-clink, glass-wobble, fizz, furnace-roar, air-hiss, mold-clamp, glob-thud, pressure-creak, glass-scrape.
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
// spark-crackle: a short electric spark, 0.5 s
{ const a = len(0.5), r = rng(9021), h = svf(noise(a.length, 9022), 6000, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (Math.abs(r()) > 0.93 ? 1 : 0.08) * Math.exp(-t * 9); }
  write("spark-crackle.wav", fades(a, 0, 120), -6); }
// button-click: plastic push button, 0.25 s
{ const a = len(0.25); add(a, svf(noise(300, 9031), 3000, 0.5), 0.8); modal(a, 0.002, 1800, [[1, 1, 1], [2.4, 0.4, 2]], 0.3, 60); write("button-click.wav", fades(a, 0, 60), -6); }
// room-tone: quiet hallway (low air + faint hum), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 9051), 300, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] + 0.05 * Math.sin(2 * Math.PI * 120 * t); }
  write("room-tone.wav", fades(a, 300, 300), -20); }
// drip: grease / damp droplet landing, 0.3 s
{ const a = len(0.3); blips(a, 1, 0.0, 0.0, 900, 900, 1, 470, 30); write("drip.wav", fades(a, 0, 60), -9); }
// glass-clink: glass bottle set down / tapped (bright modal ring), 0.6 s
{ const a = len(0.6); add(a, svf(noise(200, 601), 5000, 0.4), 0.5); modal(a, 0.0, 1850, [[1, 1, 1], [2.32, 0.6, 1.4], [4.1, 0.35, 2.2], [6.7, 0.2, 3]], 0.6, 9);
  write("glass-clink.wav", fades(a, 0, 80), -5); }
// glass-wobble: a pointy bottle rocking on wood (clinks + low knocks), 1.6 s
{ const a = len(1.6);
  [[0.0, 1.0], [0.28, 0.7], [0.5, 0.55], [0.68, 0.4], [0.82, 0.3], [0.93, 0.22], [1.02, 0.16]].forEach(([t, g], k) => {
    modal(a, t, 1650 + 90 * k, [[1, 1, 1], [2.4, 0.5, 1.5], [4.3, 0.25, 2.5]], 0.45 * g, 14); thump(a, t, 160, 0.4 * g, 40); });
  write("glass-wobble.wav", fades(a, 0, 150), -5); }
// fizz: champagne bubbles (dense tiny blips + airy hiss), 3 s (loops)
{ const a = len(3); blips(a, 260, 0, 2.9, 2500, 7000, 0.18, 611, 90); add(a, svf(noise(a.length, 612), 7000, 0.3, "high"), 0.06);
  write("fizz.wav", fades(a, 40, 40), -12); }
// furnace-roar: glory hole (low gas roar), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 621), t => 180 + 40 * Math.sin(t * 2.1), 0.5, "low");
  for (let i = 0; i < a.length; i++) a[i] = lo[i] * (0.85 + 0.15 * Math.sin(2 * Math.PI * 0.7 * i / SR));
  write("furnace-roar.wav", fades(a, 60, 60), -10); }
// air-hiss: compressed air blowing the glass into the mold, 1.5 s
{ const a = len(1.5), h = svf(noise(a.length, 631), t => 2500 + 1800 * Math.min(1, t * 2), 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.min(1, t * 12) * Math.exp(-Math.max(0, t - 1.0) * 6); }
  write("air-hiss.wav", fades(a, 0, 120), -6); }
// mold-clamp: steel mold halves closing (heavy metallic clunk), 0.7 s
{ const a = len(0.7); thump(a, 0.0, 90, 1, 14); modal(a, 0.0, 620, METAL, 0.35, 10); add(a, svf(noise(1500, 641), 1800, 0.5), 0.4);
  write("mold-clamp.wav", fades(a, 0, 100), -4); }
// glob-thud: molten gob landing in the mold (soft heavy plop + sizzle), 0.8 s
{ const a = len(0.8), h = svf(noise(a.length, 651), 5200, 0.3, "high"); thump(a, 0.0, 70, 1, 12);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.25 * h[i] * Math.exp(-t * 5); }
  write("glob-thud.wav", fades(a, 0, 120), -5); }
// pressure-creak: glass under strain (low tonal groan), 1.4 s
{ const a = len(1.4); for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(2 * Math.PI * (55 + 12 * t) * t) * Math.sin(Math.PI * t / 1.4) * (0.7 + 0.3 * Math.sin(2 * Math.PI * 9 * t)); }
  add(a, svf(noise(a.length, 661), 900, 0.6), 0.15); write("pressure-creak.wav", fades(a, 30, 120), -7); }
// glass-scrape: hot glass being pushed by the tool (gritty scrape + sizzle), 1.4 s
{ const a = len(1.4), s = svf(noise(a.length, 671), t => 1400 + 800 * t, 0.35), r = rng(672);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (0.6 + 0.4 * Math.abs(r())) * Math.sin(Math.PI * Math.min(1, t / 1.4)); }
  write("glass-scrape.wav", fades(a, 20, 150), -6); }
