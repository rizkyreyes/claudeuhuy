// Procedural T&P valve / water heater foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, water-rush, splash, spark-crackle, button-click, room-tone. New: heater-rumble, tank-burst, debris-crash, steam-hiss, burner-whoosh, valve-pop, spring-creak, drip, water-gush.
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
// spark-crackle: a short electric spark, 0.5 s
{ const a = len(0.5), r = rng(9021), h = svf(noise(a.length, 9022), 6000, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (Math.abs(r()) > 0.93 ? 1 : 0.08) * Math.exp(-t * 9); }
  write("spark-crackle.wav", fades(a, 0, 120), -6); }
// button-click: plastic push button, 0.25 s
{ const a = len(0.25); add(a, svf(noise(300, 9031), 3000, 0.5), 0.8); modal(a, 0.002, 1800, [[1, 1, 1], [2.4, 0.4, 2]], 0.3, 60); write("button-click.wav", fades(a, 0, 60), -6); }
// room-tone: small tiled bathroom (low air + faint hum), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 9051), 300, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] + 0.05 * Math.sin(2 * Math.PI * 120 * t); }
  write("room-tone.wav", fades(a, 300, 300), -20); }
// ---- new for the T&P valve (3d-44a) ----
// heater-rumble: overpressured tank shaking before it lets go, 1.5 s (loops)
{ const a = len(1.5), lo = svf(noise(a.length, 9301), 90, 0.3, "low"), r = rng(9302);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * (0.7 + 0.3 * Math.sin(t * 40)) + 0.15 * Math.sin(2 * Math.PI * 55 * t) * (Math.abs(r()) > 0.5 ? 1 : 0.6); }
  for (let k = 0; k < 6; k++) modal(a, 0.1 + 0.22 * k, 310 + 37 * k, METAL, 0.12, 14);
  write("heater-rumble.wav", fades(a, 200, 200), -8); }
// tank-burst: the launch (deep boom + metal tear + steam blast), 2 s
{ const a = len(2.0); thump(a, 0, 38, 1.0, 3.5); thump(a, 0.02, 75, 0.6, 6);
  const tear = svf(noise(a.length, 9311), t => 900 + 1400 * Math.exp(-t * 3), 0.25);
  const hiss = svf(noise(a.length, 9312), 4500, 0.4, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.5 * tear[i] * Math.exp(-t * 5) + 0.45 * hiss[i] * Math.min(1, t * 30) * Math.exp(-t * 1.4); }
  modal(a, 0.0, 180, METAL, 0.35, 5); write("tank-burst.wav", fades(a, 0, 300), -3); }
// debris-crash: ceiling chunks landing (several thuds + crumbles), 1.4 s
{ const a = len(1.4), r = rng(9321);
  for (let k = 0; k < 7; k++) { const t0 = 0.05 + 0.18 * k + 0.05 * Math.abs(r()); thump(a, t0, 70 + 40 * Math.abs(r()), 0.5, 18);
    add(a, svf(noise(5000, 9330 + k), 1200, 0.5), 0.35, t0); }
  write("debris-crash.wav", fades(a, 0, 200), -5); }
// steam-hiss: hot water flashing / venting, 2 s (loops)
{ const a = len(2.0), h = svf(noise(a.length, 9341), t => 5200 + 800 * Math.sin(t * 5), 0.5), b = svf(noise(a.length, 9342), 2200, 0.6);
  for (let i = 0; i < a.length; i++) a[i] = 0.8 * h[i] + 0.3 * b[i];
  write("steam-hiss.wav", fades(a, 150, 250), -12); }
// burner-whoosh: gas burner lighting (soft whump + flame roar), 1.2 s
{ const a = len(1.2), f = svf(noise(a.length, 9351), 380, 0.5, "low"); thump(a, 0, 60, 0.5, 9);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += f[i] * Math.min(1, t * 6) * (0.6 + 0.4 * Math.exp(-t * 3)); }
  write("burner-whoosh.wav", fades(a, 0, 300), -8); }
// valve-pop: disc lifting off the brass seat (metal click + short spit), 0.5 s
{ const a = len(0.5); modal(a, 0.0, 2300, METAL, 0.5, 40); add(a, svf(noise(SR * 0.3, 9361), 3800, 0.5), 0.4, 0.01);
  for (let i = Math.round(0.01 * SR); i < a.length; i++) a[i] *= 1; write("valve-pop.wav", fades(a, 0, 120), -6); }
// spring-creak: steel spring loading up (twangy boing), 0.6 s
{ const a = len(0.6); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 210 + 60 * Math.sin(t * 28) * Math.exp(-t * 4); ph += 2 * Math.PI * f / SR; a[i] = (Math.sin(ph) + 0.4 * Math.sin(3.1 * ph)) * Math.exp(-t * 6); }
  write("spring-creak.wav", fades(a, 5, 120), -9); }
// drip: one drop on the floor drain, 0.35 s
{ const a = len(0.35); blips(a, 1, 0.0, 0.01, 1100, 1300, 0.9, 9371, 30); add(a, svf(noise(800, 9372), 4000, 0.5), 0.15);
  write("drip.wav", fades(a, 0, 80), -8); }
// water-gush: test-lever discharge hitting the drain, 2 s (loops)
{ const a = len(2.0), lo = svf(noise(a.length, 9381), 500, 0.4, "low"), hi = svf(noise(a.length, 9382), 2600, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.7 * lo[i] + 0.45 * hi[i] * (0.8 + 0.2 * Math.sin(t * 13)); }
  blips(a, 30, 0.0, 1.9, 600, 1600, 0.12, 9383, 30); write("water-gush.wav", fades(a, 60, 200), -9); }
