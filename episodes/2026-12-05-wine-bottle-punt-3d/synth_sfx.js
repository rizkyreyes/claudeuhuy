// Procedural wine-bottle foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, spark-crackle, button-click, room-tone, drip. New: glass-clink, glass-ring, furnace-roar, glass-sizzle, rod-scrape,
// glass-wobble, conveyor-rattle, fizz, pressure-creak, glass-shatter, liquid-splash, sediment-sift.
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
// drip: a droplet landing, 0.3 s
{ const a = len(0.3); blips(a, 1, 0.0, 0.0, 900, 900, 1, 470, 30); write("drip.wav", fades(a, 0, 60), -9); }
const GLASS = [[1, 1, 1], [2.32, 0.55, 1.4], [4.25, 0.3, 2.1], [6.8, 0.18, 2.8]];
// glass-clink: a glass bottle set down / tapped, 0.6 s
{ const a = len(0.6); modal(a, 0.0, 1650, GLASS, 0.8, 9); add(a, svf(noise(400, 601), 5000, 0.5), 0.4); write("glass-clink.wav", fades(a, 0, 120), -6); }
// glass-ring: the standing ring glowing (bright sustained glass tone), 1.6 s
{ const a = len(1.6); modal(a, 0.0, 2480, GLASS, 0.6, 3.2); modal(a, 0.01, 1240, [[1, 1, 1]], 0.25, 4); write("glass-ring.wav", fades(a, 0, 300), -9); }
// furnace-roar: glass-shop furnace (low rumbling roar), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 611), t => 180 + 40 * Math.sin(t * 2.1), 0.35, "low"), mid = svf(noise(a.length, 612), 900, 0.6);
  for (let i = 0; i < a.length; i++) a[i] = lo[i] + 0.25 * mid[i]; write("furnace-roar.wav", fades(a, 300, 300), -16); }
// glass-sizzle: hot glass touching steel (short hiss + tick), 1.0 s
{ const a = len(1.0), h = svf(noise(a.length, 621), 5800, 0.3, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.min(1, t * 40) * Math.exp(-t * 3.2); }
  modal(a, 0.0, 1900, GLASS, 0.3, 20); write("glass-sizzle.wav", fades(a, 0, 150), -10); }
// rod-scrape: steel rod pushing into soft hot glass (low scrape + push), 1.2 s
{ const a = len(1.2), s = svf(noise(a.length, 631), t => 500 + 700 * t, 0.45);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.sin(Math.PI * Math.min(1, t / 1.15)); }
  thump(a, 0.0, 90, 0.5, 6); write("rod-scrape.wav", fades(a, 10, 150), -9); }
// glass-wobble: bottle rocking on its point on a steel table (fast double ticks), 1.2 s
{ const a = len(1.2); for (let k = 0; k < 4; k++) modal(a, 0.02 + k * 0.32, 2100 + 90 * k, GLASS, 0.55 * (1 - 0.15 * k), 30); write("glass-wobble.wav", fades(a, 0, 120), -7); }
// conveyor-rattle: bottles riding a belt (clinks over a motor hum), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 641), 250, 0.5, "low"), r = rng(642);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * lo[i] + 0.08 * Math.sin(2 * Math.PI * 100 * t); }
  for (let k = 0; k < 14; k++) modal(a, Math.abs(r()) * 2.8, 1500 + 900 * Math.abs(r()), GLASS, 0.12, 25);
  write("conveyor-rattle.wav", fades(a, 200, 200), -14); }
// fizz: champagne bubbles (crackly high hiss of tiny pops), 3 s (loops)
{ const a = len(3), r = rng(651), h = svf(noise(a.length, 652), 7000, 0.3, "high");
  for (let i = 0; i < a.length; i++) a[i] = h[i] * (Math.abs(r()) > 0.985 ? 1 : 0.05);
  blips(a, 40, 0.0, 2.9, 2500, 5000, 0.12, 653, 120); write("fizz.wav", fades(a, 200, 200), -14); }
// pressure-creak: glass straining under pressure (low groan + ticks), 1.5 s
{ const a = len(1.5), s = svf(noise(a.length, 661), t => 140 + 90 * t, 0.15);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.min(1, t * 2) ; }
  for (const t0 of [0.4, 0.85, 1.2]) modal(a, t0, 2800, GLASS, 0.25, 60); write("pressure-creak.wav", fades(a, 50, 200), -8); }
// glass-shatter: the flat base bursting (burst + many tinkling shards), 1.8 s
{ const a = len(1.8), r = rng(671); thump(a, 0.0, 70, 0.9, 10); add(a, svf(noise(9000, 672), 3500, 0.4), 1.0);
  for (let k = 0; k < 40; k++) { const t0 = 0.02 + 1.4 * Math.pow(Math.abs(r()), 1.6); modal(a, t0, 2200 + 4000 * Math.abs(r()), GLASS, 0.25 * (1 - t0 / 1.6), 35); }
  write("glass-shatter.wav", fades(a, 0, 250), -3); }
// liquid-splash: champagne gushing out onto the tray, 1.5 s
{ const a = len(1.5), s = svf(noise(a.length, 681), t => 600 + 900 * Math.exp(-t * 3), 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.min(1, t * 30) * Math.exp(-t * 1.6); }
  blips(a, 18, 0.05, 1.3, 500, 1400, 0.25, 682, 30); write("liquid-splash.wav", fades(a, 0, 250), -8); }
// sediment-sift: soft grainy settle, 2.5 s
{ const a = len(2.5), r = rng(691), h = svf(noise(a.length, 692), 2400, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (Math.abs(r()) > 0.96 ? 0.8 : 0.05) * Math.sin(Math.PI * t / 2.5); }
  write("sediment-sift.wav", fades(a, 100, 300), -16); }
