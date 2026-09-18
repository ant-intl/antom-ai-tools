import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { buildRelease, validateManifest, sha256 } from './lib/skill-artifacts.mjs';
import { prepareDraft } from './skills-release.mjs';
import { collectStats, reports } from './skills-stats.mjs';
import { pages } from './lib/github.mjs';

async function fixture(t) {
  const root = await mkdtemp(path.join(tmpdir(), 'skills-publisher-')); t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, 'skills/test-skill/scripts'), { recursive: true });
  await writeFile(path.join(root, 'skills/test-skill/SKILL.md'), '---\nname: test-skill\ndescription: A sample skill\n---\n# Skill\n');
  await writeFile(path.join(root, 'skills/test-skill/scripts/__init__.py'), '');
  await writeFile(path.join(root, 'skills/test-skill/scripts/demo.py'), 'print("hello")\n');
  const git = (...args) => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
  git('init'); git('add', '.'); git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture');
  return { root, git, output: path.join(root, 'dist') };
}
test('packaging is deterministic and keeps complete files including empty files', async t => {
  const { root, output } = await fixture(t);
  const a = await buildRelease(root, 'v1.0.0', output); const bytes = await readFile(path.join(output, 'test-skill.zip'));
  const b = await buildRelease(root, 'v1.0.0', output);
  assert.deepEqual(a, b); assert.equal(a.skills[0].sha256, sha256(bytes)); assert.equal(a.skills[0].files.length, 3);
  assert.equal(a.skills[0].files.find(f => f.path.endsWith('__init__.py')).size, 0);
});
test('invalid metadata and uncommitted content fail closed', async t => {
  const { root, output, git } = await fixture(t);
  await writeFile(path.join(root, 'skills/test-skill/SKILL.md'), '---\nname: wrong\ndescription: Wrong\n---\n');
  await assert.rejects(buildRelease(root, 'v1.0.0', output), /Commit all skill changes/);
  git('add', '.'); git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','bad metadata');
  await assert.rejects(buildRelease(root, 'v1.0.0', output), /name differs/);
});
function fakeGitHub() {
  const state = { release: null, assets: [], uploads: 0, writes: 0 };
  const client = {
    pages: () => state.release ? [state.release] : [],
    api(endpoint, method = 'GET', body) {
      if (endpoint.startsWith('git/')) return [];
      if (method === 'POST') { state.writes++; state.release = { ...body, id: 7, html_url: 'https://github.com/example/draft' }; return state.release; }
      if (method === 'PATCH') { state.writes++; Object.assign(state.release, body); }
      return state.release;
    },
    releaseAssets: () => state.assets,
    assetBytes: id => state.assets.find(a => a.id === id).bytes,
    gh(args) {
      const bytes = execFileSync(process.execPath, ['-e', 'process.stdout.write(require("fs").readFileSync(process.argv[1]))', args[3]]);
      state.uploads++; state.assets.push({ name: path.basename(args[3]), id: state.uploads, bytes, size: bytes.length, state: 'uploaded', digest: `sha256:${sha256(bytes)}` });
    },
  };
  return { state, client };
}
test('draft retries reuse identical assets and never overwrite published versions', async t => {
  const { root, output } = await fixture(t); const manifest = await buildRelease(root, 'v1.0.0', output);
  const { state, client } = fakeGitHub();
  await prepareDraft(manifest, output, client); assert.equal(state.uploads, 2);
  await prepareDraft(manifest, output, client); assert.equal(state.uploads, 2);
  state.release.draft = false;
  await assert.rejects(prepareDraft(manifest, output, client), /already published/); assert.equal(state.uploads, 2);
});
test('updating draft notes preserves the requested version and verifies persisted metadata', async t => {
  const { root, output } = await fixture(t); const manifest = await buildRelease(root, 'v1.0.0', output);
  const { state, client } = fakeGitHub(); const api = client.api;
  client.api = (endpoint, method, body) => {
    const result = api(endpoint, method, body);
    if (method === 'PATCH' && body.tag_name === undefined) state.release.tag_name = 'untagged-placeholder';
    return result;
  };
  const release = await prepareDraft(manifest, output, client);
  assert.equal(release.tag_name, manifest.tag);
  assert.equal(release.target_commitish, manifest.sourceCommit);
  client.api = (endpoint, method, body) => {
    const result = api(endpoint, method, body);
    if (method === 'PATCH') state.release.tag_name = 'unexpected-tag';
    return result;
  };
  await assert.rejects(prepareDraft(manifest, output, client), /Draft version or source changed/);
});
test('partial draft resumes, but different bytes or source never get overwritten', async t => {
  const { root, output } = await fixture(t); const manifest = await buildRelease(root, 'v1.0.0', output);
  const { state, client } = fakeGitHub();
  const upload = client.gh; client.gh = args => { if (state.uploads === 1) throw new Error('network failure'); return upload(args); };
  await assert.rejects(prepareDraft(manifest, output, client), /network/); assert.equal(state.assets.length, 1);
  client.gh = upload; await prepareDraft(manifest, output, client); assert.equal(state.assets.length, 2);
  state.assets[0].bytes = Buffer.from('tampered');
  await assert.rejects(prepareDraft(manifest, output, client), /differs/);
  await assert.rejects(prepareDraft({ ...manifest, sourceCommit: 'f'.repeat(40) }, output, client), /source differs/);
});
test('statistics exclude drafts, map all versions and fail on incomplete counts', async t => {
  const { root, output } = await fixture(t); const manifest = await buildRelease(root, 'v1.0.0', output);
  const client = {
    releases: () => [{ id: 1, tag_name: 'v1.0.0' }, { id: 2, tag_name: 'v2.0.0' }, { id: 3, draft: true }],
    assets: r => [{ name: 'skills-manifest.json', state: 'uploaded', id: r.id, size: 100 }, { name: 'test-skill.zip', state: 'uploaded', id: r.id + 10, size: manifest.skills[0].size, download_count: 42 }],
    manifest: id => Buffer.from(JSON.stringify({ ...manifest, tag: `v${id}.0.0` })),
  };
  const rows = await collectStats(client, '2026-09-18T00:00:00Z'); assert.equal(rows.length, 2); assert.equal(rows[1].downloads, 42);
  const { csv, markdown } = reports(rows, '2026-09-18T00:00:00Z'); assert.equal(csv.split('\r\n').length, 4); assert.match(markdown, /v2.0.0/);
  const original = client.assets; client.assets = r => original(r).map(a => ({ ...a, download_count: undefined }));
  await assert.rejects(collectStats(client, 'now'), /unavailable/);
  client.assets = () => []; await assert.rejects(collectStats(client, 'now'), /Missing/);
});
test('GitHub collection explicitly flattens paginated responses', () => {
  const list = pages('releases', args => { assert.ok(args.includes('--paginate')); assert.ok(args.includes('--slurp')); return '[[{"id":1}],[{"id":2}]]'; });
  assert.deepEqual(list, [{ id: 1 }, { id: 2 }]);
});

test('packager rejects tracked symlinks', async t => {
  const { root, output, git } = await fixture(t);
  await symlink('demo.py', path.join(root, 'skills/test-skill/scripts/link.py'));
  git('add', '.'); git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','link');
  await assert.rejects(buildRelease(root, 'v1.0.0', output), /Not a regular file/);
});
