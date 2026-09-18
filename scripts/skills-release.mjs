import { readFile, appendFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildRelease, REPOSITORY, sha256, check } from './lib/skill-artifacts.mjs';
import { api, pages, gh, assetBytes, releaseAssets, markdownCell } from './lib/github.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [mode, tag] = process.argv.slice(2);
const output = path.join(root, 'dist/skills-release');

async function run() {
  check(mode === 'build' || mode === 'prepare', 'Usage: node scripts/skills-release.mjs build|prepare vX.Y.Z');
  const manifest = await buildRelease(root, tag, output);
  if (mode === 'build') { console.log(`Validated ${manifest.skills.length} skill ZIPs in ${output}`); return; }
  check(process.env.GITHUB_REF === 'refs/heads/main' && process.env.GITHUB_REPOSITORY === REPOSITORY, 'Prepare must run on main in the official GitHub repository');
  check(manifest.sourceCommit === process.env.GITHUB_SHA, 'Checkout differs from workflow source');
  await prepareDraft(manifest, output);
}

export async function prepareDraft(manifest, output, client = { api, pages, gh, assetBytes, releaseAssets }) {
  const { api, pages, gh, assetBytes, releaseAssets } = client;
  const tag = manifest.tag;
  const marker = `<!-- antom-skills:${tag}:${manifest.sourceCommit} -->`;
  let release = pages('releases').find(r => r.tag_name === tag);
  if (release) check(release.draft && release.body?.includes(marker), 'Version already published or draft source differs; use a new version');
  const refs = api(`git/matching-refs/tags/${encodeURIComponent(tag)}`);
  const existingTag = refs.find(r => r.ref === `refs/tags/${tag}`);
  if (existingTag) check(existingTag.object.type === 'commit' && existingTag.object.sha === manifest.sourceCommit, 'Tag already points to a different source');
  if (!release) release = api('releases', 'POST', { tag_name: tag, target_commitish: manifest.sourceCommit, name: `Antom Skills ${tag}`, draft: true, prerelease: false, body: `${marker}\nPreparing and validating assets. Do not publish yet.` });
  const assets = releaseAssets(release);
  const names = [...manifest.skills.map(s => s.asset), 'skills-manifest.json'];
  check(assets.every(a => names.includes(a.name)), 'Draft contains unexpected assets');
  for (const name of names) {
    check(api(`releases/${release.id}`).draft, 'Release was published while uploading; stopped');
    const bytes = await readFile(path.join(output, name));
    const existing = assets.filter(a => a.name === name);
    check(existing.length <= 1, `Duplicate draft asset: ${name}`);
    if (existing.length) {
      check(existing[0].state === 'uploaded' && existing[0].size === bytes.length && sha256(assetBytes(existing[0].id)) === sha256(bytes), `Existing draft asset differs: ${name}`);
      continue;
    }
    gh(['release', 'upload', tag, path.join(output, name), '--repo', REPOSITORY]);
  }
  const verifiedAssets = releaseAssets(release);
  check(verifiedAssets.length === names.length, 'Draft asset list incomplete');
  for (const name of names) {
    const asset = verifiedAssets.find(a => a.name === name); const bytes = await readFile(path.join(output, name));
    check(asset?.state === 'uploaded' && asset.size === bytes.length, `Incomplete upload: ${name}`);
    // GitHub exposes digest for uploaded assets. Older responses require a byte readback.
    const digest = asset.digest ?? `sha256:${sha256(assetBytes(asset.id))}`;
    check(digest === `sha256:${sha256(bytes)}`, `Uploaded digest mismatch: ${name}`);
  }
  check(api(`releases/${release.id}`).draft, 'Release was published before validation finished');
  const table = ['| Skill | ZIP bytes | SHA-256 |', '| --- | ---: | --- |', ...manifest.skills.map(s => `| ${markdownCell(s.name)} | ${s.size} | ${s.sha256} |`)].join('\n');
  const body = `${marker}\nSource: ${manifest.sourceCommit}\n\n${table}\n\nValidated. Review the source and assets, then publish this release. Published assets must never be replaced.\n`;
  // Preserve the intended tag and source when updating an unpublished release.
  api(`releases/${release.id}`, 'PATCH', { body, tag_name: tag, target_commitish: manifest.sourceCommit });
  release = api(`releases/${release.id}`);
  check(release.draft && release.tag_name === tag && release.target_commitish === manifest.sourceCommit, 'Draft version or source changed; review the release before publishing');
  if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY, `## Skills draft ready\n\n[Review draft](${release.html_url})\n\n${body}`);
  console.log(`Draft ready: ${release.html_url}. Human publication required.`);
  return release;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) run().catch(error => { console.error(error.message); process.exitCode = 1; });
