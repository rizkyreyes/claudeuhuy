// typo.mjs: kinetic typography layer for build-broll.mjs (Rizky, 18 Oct 2026: "so it doesn't look flat").
// Optional exports in shots.mjs, all anchored to spoken words (never to clock times):
//   export const emphasis = ["cup", "180", "quarters"];            // caption words shown bigger + yellow (gen-shared buildCaptions)
//   export const slams = [{ word: "not", nth: 1, lines: ["NOT A", "REAL CUP"], dur: 1.2 }];
//        big two-line text in the upper middle; the LAST line is in the accent color; the frame dims behind it
//   export const counters = [{ word: "180", nth: 1, to: 180, unit: "ML", dur: 1.5 }];
//        a number that counts up to `to` and lands on the spoken word, unit underneath
// Sound: each moment gets a matching effect from pipeline/sfx (ElevenLabs-generated, ours to use; manifest sfx.json):
//   slam = whoosh into an impact, counter = fast ticks then an impact on the spoken number, emphasis word = soft pop.
//   Each family has 3 variants; one variant per family is picked per video from the slug, so videos rotate but a
//   video stays consistent. The FIRST moment (the hook) gets a payoff sound instead of the impact (Rizky, 19 Oct 2026):
//   export const payoff = "myth-bust";   // from the queue row tag: myth-bust | history | safety | hack | convenience | manufacturing
// How many (Rizky, 18 Oct 2026: "not too few, not too many", fit it to the video), enforced below:
//   videos of 45 s or more: 3–6 moments (slams + counters), the first one inside the first 4 s (the hook claim),
//   at least 5 s between moments, 5–12 emphasis words; shorter cuts: 2–4 moments, at least 2 s apart.
// Every number shown must be spoken, nothing in the right 140 px (app buttons) or below y 1450 (captions).
// Text never covers the object for more than ~1.5 s.
import fs from "node:fs";
import path from "node:path";

const fx = (n) => +(+n).toFixed(3);
const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, "");
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export function buildTypography({ VO, VO_START, proj, slams = [], counters = [], emphasis = [], payoff = null }) {
  if (!slams.length && !counters.length && !emphasis.length) return { css: "", html: [], tl: [] };
  // the font travels with the project so the renderer can load it
  const fontSrc = path.join(path.dirname(new URL(import.meta.url).pathname), "fonts", "ArchivoBlack-Regular.ttf");
  fs.mkdirSync(path.join(proj, "assets/fonts"), { recursive: true });
  fs.copyFileSync(fontSrc, path.join(proj, "assets/fonts/ArchivoBlack-Regular.ttf"));

  const at = (word, nth = 1) => {
    let n = 0;
    for (const w of VO.words) if (norm(w.text).startsWith(norm(word)) && ++n === nth) return { t: fx(VO_START + w.start), end: fx(VO_START + w.end) };
    throw new Error(`typography cue "${word}" (#${nth}) not found in the voice-over`);
  };
  // ---- how many moments: fit the length, never a wall of effects
  const total = VO_START + VO.duration;
  const moments = [...slams.map((s) => at(s.word, s.nth).t), ...counters.map((c) => at(c.word, c.nth).t)].sort((a, b) => a - b);
  const long = total >= 45;
  const [minM, maxM] = long ? [3, 6] : [2, 4];
  if (moments.length < minM || moments.length > maxM) throw new Error(`typography: ${moments.length} moments (slams + counters) for a ${total.toFixed(0)} s video; use ${minM}–${maxM}`);
  if (long && moments[0] > 4) throw new Error(`typography: first moment at ${moments[0]} s; put one on the hook claim inside the first 4 s`);
  const gap = long ? 5 : 2;
  for (let i = 1; i < moments.length; i++) if (moments[i] - moments[i - 1] < gap) throw new Error(`typography: moments at ${moments[i - 1]} s and ${moments[i]} s are under ${gap} s apart; drop one or move it`);
  if (long && (emphasis.length < 5 || emphasis.length > 12)) throw new Error(`typography: ${emphasis.length} emphasis words; use 5–12 for a video this long`);

  // ---- sound effects travel with the project like the font
  const sfxDir = path.join(path.dirname(new URL(import.meta.url).pathname), "sfx");
  fs.mkdirSync(path.join(proj, "assets/sfx"), { recursive: true });
  const MAN = JSON.parse(fs.readFileSync(path.join(sfxDir, "sfx.json"), "utf8"));
  const slug = path.basename(path.resolve(proj));
  const hash = (str) => { let h = 2166136261; for (const ch of str) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0; return h; };
  const pick = (fam) => { const v = hash(slug + ":" + fam) % 3; return v === 0 ? fam : `${fam}${v + 1}`; };
  const HOOK = { "myth-bust": "hook-myth", history: "hook-history", safety: "hook-safety", hack: "hook-hack", convenience: "hook-hack", manufacturing: "hook-manufacturing" };
  const P = { whoosh: pick("whoosh"), impact: pick("impact"), ticks: pick("ticks"), pop: pick("pop"), hook: payoff && HOOK[payoff] };
  if (payoff && !P.hook) throw new Error(`typography: unknown payoff "${payoff}" (use ${Object.keys(HOOK).join(", ")})`);
  for (const f of new Set(Object.values(P).filter(Boolean))) fs.copyFileSync(path.join(sfxDir, `${f}.wav`), path.join(proj, `assets/sfx/${f}.wav`));
  let sfxN = 0;
  // `at` is when the HIT of the sound should land; the file starts `hit` seconds earlier
  const sfx = (fam, at, vol) => { const name = P[fam], m = MAN[name]; return `<audio id="sfx-${sfxN}" src="assets/sfx/${name}.wav" data-start="${fx(Math.max(0, at - m.hit))}" data-duration="${m.len}" data-track-index="${40 + sfxN++}" data-volume="${vol}"></audio>`; };
  const first = moments[0];
  const hitSfx = (t, vol) => (P.hook && Math.abs(t - first) < 0.01 ? sfx("hook", t + 0.02, 0.55) : sfx("impact", t + 0.02, vol));
  console.log(`typography sounds for ${slug}: ${Object.values(P).filter(Boolean).join(", ")}`);

  const html = [`<div id="tdim" class="clip" data-start="0" data-duration="${fx(VO_START + VO.duration + 1.2)}" data-track-index="8"></div>`];
  const tl = [`tl.set("#tdim",{opacity:0},0);`];

  slams.forEach((s, i) => {
    const { t } = at(s.word, s.nth);
    const dur = s.dur ?? 1.2, id = `slam-${i}`;
    const lines = s.lines.map((l, k) => `<div class="sl${k === s.lines.length - 1 ? " acc" : ""}" id="${id}-l${k}">${esc(l)}</div>`).join("");
    html.push(sfx("whoosh", t - 0.1, 0.35), hitSfx(t, 0.5));
    html.push(`<div class="slam clip" id="${id}" data-start="${fx(t - 0.02)}" data-duration="${fx(dur + 0.25)}" data-track-index="9">${lines}</div>`);
    tl.push(`tl.to("#tdim",{opacity:0.5,duration:0.12,ease:"power1.out"},${fx(t - 0.02)});`);
    s.lines.forEach((_, k) => tl.push(`tl.fromTo("#${id}-l${k}",{opacity:0,scale:1.7,y:-30,rotation:${k % 2 ? 2 : -2}},{opacity:1,scale:1,y:0,rotation:0,duration:0.22,ease:"back.out(2.6)"},${fx(t + k * 0.09)});`));
    tl.push(`tl.fromTo("#${id}",{x:0},{x:6,duration:0.05,yoyo:true,repeat:3,ease:"none"},${fx(t + 0.2)});`);
    tl.push(`tl.to("#${id}",{opacity:0,scale:0.92,duration:0.16,ease:"power2.in"},${fx(t + dur)});`);
    tl.push(`tl.to("#tdim",{opacity:0,duration:0.2},${fx(t + dur)});`);
  });

  counters.forEach((c, i) => {
    const { t } = at(c.word, c.nth);
    const dur = c.dur ?? 1.5, id = `cnt-${i}`, steps = 14, start = fx(t - 0.55);
    const vals = Array.from({ length: steps + 1 }, (_, k) => Math.round((c.to * (1 - Math.pow(1 - k / steps, 3)))));
    const nums = vals.map((v, k) => `<span class="cn" id="${id}-n${k}">${v.toLocaleString("en-US")}</span>`).join("");
    html.push(sfx("ticks", start + MAN[P.ticks].hit, 0.32), hitSfx(t, 0.42));
    html.push(`<div class="counter clip" id="${id}" data-start="${start}" data-duration="${fx(t - start + dur + 0.2)}" data-track-index="10"><div class="cnum">${nums}</div>${c.unit ? `<div class="cunit">${esc(c.unit)}</div>` : ""}</div>`);
    tl.push(`tl.to("#tdim",{opacity:0.45,duration:0.12},${start});`);
    tl.push(`tl.fromTo("#${id}",{opacity:0,scale:0.7},{opacity:1,scale:1,duration:0.18,ease:"back.out(2)"},${start});`);
    vals.forEach((_, k) => {
      const tk = fx(start + (0.55 * k) / steps);
      tl.push(`tl.set("#${id} .cn",{opacity:0},${tk});`, `tl.set("#${id}-n${k}",{opacity:1},${tk});`);
    });
    tl.push(`tl.fromTo("#${id} .cnum",{scale:1},{scale:1.12,duration:0.1,yoyo:true,repeat:1,ease:"power1.out"},${fx(t)});`);
    tl.push(`tl.to("#${id}",{opacity:0,y:-20,duration:0.16,ease:"power2.in"},${fx(t + dur)});`);
    tl.push(`tl.to("#tdim",{opacity:0,duration:0.2},${fx(t + dur)});`);
  });

  // soft pop on emphasis words, skipped next to a slam or counter so the big moments stay clean
  const EM = new Set(emphasis.map(norm));
  for (const w of VO.words) {
    const t = fx(VO_START + w.start);
    if (EM.has(norm(w.text)) && !moments.some((m) => Math.abs(m - t) < 0.8)) html.push(sfx("pop", t + 0.02, 0.22));
  }

  const css = `
@font-face{font-family:"ArchivoBlack";src:url("assets/fonts/ArchivoBlack-Regular.ttf")}
#tdim{position:absolute;inset:0;background:#05070A;opacity:0;z-index:92}
.slam{position:absolute;left:70px;right:150px;top:520px;z-index:96;text-align:left;opacity:1}
.slam .sl{font-family:"ArchivoBlack",Inter,sans-serif;font-size:150px;line-height:0.98;letter-spacing:-2px;color:#FFFFFF;opacity:0;transform-origin:0% 60%;text-shadow:0 8px 0 rgba(0,0,0,0.45),0 0 30px rgba(0,0,0,0.6)}
.slam .sl.acc{color:#FFD43B}
.counter{position:absolute;left:70px;right:150px;top:470px;z-index:96;text-align:center;opacity:0}
.counter .cnum{position:relative;height:330px;transform-origin:50% 60%}
.counter .cn{position:absolute;left:0;right:0;top:0;font-family:"ArchivoBlack",Inter,sans-serif;font-size:300px;line-height:1.05;color:#FFD43B;opacity:0;text-shadow:0 10px 0 rgba(0,0,0,0.45),0 0 40px rgba(0,0,0,0.6)}
.counter .cunit{font-family:"ArchivoBlack",Inter,sans-serif;font-size:96px;color:#FFFFFF;letter-spacing:4px;margin-top:-6px;text-shadow:0 6px 0 rgba(0,0,0,0.45)}
`;
  return { css, html, tl };
}
