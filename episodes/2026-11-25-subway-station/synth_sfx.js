// Procedural subway-station foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept: deny-thud, steel-clunk, block-thud, street-amb. New: city-traffic, diesel-rumble, bucket-clank, slurry-churn, rebar-rattle, concrete-pour,
// soil-collapse, dirt-dump, deck-thunk, strut-clank, train-arrive, plate-lift, tunnel-tone.
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
// steel-clunk: beam / strut seated, 0.7 s
{ const a = len(0.7); modal(a, 0, 260, METAL, 0.6, 10); thump(a, 0, 65, 0.7, 12); write("steel-clunk.wav", fades(a, 0, 120), -6); }
// block-thud: heavy slab landing, 0.5 s
{ const a = len(0.5); thump(a, 0, 70, 1, 14); add(a, svf(noise(4000, 4061), 400, 0.6, "low"), 0.4); write("block-thud.wav", fades(a, 0, 100), -6); }
// street-amb: city air + far traffic, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 4081), t => 260 + 80 * Math.sin(t * 0.9), 0.4, "low"), mid = svf(noise(a.length, 4082), 900, 0.3);
  for (let i = 0; i < a.length; i++) a[i] = lo[i] + 0.08 * mid[i];
  write("street-amb.wav", fades(a, 300, 300), -16); }
// city-traffic: two cars passing over the deck (tyre roar swelling, plate rumble), 3 s
{ const a = len(3), n = svf(noise(a.length, 5011), t => 500 + 400 * Math.sin(Math.PI * t / 3), 0.35), lo = svf(noise(a.length, 5012), 90, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; const env = Math.exp(-Math.pow((t - 0.9) / 0.5, 2)) + 0.8 * Math.exp(-Math.pow((t - 2.1) / 0.5, 2)); a[i] = (0.5 * n[i] + lo[i]) * (0.25 + env); }
  for (const t0 of [0.85, 1.0, 2.05, 2.2]) thump(a, t0, 55, 0.25, 18);
  write("city-traffic.wav", fades(a, 200, 300), -12); }
// diesel-rumble: crane / excavator engine idle with firing pulses, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 5021), 160, 0.5, "low"); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; ph += 2 * Math.PI * 28 / SR; a[i] = lo[i] * (0.6 + 0.4 * Math.max(0, Math.sin(ph))) + 0.25 * Math.sin(ph * 2); }
  write("diesel-rumble.wav", fades(a, 200, 200), -12); }
// bucket-clank: clamshell jaws biting + cable rattle, 0.8 s
{ const a = len(0.8); modal(a, 0, 180, METAL, 0.55, 8); modal(a, 0.06, 420, METAL, 0.3, 14); thump(a, 0, 60, 0.6, 10);
  add(a, svf(noise(SR * 0.5, 5031), 3000, 0.5), 0.15, 0.1); write("bucket-clank.wav", fades(a, 0, 150), -6); }
// slurry-churn: thick muddy liquid sloshing, 3 s
{ const a = len(3), n = svf(noise(a.length, 5041), t => 380 + 120 * Math.sin(t * 3.1), 0.25), lo = svf(noise(a.length, 5042), 120, 0.5, "low");
  for (let i = 0; i < a.length; i++) a[i] = 0.6 * n[i] + 0.7 * lo[i];
  blips(a, 26, 0.1, 2.8, 140, 420, 0.25, 5043, 22); write("slurry-churn.wav", fades(a, 200, 300), -10); }
// rebar-rattle: steel cage swinging down (many small metal ticks), 1.5 s
{ const a = len(1.5), r = rng(5051);
  for (let k = 0; k < 40; k++) modal(a, 1.3 * Math.abs(r()), 900 + 1400 * Math.abs(r()), METAL, 0.12, 30);
  add(a, svf(noise(a.length, 5052), 2500, 0.5), 0.05); write("rebar-rattle.wav", fades(a, 50, 250), -8); }
// concrete-pour: heavy wet flow through the pipe, 3 s
{ const a = len(3), n = svf(noise(a.length, 5061), t => 300 - 60 * t, 0.3), lo = svf(noise(a.length, 5062), 90, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.5 * n[i] + 0.9 * lo[i]) * Math.min(1, t * 3); }
  blips(a, 14, 0.2, 2.8, 90, 220, 0.3, 5063, 18); write("concrete-pour.wav", fades(a, 100, 400), -9); }
// soil-collapse: rumble + cascading dirt + chunks, 2.5 s
{ const a = len(2.5), lo = svf(noise(a.length, 5071), 110, 0.6, "low"), n = svf(noise(a.length, 5072), 1200, 0.4), r = rng(5073);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (1.0 * lo[i] + 0.5 * n[i]) * Math.min(1, t * 6) * Math.exp(-t * 0.9); }
  for (let k = 0; k < 9; k++) thump(a, 0.1 + 1.8 * Math.abs(r()), 50 + 40 * Math.abs(r()), 0.4, 12);
  write("soil-collapse.wav", fades(a, 0, 400), -5); }
// dirt-dump: loose soil poured back in, 1.6 s
{ const a = len(1.6), n = svf(noise(a.length, 5081), 900, 0.4), lo = svf(noise(a.length, 5082), 140, 0.5, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = (0.6 * n[i] + 0.8 * lo[i]) * Math.sin(Math.PI * Math.min(1, t / 1.6)); }
  write("dirt-dump.wav", fades(a, 50, 200), -8); }
// deck-thunk: deck panel dropped on the beams, 0.45 s
{ const a = len(0.45); thump(a, 0, 85, 0.9, 18); modal(a, 0, 340, METAL, 0.25, 22); write("deck-thunk.wav", fades(a, 0, 80), -6); }
// strut-clank: big steel pipe wedged between the walls (ring + jack), 0.9 s
{ const a = len(0.9); modal(a, 0, 150, METAL, 0.7, 5); thump(a, 0, 55, 0.6, 9); write("strut-clank.wav", fades(a, 0, 200), -6); }
// train-arrive: rumble swelling, wheel squeal, brake hiss, 3.5 s
{ const a = len(3.5), lo = svf(noise(a.length, 5091), 120, 0.5, "low"), hs = svf(noise(a.length, 5092), 4500, 0.5, "high"); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR; const sw = Math.min(1, t / 2.2); ph += 2 * Math.PI * (2600 - 300 * t) / SR;
    a[i] = lo[i] * (0.3 + sw) * (t < 3 ? 1 : 1 - (t - 3) / 0.5) + 0.06 * Math.sin(ph) * Math.max(0, Math.sin(Math.PI * (t - 1.6) / 1.4)) * (t > 1.6 && t < 3 ? 1 : 0) + 0.25 * hs[i] * (t > 2.9 ? Math.exp(-(t - 2.9) * 3) : 0); }
  write("train-arrive.wav", fades(a, 300, 200), -7); }
// plate-lift: chain clink + steel plate scraping off the road, 1.2 s
{ const a = len(1.2), n = svf(noise(a.length, 5101), 1600, 0.3), r = rng(5102);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * n[i] * Math.exp(-t * 3); }
  for (let k = 0; k < 6; k++) modal(a, 0.05 + 0.15 * k, 1800 + 300 * r(), METAL, 0.15, 25);
  write("plate-lift.wav", fades(a, 20, 250), -8); }
// tunnel-tone: low hollow room tone under the deck / in the station, 3 s (loops)
{ const a = len(3), lo = svf(noise(a.length, 5111), t => 90 + 20 * Math.sin(t * 0.7), 0.2, "band");
  for (let i = 0; i < a.length; i++) a[i] = lo[i];
  write("tunnel-tone.wav", fades(a, 300, 300), -14); }
