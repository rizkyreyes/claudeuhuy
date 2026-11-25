// Procedural smoke-alarm foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from dryer-vent: deny-thud, spark-crackle, button-click, room-tone, fire-crackle, fire-roar. New: alarm-beep, twist-click, flip-whoosh, plastic-clunk, cover-slide, light-hum, ion-buzz, grit-patter, bug-skitter, drip, pop-in.
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
// fire-crackle: burning lint (pops over a low roar), 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 4631), 260, 0.4, "low"), h = svf(noise(a.length, 4632), 3500, 0.3, "high"), r = rng(4633);
  for (let i = 0; i < a.length; i++) a[i] = 0.7 * lo[i] + h[i] * (Math.abs(r()) > 0.985 ? 1.0 : 0.03);
  write("fire-crackle.wav", fades(a, 200, 200), -8); }
// fire-roar: fire racing down the duct (rising whoosh), 2.5 s
{ const a = len(2.5), f = svf(noise(a.length, 4641), t => 200 + 700 * t, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = f[i] * Math.min(1, t * 2) * (1.2 - 0.3 * t); }
  write("fire-roar.wav", fades(a, 50, 400), -6); }
// alarm-beep: piezo horn, ~3.1 kHz harsh square-ish tone, three 0.35 s pulses (1.2 s)
{ const a = len(1.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR, on = (t % 0.42) < 0.35 ? 1 : 0, ph = 2 * Math.PI * 3100 * t;
    a[i] = on * (Math.tanh(4 * Math.sin(ph)) * 0.8 + 0.2 * Math.sin(3 * ph)); }
  write("alarm-beep.wav", fades(a, 3, 30), -9); }
// twist-click: plastic alarm twisting off its base (ratchet ticks + release snap), 0.6 s
{ const a = len(0.6); for (let k = 0; k < 5; k++) { add(a, svf(noise(400, 300 + k), 3500, 0.5), 0.4, 0.05 + 0.07 * k); }
  modal(a, 0.42, 1400, [[1, 1, 1], [2.3, 0.5, 2]], 0.6, 45); add(a, svf(noise(1500, 399), 2200, 0.5), 0.5, 0.42); write("twist-click.wav", fades(a, 0, 60), -7); }
// flip-whoosh: short air swish as the alarm flips, 0.5 s
{ const a = len(0.5), f = svf(noise(a.length, 410), t => 600 + 2400 * Math.sin(Math.PI * t / 0.5), 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = f[i] * Math.sin(Math.PI * Math.min(1, t / 0.5)); }
  write("flip-whoosh.wav", fades(a, 5, 60), -12); }
// plastic-clunk: the old alarm hitting the floor and bouncing, 1.0 s
{ const a = len(1.0); thump(a, 0.0, 110, 0.7, 22); modal(a, 0.0, 820, [[1, 1, 1], [2.2, 0.5, 2], [3.9, 0.25, 3]], 0.6, 28);
  add(a, svf(noise(2500, 420), 1800, 0.5), 0.5); modal(a, 0.32, 860, [[1, 1, 1], [2.2, 0.5, 2]], 0.3, 32); thump(a, 0.32, 120, 0.25, 30);
  modal(a, 0.52, 880, [[1, 1, 1]], 0.12, 40); write("plastic-clunk.wav", fades(a, 0, 120), -5); }
// cover-slide: the front half of the cover sliding off (plastic scrape), 0.9 s
{ const a = len(0.9), s = svf(noise(a.length, 430), t => 1200 + 600 * t, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * Math.sin(Math.PI * Math.min(1, t / 0.85)) * 0.8; }
  write("cover-slide.wav", fades(a, 5, 80), -10); }
// light-hum: the LED beam switching on (soft rising tone + shimmer), 1.0 s
{ const a = len(1.0);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = Math.min(1, t * 6) * Math.exp(-t * 1.5) * (Math.sin(2 * Math.PI * 880 * t) + 0.5 * Math.sin(2 * Math.PI * 1320 * t + Math.sin(t * 30))); }
  write("light-hum.wav", fades(a, 5, 200), -16); }
// ion-buzz: the weak current (quiet electric buzz), 3 s (loops)
{ const a = len(3), h = svf(noise(a.length, 440), 2400, 0.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * Math.sin(2 * Math.PI * 120 * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 240 * t)) + 0.15 * h[i]; }
  write("ion-buzz.wav", fades(a, 200, 200), -18); }
// grit-patter: dust grains ticking into the chamber, 1.2 s
{ const a = len(1.2); blips(a, 40, 0.0, 1.1, 3000, 6000, 0.3, 450, 200); write("grit-patter.wav", fades(a, 20, 200), -14); }
// bug-skitter: tiny legs on plastic, 1.2 s
{ const a = len(1.2), r = rng(460); for (let k = 0; k < 26; k++) add(a, svf(noise(200, 461 + k), 5000, 0.6), 0.5 + 0.5 * Math.abs(r()), 0.04 * k);
  write("bug-skitter.wav", fades(a, 10, 150), -14); }
// drip: grease / damp droplet landing, 0.3 s
{ const a = len(0.3); blips(a, 1, 0.0, 0.0, 900, 900, 1, 470, 30); write("drip.wav", fades(a, 0, 60), -9); }
// pop-in: new alarm clicking onto the base (bright plastic snap), 0.4 s
{ const a = len(0.4); modal(a, 0.0, 1600, [[1, 1, 1], [2.6, 0.5, 2]], 0.7, 40); add(a, svf(noise(800, 480), 4000, 0.5), 0.6); thump(a, 0, 180, 0.3, 40);
  write("pop-in.wav", fades(a, 0, 80), -6); }
