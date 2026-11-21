// Procedural jeans-rivet foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, dust-crumble. New: cloth-rip, coin-drop, cloth-slide, metal-clink, stretch-creak, thread-snap, rivet-clank, hammer-hit, spark-crackle, paper-slide, tick-tock, room-tone.
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
// dust-crumble: grit and chips falling, 1.0 s
{ const a = len(1.0), h = svf(noise(a.length, 7031), 3500, 0.5), r = rng(7032);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.3 * h[i] * Math.exp(-t * 3); }
  for (let k = 0; k < 26; k++) modal(a, 0.6 * Math.abs(r()), 1500 + 2500 * Math.abs(r()), [[1, 1, 1], [2.3, 0.4, 2]], 0.08, 60);
  write("dust-crumble.wav", fades(a, 5, 200), -9); }
// cloth-rip: denim tearing, 0.9 s of dense crackly noise bursts
{ const a = len(0.9), r = rng(9101), h = svf(noise(a.length, 9102), t => 2600 - 1400 * t, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR, g = (Math.abs(r()) > 0.55 ? 1 : 0.35) * Math.min(1, t * 30) * Math.exp(-t * 2.2); a[i] = h[i] * g; }
  add(a, svf(noise(a.length, 9103), 400, 0.5, "low"), 0.25); write("cloth-rip.wav", fades(a, 2, 150), -5); }
// coin-drop: 5 small metal ticks bouncing, 1.2 s
{ const a = len(1.2), r = rng(9201); let t = 0.02, gap = 0.22;
  for (let k = 0; k < 7; k++) { modal(a, t, 2400 + 900 * Math.abs(r()), METAL, 0.5 * Math.pow(0.7, k), 18); t += gap; gap *= 0.72; }
  write("coin-drop.wav", fades(a, 0, 150), -7); }
// cloth-slide: a tool sliding into a denim pocket, 0.8 s
{ const a = len(0.8), h = svf(noise(a.length, 9301), 1800, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.sin(Math.PI * t / 0.8); }
  write("cloth-slide.wav", fades(a, 20, 80), -12); }
// metal-clink: wrench settling, 0.6 s
{ const a = len(0.6); modal(a, 0, 1650, METAL, 0.8, 10); write("metal-clink.wav", fades(a, 0, 120), -8); }
// stretch-creak: thread under tension, 1.2 s rising creak
{ const a = len(1.2), r = rng(9401);
  for (let k = 0; k < 40; k++) { const ts = 1.1 * k / 40, i0 = Math.round(ts * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.02; i++) a[i] += (0.2 + 0.8 * ts) * Math.abs(r()) * Math.exp(-((i - i0) / SR) * 300); }
  write("stretch-creak.wav", fades(svf(a, t => 700 + 900 * t, 0.3), 30, 100), -10); }
// thread-snap: sharp pluck, 0.4 s
{ const a = len(0.4); modal(a, 0, 980, [[1, 1, 1], [2.1, 0.5, 2]], 1, 22); add(a, svf(noise(1800, 9501), 4000, 0.5), 0.8); write("thread-snap.wav", fades(a, 0, 80), -4); }
// rivet-clank: small copper part landing, 0.5 s
{ const a = len(0.5); modal(a, 0, 1900, METAL, 0.9, 14); thump(a, 0, 160, 0.4, 25); write("rivet-clank.wav", fades(a, 0, 100), -6); }
// hammer-hit: steel punch on copper, 0.9 s
{ const a = len(0.9); thump(a, 0, 70, 1, 9); modal(a, 0, 1250, METAL, 0.7, 7); add(a, svf(noise(3000, 9601), 3000, 0.5), 0.6); write("hammer-hit.wav", fades(a, 0, 150), -3); }
// spark-crackle: 0.7 s of tiny crackles
{ const a = len(0.7); blips(a, 60, 0, 0.6, 3000, 6000, 0.25, 9701, 120); write("spark-crackle.wav", fades(a, 0, 150), -10); }
// paper-slide: parchment sliding on wood, 0.7 s
{ const a = len(0.7), h = svf(noise(a.length, 9801), 3200, 0.7);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.sin(Math.PI * t / 0.7) * (0.7 + 0.3 * Math.sin(t * 60)); }
  write("paper-slide.wav", fades(a, 10, 100), -11); }
// tick-tock: pocket watch ticks, 2 s (5 ticks per second)
{ const a = len(2.0); for (let k = 0; k < 10; k++) modal(a, 0.2 * k, k % 2 ? 3100 : 2700, [[1, 1, 1], [1.9, 0.4, 2]], 0.6, 90); write("tick-tock.wav", fades(a, 0, 100), -14); }
// room-tone: quiet workshop air, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 9901), 260, 0.3, "low"); for (let i = 0; i < a.length; i++) a[i] = lo[i]; write("room-tone.wav", fades(a, 300, 300), -20); }
