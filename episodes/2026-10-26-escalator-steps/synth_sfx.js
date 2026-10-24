// Procedural escalator foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Steel uses inharmonic modal partials; hum, rattle and reel are modulated tones + filtered noise. Loops fade in/out.
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
const STEEL = [[1, 1, 1], [2.32, 0.6, 1.4], [4.25, 0.35, 2.0], [6.63, 0.2, 2.8]];
const add = (a, b, g = 1, at = 0) => { const i0 = Math.round(at * SR); for (let i = 0; i < b.length && i0 + i < a.length; i++) a[i0 + i] += g * b[i]; return a; };

// escalator-hum: 8 s machine bed (50/100 Hz motor hum, gear whine, soft step rumble)
{ const a = len(8), rum = svf(noise(a.length, 21), 160, 0.8, "low"), air = svf(noise(a.length, 22), 1200, 1.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR;
    a[i] = 0.45 * Math.sin(2 * Math.PI * 50 * t) + 0.3 * Math.sin(2 * Math.PI * 100 * t + 0.3) + 0.06 * Math.sin(2 * Math.PI * 612 * t) * (0.7 + 0.3 * Math.sin(t * 3.1))
      + 0.5 * rum[i] * (0.8 + 0.2 * Math.sin(2 * Math.PI * 1.1 * t)) + 0.08 * air[i]; }
  write("escalator-hum.wav", fades(a, 600, 600), -14); }
// comb-clack: a step tread passing the comb plate (two quick metal ticks)
{ const a = len(0.22); modal(a, 0, 1350, STEEL, 0.6, 40); modal(a, 0.045, 1180, STEEL, 0.45, 45); add(a, svf(noise(700, 23), 4200, 0.6), 0.5); write("comb-clack.wav", fades(a, 0, 30), -8); }
// chain-rattle: 2 s of links running over a sprocket (random link ticks over a low drone)
{ const a = len(2), r = rng(24);
  for (let k = 0; k < 70; k++) { const t = 0.05 + k * 0.026 + 0.004 * r(); modal(a, t, 900 + 300 * r(), STEEL, 0.18 + 0.06 * r(), 60); }
  const lo = svf(noise(a.length, 25), 300, 0.9, "low"); add(a, lo, 0.35); write("chain-rattle.wav", fades(a, 120, 400), -10); }
// gear-clunk: heavy sprocket engaging
{ const a = len(0.6); thump(a, 0, 70, 1, 10); modal(a, 0, 310, STEEL, 0.5, 11); add(a, svf(noise(2000, 26), 1500, 0.7), 0.3); write("gear-clunk.wav", fades(a, 0, 80), -5); }
// motor-start: electric motor spinning up (rising hum + whine)
{ const a = len(2.2), g = svf(noise(a.length, 27), 700, 1.0); let ph = 0, ph2 = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, k = Math.min(1, t / 1.3), f = 25 + 25 * k;
    ph += 2 * Math.PI * f / SR; ph2 += 2 * Math.PI * (200 + 500 * k) / SR;
    a[i] = (0.6 * Math.sin(ph) + 0.3 * Math.sin(2 * ph) + 0.12 * Math.sin(ph2) + 0.15 * g[i]) * (0.3 + 0.7 * k); }
  write("motor-start.wav", fades(a, 30, 500), -9); }
// panel-off: cladding sliding off (metal scrape that thins out + light clank)
{ const a = len(0.9), s = svf(noise(a.length, 28), t => 1600 + 1400 * Math.min(1, t / 0.6), 0.5);
  for (let i = 0; i < a.length; i++) a[i] = s[i] * Math.exp(-i / SR * 3.2) * 0.6; modal(a, 0, 520, STEEL, 0.5, 12); write("panel-off.wav", fades(a, 3, 150), -8); }
// wheel-roll: 3 s of small wheels rolling on a rail (soft rumble with a periodic bump)
{ const a = len(3), lo = svf(noise(a.length, 29), 260, 0.7, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.7 + 0.3 * Math.sin(2 * Math.PI * 2.2 * t)); }
  for (let t = 0.1; t < 2.9; t += 0.45) modal(a, t, 700, STEEL, 0.05, 50); write("wheel-roll.wav", fades(a, 300, 600), -13); }
// film-reel: 5 s old projector clatter for the 1896 beat
{ const a = len(5), hiss = svf(noise(a.length, 30), 3500, 0.8);
  for (let i = 0; i < a.length; i++) a[i] = 0.12 * hiss[i];
  for (let t = 0.02; t < 4.95; t += 1 / 18) { const i0 = Math.round(t * SR); for (let k = 0; k < 220 && i0 + k < a.length; k++) a[i0 + k] += 0.5 * Math.exp(-k / 40) * (k % 2 ? 1 : -1); }
  write("film-reel.wav", fades(a, 300, 600), -12); }
// rubber-stamp: "OTIS LOST IT" (thick dull hit with a paper slap)
{ const a = len(0.5); thump(a, 0, 95, 1, 16); add(a, svf(noise(1500, 31), 2200, 0.5), 0.6); write("rubber-stamp.wav", fades(a, 0, 60), -5); }
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 16), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
