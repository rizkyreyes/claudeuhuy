// Procedural iron foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from smoke-alarm: deny-thud, spark-crackle, button-click, room-tone, drip. New: iron-glide, plastic-crack, melt-sizzle, cover-lift,
// thermo-click, element-hum, water-slosh, drop-sizzle, steam-hiss, leak-patter, valve-clunk, power-down.
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
// drip: grease / damp droplet landing, 0.3 s
{ const a = len(0.3); blips(a, 1, 0.0, 0.0, 900, 900, 1, 470, 30); write("drip.wav", fades(a, 0, 60), -9); }
// iron-glide: soleplate sliding over cotton (soft brushed noise), 1.5 s
{ const a = len(1.5), s = svf(noise(a.length, 501), t => 700 + 300 * Math.sin(t * 4), 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.sin(Math.PI * Math.min(1, t / 1.5)); }
  write("iron-glide.wav", fades(a, 30, 200), -14); }
// plastic-crack: the melted button snapping, 0.5 s
{ const a = len(0.5); add(a, svf(noise(1200, 511), 4200, 0.4), 1.0); modal(a, 0.0, 2300, [[1, 1, 1], [2.7, 0.6, 2], [4.1, 0.3, 3]], 0.5, 60);
  add(a, svf(noise(900, 512), 2600, 0.5), 0.5, 0.05); thump(a, 0.0, 160, 0.3, 40); write("plastic-crack.wav", fades(a, 0, 80), -5); }
// melt-sizzle: hot plate on plastic (frying hiss), 2 s
{ const a = len(2.0), h = svf(noise(a.length, 521), 5200, 0.3, "high"), r = rng(522);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * (0.35 + (Math.abs(r()) > 0.97 ? 0.9 : 0)) * Math.min(1, t * 3) * (1 - 0.3 * t); }
  write("melt-sizzle.wav", fades(a, 20, 300), -12); }
// cover-lift: the front half of the housing lifting away (plastic scrape + whoosh), 1.0 s
{ const a = len(1.0), s = svf(noise(a.length, 531), t => 900 + 1500 * t, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.sin(Math.PI * Math.min(1, t / 0.95)); }
  modal(a, 0.0, 900, [[1, 1, 1], [2.3, 0.4, 2]], 0.4, 40); write("cover-lift.wav", fades(a, 0, 120), -9); }
// thermo-click: bimetal contacts snapping (sharp metallic tick), 0.3 s
{ const a = len(0.3); modal(a, 0.0, 3400, [[1, 1, 1], [2.2, 0.5, 2], [3.7, 0.3, 3]], 0.8, 80); add(a, svf(noise(300, 541), 6000, 0.5), 0.6);
  write("thermo-click.wav", fades(a, 0, 60), -6); }
// element-hum: the heating element on (low mains hum + warm air), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 551), 400, 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * Math.sin(2 * Math.PI * 60 * t) + 0.25 * Math.sin(2 * Math.PI * 120 * t) + 0.6 * lo[i]; }
  write("element-hum.wav", fades(a, 200, 200), -18); }
// water-slosh: water moving in the tank, 1.2 s
{ const a = len(1.2), s = svf(noise(a.length, 561), t => 300 + 400 * Math.abs(Math.sin(t * 6)), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.sin(Math.PI * Math.min(1, t / 1.2)); }
  blips(a, 8, 0.1, 1.0, 400, 900, 0.3, 562, 25); write("water-slosh.wav", fades(a, 30, 200), -11); }
// drop-sizzle: a drop hitting the hot chamber floor and flashing into steam, 0.5 s
{ const a = len(0.5), h = svf(noise(a.length, 571), 6500, 0.3, "high");
  blips(a, 1, 0.0, 0.0, 1100, 1100, 0.6, 572, 40);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += h[i] * Math.exp(-t * 7) * Math.min(1, t * 60); }
  write("drop-sizzle.wav", fades(a, 0, 100), -8); }
// steam-hiss: the steam burst out of the holes, 2.5 s
{ const a = len(2.5), h = svf(noise(a.length, 581), t => 3500 + 1500 * Math.min(1, t * 4), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.min(1, t * 10) * (1 - 0.35 * t); }
  write("steam-hiss.wav", fades(a, 10, 400), -7); }
// leak-patter: water drops pattering on fabric, 1.5 s
{ const a = len(1.5); blips(a, 7, 0.0, 1.4, 700, 1200, 0.8, 591, 45); add(a, svf(noise(a.length, 592), 900, 0.6, "low"), 0.08);
  write("leak-patter.wav", fades(a, 10, 200), -10); }
// valve-clunk: needle valve seating shut (dull metallic clunk), 0.5 s
{ const a = len(0.5); thump(a, 0.0, 140, 0.8, 28); modal(a, 0.0, 1150, [[1, 1, 1], [2.6, 0.4, 2]], 0.5, 35); write("valve-clunk.wav", fades(a, 0, 80), -6); }
// power-down: auto shut-off (two falling blips + relay tick), 0.9 s
{ const a = len(0.9); modal(a, 0.0, 2600, [[1, 1, 1]], 0.4, 90);
  for (const [t0, f] of [[0.08, 1320], [0.32, 880]]) { const i0 = Math.round(t0 * SR); for (let i = i0; i < i0 + SR * 0.18; i++) { const t = (i - i0) / SR; a[i] += 0.5 * Math.sin(2 * Math.PI * f * t) * Math.min(1, t * 200) * Math.exp(-t * 14); } }
  write("power-down.wav", fades(a, 0, 120), -9); }
