// Procedural toilet foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Porcelain slide, handle click, chain rattle, flapper thunk, water rush, siphon suck, gurgle, pour, trickle, fill hiss, bubble pop, gas hiss, deny thud.
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
// porcelain-slide: the front half sliding off (ceramic scrape, light knock)
{ const a = len(0.9), s = svf(noise(a.length, 41), t => 900 + 1500 * Math.min(1, t / 0.7), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.45 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  modal(a, 0.7, 1300, [[1, 1, 1], [2.3, 0.4, 1.8]], 0.25, 30); write("porcelain-slide.wav", fades(a, 20, 120), -7); }
// handle-click: chrome lever pressed
{ const a = len(0.3); modal(a, 0, 2400, METAL, 0.5, 60); thump(a, 0, 160, 0.4, 60); modal(a, 0.09, 1800, METAL, 0.25, 70); write("handle-click.wav", fades(a, 0, 60), -6); }
// chain-rattle: small links shaking
{ const a = len(0.7), r = rng(43);
  for (let k = 0; k < 14; k++) modal(a, 0.02 + 0.5 * Math.abs(r()), 3000 + 2500 * Math.abs(r()), METAL, 0.12, 90);
  write("chain-rattle.wav", fades(a, 0, 120), -9); }
// flapper-thunk: rubber flap closing on the seat under water
{ const a = len(0.45); thump(a, 0, 85, 0.9, 16); add(a, svf(noise(8000, 44), 300, 0.5, "low"), 0.4); blips(a, 3, 0.03, 0.2, 300, 500, 0.15, 45); write("flapper-thunk.wav", fades(a, 0, 100), -5); }
// water-rush: tank emptying into the bowl, 4 s
{ const a = len(4), n = svf(noise(a.length, 46), 900, 0.35), lo = svf(noise(a.length, 47), 180, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR, env = Math.min(1, t / 0.15) * (t < 2.8 ? 1 : Math.max(0, 1 - (t - 2.8) / 1.2));
    a[i] = (0.55 * n[i] + 0.6 * lo[i]) * env * (0.85 + 0.15 * Math.sin(2 * Math.PI * 5 * t)); }
  blips(a, 40, 0.2, 3.4, 250, 700, 0.08, 48); write("water-rush.wav", fades(a, 10, 300), -10); }
// siphon-suck: the bowl pulled down the trap (falling filter + low swirl)
{ const a = len(3.5), n = svf(noise(a.length, 49), t => 1400 - 1000 * Math.min(1, t / 3), 0.25), lo = svf(noise(a.length, 50), 120, 0.3, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.6 * n[i] + 0.7 * lo[i]) * Math.min(1, t / 0.3) * Math.sin(Math.PI * Math.min(1, t / 3.5)) * (0.8 + 0.2 * Math.sin(2 * Math.PI * 7 * t)); }
  write("siphon-suck.wav", fades(a, 50, 400), -10); }
// gurgle: air breaking the siphon (big glugs)
{ const a = len(1.6); blips(a, 18, 0.0, 1.2, 120, 320, 0.6, 52, 14); add(a, svf(noise(a.length, 53), 250, 0.4, "low"), 0.25); write("gurgle.wav", fades(a, 10, 300), -5); }
// water-pour: a cup poured into the bowl
{ const a = len(1.4), n = svf(noise(a.length, 54), 1600, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.sin(Math.PI * Math.min(1, t / 1.3)); }
  blips(a, 20, 0.1, 1.2, 500, 1200, 0.15, 55, 40); write("water-pour.wav", fades(a, 30, 200), -9); }
// trickle: thin stream over the bend / into the bowl
{ const a = len(2.5); blips(a, 70, 0.0, 2.4, 600, 1500, 0.2, 56, 45); add(a, svf(noise(a.length, 57), 2200, 0.5), 0.12); write("trickle.wav", fades(a, 100, 400), -11); }
// fill-hiss: the fill valve running (pressurised hiss), 4 s
{ const a = len(4), n = svf(noise(a.length, 58), 3500, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.min(1, t / 0.2) * (0.9 + 0.1 * Math.sin(2 * Math.PI * 11 * t)); }
  write("fill-hiss.wav", fades(a, 20, 500), -14); }
// bubble-pop: one air bubble
{ const a = len(0.25); blips(a, 1, 0, 0.001, 380, 380, 0.8, 59, 22); write("bubble-pop.wav", fades(a, 0, 60), -8); }
// gas-hiss: sewer gas drifting up (low airy whoosh)
{ const a = len(1.5), n = svf(noise(a.length, 60), t => 400 + 300 * t, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * Math.sin(Math.PI * t / 1.5); }
  write("gas-hiss.wav", fades(a, 60, 300), -12); }
// deny-thud: failure stinger
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
