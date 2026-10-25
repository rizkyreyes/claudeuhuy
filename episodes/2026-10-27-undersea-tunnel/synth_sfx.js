// Procedural TBM / tunnel foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Steel uses inharmonic modal partials; rumble, grind, water and pumps are modulated tones + filtered noise. Loops fade in/out.
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

// tbm-rumble: 8 s machine bed (low drive hum, cutterhead rumble, distant hydraulics)
{ const a = len(8), rum = svf(noise(a.length, 41), 120, 0.7, "low"), mid = svf(noise(a.length, 42), 500, 1.0);
  for (let i = 0; i < a.length; i++) { const t = i / SR;
    a[i] = 0.4 * Math.sin(2 * Math.PI * 45 * t) + 0.22 * Math.sin(2 * Math.PI * 90 * t + 0.4) + 0.7 * rum[i] * (0.75 + 0.25 * Math.sin(2 * Math.PI * 0.55 * t))
      + 0.12 * mid[i] * (0.6 + 0.4 * Math.sin(2 * Math.PI * 0.9 * t)); }
  write("tbm-rumble.wav", fades(a, 600, 600), -14); }
// rock-grind: 3 s of disc cutters rolling and cracking rock (grinding noise + random cracks)
{ const a = len(3), g = svf(noise(a.length, 43), t => 700 + 300 * Math.sin(t * 5), 0.6), lo = svf(noise(a.length, 44), 200, 0.8, "low"), r = rng(45);
  for (let i = 0; i < a.length; i++) a[i] = 0.35 * g[i] + 0.5 * lo[i];
  for (let k = 0; k < 40; k++) { const t = 0.05 + 2.85 * (k / 40) + 0.03 * r(); modal(a, t, 1800 + 900 * r(), STEEL, 0.06, 90); }
  write("rock-grind.wav", fades(a, 200, 500), -10); }
// chip-fall: 1.5 s of rock chips tumbling down
{ const a = len(1.5), r = rng(46);
  for (let k = 0; k < 45; k++) { const t = 0.02 + 1.3 * Math.pow(k / 45, 0.8) + 0.02 * r(); modal(a, t, 1300 + 900 * r(), [[1, 1, 1], [2.7, 0.4, 1.8]], 0.25 * (0.6 + 0.4 * r()), 110); }
  add(a, svf(noise(a.length, 47), 2500, 0.8), 0.06); write("chip-fall.wav", fades(a, 0, 250), -9); }
// water-rush: 2 s of water forcing in (rising band noise)
{ const a = len(2), n = svf(noise(a.length, 48), t => 600 + 1400 * Math.min(1, t / 0.5), 0.5), lo = svf(noise(a.length, 49), 180, 0.7, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.6 * n[i] + 0.5 * lo[i]) * Math.min(1, t / 0.25); }
  write("water-rush.wav", fades(a, 20, 500), -9); }
// slurry-pump: 3 s thick pumped slurry (low chug + wet gurgle)
{ const a = len(3), wet = svf(noise(a.length, 50), t => 320 + 160 * Math.sin(2 * Math.PI * 2.4 * t), 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR, ch = Math.pow(0.5 + 0.5 * Math.sin(2 * Math.PI * 2.4 * t), 3);
    a[i] = 0.5 * Math.sin(2 * Math.PI * 38 * t) * ch + 0.5 * wet[i]; }
  write("slurry-pump.wav", fades(a, 250, 600), -10); }
// segment-clunk: a concrete segment seating against the ring (dull concrete knock + steel tick)
{ const a = len(0.6); thump(a, 0, 85, 1, 14); modal(a, 0.004, 640, STEEL, 0.25, 22); add(a, svf(noise(3000, 51), 900, 0.6), 0.4); write("segment-clunk.wav", fades(a, 0, 80), -5); }
// hydraulic-push: 2.5 s of jacks under load (hiss + strained low tone)
{ const a = len(2.5), h = svf(noise(a.length, 52), 3200, 0.7), lo = svf(noise(a.length, 53), 140, 0.8, "low"); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (60 + 8 * Math.min(1, t / 2)) / SR;
    a[i] = 0.25 * h[i] * Math.exp(-t * 1.2) + 0.45 * Math.sin(ph) * Math.min(1, t / 0.2) + 0.4 * lo[i]; }
  write("hydraulic-push.wav", fades(a, 20, 500), -9); }
// shell-off: the shield's front half lifting away (heavy steel scrape + clank)
{ const a = len(0.9), s = svf(noise(a.length, 54), t => 900 + 900 * Math.min(1, t / 0.6), 0.5);
  for (let i = 0; i < a.length; i++) a[i] = s[i] * Math.exp(-i / SR * 3.0) * 0.6; modal(a, 0, 260, STEEL, 0.6, 9); write("shell-off.wav", fades(a, 3, 150), -7); }
// gasket-squeeze: rubber compressing (short low squeak)
{ const a = len(0.4); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (420 - 260 * t / 0.4) / SR; a[i] = Math.sin(ph) * Math.sin(Math.PI * t / 0.4) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 38 * t)); }
  write("gasket-squeeze.wav", fades(a, 10, 60), -9); }
// grout-pour: 2 s of grout pumped into the gap (thick low flow)
{ const a = len(2), f = svf(noise(a.length, 55), 260, 0.4), lo = svf(noise(a.length, 56), 90, 0.7, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.6 * f[i] + 0.5 * lo[i];
  write("grout-pour.wav", fades(a, 200, 600), -11); }
// breakthrough: last rock crumbling as the two drives meet (crumble + deep hit)
{ const a = len(1.2), r = rng(57); thump(a, 0.05, 55, 1, 5);
  for (let k = 0; k < 30; k++) modal(a, 0.02 + 0.9 * Math.pow(k / 30, 0.7), 900 + 700 * r(), [[1, 1, 1], [2.7, 0.4, 1.8]], 0.12, 90);
  add(a, svf(noise(a.length, 58), 700, 0.8), 0.25); write("breakthrough.wav", fades(a, 0, 300), -4); }
// earth-thud: rock closing over the buried machine
{ const a = len(0.9); thump(a, 0, 42, 1, 6); add(a, svf(noise(8000, 59), 300, 0.7, "low"), 0.7); write("earth-thud.wav", fades(a, 0, 150), -4); }
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 16), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
