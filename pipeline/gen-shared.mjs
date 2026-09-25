// gen-shared.mjs — shared helpers for the "Hidden In Your Home" hyperframe-pro builds.
// Kept close to the plugin's worked example (example/build.mjs) so lint's assumptions hold.
import fs from "node:fs";
import path from "node:path";
export const fx = (n) => +n.toFixed(3);
export const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

/** TA = Time After. Next occurrence of `word` strictly after `after`, in seconds (VO_START baked in). */
export function makeTA(VO, VO_START) {
  return function TA(word, after) {
    for (const w of VO.words) {
      const t = fx(VO_START + w.start);
      if (t > after + 0.01 && norm(w.text).startsWith(norm(word))) return t;
    }
    throw new Error(`cue "${word}" after ${after}s not found — the script changed; re-cue this beat`);
  };
}

export function makeMotion(tl) {
  const enter = (sel, at, { d = 0.34, y = 28, scale = null } = {}) =>
    tl.push(`tl.fromTo("${sel}",{autoAlpha:0,y:${y}${scale ? `,scale:${scale}` : ""}},{autoAlpha:1,y:0${scale ? ",scale:1" : ""},duration:${d},ease:"power3.out"},${fx(at)});`);
  const exit = (sel, at, { d = 0.22, y = -30 } = {}) => {
    tl.push(`tl.to("${sel}",{autoAlpha:0,y:${y},duration:${d},ease:"power2.in"},${fx(at)});`);
    tl.push(`tl.set("${sel}",{autoAlpha:0},${fx(at + d)});`);
  };
  const slam = (sel, at, { d = 0.34, from = 1.28 } = {}) =>
    tl.push(`tl.fromTo("${sel}",{autoAlpha:0,scale:${from},filter:"blur(10px)"},{autoAlpha:1,scale:1,filter:"blur(0px)",duration:${d},ease:"power4.out"},${fx(at)});`);
  const kenBurns = (sel, at, hold, { to = 1.06, dir = 1 } = {}) => {
    const a = dir > 0 ? 1 : to, b = dir > 0 ? to : 1;
    tl.push(`tl.fromTo("${sel}",{scale:${a}},{scale:${b},duration:${fx(hold)},ease:"sine.inOut"},${fx(at)});`);
  };
  return { enter, exit, slam, kenBurns };
}

/** Four-word (or sentence-boundary) caption lines timed off the VO word table. */
export function buildCaptions(VO, VO_START) {
  const caps = [], tlLines = [];
  const lines = []; let line = [];
  for (const w of VO.words) { line.push(w); if (line.length === 4 || /[.?!]$/.test(w.text)) { lines.push(line); line = []; } }
  if (line.length) lines.push(line);
  lines.forEach((ln, i) => {
    const st = fx(VO_START + ln[0].start - 0.06);
    const nx = lines[i + 1];
    const en = fx(nx ? VO_START + nx[0].start - 0.06 : VO_START + ln.at(-1).end + 0.3);
    caps.push(`<div class="cap clip" id="cap-${i}" data-start="${st}" data-duration="${fx(en - st)}" data-track-index="7">${ln.map((w, j) => `<span class="w" id="w-${i}-${j}">${esc(w.text)}</span>`).join(" ")}</div>`);
    tlLines.push(`tl.fromTo("#cap-${i}",{y:16,opacity:0},{y:0,opacity:1,duration:0.18,ease:"power2.out"},${st});`);
    // karaoke: each word lights up on the frame it is spoken, then settles to "already said"
    ln.forEach((w, j) => {
      const ws = fx(VO_START + w.start);
      const we = fx(Math.max(VO_START + w.end, ws + 0.12));
      tlLines.push(`tl.fromTo("#w-${i}-${j}",{color:"rgba(244,245,247,0.45)",scale:1},{color:"#F5C242",scale:1.06,duration:0.08,ease:"power2.out",immediateRender:false},${ws});`);
      tlLines.push(`tl.to("#w-${i}-${j}",{color:"#F4F5F7",scale:1,duration:0.1,ease:"power1.out"},${we});`);
    });
  });
  return { caps, tlLines };
}

/**
 * Full-bleed b-roll track. SHOTS = [{ at, img } | { at, clip }] in time order; each shot holds until the next
 * one's `at`. Stills get a Ken Burns drift (direction alternates) and a 0.14 s cross-fade in; the previous
 * shot is hard-hidden just after the new one is fully up, so there is never a black frame between them.
 * A clip plays via data-start/data-duration (framework-owned — no GSAP autoAlpha on it). If a clip is shorter
 * than its window, its last frame (<clip>_last.jpg) takes over as a still for the remainder.
 */
export function buildBroll({ SHOTS, TOTAL, proj }) {
  const html = [], tl = [];
  const clipDur = (rel) => {
    const meta = path.join(proj, rel.replace(/\.mp4$/, ".json"));
    return fs.existsSync(meta) ? JSON.parse(fs.readFileSync(meta, "utf8")).duration : 0;
  };
  // expand clips that run short into clip + held last frame
  const seq = [];
  for (let i = 0; i < SHOTS.length; i++) {
    const s = SHOTS[i], end = i + 1 < SHOTS.length ? SHOTS[i + 1].at : TOTAL;
    if (s.clip && fs.existsSync(path.join(proj, s.clip))) {
      const d = clipDur(s.clip);
      if (d >= end - s.at - 0.01) seq.push({ ...s, end });
      else { seq.push({ ...s, end: fx(s.at + d) }); seq.push({ at: fx(s.at + d), img: s.clip.replace(/\.mp4$/, "_last.jpg"), end, still: "hold" }); }
    } else seq.push({ at: s.at, img: s.img || s.fallback, end });
  }
  seq.forEach((s, i) => {
    const id = `b${i}`, z = 10 + i, win = fx(s.end - s.at);
    if (s.clip) {
      html.push(`<video id="${id}" class="clip footage" muted playsinline preload="auto" src="${s.clip}" data-start="${fx(s.at)}" data-duration="${win}" data-track-index="${11 + (i % 2)}" style="position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:${z}"></video>`);
      return;
    }
    html.push(`<div id="${id}" class="ct footage bshot" style="z-index:${z}"><img id="${id}-img" src="${s.img}" alt=""></div>`);
    const fadeIn = i === 0 ? 0 : 0.14;
    if (i === 0) tl.push(`tl.set("#${id}",{autoAlpha:1},0);`);
    else if (s.still === "hold") tl.push(`tl.set("#${id}",{autoAlpha:1},${fx(s.at)});`);
    else tl.push(`tl.fromTo("#${id}",{autoAlpha:0},{autoAlpha:1,duration:${fadeIn},ease:"none"},${fx(s.at)});`);
    if (i + 1 < seq.length) tl.push(`tl.set("#${id}",{autoAlpha:0},${fx(s.end + 0.2)});`);
    // Ken Burns: alternate push-in / pull-out with a small lateral drift so consecutive stills never move alike
    const dir = i % 2 === 0, x = (i % 3 === 0 ? -1 : 1) * 26;
    const a = dir ? `scale:1.02,x:0` : `scale:1.14,x:${x}`, b = dir ? `scale:1.14,x:${x}` : `scale:1.02,x:0`;
    if (s.still !== "hold") tl.push(`tl.fromTo("#${id}-img",{${a}},{${b},duration:${fx(win + 0.35)},ease:"sine.inOut"},${fx(s.at)});`);
    else tl.push(`tl.fromTo("#${id}-img",{scale:1},{scale:1.06,duration:${fx(win + 0.35)},ease:"sine.out"},${fx(s.at)});`);
  });
  return { html, tl };
}

export function renderPage({ W, H, BG, INK, MUTED, ACCENT, DIM, TOTAL, extraCSS = "", bodyHTML, rootHTML = "", tl, caps, VO, VO_START, title }) {
  return `<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=${W}, height=${H}" /><title>${esc(title)}</title>
<script src="vendor/gsap.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:${W}px;height:${H}px;overflow:hidden;background:${BG}}
body{font-family:Inter,system-ui,sans-serif;color:${INK};-webkit-font-smoothing:antialiased}
#root{position:relative;width:${W}px;height:${H}px;overflow:hidden;background:${BG}}
#scene{position:absolute;inset:0;background:${BG}}
.ct{position:absolute;opacity:0;visibility:hidden;will-change:transform;z-index:4}
.card{top:620px;left:72px;right:72px;text-align:center}
.eyebrow{font-size:34px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:${ACCENT};margin-bottom:22px}
.headline{font-size:96px;font-weight:800;letter-spacing:-0.04em;line-height:1.14;padding-top:6px}
.headline b{color:${ACCENT}}
.note{font-size:46px;font-weight:600;line-height:1.3;color:${MUTED};margin-top:26px}
.chipRow{display:flex;gap:24px;justify-content:center;flex-wrap:wrap}
.chip{display:inline-block;padding:16px 32px;border-radius:100px;border:3px solid ${ACCENT};font-weight:800;font-size:38px;letter-spacing:-0.01em}
.chip.dim{border-color:${MUTED};color:${MUTED}}
.diagram{position:relative;height:420px;display:flex;align-items:center;justify-content:center}
.cap{position:absolute;left:50px;right:50px;top:1600px;text-align:center;font-size:62px;font-weight:900;line-height:1.2;letter-spacing:-0.01em;color:rgba(244,245,247,0.45);opacity:0;text-shadow:0 4px 18px rgba(0,0,0,0.85),0 0 3px rgba(0,0,0,0.9)}
.bshot{position:absolute;inset:0;overflow:hidden;opacity:0;visibility:hidden}
.bshot img{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;will-change:transform}
#scrim{position:absolute;left:0;right:0;bottom:0;height:720px;z-index:90;background:linear-gradient(to bottom,rgba(0,0,0,0) 0%,rgba(0,0,0,0.55) 45%,rgba(0,0,0,0.82) 100%)}
#topfade{position:absolute;left:0;right:0;top:0;height:260px;z-index:90;background:linear-gradient(to bottom,rgba(0,0,0,0.35),rgba(0,0,0,0))}
.cap{z-index:100}
.cap .w{display:inline-block;margin:0 5px;transform-origin:50% 70%;color:rgba(244,245,247,0.45)}
${extraCSS}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${TOTAL}" data-width="${W}" data-height="${H}">
  <div id="scene" class="clip" data-start="0" data-duration="${TOTAL}" data-track-index="3">
  ${bodyHTML}
  </div>
  ${rootHTML}
  ${caps.join("\n  ")}
  <audio id="vo" src="assets/vo/${VO.wav}" data-start="${VO_START}" data-duration="${fx(VO.duration)}" data-track-index="30" data-volume="1"></audio>
</div>
<script>
  window.__timelines = window.__timelines || {};
  gsap.set(".ct",{autoAlpha:0});
  const tl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });
  ${tl.join("\n  ")}
  window.__timelines["main"] = tl;
</script>
</body></html>
`;
}
