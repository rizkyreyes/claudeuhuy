// Procedural breaker foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from iron: deny-thud, spark-crackle, button-click, room-tone, thermo-click, element-hum, power-down. New: breaker-snap, breaker-reset,
// arc-zap, short-bang, fire-crackle, heater-fan, dryer-whir, nail-tap, breaker-drop, wire-sizzle, coil-clunk.
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
// spark-crackle: a short electric spark, 0.5 s
{ const a = len(0.5), r = rng(9021), h = svf(noise(a.length, 9022), 6000, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (Math.abs(r()) > 0.93 ? 1 : 0.08) * Math.exp(-t * 9); }
  write("spark-crackle.wav", fades(a, 0, 120), -6); }
// button-click: plastic push button, 0.25 s
{ const a = len(0.25); add(a, svf(noise(300, 9031), 3000, 0.5), 0.8); modal(a, 0.002, 1800, [[1, 1, 1], [2.4, 0.4, 2]], 0.3, 60); write("button-click.wav", fades(a, 0, 60), -6); }
// room-tone: quiet hallway (low air + faint hum), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 9051), 300, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] + 0.05 * Math.sin(2 * Math.PI * 120 * t); }
  write("room-tone.wav", fades(a, 300, 300), -20); }
// thermo-click: bimetal contacts snapping (sharp metallic tick), 0.3 s
{ const a = len(0.3); modal(a, 0.0, 3400, [[1, 1, 1], [2.2, 0.5, 2], [3.7, 0.3, 3]], 0.8, 80); add(a, svf(noise(300, 541), 6000, 0.5), 0.6);
  write("thermo-click.wav", fades(a, 0, 60), -6); }
// element-hum: the heating element on (low mains hum + warm air), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 551), 400, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * Math.sin(2 * Math.PI * 60 * t) + 0.25 * Math.sin(2 * Math.PI * 120 * t) + 0.6 * lo[i]; }
  write("element-hum.wav", fades(a, 200, 200), -18); }
// power-down: auto shut-off (two falling blips + relay tick), 0.9 s
{ const a = len(0.9); modal(a, 0.0, 2600, [[1, 1, 1]], 0.4, 90);
  for (const [t0, f] of [[0.08, 1320], [0.32, 880]]) { const i0 = Math.round(t0 * SR); for (let i = i0; i < i0 + SR * 0.18; i++) { const t = (i - i0) / SR; a[i] += 0.5 * Math.sin(2 * Math.PI * f * t) * Math.min(1, t * 200) * Math.exp(-t * 14); } }
  write("power-down.wav", fades(a, 0, 120), -9); }
// breaker-snap: spring-loaded trip (hard plastic snap + metal ring + body thump), 0.45 s
{ const a = len(0.45); add(a, svf(noise(600, 101), 4200, 0.4), 1.0); modal(a, 0.001, 2300, METAL, 0.35, 45); thump(a, 0.004, 110, 0.6, 30);
  write("breaker-snap.wav", fades(a, 0, 80), -3); }
// breaker-reset: handle pushed to OFF (stiff click), 0.3 s
{ const a = len(0.3); add(a, svf(noise(500, 111), 2600, 0.5), 0.9); thump(a, 0.002, 160, 0.4, 40); modal(a, 0.002, 1500, METAL, 0.15, 60);
  write("breaker-reset.wav", fades(a, 0, 60), -5); }
// arc-zap: buzzing electric arc with crackle, 1.4 s
{ const a = len(1.4), r = rng(121), h = svf(noise(a.length, 122), 5000, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; const env = Math.min(1, t / 0.01) * (t < 1.0 ? 1 : Math.exp(-(t - 1.0) * 9));
    a[i] = env * (0.5 * Math.sign(Math.sin(2 * Math.PI * 120 * t)) * (0.6 + 0.4 * Math.abs(r())) * 0.35 + h[i] * (Math.abs(r()) > 0.85 ? 1 : 0.25)); }
  write("arc-zap.wav", fades(a, 0, 100), -4); }
// short-bang: a short circuit (loud pop + crackle tail), 0.8 s
{ const a = len(0.8); thump(a, 0, 70, 1.0, 9); add(a, svf(noise(SR * 0.05, 131), 3000, 0.3), 1.2);
  const h = svf(noise(a.length, 132), 6000, 0.3, "high"), r = rng(133);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.5 * h[i] * (Math.abs(r()) > 0.9 ? 1 : 0.1) * Math.exp(-t * 5); }
  write("short-bang.wav", fades(a, 0, 120), -2); }
// fire-crackle: small fire inside the wall (roar + pops), 2.5 s (loops)
{ const a = len(2.5), lo = svf(noise(a.length, 141), 400, 0.5, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.6 * lo[i];
  blips(a, 26, 0.05, 2.4, 900, 2600, 0.5, 142, 120);
  write("fire-crackle.wav", fades(a, 200, 200), -10); }
// heater-fan: space heater fan + element, 2.9 s (loops)
{ const a = len(2.9), b = svf(noise(a.length, 151), 700, 0.7);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = b[i] + 0.15 * Math.sin(2 * Math.PI * 95 * t); }
  write("heater-fan.wav", fades(a, 150, 150), -16); }
// dryer-whir: hair dryer motor + air, 1.5 s
{ const a = len(1.5), b = svf(noise(a.length, 161), 2400, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.min(1, t / 0.15) * (b[i] + 0.25 * Math.sin(2 * Math.PI * 410 * t)); }
  write("dryer-whir.wav", fades(a, 0, 250), -12); }
// nail-tap: hammer drives a nail (two taps), 0.6 s
{ const a = len(0.6); for (const t0 of [0.0, 0.28]) { add(a, svf(noise(400, 171 + t0 * 10), 3500, 0.4), 0.8, t0); modal(a, t0 + 0.001, 3100, METAL, 0.3, 50); thump(a, t0, 140, 0.35, 35); }
  write("nail-tap.wav", fades(a, 0, 80), -5); }
// breaker-drop: plastic breaker hits the floor and bounces, 0.7 s
{ const a = len(0.7); for (const [t0, g] of [[0, 1], [0.22, 0.45], [0.38, 0.2]]) { add(a, svf(noise(700, 181 + g * 9), 1800, 0.5), g, t0); thump(a, t0, 220, 0.4 * g, 40); }
  write("breaker-drop.wav", fades(a, 0, 100), -5); }
// wire-sizzle: overheating insulation (hiss + crackle), 2.5 s (loops)
{ const a = len(2.5), h = svf(noise(a.length, 191), 5000, 0.5, "high"), r = rng(192);
  for (let i = 0; i < a.length; i++) a[i] = 0.3 * h[i] + 0.6 * h[i] * (Math.abs(r()) > 0.97 ? 1 : 0);
  write("wire-sizzle.wav", fades(a, 200, 200), -14); }
// coil-clunk: plunger yanked into the coil (magnetic clunk + 60 Hz buzz), 0.6 s
{ const a = len(0.6); thump(a, 0, 90, 0.9, 14); modal(a, 0.002, 900, METAL, 0.3, 30);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.25 * Math.sin(2 * Math.PI * 120 * t) * Math.exp(-t * 4); }
  write("coil-clunk.wav", fades(a, 0, 100), -4); }
