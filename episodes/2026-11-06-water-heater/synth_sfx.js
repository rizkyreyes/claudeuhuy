// Procedural water-heater foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Jacket slide, rod scrape, corrosion fizz, water in, burner ignite, burner roar, electric hum, water rush, bubble pop, sediment rumble, valve click, steam hiss, deny thud.
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
// jacket-slide: the sheet-steel front half sliding off (metal scrape + light knock)
{ const a = len(0.9), s = svf(noise(a.length, 41), t => 700 + 1800 * Math.min(1, t / 0.7), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.45 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  modal(a, 0.7, 900, METAL, 0.25, 22); write("jacket-slide.wav", fades(a, 20, 120), -7); }
// rod-scrape: the anode rod pulled up through its port (metal-on-metal rasp)
{ const a = len(1.2), s = svf(noise(a.length, 61), t => 1800 + 600 * Math.sin(2 * Math.PI * 3 * t), 0.15);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * Math.sin(Math.PI * Math.min(1, t / 1.15)) * (0.7 + 0.3 * Math.sin(2 * Math.PI * 23 * t)); }
  modal(a, 1.0, 2200, METAL, 0.2, 40); write("rod-scrape.wav", fades(a, 30, 150), -9); }
// corrosion-fizz: crackly fizz while metal is eaten
{ const a = len(1.8), r = rng(62);
  for (let k = 0; k < 220; k++) { const i0 = Math.round(Math.abs(r()) * (a.length - 400)), g = 0.3 * Math.abs(r());
    for (let i = 0; i < 300; i++) a[i0 + i] += g * r() * Math.exp(-i / 50); }
  add(a, svf(noise(a.length, 63), 5000, 0.5), 0.08); write("corrosion-fizz.wav", fades(a, 60, 400), -11); }
// water-in: cold water running down a pipe
{ const a = len(2.5), n = svf(noise(a.length, 64), 1100, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.min(1, t / 0.2) * (t < 2 ? 1 : 1 - (t - 2) / 0.5); }
  blips(a, 30, 0.1, 2.2, 400, 900, 0.1, 65, 40); write("water-in.wav", fades(a, 20, 200), -11); }
// ignite: gas catching (click + soft whoomp)
{ const a = len(1.0); modal(a, 0, 3200, METAL, 0.3, 120);
  const n = svf(noise(a.length, 66), t => 200 + 900 * Math.min(1, t / 0.15), 0.6, "low");
  for (let i = Math.round(0.08 * SR); i < a.length; i++) { const t = i / SR - 0.08; a[i] += 0.9 * n[i] * Math.min(1, t / 0.05) * Math.exp(-t * 3.5); }
  thump(a, 0.08, 70, 0.5, 9); write("ignite.wav", fades(a, 0, 200), -5); }
// burner-roar: steady gas burner, 6 s
{ const a = len(6), n = svf(noise(a.length, 67), 300, 0.5), h = svf(noise(a.length, 68), 1800, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.7 * n[i] + 0.15 * h[i]) * Math.min(1, t / 0.4) * (0.9 + 0.1 * Math.sin(2 * Math.PI * 4.3 * t)); }
  write("burner-roar.wav", fades(a, 50, 800), -14); }
// elec-hum: element switching on (relay click + 60 Hz hum)
{ const a = len(2.5); modal(a, 0, 2600, METAL, 0.35, 80);
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.3);
    a[i] += 0.25 * env * (Math.sin(2 * Math.PI * 120 * t) + 0.4 * Math.sin(2 * Math.PI * 240 * t) + 0.2 * Math.sin(2 * Math.PI * 360 * t)); }
  write("elec-hum.wav", fades(a, 0, 500), -10); }
// water-rush: tap open, water running through the pipes, 3.5 s
{ const a = len(3.5), n = svf(noise(a.length, 69), 900, 0.35), lo = svf(noise(a.length, 70), 180, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.15) * (t < 2.6 ? 1 : Math.max(0, 1 - (t - 2.6) / 0.9));
    a[i] = (0.55 * n[i] + 0.6 * lo[i]) * env * (0.85 + 0.15 * Math.sin(2 * Math.PI * 5 * t)); }
  write("water-rush.wav", fades(a, 10, 300), -11); }
// bubble-pop: trapped water flashing to steam under the sediment (sharp pop)
{ const a = len(0.25); blips(a, 1, 0, 0.001, 240, 240, 0.8, 71, 30); thump(a, 0, 90, 0.4, 40); write("bubble-pop.wav", fades(a, 0, 60), -7); }
// sediment-rumble: low rumbling boil with knocks, 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 72), 90, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.9 * lo[i] * Math.sin(Math.PI * Math.min(1, t / 2.5)); }
  const r = rng(73); for (let k = 0; k < 9; k++) thump(a, 0.1 + 2.1 * Math.abs(r()), 60 + 40 * Math.abs(r()), 0.35, 22);
  write("sediment-rumble.wav", fades(a, 80, 400), -6); }
// valve-click: T&P lever snapping open / drain valve turned
{ const a = len(0.35); modal(a, 0, 1900, METAL, 0.5, 55); thump(a, 0, 180, 0.3, 50); write("valve-click.wav", fades(a, 0, 60), -6); }
// steam-hiss: relief valve venting, 4 s
{ const a = len(4), n = svf(noise(a.length, 74), 4200, 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * n[i] * Math.min(1, t / 0.08) * (t < 3.2 ? 1 : 1 - (t - 3.2) / 0.8); }
  write("steam-hiss.wav", fades(a, 0, 300), -12); }
// deny-thud: failure stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
