// Procedural offshore-build foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// Weld crackle, skid scrape, tug horn, steel slide, big splash, water rush, steel groan, mud thud, pile slide, hammer blow, grout pump, crane whine, deck clunk, wave wash, seabed rumble, tendon clank, deny thud.
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
// weld-crackle: arc welding crackle (bursty band noise)
{ const a = len(1.8), n = svf(noise(a.length, 11), 3500, 0.4, "high"), r = rng(12);
  let env = 0; for (let i = 0; i < a.length; i++) { if (i % 240 === 0) env = Math.abs(r()) > 0.55 ? Math.abs(r()) : env * 0.3; a[i] = n[i] * env; }
  write("weld-crackle.wav", fades(a, 30, 200), -10); }
// skid-scrape: steel jacket skidding on greased beams (low grinding scrape)
{ const a = len(1.6), s = svf(noise(a.length, 13), t => 220 + 160 * Math.sin(t * 9), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = s[i] * (0.6 + 0.4 * Math.sin(t * 23)) * Math.sin(Math.PI * Math.min(1, t / 1.6)); }
  write("skid-scrape.wav", fades(a, 40, 200), -6); }
// tug-horn: two-tone ship horn
{ const a = len(1.4); for (let i = 0; i < a.length; i++) { const t = i / SR; let v = 0;
    for (const [f, g] of [[110, 1], [220, 0.5], [330, 0.3], [440, 0.15]]) v += g * Math.sin(2 * Math.PI * f * t); a[i] = 0.4 * v * Math.min(1, t / 0.08) * Math.min(1, (1.4 - t) / 0.3); }
  write("tug-horn.wav", fades(a, 10, 150), -8); }
// steel-slide: jacket sliding off the stern (rising scrape + creak)
{ const a = len(1.6), s = svf(noise(a.length, 15), t => 300 + 900 * Math.min(1, t / 1.4), 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.6 * s[i] * Math.min(1, t / 0.5); }
  modal(a, 0.4, 180, METAL, 0.3, 4); write("steel-slide.wav", fades(a, 20, 200), -6); }
// splash-big: heavy body into the sea (thump + broadband wash)
{ const a = len(2.6); thump(a, 0.02, 55, 1, 5); const w = svf(noise(a.length, 17), t => 2500 - 1800 * Math.min(1, t / 2.2), 0.6);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.9 * w[i] * Math.exp(-t * 1.4); }
  blips(a, 40, 0.3, 2.3, 400, 1400, 0.12, 18, 30); write("splash-big.wav", fades(a, 0, 300), -3); }
// water-rush: flooding / waves (filtered noise swell)
{ const a = len(3.0), w = svf(noise(a.length, 19), 700, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = w[i] * Math.sin(Math.PI * Math.min(1, t / 3.0)) * (0.8 + 0.2 * Math.sin(t * 7)); }
  blips(a, 18, 0.2, 2.6, 300, 900, 0.1, 20); write("water-rush.wav", fades(a, 100, 300), -7); }
// steel-groan: big structure turning (slow low creak, pitch sliding)
{ const a = len(2.6); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 70 + 40 * Math.sin(t * 1.3) + 25 * t; ph += 2 * Math.PI * f / SR;
    a[i] = (Math.sin(ph) + 0.5 * Math.sin(2.7 * ph) + 0.3 * Math.sin(4.1 * ph)) * (0.5 + 0.5 * Math.abs(Math.sin(t * 5))) * Math.sin(Math.PI * t / 2.6); }
  add(a, svf(noise(a.length, 21), 160, 0.5, "low"), 0.4); write("steel-groan.wav", fades(a, 60, 300), -6); }
// mud-thud: jacket landing on the seabed (deep muffled thud + soft cloud)
{ const a = len(1.6); thump(a, 0, 34, 1, 4); add(a, svf(noise(a.length, 23), 120, 0.6, "low"), 0.5);
  write("mud-thud.wav", fades(a, 0, 400), -3); }
// pile-slide: long steel pile sliding through the sleeve (metal ring + scrape)
{ const a = len(1.5), s = svf(noise(a.length, 25), t => 1200 - 700 * t / 1.5, 0.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * s[i] * Math.sin(Math.PI * Math.min(1, t / 1.5)); }
  modal(a, 1.3, 260, METAL, 0.5, 6); write("pile-slide.wav", fades(a, 20, 150), -6); }
// hammer-blow: hydraulic pile hammer hit (sharp metal clang + low body)
{ const a = len(0.7); thump(a, 0, 60, 0.9, 12); modal(a, 0, 420, METAL, 0.6, 9); add(a, svf(noise(a.length, 27), 2000, 0.5), 0.3);
  write("hammer-blow.wav", fades(a, 0, 120), -2); }
// grout-pump: pump chug + thick fluid gurgle
{ const a = len(2.0);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.4 * Math.sin(2 * Math.PI * 48 * t) * Math.max(0, Math.sin(2 * Math.PI * 3 * t)) ** 3; }
  blips(a, 26, 0.1, 1.9, 120, 380, 0.25, 28, 18); write("grout-pump.wav", fades(a, 50, 250), -8); }
// crane-whine: winch motor rising
{ const a = len(2.2); let ph = 0;
  for (let i = 0; i < a.length; i++) { const t = i / SR, f = 140 + 120 * Math.min(1, t / 1.2); ph += 2 * Math.PI * f / SR;
    a[i] = (0.6 * Math.sin(ph) + 0.3 * Math.sin(3 * ph)) * Math.min(1, t / 0.2) * Math.min(1, (2.2 - t) / 0.4); }
  add(a, svf(noise(a.length, 29), 900, 0.4), 0.15); write("crane-whine.wav", fades(a, 30, 200), -10); }
// deck-clunk: topsides set down on the jacket (heavy metal clunk)
{ const a = len(1.2); thump(a, 0, 48, 1, 6); modal(a, 0.005, 150, METAL, 0.6, 5); write("deck-clunk.wav", fades(a, 0, 250), -3); }
// wave-wash: waves passing (slow swell of band noise)
{ const a = len(3.5), w = svf(noise(a.length, 31), t => 500 + 400 * Math.sin(t * 1.8), 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = w[i] * (0.4 + 0.6 * Math.max(0, Math.sin(t * 1.8))); }
  write("wave-wash.wav", fades(a, 200, 400), -9); }
// seabed-rumble: the seabed dropping away (long sub rumble)
{ const a = len(2.0), lo = svf(noise(a.length, 33), t => 120 - 60 * Math.min(1, t / 1.8), 0.4, "low");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = lo[i] * Math.min(1, t / 0.2) * Math.max(0, 1 - t / 2.0); }
  write("seabed-rumble.wav", fades(a, 10, 300), -4); }
// tendon-clank: tendons latching tight (metal clank + ring)
{ const a = len(1.0); modal(a, 0, 330, METAL, 0.8, 5); thump(a, 0, 70, 0.5, 14); write("tendon-clank.wav", fades(a, 0, 200), -4); }
// deny-thud (stinger)
{ const a = len(0.6); thump(a, 0, 50, 1, 8); modal(a, 0.01, 180, METAL, 0.4, 10); write("deny-thud.wav", fades(a, 0, 150), -3); }
