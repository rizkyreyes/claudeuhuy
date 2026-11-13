// Procedural city-sewer foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny thud; new: flush, gurgle, pipe-flow, splash, cover-clank, cover-scrape, dig-scoop, pump-hum, float-click, pressure-rush, street-tone, coin-drop.
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
// gurgle-ish bubbles: band-passed noise bursts with rising pitch
function bubbles(a, n, t0, t1, f0, f1, amp, seed) {
  const r = rng(seed);
  for (let k = 0; k < n; k++) {
    const tb = t0 + (t1 - t0) * (r() * 0.5 + 0.5) * (k / n + 0.02), f = f0 + (f1 - f0) * (r() * 0.5 + 0.5), d = 0.04 + 0.04 * (r() * 0.5 + 0.5);
    const i0 = Math.round(tb * SR);
    for (let i = i0; i < Math.min(a.length, i0 + d * SR * 3); i++) { const t = (i - i0) / SR; a[i] += amp * Math.sin(2 * Math.PI * f * (1 + 2.5 * t) * t) * Math.exp(-t / d); }
  }
}
// flush: rushing water swell + gurgles + a low drain swallow, 2.2 s
{ const a = len(2.2), n = svf(noise(a.length, 801), t => 900 + 700 * Math.sin(Math.PI * t / 2.2), 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * 0.7 * Math.min(1, t / 0.15) * Math.exp(-Math.max(0, t - 1.0) * 1.8); }
  bubbles(a, 40, 0.3, 2.0, 250, 700, 0.18, 802); thump(a, 1.3, 55, 0.35, 5); write("flush.wav", fades(a, 10, 300), -5); }
// gurgle: water glugging down a pipe, 1.4 s
{ const a = len(1.4); bubbles(a, 26, 0, 1.3, 150, 420, 0.5, 811); add(a, svf(noise(a.length, 812), 500, 0.5), 0.15); write("gurgle.wav", fades(a, 10, 250), -6); }
// pipe-flow: steady water running in a big pipe (loopable bed), 3 s
{ const a = len(3), lo = svf(noise(a.length, 821), t => 350 + 80 * Math.sin(t * 3.1), 0.3), hi = svf(noise(a.length, 822), 2200, 0.5);
  for (let i = 0; i < a.length; i++) a[i] = lo[i] * 0.7 + hi[i] * 0.12;
  bubbles(a, 10, 0, 2.9, 300, 600, 0.06, 823); write("pipe-flow.wav", fades(a, 300, 300), -12); }
// splash: water hitting water, 0.7 s
{ const a = len(0.7), n = svf(noise(a.length, 831), 1800, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 7); }
  bubbles(a, 10, 0.03, 0.5, 400, 900, 0.2, 832); write("splash.wav", fades(a, 3, 150), -6); }
// cover-clank: a cast-iron manhole cover lifted and dropped, 0.8 s
{ const a = len(0.8); thump(a, 0, 85, 0.8, 12); modal(a, 0, 520, METAL, 0.5, 7); modal(a, 0.02, 830, METAL, 0.2, 10); write("cover-clank.wav", fades(a, 0, 150), -4); }
// cover-scrape: iron dragged over concrete, 0.7 s
{ const a = len(0.7), n = svf(noise(a.length, 841), t => 1200 + 500 * Math.sin(t * 40), 0.15), r = rng(842);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.sin(Math.PI * t / 0.7) * (0.7 + 0.3 * r()); }
  write("cover-scrape.wav", fades(a, 20, 120), -8); }
// dig-scoop: bucket into dirt (crunch + thud), 0.9 s
{ const a = len(0.9), n = svf(noise(a.length, 851), 700, 0.6), r = rng(852);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.exp(-t * 4) * (r() > 0.6 ? 1 : 0.4); }
  thump(a, 0.05, 60, 0.6, 9); write("dig-scoop.wav", fades(a, 5, 150), -5); }
// pump-hum: electric motor spin-up + steady hum with a slosh, 3 s
{ const a = len(3), lo = svf(noise(a.length, 861), 200, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 60 * Math.min(1, t / 0.6 + 0.3);
    a[i] = (Math.sin(2 * Math.PI * f * t) * 0.6 + Math.sin(2 * Math.PI * 2 * f * t) * 0.3 + Math.sin(2 * Math.PI * 7.5 * f * t) * 0.05) * Math.min(1, t / 0.4) + lo[i] * 0.4; }
  write("pump-hum.wav", fades(a, 20, 300), -10); }
// float-click: switch contact, 0.25 s
{ const a = len(0.25); modal(a, 0, 3200, METAL, 0.5, 40); thump(a, 0, 180, 0.4, 40); write("float-click.wav", fades(a, 0, 40), -6); }
// pressure-rush: water forced through a pipe (whoosh with a pitch rise), 1.5 s
{ const a = len(1.5), n = svf(noise(a.length, 871), t => 300 + 900 * t, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * Math.sin(Math.PI * Math.min(1, t / 1.5)) ; }
  write("pressure-rush.wav", fades(a, 50, 200), -7); }
// street-tone: distant traffic room tone, 3 s
{ const a = len(3), lo = svf(noise(a.length, 881), t => 140 + 40 * Math.sin(t * 1.3), 0.4, "low"), mid = svf(noise(a.length, 882), 900, 0.2);
  for (let i = 0; i < a.length; i++) a[i] = lo[i] * 0.8 + mid[i] * 0.08;
  write("street-tone.wav", fades(a, 300, 300), -16); }
// coin-drop: small metallic "cost" accent, 0.6 s
{ const a = len(0.6); modal(a, 0, 2600, METAL, 0.5, 10); modal(a, 0.09, 3100, METAL, 0.4, 12); modal(a, 0.17, 2850, METAL, 0.3, 14); write("coin-drop.wav", fades(a, 0, 120), -6); }
