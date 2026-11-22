// Procedural hair-dryer-plug foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, water-rush. New: splash, mains-hum, relay-snap, spark-crackle, button-click, plug-pull, solenoid-thunk, room-tone, bar-rise.
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
// water-rush: water/air through a closed pipe, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 6021), 180, 0.35, "low"), mid = svf(noise(a.length, 6022), t => 620 + 90 * Math.sin(t * 2.3), 0.15);
  for (let i = 0; i < a.length; i++) a[i] = 0.9 * lo[i] + 0.35 * mid[i];
  write("water-rush.wav", fades(a, 250, 250), -11); }
// splash: a dryer hitting water (thump + spray), 1.2 s
{ const a = len(1.2); thump(a, 0, 70, 0.8, 9); const s = svf(noise(a.length, 9001), t => 2500 - 1500 * t, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.7 * s[i] * Math.exp(-t * 4) * Math.min(1, t * 80); }
  blips(a, 18, 0.15, 1.0, 500, 1400, 0.25, 9002, 25); write("splash.wav", fades(a, 0, 200), -4); }
// mains-hum: 60 Hz electric hum with buzz harmonics, 2 s (loops)
{ const a = len(2.0); for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(2 * Math.PI * 60 * t) + 0.5 * Math.sin(2 * Math.PI * 120 * t) + 0.25 * Math.sin(2 * Math.PI * 180 * t) + 0.12 * Math.sign(Math.sin(2 * Math.PI * 120 * t)); }
  write("mains-hum.wav", fades(a, 120, 120), -16); }
// relay-snap: contacts snapping open (sharp metallic click + small clack), 0.5 s
{ const a = len(0.5); add(a, svf(noise(600, 9011), 5000, 0.4), 1.0); modal(a, 0.004, 2400, METAL, 0.5, 40); modal(a, 0.03, 900, METAL, 0.3, 30);
  write("relay-snap.wav", fades(a, 0, 100), -3); }
// spark-crackle: a short electric spark, 0.5 s
{ const a = len(0.5), r = rng(9021), h = svf(noise(a.length, 9022), 6000, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (Math.abs(r()) > 0.93 ? 1 : 0.08) * Math.exp(-t * 9); }
  write("spark-crackle.wav", fades(a, 0, 120), -6); }
// button-click: plastic push button, 0.25 s
{ const a = len(0.25); add(a, svf(noise(300, 9031), 3000, 0.5), 0.8); modal(a, 0.002, 1800, [[1, 1, 1], [2.4, 0.4, 2]], 0.3, 60); write("button-click.wav", fades(a, 0, 60), -6); }
// plug-pull: plug sliding out of an outlet (scrape + release), 0.6 s
{ const a = len(0.6), s = svf(noise(a.length, 9041), 1400, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * s[i] * Math.min(1, t * 20) * Math.exp(-t * 6); }
  modal(a, 0.32, 1100, METAL, 0.4, 35); write("plug-pull.wav", fades(a, 5, 120), -6); }
// solenoid-thunk: electromagnet firing the plunger, 0.4 s
{ const a = len(0.4); thump(a, 0, 160, 0.9, 30); modal(a, 0.01, 650, METAL, 0.35, 25); write("solenoid-thunk.wav", fades(a, 0, 80), -4); }
// room-tone: small tiled bathroom (low air + faint hum), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 9051), 300, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] + 0.05 * Math.sin(2 * Math.PI * 120 * t); }
  write("room-tone.wav", fades(a, 300, 300), -20); }
// bar-rise: chart bar growing (soft rising tone), 0.6 s
{ const a = len(0.6); for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(2 * Math.PI * (300 + 500 * t) * t) * Math.min(1, t * 10) * Math.exp(-t * 3); }
  write("bar-rise.wav", fades(a, 10, 150), -10); }
