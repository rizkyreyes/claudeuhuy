// Procedural lock foley (48 kHz 16-bit mono WAV). Metallic sounds use inharmonic modal partials.
const fs = require("fs"), path = require("path");
const SR = 48000, OUT = __dirname;
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
const fade = (a, ms) => { const n = SR * ms / 1000; for (let i = 0; i < n; i++) a[a.length - 1 - i] *= i / n; return a; };
// modal metal ping: sum of inharmonic partials with individual decays
function modal(a, t0, f0, partials, amp, decay) {
  const i0 = Math.round(t0 * SR);
  for (let i = i0; i < a.length; i++) {
    const t = (i - i0) / SR; let v = 0;
    for (const [ratio, g, d] of partials) v += g * Math.sin(2 * Math.PI * f0 * ratio * t) * Math.exp(-t * decay * d);
    a[i] += amp * v; if (t > 6 / decay) break;
  }
}
const PIN = [[1, 1, 1], [2.76, 0.5, 1.6], [5.4, 0.25, 2.4], [8.93, 0.12, 3.2]];
const len = s => new Float32Array(Math.round(SR * s));

// pin click: bright tick + tiny modal ring (several variants)
for (let v = 0; v < 4; v++) {
  const a = len(0.12), n = svf(noise(a.length, 10 + v), 6500, 0.5, "high");
  for (let i = 0; i < 300; i++) a[i] += n[i] * (1 - i / 300) * 0.8;
  modal(a, 0, 2600 + v * 230, PIN, 0.35, 60);
  write(`pin-click-${v + 1}.wav`, fade(a, 8), -10);
}
// metal tick (key stops at the keyway)
{ const a = len(0.25); modal(a, 0, 1850, PIN, 1, 22); const n = noise(400, 3); for (let i = 0; i < 400; i++) a[i] += n[i] * (1 - i / 400) * 0.5; write("metal-tick.wav", fade(a, 20), -8); }
// slice "shing": rising band sweep into a bright ring (peak at 0.32 s)
{
  const a = len(1.4), s = svf(noise(a.length, 21), t => 800 + 7000 * Math.min(1, t / 0.32), 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (t < 0.32 ? Math.pow(t / 0.32, 2) : Math.exp(-(t - 0.32) * 9)); }
  modal(a, 0.32, 3100, [[1, 1, 1], [1.5, 0.6, 1.3], [2.3, 0.4, 1.8], [3.7, 0.2, 2.5]], 0.9, 4.5);
  write("slice-shing.wav", fade(a, 60), -6);
}
// spring boing: vibrato-modulated low ring + coil rattle
{
  const a = len(0.7); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (220 + 60 * Math.sin(2 * Math.PI * 14 * t) * Math.exp(-t * 4)) / SR; a[i] = Math.sin(ph) * Math.exp(-t * 7) * 0.7; }
  modal(a, 0, 1400, PIN, 0.25, 30); write("spring-boing.wav", fade(a, 40), -12);
}
// key scrape: band noise with a ratchet grain (insertion), 2.6 s
{
  const n = len(4.6), b = svf(noise(n.length, 31), 3200, 0.9), a = len(4.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR, grain = 0.55 + 0.45 * Math.abs(Math.sin(2 * Math.PI * 38 * t)); a[i] = b[i] * grain * Math.min(1, t / 0.06) * (t > 4.4 ? (4.6 - t) / 0.2 : 1); }
  write("key-scrape.wav", a, -18);
}
// plug turn: smooth rotational friction + detent click at the end (0.8 s)
{
  const a = len(0.9), b = svf(noise(a.length, 41), 1800, 1.1);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = b[i] * 0.5 * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  modal(a, 0.74, 1300, PIN, 0.9, 30); write("plug-turn.wav", fade(a, 30), -10);
}
// bolt clunk: low body + metal slap
{
  const a = len(0.7); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (95 + 60 * Math.exp(-t * 30)) / SR; a[i] = (Math.sin(ph) + 0.4 * Math.sin(2 * ph)) * Math.exp(-t * 11); }
  modal(a, 0, 780, PIN, 0.6, 18); const n = noise(500, 51); for (let i = 0; i < 500; i++) a[i] += n[i] * (1 - i / 500) * 0.7;
  write("bolt-clunk.wav", fade(a, 30), -6);
}
// denial: dull double thud + low buzz
{
  const a = len(0.6);
  for (const t0 of [0, 0.16]) { const i0 = t0 * SR; let ph = 0; for (let i = i0; i < a.length; i++) { const t = (i - i0) / SR; ph += 2 * Math.PI * 70 / SR; a[i] += (Math.sign(Math.sin(ph)) * 0.25 + Math.sin(ph)) * Math.exp(-t * 16); } }
  write("deny-thud.wav", fade(a, 40), -8);
}
// wood knock: resonant mid body
{ const a = len(0.4); modal(a, 0, 420, [[1, 1, 1], [2.1, 0.5, 1.8], [3.4, 0.3, 2.5]], 1, 28); modal(a, 0.13, 470, [[1, 1, 1], [2.1, 0.5, 1.8]], 0.7, 30); write("wood-knock.wav", fade(a, 30), -8); }
// ambient pad bed: soft minor chord drone with slow movement (76 s), very quiet in the mix
{
  const a = len(76), f = [110, 130.81, 164.81, 220, 261.63], r = rng(77);
  const ph = f.map(() => r() * 6.28);
  for (let i = 0; i < a.length; i++) {
    const t = i / SR; let v = 0;
    f.forEach((fr, k) => { v += Math.sin(2 * Math.PI * fr * (1 + 0.002 * Math.sin(0.1 * t + k)) * t + ph[k]) * (0.6 + 0.4 * Math.sin(0.07 * t * (k + 1) + k)) / (k + 1.5); });
    a[i] = v * Math.min(1, t / 2) * Math.min(1, (76 - t) / 2);
  }
  const lp = svf(a, 1200, 1.0, "low"); write("pad-bed.wav", lp, -20);
}
