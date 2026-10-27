// Procedural elevator foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Rope strain + snap, motor hum, drum brake clamp, magnet release, power down, governor whirr / pawl / lock, lever, wedge bite,
// rail grind, counterweight landing, buffer spring, oil hiss, wooden hoist creak, rope cut, ratchet catch, deny thud, wall drop.
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
// rope-strain: steel ropes taking load (low creak + a few wire ticks)
{ const a = len(1.2), lo = svf(noise(a.length, 1), 180, 0.3), r = rng(2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * lo[i] * Math.sin(Math.PI * t / 1.2); }
  for (let k = 0; k < 8; k++) modal(a, 1.1 * Math.abs(r()), 1800 + 1500 * Math.abs(r()), METAL, 0.08, 60);
  write("rope-strain.wav", fades(a, 50, 200), -10); }
// motor-hum: traction motor (mains hum + whine)
{ const a = len(4), w = svf(noise(a.length, 3), 900, 0.2); let p1 = 0, p2 = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; p1 += 2 * Math.PI * 100 / SR; p2 += 2 * Math.PI * (420 + 30 * Math.min(1, t)) / SR;
    a[i] = 0.4 * Math.sin(p1) + 0.12 * Math.sin(2 * p1) + 0.12 * Math.sin(p2) + 0.08 * w[i]; }
  write("motor-hum.wav", fades(a, 300, 600), -14); }
// brake-clamp: shoes slam the drum (metal thunk + ring)
{ const a = len(0.6); thump(a, 0, 70, 1, 14); modal(a, 0.0, 620, METAL, 0.35, 18); add(a, svf(noise(3000, 4), 2500, 0.5), 0.4);
  write("brake-clamp.wav", fades(a, 0, 120), -4); }
// magnet-release: solenoid clack (brake lifts)
{ const a = len(0.3); modal(a, 0, 1400, METAL, 0.4, 40); thump(a, 0, 120, 0.5, 30); write("magnet-release.wav", fades(a, 0, 60), -6); }
// power-down: hum sliding down + relay click
{ const a = len(0.9); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * 100 * Math.exp(-t * 3) / SR; a[i] = 0.5 * Math.sin(ph) * Math.exp(-t * 2.5); }
  modal(a, 0, 2200, METAL, 0.3, 60); write("power-down.wav", fades(a, 0, 150), -6); }
// rope-snap: steel wire breaking (crack + whip + ring)
{ const a = len(0.9), cr = svf(noise(a.length, 5), 3000, 0.4), r = rng(6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.9 * cr[i] * Math.exp(-t * 30); }
  for (let k = 0; k < 3; k++) modal(a, 0.02 * k, 900 + 400 * k, METAL, 0.3, 6);
  const wh = svf(noise(a.length, 7), t => 4000 - 3500 * Math.min(1, t / 0.5), 0.4); add(a, wh.map((v, i) => v * Math.exp(-i / SR * 6)), 0.4);
  write("rope-snap.wav", fades(a, 0, 200), -2); }
// cw-land: counterweight hitting its buffer far below
{ const a = len(0.7); thump(a, 0, 45, 1, 8); add(a, svf(noise(5000, 8), 300, 0.6, "low"), 0.6); write("cw-land.wav", fades(a, 0, 150), -8); }
// governor-whirr: small sheave spinning up (pitch rises)
{ const a = len(3.5), n = svf(noise(a.length, 9), t => 300 + 500 * t, 0.15); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (6 + 5 * t) / SR; a[i] = n[i] * (0.6 + 0.4 * Math.sin(ph)); }
  write("governor-whirr.wav", fades(a, 400, 400), -12); }
// pawl-clack: the pawl dropping into a tooth
{ const a = len(0.25); modal(a, 0, 1900, METAL, 0.5, 45); modal(a, 0.05, 2300, METAL, 0.3, 50); write("pawl-clack.wav", fades(a, 0, 40), -5); }
// governor-lock: hard stop of the sheave
{ const a = len(0.5); thump(a, 0, 90, 1, 16); modal(a, 0, 800, METAL, 0.4, 14); write("governor-lock.wav", fades(a, 0, 100), -3); }
// lever-yank: rope jerks the lever (scrape + clunk)
{ const a = len(0.4), s = svf(noise(a.length, 10), 1600, 0.5);
  for (let i = 0; i < a.length; i++) a[i] = 0.4 * s[i] * Math.exp(-i / SR * 12);
  thump(a, 0.12, 110, 0.8, 22); modal(a, 0.12, 1100, METAL, 0.2, 30); write("lever-yank.wav", fades(a, 0, 60), -5); }
// wedge-bite: steel on steel, a sharp bite into a short screech
{ const a = len(0.7); modal(a, 0, 1300, METAL, 0.5, 12); thump(a, 0, 80, 0.6, 18);
  const sc = svf(noise(a.length, 11), 3200, 0.08); add(a, sc.map((v, i) => v * Math.min(1, i / SR / 0.05) * Math.exp(-i / SR * 4)), 0.5);
  write("wedge-bite.wav", fades(a, 0, 150), -3); }
// rail-grind: long braking screech, slowing down (pitch + level fall)
{ const a = len(7), r = rng(12);
  const sc = svf(noise(a.length, 13), t => 2600 - 1800 * (t / 7), 0.06), gr = svf(noise(a.length, 14), 600, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; const env = Math.min(1, t / 0.2) * (1 - 0.8 * t / 7); a[i] = env * (0.55 * sc[i] + 0.35 * gr[i] * (0.6 + 0.4 * r())); }
  write("rail-grind.wav", fades(a, 50, 800), -10); }
// buffer-spring: heavy coil compressing (thud + boing)
{ const a = len(0.9); thump(a, 0, 55, 1, 9); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (180 - 60 * t) / SR; a[i] += 0.3 * Math.sin(ph) * Math.exp(-t * 4) * (1 + 0.5 * Math.sin(2 * Math.PI * 9 * t)); }
  write("buffer-spring.wav", fades(a, 0, 150), -4); }
// oil-hiss: oil forced through the buffer orifice
{ const a = len(0.8), h = svf(noise(a.length, 15), 1800, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.min(1, t / 0.05) * Math.exp(-t * 2.5); }
  write("oil-hiss.wav", fades(a, 0, 150), -12); }
// wood-creak: the 1854 platform being hoisted (creaks + rope groan)
{ const a = len(4), r = rng(16), lo = svf(noise(a.length, 17), 220, 0.3);
  for (let i = 0; i < a.length; i++) a[i] = 0.25 * lo[i];
  for (let k = 0; k < 10; k++) { const t0 = 3.6 * Math.abs(r()), f0 = 260 + 200 * Math.abs(r()), i0 = Math.round(t0 * SR);
    for (let i = i0; i < Math.min(a.length, i0 + SR * 0.3); i++) { const t = (i - i0) / SR; a[i] += 0.3 * Math.sign(Math.sin(2 * Math.PI * f0 * t)) * Math.sin(Math.PI * t / 0.3) * 0.5; } }
  write("wood-creak.wav", fades(a, 300, 400), -12); }
// rope-cut: hemp rope parting (crack + whip)
{ const a = len(0.6), cr = svf(noise(a.length, 18), 1800, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = cr[i] * Math.exp(-t * 18); }
  const wh = svf(noise(a.length, 19), t => 3000 - 2500 * Math.min(1, t / 0.4), 0.5); add(a, wh.map((v, i) => v * Math.exp(-i / SR * 8)), 0.35);
  write("rope-cut.wav", fades(a, 0, 120), -3); }
// ratchet-catch: spring ends slamming into the iron teeth
{ const a = len(0.5); thump(a, 0, 85, 1, 14); modal(a, 0, 950, METAL, 0.4, 20); modal(a, 0.04, 1250, METAL, 0.25, 25);
  write("ratchet-catch.wav", fades(a, 0, 100), -3); }
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
// slab-drop: the front wall dropping away (scrape + heavy thud)
{ const a = len(0.9), s = svf(noise(a.length, 21), 700, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * Math.exp(-t * 5); }
  thump(a, 0.12, 52, 1, 7); write("slab-drop.wav", fades(a, 5, 150), -5); }
