# Skills 发布与下载统计

技能唯一源码是 `skills/`；provider 同步流程保持不变。官网只选择正式 Release，不追踪 main。

## 准备和发布版本

1. 将技能及相应 provider 副本通过现有 PR 审核合入 main，确保 `skills-sync-check` 通过。
2. 打开 Actions → sync-skills → Run workflow，选择 main、operation=`prepare-release`，version=`vX.Y.Z`。
3. 查看运行摘要中的源 commit、技能列表及草稿链接。工作流将每个技能打成一个独立 ZIP，附带 `skills-manifest.json`。整个流程不执行技能脚本。
4. 检查源码、产物和校验结果后，人工发布草稿 Release。GitHub 发布不会自动更新官网。
5. 官网维护人在 idocs-next 执行 `npm run skills:sync`，选择版本和技能，审查 diff 后走官网发布流程。

相同版本重跑只补齐同源码、同内容的草稿。正式版本禁止覆盖资产或移动 tag；有变化请用新版本。保留历史版本以支持官网回滚。发布时不要提前点击尚未完成上传、校验的草稿。

本地只打包验证：`bun install --frozen-lockfile`，然后 `bun run test:skills` 和 `bun run skills:build v0.0.0`。输出位于忽略目录 `dist/skills-release/`，不会创建远端 Release。

## 下载统计

Actions → sync-skills → Run workflow → operation=`download-stats`；无需填写 version。

运行摘要展示所有正式版本的 Skill、版本、asset ID、GitHub 累计下载次数和查询时间。Artifacts 中下载 `skill-download-report-<run-id>`，里面的 CSV 和 Markdown 与摘要使用同一份数据；报告保留 30 天。

该任务只有读取权限，只下载小型发布清单，不下载 ZIP，不增加 ZIP 下载计数。分页读取 Releases 与 assets，任何数据缺失或请求失败都会使任务失败，不提供部分成功的报告或用 0 代替未知。

口径是 GitHub 全渠道累计 ZIP 下载量，包括官网、人工下载、同步和验收。CLI 在选择安装前可能已下载技能，因此不等于安装成功量、独立用户或使用次数，也不包含旧版逐文件获取。GitHub 原生保存累计值，手动查询不影响累计统计；本期不提供每日趋势。

## 发布契约 v1

`skills-manifest.json` 顶层为 `schemaVersion: 1`、`repository`、`tag`、`sourceCommit`、`skills`。每个技能包含 `name`、`description`、`asset`、`size`、`sha256` 和 `files`；每个文件记录 `path`、`size`、`sha256`。JSON 和 ZIP 以实际字节为准，不手工改摘要。

ZIP 根目录直接包含 `SKILL.md`。全部文件（含空文件）保留，最大 50 MiB 解压体积及 1000 文件；不接受链接、加密包、危险或重复路径。已发布 Release 应当同时具有完整清单和对应 ZIP。
