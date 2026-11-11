// Procedural pipe-under-river foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from the water-well set: deny thud, wind, water rush, pump hum, power-down, splash, birds, drill rumble, crumble, pipe slide, slurry;
// new (appended at the end): rod clank, spin whir, transmitter beeps, mud bubbles, weld zap, boat motor, excavator scoop.
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
// wind-gust: soft outdoor air, 3 s
{ const a = len(3), n = svf(noise(a.length, 105), t => 500 + 350 * Math.sin(2 * Math.PI * 0.4 * t), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.33 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  write("wind-gust.wav", fades(a, 200, 500), -14); }
// water-rush: water running up a pipe, 3 s
{ const a = len(3), n = svf(noise(a.length, 301), t => 700 + 250 * Math.sin(2 * Math.PI * 0.8 * t), 0.3), lo = svf(noise(a.length, 302), 160, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.35 * n[i] + 0.35 * lo[i]) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  blips(a, 30, 0.2, 2.8, 300, 900, 0.05, 303); write("water-rush.wav", fades(a, 150, 400), -12); }
// pump-hum: submersible motor with a spin-up, 4 s
{ const a = len(4), n = svf(noise(a.length, 304), 900, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR, sp = Math.min(1, t / 0.6);
    a[i] = Math.sin(Math.PI * Math.min(1, t / 4)) ** 0.3 * (0.35 * Math.sin(2 * Math.PI * 120 * sp * t) + 0.15 * Math.sin(2 * Math.PI * 240 * sp * t) + 0.08 * n[i]); }
  write("pump-hum.wav", fades(a, 60, 500), -11); }
// pump-blip: a short start-stop of the motor (short cycling), 0.45 s
{ const a = len(0.45);
  for (let i = 0; i < a.length; i++) { const t = i / SR, sp = Math.min(1, t / 0.12); a[i] = (0.4 * Math.sin(2 * Math.PI * 120 * sp * t) + 0.15 * Math.sin(2 * Math.PI * 240 * sp * t)) * Math.max(0, 1 - t / 0.45); }
  modal(a, 0, 1600, [[1, 1, 1]], 0.3, 90); write("pump-blip.wav", fades(a, 5, 80), -9); }
// power-down: motor winding down + relay clack, 1.4 s
{ const a = len(1.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 120 * Math.max(0.15, 1 - t / 1.2); a[i] = 0.5 * Math.sin(2 * Math.PI * f * t) * Math.max(0, 1 - t / 1.3); }
  modal(a, 0, 900, [[1, 1, 1], [2.4, 0.5, 2]], 0.4, 50); thump(a, 0, 70, 0.4, 20); write("power-down.wav", fades(a, 0, 150), -7); }
// splash: bucket hitting the water, 1.2 s
{ const a = len(1.2), n = svf(noise(a.length, 309), 1800, 0.5), lo = svf(noise(a.length, 310), 300, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.4 * n[i] + 0.35 * lo[i]) * Math.min(1, t / 0.01) * Math.exp(-t * 3.5); }
  blips(a, 18, 0.05, 1.0, 500, 1400, 0.07, 311); thump(a, 0, 90, 0.35, 14); write("splash.wav", fades(a, 0, 200), -9); }
// rope-creak: rope over a wooden bar, 1.2 s
{ const a = len(1.2), r = rng(401);
  for (let k = 0; k < 9; k++) { const t0 = 0.05 + k * 0.12 + 0.02 * r(); modal(a, t0, 380 + 60 * r(), [[1, 1, 1], [1.9, 0.5, 1.5]], 0.25, 40); }
  add(a, svf(noise(a.length, 402), 900, 0.3), 0.08); write("rope-creak.wav", fades(a, 10, 150), -12); }
// birds: yard ambience, 3 s
{ const a = len(3), r = rng(308);
  for (let k = 0; k < 12; k++) { const t0 = 2.7 * Math.abs(r()), f0 = 2600 + 900 * Math.abs(r()), i0 = Math.round(t0 * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.12; i++) { const t = (i - i0) / SR; a[i] += 0.2 * Math.sin(2 * Math.PI * (f0 + 2500 * t) * t) * Math.sin(Math.PI * t / 0.12); } }
  write("birds.wav", fades(a, 50, 300), -16); }
// pump-squeak: cast-iron hand pump handle stroke (squeak + clank), 0.7 s
{ const a = len(0.7);
  for (let i = 0; i < a.length && i < SR * 0.35; i++) { const t = i / SR; a[i] += 0.18 * Math.sin(2 * Math.PI * (900 + 500 * Math.sin(Math.PI * t / 0.35)) * t) * Math.sin(Math.PI * t / 0.35); }
  modal(a, 0.36, 420, METAL, 0.5, 18); write("pump-squeak.wav", fades(a, 10, 120), -9); }
// slurp: suction drawing water up a pipe then stalling, 1.6 s
{ const a = len(1.6), n = svf(noise(a.length, 403), t => 300 + 900 * Math.min(1, t / 1.2), 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.45 * n[i] * Math.min(1, t / 0.1) * (t < 1.2 ? 1 : Math.max(0, 1 - (t - 1.2) / 0.3)); }
  blips(a, 26, 0.1, 1.2, 250, 700, 0.07, 404, 20); write("slurp.wav", fades(a, 20, 200), -10); }
// drill-rumble: rotary drill boring down, 3 s
{ const a = len(3), lo = svf(noise(a.length, 405), 120, 0.5, "low"), mid = svf(noise(a.length, 406), 600, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.55 * lo[i] + 0.12 * mid[i] * (0.6 + 0.4 * Math.sin(2 * Math.PI * 11 * t)) + 0.15 * Math.sin(2 * Math.PI * 55 * t)) * Math.sin(Math.PI * Math.min(1, t / 3)) ** 0.4; }
  write("drill-rumble.wav", fades(a, 100, 400), -9); }
// crumble: soil and gravel falling into the hole, 1.4 s
{ const a = len(1.4), r = rng(407), n = svf(noise(a.length, 408), 1200, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.25 * n[i] * Math.exp(-t * 1.8) * Math.min(1, t / 0.05); }
  for (let k = 0; k < 35; k++) { const t0 = 1.2 * Math.abs(r()) ** 1.5; thump(a, t0, 80 + 120 * Math.abs(r()), 0.12, 30); }
  thump(a, 0, 55, 0.5, 6); write("crumble.wav", fades(a, 0, 200), -7); }
// pipe-slide: long pipe sliding down the hole (scrape + clunk), 1.8 s
{ const a = len(1.8), s = svf(noise(a.length, 409), t => 500 + 300 * t, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * Math.sin(Math.PI * Math.min(1, t / 1.6)); }
  modal(a, 1.6, 260, METAL, 0.5, 12); thump(a, 1.6, 70, 0.5, 14); write("pipe-slide.wav", fades(a, 30, 150), -8); }
// rain: steady rain on grass, 4.5 s
{ const a = len(4.5), n = svf(noise(a.length, 410), 3000, 0.6), r = rng(411);
  for (let i = 0; i < a.length; i++) a[i] = 0.25 * n[i];
  for (let k = 0; k < 220; k++) { const t0 = 4.4 * Math.abs(r()), i0 = Math.round(t0 * SR), f = 2000 + 3000 * Math.abs(r());
    for (let i = i0; i < a.length && i < i0 + SR * 0.01; i++) a[i] += 0.15 * Math.sin(2 * Math.PI * f * (i - i0) / SR) * Math.exp(-(i - i0) / SR * 400); }
  write("rain.wav", fades(a, 300, 500), -14); }
// slurry: grout being poured into the gap (thick wet pour), 1.4 s
{ const a = len(1.4), lo = svf(noise(a.length, 412), 220, 0.6, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * lo[i] * Math.sin(Math.PI * Math.min(1, t / 1.4)); }
  blips(a, 24, 0.05, 1.3, 120, 320, 0.12, 413, 14); write("slurry.wav", fades(a, 50, 200), -9); }
// switch-click: pressure switch contacts, 0.12 s
{ const a = len(0.12); modal(a, 0, 3200, [[1, 1, 1], [1.7, 0.5, 1.5]], 0.5, 160); thump(a, 0, 180, 0.2, 60); write("switch-click.wav", fades(a, 0, 20), -10); }
// spigot: tap squeak + water stream into a bucket, 3 s
{ const a = len(3), n = svf(noise(a.length, 414), 2400, 0.6), lo = svf(noise(a.length, 415), 500, 0.5);
  for (let i = 0; i < a.length && i < SR * 0.18; i++) { const t = i / SR; a[i] += 0.15 * Math.sin(2 * Math.PI * (1300 + 700 * t) * t) * Math.sin(Math.PI * t / 0.18); }
  for (let i = Math.round(0.15 * SR); i < a.length; i++) { const t = i / SR; a[i] += (0.3 * n[i] + 0.25 * lo[i] * (0.8 + 0.2 * Math.sin(2 * Math.PI * 6 * t))) * Math.min(1, (t - 0.15) / 0.08); }
  write("spigot-stream.wav", fades(a, 0, 500), -12); }
// rod-clank: a steel drill rod seating in the carriage, 0.7 s
{ const a = len(0.7); modal(a, 0, 520, METAL, 0.6, 14); modal(a, 0.02, 1210, METAL, 0.25, 22); thump(a, 0, 80, 0.5, 18);
  add(a, svf(noise(3000, 501), 2500, 0.4), 0.15); write("rod-clank.wav", fades(a, 0, 120), -7); }
// spin-whir: drill string spinning in the ground, 2 s
{ const a = len(2), n = svf(noise(a.length, 511), 380, 0.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.4 * n[i] + 0.25 * Math.sin(2 * Math.PI * 95 * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 9 * t))) * Math.min(1, t / 0.2); }
  write("spin-whir.wav", fades(a, 50, 300), -11); }
// signal-beep: three soft transmitter beeps, 1.6 s
{ const a = len(1.6); for (const t0 of [0, 0.5, 1.0]) modal(a, t0, 1760, [[1, 1, 1], [2, 0.25, 1.5]], 0.5, 9); write("signal-beep.wav", fades(a, 5, 200), -12); }
// mud-bubble: thick mud bubbling up through water, 2 s
{ const a = len(2), lo = svf(noise(a.length, 521), 200, 0.5, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.3 * lo[i];
  blips(a, 40, 0.05, 1.8, 90, 320, 0.14, 522, 12); write("mud-bubble.wav", fades(a, 60, 300), -9); }
// weld-zap: an arc-weld crackle, 0.4 s
{ const a = len(0.4), n = noise(a.length, 531), r = rng(532);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * (Math.abs(r()) > 0.92 ? 1 : 0.18) * Math.exp(-t * 4); }
  write("weld-zap.wav", fades(svf(a, 3500, 0.6, "high"), 2, 80), -12); }
// boat-motor: a distant outboard passing, 3 s
{ const a = len(3), n = svf(noise(a.length, 541), 160, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.5 * n[i] + 0.3 * Math.sin(2 * Math.PI * 62 * t) * (0.7 + 0.3 * Math.sin(2 * Math.PI * 31 * t))) * Math.sin(Math.PI * t / 3); }
  write("boat-motor.wav", fades(a, 200, 400), -14); }
// scoop: an excavator bucket biting into a wet riverbed, 1.2 s
{ const a = len(1.2); add(a, svf(noise(a.length, 551), 260, 0.4, "low"), 0.6); thump(a, 0.05, 60, 0.6, 8); modal(a, 0.0, 300, METAL, 0.3, 16);
  blips(a, 14, 0.3, 1.1, 150, 500, 0.08, 552, 18); write("scoop.wav", fades(a, 0, 200), -8); }
