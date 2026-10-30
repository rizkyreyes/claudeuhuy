// After the three create_post calls: mark the queue row scheduled, append the run log, commit + push.
//   node mark-scheduled.mjs <episode dir> <A|B> <tiktokId> <youtubeId> <instagramId> ["note"]
import fs from "fs"; import path from "path"; import { fileURLToPath } from "url"; import { execFileSync } from "child_process";
const [epDir, opt, tt, yt, ig, note = ""] = process.argv.slice(2);
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const slug = path.basename(epDir).split("-").slice(3).join("-");
const qf = path.join(REPO, "state/queue-3d.md");
let hit = null;
const q = fs.readFileSync(qf, "utf8").split(/\r?\n/).map(l => {
  if (!l.includes(`| ${slug} |`)) return l;
  const c = l.split("|"); hit = c[2].trim();
  c[5] = " scheduled "; c[6] = ` ${path.relative(REPO, epDir).replace(/\\/g, "/")} `;
  c[7] = ` cover ${opt}. Buffer: TikTok ${tt}, YT ${yt}, IG ${ig}. ${note} `;
  return c.join("|");
});
if (!hit) throw new Error(`no queue row for ${slug}`);
fs.writeFileSync(qf, q.join("\n"));
const today = new Date().toISOString().slice(0, 10);
fs.appendFileSync(path.join(REPO, "docs/run-log.md"), `\n## ${today} (laptop) ${slug}\n- Approved cover ${opt}, scheduled for ${hit}: TikTok ${tt}, YT ${yt}, IG ${ig}. ${note}\n`);
const git = (...a) => execFileSync("git", a, { cwd: REPO, stdio: "inherit" });
git("add", "state/queue-3d.md", "docs/run-log.md");
git("commit", "-q", "-m", `${slug} scheduled in Buffer\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`);
git("push", "-q", "origin", "main");
console.log(`queue: ${slug} -> scheduled (${hit})`);
