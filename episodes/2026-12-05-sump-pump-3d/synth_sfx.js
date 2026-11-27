// Procedural sump-pump foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from septic: deny-thud, water-rush, yard-air, drip-plink, gurgle-rise. New: rain-storm, thunder, pump-motor, float-click, valve-thunk, power-down, spark-crackle, branch-crack, ice-crackle, basement-hum.
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

// deny-thud: the stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }

// water-rush: water/air through a closed pipe, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6021), 180, 0.35, "low"), mid = svf(noise(a.length, 6022), t => 620 + 90 * Math.sin(t * 2.3), 0.15);
  for (let i = 0; i < a.length; i++) a[i] = 0.9 * lo[i] + 0.35 * mid[i];
  write("water-rush.wav", fades(a, 250, 250), -11); }

// yard-air: outdoor ambience (soft wind + birds-free), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6011), t => 380 + 160 * Math.sin(t * 1.3), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.6 + 0.4 * Math.sin(Math.PI * t / 3)); }
  write("yard-air.wav", fades(a, 300, 300), -18); }

// drip-plink: single water drop into gravel/soil, 0.3 s
{ const a = len(0.3); blips(a, 1, 0.0, 0.01, 1100, 1300, 0.8, 9101, 40); add(a, svf(noise(2000, 9102), 2600, 0.5), 0.12); write("drip-plink.wav", fades(a, 0, 60), -10); }

// gurgle-rise: water rising through the trench, 2.0 s
{ const a = len(2.0), lo = svf(noise(a.length, 9131), t => 160 + 220 * t, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * lo[i] * Math.min(1, t * 2); }
  blips(a, 14, 0.1, 1.9, 300, 700, 0.3, 9132, 22); write("gurgle-rise.wav", fades(a, 80, 300), -9); }
// rain-storm: heavy rain on the roof and lawn, 3 s (loops)
{ const a = len(3), h = svf(noise(a.length, 1201), 2400, 0.4), lo = svf(noise(a.length, 1202), 500, 0.4, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.55 * h[i] + 0.35 * lo[i];
  blips(a, 60, 0.0, 2.95, 2500, 4200, 0.06, 1203, 90); write("rain-storm.wav", fades(a, 250, 250), -12); }
// thunder: low rumble with a crack at the start, 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 1211), t => 140 - 40 * t, 0.3, "low"), cr = svf(noise(a.length, 1212), 1800, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.9 * lo[i] * Math.exp(-t * 1.1) * (0.6 + 0.4 * Math.sin(t * 9)) + 0.5 * cr[i] * Math.exp(-t * 14); }
  write("thunder.wav", fades(a, 5, 500), -4); }
// pump-motor: submersible motor hum + water churn, 2 s (loops)
{ const a = len(2), ch = svf(noise(a.length, 1221), 700, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.35 * Math.sin(2 * Math.PI * 120 * t) + 0.18 * Math.sin(2 * Math.PI * 240 * t) + 0.08 * Math.sin(2 * Math.PI * 360 * t) + 0.35 * ch[i]; }
  write("pump-motor.wav", fades(a, 120, 120), -12); }
// float-click: the switch flipping (dry plastic snap), 0.25 s
{ const a = len(0.25); modal(a, 0, 2400, [[1, 1, 1], [2.3, 0.5, 2]], 0.7, 70); add(a, svf(noise(1200, 1231), 4000, 0.5), 0.3); write("float-click.wav", fades(a, 0, 40), -8); }
// valve-thunk: the check-valve flap slamming shut / water hammer, 0.7 s
{ const a = len(0.7); thump(a, 0, 70, 1, 9); modal(a, 0.0, 420, METAL, 0.25, 16); add(a, svf(noise(3000, 1241), 600, 0.5, "low"), 0.4); write("valve-thunk.wav", fades(a, 0, 120), -4); }
// power-down: everything winding down + click, 1.2 s
{ const a = len(1.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * Math.sin(2 * Math.PI * (120 * Math.exp(-t * 2.5)) * t) * Math.exp(-t * 2.2); }
  modal(a, 0, 1800, [[1, 1, 1]], 0.4, 80); write("power-down.wav", fades(a, 0, 200), -7); }
// spark-crackle: electrical arcing, 0.9 s
{ const a = len(0.9), h = svf(noise(a.length, 1251), 5200, 0.4), r = rng(1252);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (Math.abs(r()) > 0.7 ? 1 : 0.15) * h[i] * Math.exp(-t * 3); }
  for (let i = 0; i < a.length; i++) a[i] += 0.12 * Math.sin(2 * Math.PI * 60 * i / SR) * Math.exp(-i / SR * 3);
  write("spark-crackle.wav", fades(a, 0, 150), -7); }
// branch-crack: wood snapping + leaves, 1.0 s
{ const a = len(1.0), lf = svf(noise(a.length, 1261), 3000, 0.6);
  modal(a, 0, 900, [[1, 1, 1], [1.7, 0.6, 1.4], [3.1, 0.3, 2]], 0.8, 30); thump(a, 0.35, 55, 0.6, 8);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.25 * lf[i] * Math.exp(-t * 3); }
  write("branch-crack.wav", fades(a, 0, 200), -5); }
// ice-crackle: water freezing in the pipe, 1.2 s
{ const a = len(1.2), r = rng(1271);
  for (let k = 0; k < 40; k++) modal(a, 1.1 * Math.abs(r()), 2500 + 4000 * Math.abs(r()), [[1, 1, 1], [2.7, 0.4, 2]], 0.08, 90);
  write("ice-crackle.wav", fades(a, 10, 200), -9); }
// basement-hum: room tone, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 1281), 160, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * lo[i] + 0.05 * Math.sin(2 * Math.PI * 60 * t); }
  write("basement-hum.wav", fades(a, 300, 300), -20); }
