// Procedural pool-construction foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Excavator, rebar, concrete crack, shotcrete spray, mist, water fill, pump hum, the floating shell, relief-valve glug, cement gun.
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
const STEEL = [[1, 1, 1], [2.32, 0.6, 1.4], [4.25, 0.35, 2.0], [6.63, 0.2, 2.8]];
const add = (a, b, g = 1, at = 0) => { const i0 = Math.round(at * SR); for (let i = 0; i < b.length && i0 + i < a.length; i++) a[i0 + i] += g * b[i]; return a; };
function bubble(a, t0, f0, amp, dur = 0.06) {    // rising-pitch sine blip = a single bubble / drop
  const i0 = Math.round(t0 * SR), n = Math.round(dur * SR); let ph = 0;
  for (let i = 0; i < n && i0 + i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * f0 * (1 + 2.2 * t / dur) / SR; a[i0 + i] += amp * Math.sin(ph) * Math.exp(-t * 4 / dur) * Math.min(1, t * 2000); }
}


// excavator: 2.5 s diesel idle + hydraulic whine + a dirt scoop crumble
{ const a = len(2.5), hs = svf(noise(a.length, 81), 1200, 0.5), r = rng(82); let ph = 0, pw = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * 34 / SR; pw += 2 * Math.PI * (420 + 120 * Math.sin(t * 2.5)) / SR;
    a[i] = 0.45 * Math.sin(ph) + 0.2 * Math.sin(2 * ph) + 0.12 * Math.sign(Math.sin(3 * ph)) * 0.4 + 0.06 * Math.sin(pw); }
  for (let k = 0; k < 40; k++) { const t0 = 1.2 + 0.9 * Math.abs(r()); modal(a, t0, 500 + 600 * Math.abs(r()), [[1, 1, 1], [2.7, 0.4, 1.8]], 0.12, 80); }
  for (let i = Math.round(1.1 * SR); i < Math.round(2.2 * SR); i++) a[i] += 0.3 * hs[i];
  write("excavator.wav", fades(a, 200, 300), -9); }
// rebar-clank: steel bar dropped into place (bright metal ring)
{ const a = len(0.7); modal(a, 0, 620, STEEL, 0.8, 9); modal(a, 0.04, 910, STEEL, 0.4, 12); add(a, svf(noise(2000, 83), 3000, 0.6), 0.3);
  write("rebar-clank.wav", fades(a, 0, 120), -8); }
// tie-tick: wire tie twist (tiny dry click)
{ const a = len(0.08); add(a, svf(noise(a.length, 84), 4200, 0.4), 1); for (let i = 0; i < a.length; i++) a[i] *= Math.exp(-i / SR * 60);
  write("tie-tick.wav", a, -12); }
// concrete-crack: sharp snap + crumble
{ const a = len(0.9), s = svf(noise(a.length, 85), 2500, 0.3), r = rng(86);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.9 * s[i] * Math.exp(-t * 25); }
  thump(a, 0.0, 70, 0.7, 12); for (let k = 0; k < 25; k++) modal(a, 0.05 + 0.6 * Math.abs(r()), 800 + 900 * Math.abs(r()), [[1, 1, 1]], 0.06, 120);
  write("concrete-crack.wav", fades(a, 0, 150), -4); }
// squeeze-creak: low strained groan (compression)
{ const a = len(0.8); let ph = 0; const n = svf(noise(a.length, 87), 300, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (90 + 30 * t) / SR; a[i] = (0.5 * Math.sin(ph) * (1 + 0.5 * Math.sin(t * 60)) + 0.4 * n[i]) * Math.sin(Math.PI * t / 0.8); }
  write("squeeze-creak.wav", fades(a, 20, 100), -9); }
// pvc-click: pipe fitting snapped together
{ const a = len(0.25); modal(a, 0, 1400, [[1, 1, 1], [1.8, 0.5, 1.5]], 0.6, 40); thump(a, 0, 180, 0.4, 30); write("pvc-click.wav", fades(a, 0, 40), -9); }
// shotcrete-spray: 6 s high-pressure spray (hissing noise + slaps of concrete)
{ const a = len(6), h = svf(noise(a.length, 88), t => 2200 + 400 * Math.sin(t * 1.3), 0.6), lo = svf(noise(a.length, 89), 300, 0.7, "low"), r = rng(90);
  for (let i = 0; i < a.length; i++) a[i] = 0.5 * h[i] + 0.35 * lo[i];
  for (let k = 0; k < 90; k++) thump(a, 5.9 * Math.abs(r()), 110 + 60 * Math.abs(r()), 0.12, 40);
  write("shotcrete-spray.wav", fades(a, 300, 500), -10); }
// trowel: smoothing scrape
{ const a = len(1.0), s = svf(noise(a.length, 91), t => 1500 + 600 * Math.sin(t * 6), 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (0.5 + 0.5 * Math.sin(Math.PI * t * 2)); } write("trowel.wav", fades(a, 50, 200), -12); }
// mist: soft water spray hiss (curing)
{ const a = len(2.0), h = svf(noise(a.length, 92), 6000, 0.8); for (let i = 0; i < a.length; i++) a[i] = h[i];
  write("mist.wav", fades(a, 400, 500), -16); }
// tile-tap: ceramic tile set (bright click)
{ const a = len(0.2); modal(a, 0, 2600, [[1, 1, 1], [2.1, 0.5, 1.4]], 0.6, 50); write("tile-tap.wav", fades(a, 0, 30), -10); }
// stone-set: coping stone laid (low knock)
{ const a = len(0.5); thump(a, 0, 95, 1, 14); add(a, svf(noise(3000, 93), 900, 0.6), 0.25); write("stone-set.wav", fades(a, 0, 80), -7); }
// water-fill: 3 s gushing hose into the pool
{ const a = len(3), n = svf(noise(a.length, 94), t => 700 - 150 * Math.min(1, t / 3), 0.4), r = rng(95);
  for (let i = 0; i < a.length; i++) a[i] = 0.6 * n[i];
  for (let k = 0; k < 120; k++) bubble(a, 2.9 * Math.abs(r()), 250 + 400 * Math.abs(r()), 0.2, 0.05);
  write("water-fill.wav", fades(a, 200, 600), -10); }
// pump-hum: 6 s electric motor hum + water swirl
{ const a = len(6), w = svf(noise(a.length, 96), 500, 0.5); let ph = 0;
  for (let i = 0; i < a.length; i++) { ph += 2 * Math.PI * 120 / SR; a[i] = 0.35 * Math.sin(ph) + 0.12 * Math.sin(3 * ph) + 0.25 * w[i]; }
  write("pump-hum.wav", fades(a, 300, 500), -14); }
// pool-lift: groaning concrete + cracking soil as the shell rises
{ const a = len(1.8), lo = svf(noise(a.length, 97), 120, 0.6, "low"), r = rng(98); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * (55 + 25 * t) / SR; a[i] = (0.6 * lo[i] + 0.3 * Math.sin(ph)) * Math.min(1, t / 0.2); }
  for (let k = 0; k < 30; k++) modal(a, 1.6 * Math.abs(r()), 400 + 700 * Math.abs(r()), [[1, 1, 1], [2.7, 0.4, 1.8]], 0.1, 90);
  write("pool-lift.wav", fades(a, 10, 300), -5); }
// valve-glug: water forcing in through the valve
{ const a = len(1.2); for (let k = 0; k < 6; k++) bubble(a, k * 0.17, 160 + 30 * (k % 3), 0.9, 0.14); add(a, svf(noise(a.length, 99), 600, 0.6), 0.12);
  write("valve-glug.wav", fades(a, 0, 200), -8); }
// cement-gun: compressed-air hiss + rattle (old machine)
{ const a = len(4), h = svf(noise(a.length, 100), 3500, 0.5), r = rng(101); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * 22 / SR; a[i] = 0.45 * h[i] + 0.25 * Math.sign(Math.sin(ph)) * Math.exp(-((t * 22) % 1) * 8); }
  for (let k = 0; k < 40; k++) thump(a, 3.9 * Math.abs(r()), 150, 0.1, 40);
  write("cement-gun.wav", fades(a, 300, 500), -11); }
{ const a = len(0.6); thump(a, 0, 48, 1, 7); add(a, svf(noise(4000, 16), 220, 0.6, "low"), 0.6); write("deny-thud.wav", fades(a, 0, 80), -4); }
// slab-drop: the front half dropping away (scrape + heavy thud)
{ const a = len(0.9), s = svf(noise(a.length, 66), 700, 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * s[i] * Math.exp(-t * 5); }
  thump(a, 0.12, 52, 1, 7); write("slab-drop.wav", fades(a, 5, 150), -5); }
