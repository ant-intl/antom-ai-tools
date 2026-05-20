// Mirror the source-of-truth skills/ directory into each provider plugin package.
//
// Source: skills/<skill>/...
// Targets:
//   - providers/cursor/plugin/skills/<skill>/...
//   - providers/claude/plugin/skills/<skill>/...
//   - providers/codex/plugins/<skill>/skills/<skill>/...
//
// Usage:
//   node scripts/sync-skills.mjs
//   npm run sync-skills

import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(__filename), "..");

const SOURCE_DIR = path.join(repoRoot, "skills");

// Codex packages each skill under its own plugin directory, so the per-skill
// destination is computed dynamically below.
const CODEX_PLUGINS_DIR = path.join(repoRoot, "providers/codex/plugins");

const FLAT_TARGETS = [
  path.join(repoRoot, "providers/cursor/plugin/skills"),
  path.join(repoRoot, "providers/claude/plugin/skills"),
];

async function* walk(dir) {
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(p);
    else if (entry.isFile()) yield p;
  }
}

async function copyFile(src, dest) {
  await fs.mkdir(path.dirname(dest), { recursive: true });
  const content = await fs.readFile(src);
  await fs.writeFile(dest, content);
}

const run = async () => {
  const skillNames = (
    await fs.readdir(SOURCE_DIR, { withFileTypes: true })
  )
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

  if (skillNames.length === 0) {
    console.log("No skills found under skills/. Nothing to sync.");
    return;
  }

  let writeCount = 0;

  for (const skill of skillNames) {
    const skillSource = path.join(SOURCE_DIR, skill);
    const targets = [
      ...FLAT_TARGETS.map((base) => path.join(base, skill)),
      // Codex layout: providers/codex/plugins/<skill>/skills/<skill>/
      path.join(CODEX_PLUGINS_DIR, skill, "skills", skill),
    ];

    for await (const file of walk(skillSource)) {
      const rel = path.relative(skillSource, file);
      for (const target of targets) {
        const dest = path.join(target, rel);
        await copyFile(file, dest);
        console.log(`✓ ${path.relative(repoRoot, dest)}`);
        writeCount++;
      }
    }
  }

  console.log(
    `\nSynced ${skillNames.length} skill(s) — ${writeCount} file write(s).`,
  );
};

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
