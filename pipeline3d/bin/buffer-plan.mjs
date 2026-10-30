// Prints the three Buffer create_post payloads for an episode (it does not post).
//   node buffer-plan.mjs <episode dir> <thumbnailOffsetMs>
// Target day comes from the episode's row in state/queue-3d.md, title + caption from publish.md,
// slots from the playbook table. ET offset: -04:00 until 31 Oct 2026, -05:00 from 1 Nov 2026 (then -04:00 again from 8 Mar 2027).
import fs from "fs"; import path from "path"; import { fileURLToPath } from "url";
const [epDir, offMs] = process.argv.slice(2);
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const base = path.basename(epDir), slug = base.split("-").slice(3).join("-");

const row = fs.readFileSync(path.join(REPO, "state/queue-3d.md"), "utf8").split(/\r?\n/).find(l => l.includes(`| ${slug} |`));
if (!row) throw new Error(`no queue row for ${slug}`);
const m = row.match(/\| (Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2}) (\w{3}) (\d{4})/);
if (!m) throw new Error(`no target day in row: ${row}`);
const [, dow, dd, mon, yyyy] = m;
const MM = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 }[mon];
const date = `${yyyy}-${String(MM).padStart(2, "0")}-${dd.padStart(2, "0")}`;
const edt = (date >= "2026-03-08" && date < "2026-11-01") || (date >= "2027-03-14" && date < "2027-11-07");
const off = edt ? "-04:00" : "-05:00";

// playbook "Publishing" table, 24 h ET
const SLOTS = { Mon: { tiktok: 13, instagram: 19, youtube: 20 }, Tue: { tiktok: 6, instagram: 19, youtube: 20 },
  Wed: { tiktok: 22, instagram: 12, youtube: 19 }, Thu: { tiktok: 13, instagram: 9, youtube: 19 },
  Fri: { tiktok: 18, instagram: 22, youtube: 16 }, Sat: { tiktok: 17, instagram: 21, youtube: 19 }, Sun: { tiktok: 9, instagram: 21, youtube: 19 } }[dow];

const pub = fs.readFileSync(path.join(epDir, "publish.md"), "utf8");
const title = (pub.match(/\*\*([^*]*#shorts)\*\*/) || [])[1];
const cap = (pub.split(/^## Caption.*$/m)[1] || "").split(/^## /m)[0].trim();
if (!title || !cap) throw new Error("publish.md: title or caption not found");
if (title.length > 100) throw new Error(`YouTube title too long (${title.length})`);

const url = `https://raw.githubusercontent.com/rizkyreyes/claudeuhuy/main/media/${slug}.mp4`;
const assets = [{ video: { url, metadata: { thumbnailOffset: +offMs } } }];
const at = h => `${date}T${String(h).padStart(2, "0")}:00:00${off}`;
const plan = [
  { channel: "tiktok", channelId: "6ab28e9cea19ca0bdeb5efbd", dueAt: at(SLOTS.tiktok), metadata: { tiktok: { isAiGenerated: true } } },
  { channel: "youtube", channelId: "6ab290a4ea19ca0bdeb603a4", dueAt: at(SLOTS.youtube),
    metadata: { youtube: { title, categoryId: "27", privacy: "public", madeForKids: false, isAiGenerated: true, notifySubscribers: true } } },
  { channel: "instagram", channelId: "6abbd80aea19ca0bde2429ba", dueAt: at(SLOTS.instagram),
    metadata: { instagram: { type: "reel", shouldShareToFeed: true, isAiGenerated: true } } },
].map(p => ({ ...p, schedulingType: "automatic", mode: "customScheduled", text: cap, assets }));
console.log(`target ${dow} ${date} (ET ${off}); one video per ET day: check list_posts for ${date} before creating`);
console.log(JSON.stringify(plan, null, 1));
