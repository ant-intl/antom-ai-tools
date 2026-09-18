import { execFileSync } from 'node:child_process';
import { REPOSITORY, check } from './skill-artifacts.mjs';
const prefix = `repos/${REPOSITORY}`;
export function gh(args, options = {}) {
  return execFileSync('gh', args, { maxBuffer: 55 * 1024 * 1024, ...options });
}
export function api(endpoint, method = 'GET', body) {
  const args = ['api', '--hostname', 'github.com', `${prefix}/${endpoint}`, '--method', method];
  if (body !== undefined) args.push('--input', '-');
  return JSON.parse(gh(args, { encoding: 'utf8', ...(body !== undefined ? { input: JSON.stringify(body) } : {}) }));
}
export function pages(endpoint, request = gh) {
  return JSON.parse(request(['api', '--hostname', 'github.com', `${prefix}/${endpoint}${endpoint.includes('?') ? '&' : '?'}per_page=100`, '--paginate', '--slurp'], { encoding: 'utf8' })).flat();
}
export function assetBytes(id) {
  check(Number.isSafeInteger(id) && id > 0, 'Invalid asset ID');
  return gh(['api', '--hostname', 'github.com', `${prefix}/releases/assets/${id}`, '-H', 'Accept: application/octet-stream']);
}
export function releaseAssets(release) { return pages(`releases/${release.id}/assets`); }
export function onlyAsset(assets, name) {
  const found = assets.filter(a => a.name === name);
  check(found.length === 1 && found[0].state === 'uploaded', `Missing, duplicate or incomplete asset: ${name}`);
  return found[0];
}
export function markdownCell(value) { return String(value).replace(/\|/g, '\\|').replace(/[\r\n]/g, ' '); }
