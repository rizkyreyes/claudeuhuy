// Procedural cofferdam foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Steel uses inharmonic modal partials; water/mud/concrete are filtered noise with shaped envelopes.
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

// river-flow: 6 s loopable murmur (hook ambience)
{ const n = noise(SR * 6, 1), lo = svf(n, 420, 0.7, "low"), hi = svf(noise(SR * 6, 2), t => 1800 + 600 * Math.sin(t * 2.1), 1.2);
  const a = len(6); for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * 0.9 + hi[i] * 0.35 * (0.6 + 0.4 * Math.sin(t * 5.3) * Math.sin(t * 1.7)); }
  write("river-flow.wav", fades(a, 400, 400), -14); }
// steel-clank: frame / sheet hitting steel
{ const a = len(0.5); modal(a, 0, 420, STEEL, 1, 9); thump(a, 0, 90, 0.6, 18); add(a, svf(noise(2400, 3), 3000, 0.6), 0.5); write("steel-clank.wav", fades(a, 0, 60), -6); }
// sheet-drop: a sheet sliding into its slot, short ring
{ const a = len(0.4), s = svf(noise(a.length, 4), t => 2500 - 2000 * Math.min(1, t / 0.12), 0.8);
  for (let i = 0; i < a.length; i++) a[i] = s[i] * Math.exp(-i / SR * 14) * 0.6; modal(a, 0.09, 610, STEEL, 0.5, 14); write("sheet-drop.wav", fades(a, 2, 50), -8); }
// vibro-hammer: 3.2 s buzzing drive (amplitude-modulated low hum + grit)
{ const a = len(3.2), grit = svf(noise(a.length, 5), 900, 1.0);
  for (let i = 0; i < a.length; i++) { const t = i / SR, am = 0.55 + 0.45 * Math.sin(2 * Math.PI * 24 * t);
    a[i] = am * (0.7 * Math.sin(2 * Math.PI * 48 * t) + 0.35 * Math.sin(2 * Math.PI * 96 * t + 0.4) + 0.3 * grit[i]); }
  write("vibro-hammer.wav", fades(a, 120, 300), -8); }
// pile-thud: heavy blow on a pile
{ const a = len(0.6); thump(a, 0, 55, 1, 9); modal(a, 0, 260, STEEL, 0.25, 16); add(a, svf(noise(3000, 6), 600, 0.8), 0.5); write("pile-thud.wav", fades(a, 0, 80), -4); }
// mud-slurp: wet suction as mud is lifted
{ const a = len(0.7), s = svf(noise(a.length, 7), t => 250 + 900 * Math.min(1, t / 0.35), 0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.sin(Math.PI * Math.min(1, t / 0.7)) * (1 + 0.6 * Math.sin(2 * Math.PI * 9 * t)); }
  write("mud-slurp.wav", fades(a, 10, 80), -9); }
// concrete-pour: 7.6 s thick gloopy stream through the pipe
{ const a = len(7.6), base = svf(noise(a.length, 8), 300, 0.9, "low"), glop = noise(a.length, 9);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = base[i] * (0.8 + 0.2 * Math.sin(t * 3.1)); }
  const r = rng(10); for (let k = 0; k < 60; k++) { const t0 = Math.abs(r()) * 7.2; thump(a, t0, 70 + Math.abs(r()) * 60, 0.15, 25); }
  write("concrete-pour.wav", fades(a, 300, 600), -10); }
// pump-drone: 4 s motor hum with a little rattle
{ const a = len(4), rat = svf(noise(a.length, 11), 2200, 1.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR, up = Math.min(1, t / 0.5);
    a[i] = up * (0.6 * Math.sin(2 * Math.PI * (60 + 20 * up) * t) + 0.3 * Math.sin(2 * Math.PI * (120 + 40 * up) * t) + 0.12 * rat[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 30 * t))); }
  write("pump-drone.wav", fades(a, 20, 400), -10); }
// water-drain: 2.6 s gurgle falling in pitch
{ const a = len(2.6), s = svf(noise(a.length, 12), t => 1400 - 900 * Math.min(1, t / 2.6), 2.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (0.6 + 0.4 * Math.abs(Math.sin(2 * Math.PI * 6 * t))); }
  write("water-drain.wav", fades(a, 150, 500), -10); }
// water-rush: 1.8 s surge (water pushing up / river closing back in)
{ const a = len(1.8), s = svf(noise(a.length, 13), t => 300 + 2500 * Math.min(1, t / 0.5), 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (t < 0.45 ? t / 0.45 : Math.exp(-(t - 0.45) * 2.4)); }
  write("water-rush.wav", fades(a, 5, 200), -7); }
// steel-creak: strained steel under pressure
{ const a = len(1.4); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 140 + 60 * Math.sin(t * 2.3) + 25 * Math.sin(t * 17); ph += 2 * Math.PI * f / SR;
    const saw = (ph / Math.PI) % 2 - 1; a[i] = saw * Math.sin(Math.PI * t / 1.4) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 11 * t)); }
  write("steel-creak.wav", fades(svf(a, 900, 0.9), 30, 120), -10); }
// wood-knock: a post going in
{ const a = len(0.4); modal(a, 0, 230, [[1, 1, 1], [2.7, 0.4, 2.2], [5.1, 0.15, 3]], 1, 22); add(a, svf(noise(900, 14), 1800, 0.7), 0.4); write("wood-knock.wav", fades(a, 0, 40), -6); }
// splash: front half falling away / piles entering the water
{ const a = len(0.9), s = svf(noise(a.length, 15), t => 4000 - 3000 * Math.min(1, t / 0.6), 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (t < 0.03 ? t / 0.03 : Math.exp(-(t - 0.03) * 5)); }
  thump(a, 0, 80, 0.5, 14); write("splash.wav", fades(a, 0, 100), -7); }
// deny-thud: stinger for "not yet" / "from below"
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 16), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
