import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { lstat, readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import JSZip from 'jszip';
import matter from 'gray-matter';

export const REPOSITORY = 'ant-intl/antom-ai-tools';
export const MAX_BYTES = 50 * 1024 * 1024;
export const MAX_FILES = 1000;
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export function check(condition, message) { if (!condition) throw new Error(message); }
export function validName(name) { return typeof name === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) && name.length <= 64; }
export function safePath(file) {
  return typeof file === 'string' && file.length > 0 && !/[\\\x00-\x1f\x7f:]/.test(file) && !file.startsWith('/') && file.split('/').every(p => p && p !== '.' && p !== '..');
}
export function validateManifest(value) {
  check(value?.schemaVersion === 1 && value.repository === REPOSITORY, 'Unsupported skills manifest');
  check(/^v\d+\.\d+\.\d+$/.test(value.tag), 'Invalid release tag');
  check(/^[a-f0-9]{40}$/.test(value.sourceCommit), 'Invalid source commit');
  check(Array.isArray(value.skills) && value.skills.length > 0, 'Empty skills manifest');
  const names = new Set();
  for (const skill of value.skills) {
    check(validName(skill.name) && !names.has(skill.name), 'Invalid or duplicate skill name'); names.add(skill.name);
    check(typeof skill.description === 'string' && skill.description.trim().length > 0 && skill.description.length <= 1024, 'Invalid description');
    check(skill.asset === `${skill.name}.zip`, 'Invalid ZIP asset name');
    check(Number.isSafeInteger(skill.size) && skill.size > 0 && skill.size <= MAX_BYTES, 'Invalid ZIP size');
    check(/^[a-f0-9]{64}$/.test(skill.sha256), 'Invalid ZIP digest');
    check(Array.isArray(skill.files) && skill.files.length > 0 && skill.files.length <= MAX_FILES, 'Invalid file count');
    const files = new Set(); let size = 0;
    for (const f of skill.files) {
      check(safePath(f.path) && !files.has(f.path.toLowerCase()), 'Unsafe or duplicate file path'); files.add(f.path.toLowerCase());
      check(Number.isSafeInteger(f.size) && f.size >= 0 && /^[a-f0-9]{64}$/.test(f.sha256), 'Invalid file metadata'); size += f.size;
    }
    check(skill.files.some(f => f.path === 'SKILL.md') && size <= MAX_BYTES, 'Missing SKILL.md or oversized skill');
  }
  return value;
}
export async function buildRelease(root, tag, output) {
  check(/^v\d+\.\d+\.\d+$/.test(tag), 'Version must be vX.Y.Z');
  const git = args => execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim();
  check(!git(['status', '--porcelain', '--untracked-files=all', '--', 'skills']), 'Commit all skill changes before packaging');
  const sourceCommit = git(['rev-parse', 'HEAD']);
  const tracked = execFileSync('git', ['ls-files', '-z', '--', 'skills/'], { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean).sort();
  const groups = new Map();
  for (const filename of tracked) {
    const [, name, ...parts] = filename.split('/');
    if (!parts.length) continue;
    check(validName(name), `Invalid skill folder: ${name}`);
    const rel = parts.join('/'); check(safePath(rel), `Unsafe path: ${filename}`);
    const items = groups.get(name) ?? []; items.push({ filename, rel }); groups.set(name, items);
  }
  const manifest = { schemaVersion: 1, repository: REPOSITORY, tag, sourceCommit, skills: [] };
  const archives = new Map();
  for (const [name, items] of groups) {
    check(items.length <= MAX_FILES && items.some(f => f.rel === 'SKILL.md'), `Invalid skill: ${name}`);
    const zip = new JSZip(); const files = []; let size = 0; let description;
    for (const { filename, rel } of items) {
      const absolute = path.join(root, filename);
      const stat = await lstat(absolute); check(stat.isFile() && !stat.isSymbolicLink(), `Not a regular file: ${filename}`);
      check(stat.size <= MAX_BYTES, `File too large: ${filename}`);
      const bytes = await readFile(absolute); size += bytes.length;
      check(size <= MAX_BYTES, `Skill too large: ${name}`);
      if (rel === 'SKILL.md') {
        const data = matter(bytes.toString('utf8')).data;
        check(data.name === name, `SKILL.md name differs from folder: ${name}`);
        check(data.metadata?.internal !== true, `Internal skill cannot be released: ${name}`);
        description = data.description;
      }
      files.push({ path: rel, size: bytes.length, sha256: sha256(bytes) });
      zip.file(rel, bytes, { date: new Date('2000-01-01T00:00:00Z'), createFolders: false, unixPermissions: 0o100644 });
    }
    const bytes = await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE', compressionOptions: { level: 9 }, platform: 'UNIX' });
    const asset = `${name}.zip`; archives.set(asset, bytes);
    manifest.skills.push({ name, description, asset, size: bytes.length, sha256: sha256(bytes), files });
  }
  validateManifest(manifest);
  await mkdir(output, { recursive: true });
  for (const [name, bytes] of archives) await writeFile(path.join(output, name), bytes);
  await writeFile(path.join(output, 'skills-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}
