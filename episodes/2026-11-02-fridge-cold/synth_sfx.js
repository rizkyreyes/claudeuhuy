// Procedural fridge foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Panel slide, compressor hum + squeeze thump, refrigerant hiss, fan whirr, flap click, thermostat relay, power down, water drip, steam sizzle, deny thud.
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
// panel-slide: the near half of the cabinet sliding away (scrape that rises, then a soft thud)
{ const a = len(0.9), s = svf(noise(a.length, 41), t => 500 + 900 * Math.min(1, t / 0.7), 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.45 * s[i] * Math.sin(Math.PI * Math.min(1, t / 0.75)); }
  thump(a, 0.72, 60, 0.6, 9); write("panel-slide.wav", fades(a, 20, 120), -6); }
// compressor-hum: fridge compressor running (60 Hz mains hum + 120 Hz + soft rattle), 4 s
{ const a = len(4), w = svf(noise(a.length, 42), 350, 0.3); let p1 = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; p1 += 2 * Math.PI * 60 / SR;
    a[i] = 0.35 * Math.sin(2 * p1) + 0.18 * Math.sin(p1) + 0.08 * Math.sin(4 * p1) + 0.06 * w[i] * (1 + 0.5 * Math.sin(2 * Math.PI * 7 * t)); }
  write("compressor-hum.wav", fades(a, 400, 700), -14); }
// compressor-thump: one squeeze stroke (low thump + metal tick)
{ const a = len(0.5); thump(a, 0, 75, 1, 12); modal(a, 0.01, 1300, METAL, 0.15, 40); write("compressor-thump.wav", fades(a, 0, 100), -5); }
// refrigerant-hiss: liquid forced through the thin tube (high band noise, gentle swell), 2 s
{ const a = len(2), h = svf(noise(a.length, 43), 5200, 0.7);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = h[i] * Math.sin(Math.PI * t / 2) * (0.85 + 0.15 * Math.sin(2 * Math.PI * 11 * t)); }
  write("refrigerant-hiss.wav", fades(a, 150, 400), -14); }
// fan-whirr: small evaporator fan spinning up (blade-rate tone + air), 3 s
{ const a = len(3), air = svf(noise(a.length, 44), 1200, 0.5); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, u = Math.min(1, t / 0.8); ph += 2 * Math.PI * (40 + 110 * u) / SR;
    a[i] = (0.25 * Math.sin(5 * ph) + 0.4 * air[i]) * u; }
  write("fan-whirr.wav", fades(a, 50, 500), -14); }
// flap-click: damper flap opening (plastic click + small knock)
{ const a = len(0.25); modal(a, 0, 1900, METAL, 0.3, 70); thump(a, 0.01, 160, 0.4, 40); write("flap-click.wav", fades(a, 0, 50), -6); }
// relay-click: thermostat contacts switching
{ const a = len(0.2); modal(a, 0, 3200, METAL, 0.35, 90); modal(a, 0.012, 2400, METAL, 0.2, 90); write("relay-click.wav", fades(a, 0, 40), -6); }
// power-down: hum sliding down + relay click
{ const a = len(0.9); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * 100 * Math.exp(-t * 3) / SR; a[i] = 0.5 * Math.sin(ph) * Math.exp(-t * 2.5); }
  modal(a, 0, 2200, METAL, 0.3, 60); write("power-down.wav", fades(a, 0, 150), -6); }
// water-drip: one drop landing in the pan (pitched blip)
{ const a = len(0.35);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.sin(2 * Math.PI * (900 + 1400 * Math.exp(-t * 40)) * t) * Math.exp(-t * 22); }
  write("water-drip.wav", fades(a, 0, 60), -6); }
// steam-sizzle: melt + evaporation (crackly band noise), 2 s
{ const a = len(2), n = svf(noise(a.length, 45), 3500, 0.6), r = rng(46);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = n[i] * (0.4 + 0.6 * Math.max(0, r())) * Math.sin(Math.PI * t / 2); }
  write("steam-sizzle.wav", fades(a, 100, 400), -15); }
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 20), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
