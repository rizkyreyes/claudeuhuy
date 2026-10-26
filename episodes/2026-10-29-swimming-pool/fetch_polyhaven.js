// Download the Poly Haven (CC0) assets this scene uses into ./assets/polyhaven/<id>/ with MD5 checks. Run: node fetch_polyhaven.js
// Textures: 2k JPG maps (diffuse, normal GL, roughness). HDRI: 2k .hdr. Writes assets/polyhaven/manifest.json for build_scene.py.
const fs = require("fs"), path = require("path"), crypto = require("crypto");
const ROOT = path.join(__dirname, "assets", "polyhaven");
const H = { "User-Agent": "swimming-pool-3d (personal project)" };
const TEX = ["grass_ground", "excavated_soil_wall", "brushed_concrete", "blue_floor_tiles_01"];
const HDRIS = ["kloofendal_48d_partly_cloudy_puresky"];
async function get(url, dest, md5) {
  if (fs.existsSync(dest) && md5 && crypto.createHash("md5").update(fs.readFileSync(dest)).digest("hex") === md5) return 0;
  const r = await fetch(url, { headers: H });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  const buf = Buffer.from(await r.arrayBuffer());
  if (md5 && crypto.createHash("md5").update(buf).digest("hex") !== md5) throw new Error("MD5 mismatch " + url);
  fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, buf);
  return buf.length;
}
const files = async id => (await fetch("https://api.polyhaven.com/files/" + id, { headers: H })).json();
(async () => {
  let total = 0; const manifest = {};
  for (const id of TEX) {
    const f = await files(id); manifest[id] = {};
    for (const map of ["Diffuse", "nor_gl", "Rough"]) {
      const e = f[map] && f[map]["2k"]; if (!e) continue;
      const x = e.jpg || e.png; const name = path.basename(new URL(x.url).pathname);
      total += await get(x.url, path.join(ROOT, id, name), x.md5); manifest[id][map] = name;
    }
    console.log("tex  ", id, Object.keys(manifest[id]).join(","));
  }
  for (const id of HDRIS) {
    const x = (await files(id)).hdri["2k"].hdr, name = path.basename(new URL(x.url).pathname);
    total += await get(x.url, path.join(ROOT, id, name), x.md5); manifest[id] = { hdr: name }; console.log("hdri ", id, name);
  }
  fs.writeFileSync(path.join(ROOT, "manifest.json"), JSON.stringify(manifest, null, 1));
  fs.writeFileSync(path.join(ROOT, "LICENSE.txt"), "All assets in this folder are from Poly Haven (https://polyhaven.com), licensed CC0 1.0 (public domain).\n");
  console.log("downloaded", (total / 1e6).toFixed(1), "MB");
})().catch(e => { console.error(e.message); process.exit(1); });
