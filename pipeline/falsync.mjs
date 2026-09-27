// falsync.mjs — fal.ai calls that return media INLINE (sync_mode: true).
// Why: the fal media CDN (*.fal.media) is usually blocked by the sandbox egress proxy; queue.fal.run is not.
//
// Auth: FAL_KEY from env, else ~/.config/hyperframe-pro/fal.env, else NO header — in that case the cloud
// environment's fal.ai API credential (host queue.fal.run, header Authorization, prefix "Key") is added by the proxy.
//
//   node falsync.mjs image <out.jpg> <WxH> <low|medium|high> <prompt...>
//   node falsync.mjs video <first-frame.jpg> <out.mp4> <duration 6|10> <prompt...>      (minimax/h3-max 768P)
//   node falsync.mjs probe        # auth check: POSTs an EMPTY job (it fails validation, produces nothing).
//                                 # HTTP 200 = credential works, 401 = no credential attached.
import fs from "node:fs"; import os from "node:os"; import path from "node:path";

function key() {
  if (process.env.FAL_KEY) return process.env.FAL_KEY.trim();
  const f = path.join(os.homedir(), ".config/hyperframe-pro/fal.env");
  if (fs.existsSync(f)) { const m = fs.readFileSync(f, "utf8").match(/FAL_KEY\s*=\s*(.+)/); if (m) return m[1].trim(); }
  return null;   // proxy-injected credential
}
const K = key();
const H = { ...(K ? { Authorization: `Key ${K}` } : {}), "Content-Type": "application/json" };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function run(model, input, label = model) {
  let sub, t;
  for (let a = 1; a <= 3; a++) {            // transient "fetch failed" happens; retry the SUBMIT only
    try { sub = await fetch(`https://queue.fal.run/${model}`, { method: "POST", headers: H, body: JSON.stringify(input) }); t = await sub.text(); break; }
    catch (e) { if (a === 3) throw e; await sleep(3000 * a); }
  }
  if (!sub.ok) throw new Error(`${label} submit ${sub.status} ${t.slice(0, 400)}`);
  const { request_id, status_url, response_url } = JSON.parse(t);
  const t0 = Date.now();
  for (;;) {
    await sleep(4000);
    const j = await (await fetch(status_url, { headers: H })).json().catch(() => ({}));
    if (j.status === "COMPLETED") break;
    if (j.status === "FAILED" || j.error) throw new Error(`${label} FAILED ${JSON.stringify(j).slice(0, 400)}`);
    if (Date.now() - t0 > 20 * 60e3) throw new Error(`${label} timeout (request ${request_id})`);
  }
  // result fetch: retry — the job is already paid for, never re-submit because of a flaky download
  for (let a = 1; a <= 5; a++) {
    try {
      const r = await fetch(response_url, { headers: H }); const rt = await r.text();
      if (!r.ok) throw new Error(`result ${r.status} ${rt.slice(0, 300)}`);
      return { request_id, json: JSON.parse(rt) };
    } catch (e) { if (a === 5) throw new Error(`${label} result fetch failed for PAID request ${request_id}: ${e.message}`); await sleep(5000 * a); }
  }
}
export function saveDataUri(uri, out) {
  const m = String(uri).match(/^data:[^;]+;base64,(.*)$/s);
  if (!m) throw new Error(`expected a data URI (sync_mode), got: ${String(uri).slice(0, 80)}`);
  fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, Buffer.from(m[1], "base64")); return out;
}

if (process.argv[1] && process.argv[1].endsWith("falsync.mjs")) {
  const [cmd, ...a] = process.argv.slice(2);
  if (cmd === "probe") {
    const r = await fetch("https://queue.fal.run/openai/gpt-image-2", { method: "POST", headers: H, body: "{}" });
    console.log(`fal probe: HTTP ${r.status} — ${r.status === 200 || r.status === 422 ? "credential WORKS" : r.status === 401 ? "NO credential" : "check"} (local key: ${K ? "yes" : "no, relying on proxy"})`);
  } else if (cmd === "image") {
    const [out, size, quality, ...p] = a; const [w, h] = size.split("x").map(Number);
    const { request_id, json } = await run("openai/gpt-image-2", { prompt: p.join(" "), image_size: { width: w, height: h }, quality, num_images: 1, output_format: "jpeg", sync_mode: true }, path.basename(out));
    saveDataUri(json.images?.[0]?.url, out); console.log(`${out} ok ${request_id}`);
  } else if (cmd === "video") {
    const [img, out, dur, ...p] = a;
    const { request_id, json } = await run("minimax/h3-max/image-to-video", {
      prompt: p.join(" "), prompt_expansion_mode: "balanced", duration: +dur || 6, resolution: "768P", enable_safety_checker: true,
      image_url: `data:image/jpeg;base64,${fs.readFileSync(img).toString("base64")}`, sync_mode: true }, path.basename(out));
    saveDataUri(json.video?.url, out); console.log(`${out} ok ${request_id}`);
  } else { console.log("usage: probe | image <out> <WxH> <quality> <prompt> | video <img> <out> <dur> <prompt>"); process.exit(1); }
}
