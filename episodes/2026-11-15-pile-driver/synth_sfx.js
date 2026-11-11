// Procedural pile-driver foley (48 kHz 16-bit mono WAV, deterministic). Writes into ./sfx/. Run: node synth_sfx.js
// kept from the earlier sets: deny thud, wind, birds, crumble;
// new: pile-blow (diesel hammer stroke), stake-tap, metal-crunch, weight-thud, winch, steel-slide, air-squeeze, fuel-spray, ignite, crawler.
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
// wind-gust: soft outdoor air, 3 s
{ const a = len(3), n = svf(noise(a.length, 105), t => 500 + 350 * Math.sin(2 * Math.PI * 0.4 * t), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.5 * n[i] * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.33 * t) ** 2) * Math.sin(Math.PI * Math.min(1, t / 3)); }
  write("wind-gust.wav", fades(a, 200, 500), -14); }
// birds: yard ambience, 3 s
{ const a = len(3), r = rng(308);
  for (let k = 0; k < 12; k++) { const t0 = 2.7 * Math.abs(r()), f0 = 2600 + 900 * Math.abs(r()), i0 = Math.round(t0 * SR);
    for (let i = i0; i < a.length && i < i0 + SR * 0.12; i++) { const t = (i - i0) / SR; a[i] += 0.2 * Math.sin(2 * Math.PI * (f0 + 2500 * t) * t) * Math.sin(Math.PI * t / 0.12); } }
  write("birds.wav", fades(a, 50, 300), -16); }
// crumble: soil and gravel falling into the hole, 1.4 s
{ const a = len(1.4), r = rng(407), n = svf(noise(a.length, 408), 1200, 0.5);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] = 0.25 * n[i] * Math.exp(-t * 1.8) * Math.min(1, t / 0.05); }
  for (let k = 0; k < 35; k++) { const t0 = 1.2 * Math.abs(r()) ** 1.5; thump(a, t0, 80 + 120 * Math.abs(r()), 0.12, 30); }
  thump(a, 0, 55, 0.5, 6); write("crumble.wav", fades(a, 0, 200), -7); }

// pile-blow: one diesel hammer stroke: steel ram on the anvil (clank), the blast (low whoomp), exhaust chuff, 1.2 s
{ const a = len(1.2); modal(a, 0, 210, METAL, 0.7, 9); modal(a, 0.004, 640, METAL, 0.3, 16); thump(a, 0, 52, 1.0, 6);
  add(a, svf(noise(a.length, 601), 140, 0.5, "low"), 0.9); const ex = svf(noise(a.length, 602), 900, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.45 * ex[i] * Math.exp(-Math.max(0, t - 0.06) * 7) * (t > 0.05 ? 1 : 0); }
  write("pile-blow.wav", fades(a, 0, 200), -2); }
// stake-tap: a steel hammer on a wooden tent stake, 0.35 s
{ const a = len(0.35); modal(a, 0, 420, [[1, 1, 1], [2.3, 0.4, 1.8], [3.9, 0.2, 2.6]], 0.6, 30); thump(a, 0, 120, 0.5, 26);
  add(a, svf(noise(a.length, 611), 2500, 0.6), 0.15); write("stake-tap.wav", fades(a, 0, 60), -6); }
// metal-crunch: a pile head crushing (grinding crunch + heavy clank), 1.0 s
{ const a = len(1.0), r = rng(621), n = svf(noise(a.length, 622), 1400, 0.4);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += n[i] * 0.8 * Math.exp(-t * 5) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 37 * t)); }
  modal(a, 0, 180, METAL, 0.6, 7); thump(a, 0, 45, 0.8, 6); write("metal-crunch.wav", fades(a, 0, 150), -3); }
// weight-thud: a heavy drop weight landing on a pile (dull thud + ring), 1.0 s
{ const a = len(1.0); thump(a, 0, 40, 1.0, 5); modal(a, 0, 150, METAL, 0.35, 8); add(a, svf(noise(a.length, 631), 120, 0.5, "low"), 0.7);
  write("weight-thud.wav", fades(a, 0, 150), -3); }
// winch: a slow winch hauling a weight up (geared whine + rope creak), 1.6 s
{ const a = len(1.6), n = svf(noise(a.length, 641), 300, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.35 * Math.sin(2 * Math.PI * (180 + 40 * t) * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 9 * t)) + 0.4 * n[i]; }
  write("winch.wav", fades(a, 60, 250), -10); }
// steel-slide: the cylinder sliding down over the ram and seating (scrape + clunk), 1.0 s
{ const a = len(1.0), s = svf(noise(a.length, 651), t => 700 - 300 * t, 0.3);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.6 * s[i] * Math.min(1, t * 8) * (t < 0.7 ? 1 : Math.exp(-(t - 0.7) * 20)); }
  modal(a, 0.7, 260, METAL, 0.6, 10); thump(a, 0.7, 70, 0.6, 12); write("steel-slide.wav", fades(a, 10, 120), -4); }
// air-squeeze: air compressed under the falling ram (rising hiss, pitch climbs), 3.4 s
{ const a = len(3.4), n = svf(noise(a.length, 661), t => 300 + 1600 * Math.pow(t / 3.4, 2), 0.25);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += n[i] * (0.2 + 0.8 * t / 3.4); } write("air-squeeze.wav", fades(a, 200, 150), -10); }
// fuel-spray: a short fine mist hiss from the injector, 0.7 s
{ const a = len(0.7), n = svf(noise(a.length, 671), 5200, 0.5, "high");
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += n[i] * Math.exp(-t * 3); } write("fuel-spray.wav", fades(a, 10, 150), -12); }
// ignite: diesel lighting off (soft whoomp + crackle), 1.2 s
{ const a = len(1.2), lo = svf(noise(a.length, 681), t => 90 + 200 * Math.exp(-t * 5), 0.5, "low"), r = rng(682);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += lo[i] * 1.2 * Math.min(1, t * 30) * Math.exp(-t * 3) + (r() > 0.9985 ? r() * 0.5 : 0) * Math.exp(-t * 4); }
  write("ignite.wav", fades(a, 5, 200), -5); }
// crawler: tracked rig moving (diesel idle + track clatter), 3 s
{ const a = len(3), lo = svf(noise(a.length, 691), 90, 0.4, "low"), r = rng(692);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += lo[i] * (0.7 + 0.3 * Math.sin(2 * Math.PI * 24 * t)); }
  for (let k = 0; k < 30; k++) modal(a, k * 0.1 + 0.02 * r(), 900 + 200 * r(), METAL, 0.08, 40);
  write("crawler.wav", fades(a, 200, 400), -8); }
