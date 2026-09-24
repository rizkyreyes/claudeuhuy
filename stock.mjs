// stock.mjs — free stock footage search + download (Pexels first, Pixabay second).
//
//   node stock.mjs search "<query>" [video|photo]          # prints candidates as JSON (id, source, size, duration, url, page)
//   node stock.mjs get <url> <out>                          # downloads one file (follows redirects)
//
// Auth:
//   Pexels  — PEXELS_KEY env if set, else NO header: the cloud environment's Pexels API credential
//             (host api.pexels.com, header Authorization, empty prefix) is added by the proxy.
//   Pixabay — PIXABAY_KEY env var (Pixabay takes the key in the URL, so it cannot be a proxy credential).
//
// Licensing: Pexels and Pixabay content is free for commercial use without attribution; still log every
// file used in publish/sources.txt (source + page URL + author) so provenance is always answerable.
import fs from "node:fs"; import path from "node:path";

const PEXELS = process.env.PEXELS_KEY || null;
const PIXABAY = process.env.PIXABAY_KEY || null;

async function pexels(q, kind) {
  const base = kind === "photo" ? "https://api.pexels.com/v1/search" : "https://api.pexels.com/videos/search";
  const r = await fetch(`${base}?query=${encodeURIComponent(q)}&orientation=portrait&per_page=10`, { headers: PEXELS ? { Authorization: PEXELS } : {} });
  if (!r.ok) return { error: `pexels ${r.status}` };
  const j = await r.json();
  if (kind === "photo") return (j.photos || []).map((p) => ({ source: "pexels", id: p.id, w: p.width, h: p.height, url: p.src.original, page: p.url, author: p.photographer }));
  return (j.videos || []).map((v) => {
    const f = (v.video_files || []).filter((x) => x.width && x.height >= x.width).sort((a, b) => b.height - a.height)
      .find((x) => x.height <= 2160) || (v.video_files || [])[0];
    return { source: "pexels", id: v.id, w: f?.width, h: f?.height, duration: v.duration, url: f?.link, page: v.url, author: v.user?.name };
  });
}
async function pixabay(q, kind) {
  if (!PIXABAY) return { error: "PIXABAY_KEY not set" };
  const base = kind === "photo" ? "https://pixabay.com/api/" : "https://pixabay.com/api/videos/";
  const r = await fetch(`${base}?key=${PIXABAY}&q=${encodeURIComponent(q)}&per_page=10&safesearch=true${kind === "photo" ? "&orientation=vertical" : ""}`);
  if (!r.ok) return { error: `pixabay ${r.status}` };
  const j = await r.json();
  if (kind === "photo") return (j.hits || []).map((h) => ({ source: "pixabay", id: h.id, w: h.imageWidth, h: h.imageHeight, url: h.largeImageURL, page: h.pageURL, author: h.user }));
  return (j.hits || []).map((h) => { const v = h.videos.large?.url ? h.videos.large : h.videos.medium;
    return { source: "pixabay", id: h.id, w: v.width, h: v.height, duration: h.duration, url: v.url, page: h.pageURL, author: h.user }; });
}

const [cmd, a1, a2] = process.argv.slice(2);
if (cmd === "search") {
  const kind = a2 === "photo" ? "photo" : "video";
  const [px, pb] = await Promise.all([pexels(a1, kind), pixabay(a1, kind)]);
  console.log(JSON.stringify({ query: a1, kind, pexels: px, pixabay: pb }, null, 1));
} else if (cmd === "get") {
  const r = await fetch(a1, { redirect: "follow" });
  if (!r.ok) { console.error(`download ${r.status} ${a1}`); process.exit(1); }
  fs.mkdirSync(path.dirname(path.resolve(a2)), { recursive: true });
  fs.writeFileSync(a2, Buffer.from(await r.arrayBuffer()));
  console.log(`${a2} ${fs.statSync(a2).size} bytes`);
} else { console.log("usage: search \"<query>\" [video|photo] | get <url> <out>"); process.exit(1); }
