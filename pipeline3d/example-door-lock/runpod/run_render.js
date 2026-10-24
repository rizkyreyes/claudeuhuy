// Cloud render on Runpod: create pod -> wait for Blender -> upload .blend -> render -> download MP4 -> TERMINATE pod.
// The pod is always terminated in `finally`, even on error. RUNPOD_API_KEY comes from the environment; never printed.
// Usage: node run_render.js <packed.blend> <out.mp4>
const fs = require("fs"), path = require("path"), crypto = require("crypto");
const KEY = process.env.RUNPOD_API_KEY;
if (!KEY) { console.error("RUNPOD_API_KEY not set"); process.exit(1); }
const [blendPath, outPath] = process.argv.slice(2);
const API = "https://rest.runpod.io/v1";
const H = { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json" };
const TOKEN = crypto.randomBytes(24).toString("hex");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

async function api(method, p, body) {
  const r = await fetch(API + p, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
  const txt = await r.text();
  if (!r.ok) throw new Error(`${method} ${p} -> ${r.status} ${txt.slice(0, 300)}`);
  return txt ? JSON.parse(txt) : {};
}

(async () => {
  let podId = null; const t0 = Date.now();
  try {
    const server = fs.readFileSync(path.join(__dirname, "render_server.py")).toString("base64");
    let pod = null;
    const spec = {
      name: "door-lock-render", cloudType: "COMMUNITY", computeType: "GPU",
      gpuTypeIds: ["NVIDIA GeForce RTX 4090", "NVIDIA GeForce RTX 5090", "NVIDIA GeForce RTX 3090"], gpuTypePriority: "custom", gpuCount: 1,
      imageName: "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
      containerDiskInGb: 30, volumeInGb: 0, ports: ["8000/http"],
      env: { RENDER_TOKEN: TOKEN, SERVER_B64: server, NVIDIA_DRIVER_CAPABILITIES: "all",
             BLENDER_URL: "https://download.blender.org/release/Blender5.2/blender-5.2.3-linux-x64.tar.xz", FPS: "30" },
      dockerStartCmd: ["bash", "-c", "echo $SERVER_B64 | base64 -d > /srv.py && python3 /srv.py"],
    };
    for (let a = 1; a <= 10 && !pod; a++) {
      try { pod = await api("POST", "/pods", spec); }
      catch (e) { if (!/no instances/i.test(e.message) || a === 10) throw e; log("no GPU available yet, retry", a, "in 60 s"); await sleep(60000); }
    }
    podId = pod.id;
    log("pod created", podId, "cost/hr", pod.costPerHr ?? pod.adjustedCostPerHr, "gpu", pod.machine?.gpuDisplayName ?? "");
    const base = `https://${podId}-8000.proxy.runpod.net`;
    const PH = { "X-Token": TOKEN };
    const status = async () => { const r = await fetch(base + "/status", { headers: PH }); if (!r.ok) throw new Error("status " + r.status); return r.json(); };

    // wait for the server + Blender install (image pull can take several minutes)
    let st = null;
    for (let i = 0; i < 90; i++) {
      try { st = await status(); if (st.phase === "ready" || st.phase === "error") break; log("phase", st.phase); }
      catch (e) { if (i % 3 === 0) log("waiting for pod proxy..."); }
      await sleep(20000);
    }
    if (!st || st.phase !== "ready") throw new Error("pod not ready: " + JSON.stringify(st && { phase: st.phase, error: st.error, log: st.log_tail }));
    log("blender installed:", (st.log_tail.match(/Blender \d[\d.]+/) || ["?"])[0]);

    const blend = fs.readFileSync(blendPath);
    let r = await fetch(base + "/scene", { method: "PUT", headers: { ...PH, "Content-Length": String(blend.length) }, body: blend });
    log("uploaded", (await r.json()).received, "bytes");
    r = await fetch(base + "/start", { method: "POST", headers: PH }); log("start", await r.text());

    let last = -1, tr = Date.now();
    while (true) {
      await sleep(30000);
      try { st = await status(); } catch (e) { log("status error, retrying", e.message); continue; }
      if (st.frames !== last) { const rate = st.frames / ((Date.now() - tr) / 1000); log(`phase ${st.phase} frames ${st.frames}/2256 (${rate.toFixed(2)} fr/s)`); last = st.frames; }
      if (st.phase === "done") break;
      if (st.phase === "error") throw new Error("render error: " + st.error + "\n" + st.log_tail);
    }
    r = await fetch(base + "/result", { headers: PH });
    if (!r.ok) throw new Error("download " + r.status);
    fs.writeFileSync(outPath, Buffer.from(await r.arrayBuffer()));
    log("downloaded", outPath, (fs.statSync(outPath).size / 1e6).toFixed(1), "MB");
  } catch (e) {
    console.error("ERROR:", e.message);
    process.exitCode = 1;
  } finally {
    if (podId) {
      try { await api("DELETE", `/pods/${podId}`); log("pod TERMINATED", podId); }
      catch (e) { console.error("!!! FAILED TO TERMINATE POD", podId, e.message, "- terminate it in the Runpod console now"); process.exitCode = 2; }
    }
    log("wall time", ((Date.now() - t0) / 60000).toFixed(1), "min");
  }
})();
