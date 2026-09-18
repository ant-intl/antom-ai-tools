import { writeFile, mkdir, appendFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { validateManifest, check } from './lib/skill-artifacts.mjs';
import { pages, releaseAssets, assetBytes, onlyAsset, markdownCell } from './lib/github.mjs';

export async function collectStats(client, queriedAt) {
  const rows = [];
  const releases = await client.releases();
  for (const release of releases.filter(r => !r.draft && !r.prerelease)) {
    const assets = await client.assets(release);
    // A formal release missing its contract must not silently disappear from the report.
    const manifestAsset = onlyAsset(assets, 'skills-manifest.json');
    check(manifestAsset.size <= 5 * 1024 * 1024, 'Manifest too large');
    const manifest = validateManifest(JSON.parse((await client.manifest(manifestAsset.id)).toString('utf8')));
    check(manifest.tag === release.tag_name, 'Manifest tag mismatch');
    const expected = new Set(manifest.skills.map(s => s.asset));
    check(assets.filter(a => a.name.endsWith('.zip')).every(a => expected.has(a.name)), 'Unmapped ZIP asset');
    for (const skill of manifest.skills) {
      const asset = onlyAsset(assets, skill.asset);
      check(asset.size === skill.size && (!asset.digest || asset.digest === `sha256:${skill.sha256}`), 'Asset metadata mismatch');
      check(Number.isSafeInteger(asset.download_count) && asset.download_count >= 0, 'Download count unavailable');
      rows.push({ skill: skill.name, version: release.tag_name, assetId: asset.id, downloads: asset.download_count, queriedAt });
    }
  }
  return rows.sort((a, b) => a.skill.localeCompare(b.skill) || a.version.localeCompare(b.version));
}
export function reports(rows, queriedAt) {
  const headers = ['Skill', 'Version', 'Asset ID', 'Cumulative downloads', 'Queried at (UTC)'];
  const values = rows.map(r => [r.skill, r.version, r.assetId, r.downloads, r.queriedAt]);
  const csv = [headers, ...values].map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\r\n') + '\r\n';
  const markdown = `## Skill ZIP download report\n\nQueried at: ${queriedAt}\n\nGitHub all-channel cumulative ZIP downloads; includes CLI discovery downloads. Not successful installations or unique users. Legacy raw-file downloads are excluded.\n\n` +
    (rows.length ? [`| ${headers.join(' | ')} |`, '| --- | --- | ---: | ---: | --- |', ...values.map(row => `| ${row.map(markdownCell).join(' | ')} |`)].join('\n') : 'No published skill releases.') + '\n';
  return { csv, markdown };
}
async function main() {
  const queriedAt = new Date().toISOString();
  const rows = await collectStats({ releases: () => pages('releases'), assets: releaseAssets, manifest: assetBytes }, queriedAt);
  const output = path.resolve('dist/skills-stats'); await mkdir(output, { recursive: true });
  const { csv, markdown } = reports(rows, queriedAt);
  await writeFile(path.join(output, 'downloads.csv'), csv);
  await writeFile(path.join(output, 'downloads.md'), markdown);
  if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY, markdown);
  console.log(markdown);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(async error => {
  console.error(`Statistics incomplete: ${error.message}`);
  if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY, '\n## Statistics failed\nReport incomplete; counts are unknown. No partial CSV was published.\n');
  process.exitCode = 1;
});
