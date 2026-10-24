// Procedural physical SFX for Road-Layers-3D (48 kHz, 16-bit mono WAV), deterministic.
// rain: hook ambience | rocks: big-stone clatter | gravel: fine pour | sizzle: hot asphalt | rumble: roller engine
const fs = require("fs"), path = require("path");
const SR = 48000;
const rng = seed => { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296) * 2 - 1; };
const db = x => Math.pow(10, x / 20);

function write(name, a, peakDb) {
  let pk = 0; for (const v of a) pk = Math.max(pk, Math.abs(v));
  const g = pk ? db(peakDb) / pk : 1, buf = Buffer.alloc(44 + a.length * 2);
  buf.write("RIFF", 0); buf.writeUInt32LE(36 + a.length * 2, 4); buf.write("WAVEfmt ", 8); buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20); buf.writeUInt16LE(1, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 2, 28);
  buf.writeUInt16LE(2, 32); buf.writeUInt16LE(16, 34); buf.write("data", 36); buf.writeUInt32LE(a.length * 2, 40);
  a.forEach((v, i) => buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, v * g)) * 32767), 44 + i * 2));
  fs.writeFileSync(path.join(__dirname, name), buf); console.log(name, (a.length / SR).toFixed(2) + "s", peakDb + " dBFS");
}
function svf(x, fc, q, mode = "band") {  // state-variable filter, fc may be a function of time
  let lo = 0, bd = 0; const y = new Float32Array(x.length);
  for (let i = 0; i < x.length; i++) {
    const f = 2 * Math.sin(Math.PI * Math.min(typeof fc === "function" ? fc(i / SR) : fc, SR / 6) / SR);
    const hi = x[i] - lo - q * bd; bd += f * hi; lo += f * bd; y[i] = mode === "low" ? lo : mode === "high" ? hi : bd;
  }
  return y;
}
const noise = (n, seed) => { const r = rng(seed), a = new Float32Array(n); for (let i = 0; i < n; i++) a[i] = r(); return a; };
const fades = (a, inMs, outMs) => { const ni = SR * inMs / 1000, no = SR * outMs / 1000;
  for (let i = 0; i < ni; i++) a[i] *= i / ni; for (let i = 0; i < no; i++) a[a.length - 1 - i] *= i / no; return a; };

// Scatter short filtered impacts: count, spread window, centre frequency range, decay.
function clatter(dur, count, start, spread, fLo, fHi, decay, seed) {
  const n = Math.round(SR * dur), out = new Float32Array(n), r = rng(seed);
  for (let k = 0; k < count; k++) {
    const t0 = start + ((r() + 1) / 2) * spread, i0 = Math.round(t0 * SR);
    const fc = fLo + ((r() + 1) / 2) * (fHi - fLo), amp = 0.4 + 0.6 * (r() + 1) / 2;
    const len = Math.round(SR * (4 / decay)), burst = svf(noise(len, seed * 1000 + k), fc, 0.35);
    for (let i = 0; i < len && i0 + i < n; i++) out[i0 + i] += amp * burst[i] * Math.exp(-i / SR * decay);
  }
  return out;
}

// Rain: broadband hiss + sparse droplets, 3.0 s (trimmed at the cut on the timeline).
{
  const n = SR * 3, hiss = svf(noise(n, 5), 4500, 0.9, "band"), low = svf(noise(n, 6), 900, 1.0, "low");
  const drops = clatter(3, 160, 0, 3, 2500, 7000, 260, 7), a = new Float32Array(n);
  for (let i = 0; i < n; i++) a[i] = 0.55 * hiss[i] + 0.35 * low[i] + 0.5 * drops[i];
  write("rain-v1.wav", fades(a, 80, 30), -18);
}
// Big stones: heavy knocks, onset at 0 s, mostly within 1.1 s.
{
  const a = clatter(1.6, 42, 0.0, 1.1, 250, 1400, 38, 11), body = clatter(1.6, 14, 0.0, 1.0, 90, 200, 20, 12);
  for (let i = 0; i < a.length; i++) a[i] += 0.8 * body[i];
  write("rocks-v1.wav", fades(a, 2, 120), -6);
}
// Gravel pour: dense, small, brighter impacts.
{
  const a = clatter(1.5, 420, 0.0, 1.05, 1500, 6000, 140, 21), bed = svf(noise(SR * 1.5, 22), 3000, 1.2);
  for (let i = 0; i < a.length; i++) { const t = i / SR; a[i] += 0.15 * bed[i] * (t < 1.1 ? 1 : Math.exp(-(t - 1.1) * 8)); }
  write("gravel-v1.wav", fades(a, 10, 150), -9);
}
// Hot asphalt sizzle: high-passed crackle swelling then fading, 1.8 s.
{
  const n = Math.round(SR * 1.8), hi = svf(noise(n, 31), 6000, 0.8, "high"), cr = clatter(1.8, 90, 0, 1.6, 3000, 8000, 400, 32), a = new Float32Array(n);
  for (let i = 0; i < n; i++) { const t = i / SR, e = Math.min(1, t / 0.3) * Math.exp(-Math.max(0, t - 0.6) * 1.6); a[i] = e * (0.3 * hi[i] + cr[i]); }
  write("sizzle-v1.wav", fades(a, 5, 60), -16);
}
// Roller engine: low diesel thrum (pulse train + harmonics) with drum rumble, 2.4 s.
{
  const n = Math.round(SR * 2.4), rum = svf(noise(n, 41), 120, 0.9, "low"), a = new Float32Array(n);
  let ph = 0;
  for (let i = 0; i < n; i++) {
    const t = i / SR; ph += 2 * Math.PI * 23 / SR;
    const pulse = Math.pow(Math.max(0, Math.sin(ph)), 6);
    const tone = 0.5 * Math.sin(2 * ph * 2) + 0.3 * Math.sin(3 * ph * 2) + 0.15 * Math.sin(5 * ph * 2);
    a[i] = (0.6 * pulse + 0.35 * tone * pulse + 0.7 * rum[i]) * Math.min(1, t / 0.5);
  }
  write("rumble-v1.wav", fades(a, 5, 250), -10);
}
