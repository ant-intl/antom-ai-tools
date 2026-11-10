# Antom AI Tools

[📖 Read English version](README.md) · **简体中文**

Antom AI Tools 帮助开发者在 AI 产品中接入 Antom 支付。仓库提供可复用的 Agent 技能、适用于不同平台的编辑器插件，以及兼容 Agent Plugins 1.0 规范的可移植插件。后者可按需连接 Antom MCP 服务。

## 可用技能

| 技能 | 说明 |
|------|------|
| **antom-integration** | 接入 Antom 支付产品，包括一次性支付（One-time Payments）、令牌化支付（Tokenized Payment）和订阅支付（Subscription Payment）。 |
| **antom-reconciliation-expert** | 校验结算明细报表（CSV 或 XLSX）中的结算金额并分析费用。登录 Antom CLI 后可在线获取报表。 |
| **antom-channel-integration** | 使用 ACI 构建机构侧 AIS 渠道适配器，了解 SPI 契约，实现字段映射和安全规则，生成适配项目，并核对测试与交付要求。 |

<a name="antom-integration"></a>

<details>
<summary><strong>antom-integration</strong> · 支付接入</summary>

### 能解决什么问题

Antom 将核心支付能力封装为 AI 可读的标准技能。开发者只需用自然语言描述需求，就可以通过 Vibe Coding 快速接入支付，无需先梳理底层逻辑。

该技能帮助 AI 加载 Antom 知识库、回答接入问题并生成接入代码，降低支付接入的学习成本和开发工作量。

### 测试资源

当你向 AI 索要测试卡或要求测试支付时，它会从 Antom 官方文档实时获取最新的沙箱测试数据，无需在代码里写死测试数据。

| 来源 | 用途 |
|------|------|
| [`docs.antom.com/ac/ref/card.md`](https://docs.antom.com/ac/ref/card.md) | 沙箱测试卡，覆盖成功、失败、3DS、风控和无效输入场景 |
| [`docs.antom.com/ac/ref/wallet.md`](https://docs.antom.com/ac/ref/wallet.md) · [`testwallet.md`](https://docs.antom.com/ac/ref/testwallet.md) | 钱包、先买后付（BNPL）和网银等替代支付方式（APM）的测试方法，包括测试钱包应用及扫码或登录流程 |
| [`docs.antom.com/ac/cashierpay/testcases.md`](https://docs.antom.com/ac/cashierpay/testcases.md) | 上线验证清单，包含生产环境测试用例 |

在 Claude Code 中，插件也提供以下斜杠命令：

```text
/test-cards
/test-wallet
```

### 提示词示例

```text
帮我选择合适的 Antom 支付接入方式。
```

```text
生成 Antom 收银台接入代码。
```

```text
检查我的 Antom 支付流程是否存在安全问题。
```

### 注意事项

1. 向 AI 描述需求时，请明确支付场景，例如一次性支付（One-time Payment）或跳转至收银台支付（Redirect to CKP Payment），以免产生歧义。
2. 部署前，请自行审查 AI 生成的接入代码并验证业务逻辑。
3. 技能会随 Antom 产品迭代更新。建议定期重新运行安装命令获取最新版本。

</details>

<a name="antom-reconciliation-expert"></a>

<details>
<summary><strong>antom-reconciliation-expert</strong> · 结算对账</summary>

### 能解决什么问题

Antom 向商户提供结算明细报表（Settlement Detail）。手工核对结算金额、拆解费用构成和定位差异原因既耗时又容易出错，尤其是报表包含数百行记录，涉及多种费用类型和币种时。

你可以向 AI 提供本地结算明细报表，也可以直接用自然语言提问。这个技能可以解析报表数据、逐项校验结算公式、拆解费用构成并解释对账规则，减少手工核对结算金额所需的时间。

安装并登录 Antom CLI 后，也可以通过这个技能在线查询和下载结算明细报表。

### 安装

请按[官方安装指南](https://docs.antom.com/ac/reconcile/skill)在你使用的 AI 工具中安装技能，并配置 Antom CLI 以在线获取报表。

### 提示词示例

```text
帮我分析 SETTLEMENT_DETAIL_202604271985548486_20260428.xlsx。
```

```text
interchangeFee 是什么？它是怎么计算的？
```

```text
帮我核对报表中的结算金额，列出有差异的记录。
```

### 注意事项

1. 请提供**结算明细报表（Settlement Detail）**，文件名必须同时包含 `SETTLEMENT` 和 `DETAIL`。交易明细（Transaction Detail）和结算汇总（Settlement Summary）报表不受支持。
2. 仅支持 `.csv` 和 `.xlsx` 格式。`.xls`、`.pdf`、`.txt` 等其他格式不受支持。
3. 费用金额（如 interchangeFee、schemeFee）按报表原值展示。此技能不根据费用金额反推费率。
4. 技能会随 Antom 产品迭代更新。建议定期重新运行安装命令获取最新版本。

</details>

<a name="antom-channel-integration-aci"></a>

<details>
<summary><strong>antom-channel-integration (ACI)</strong> · 渠道接入（ACI）</summary>

### 能解决什么问题

Antom Channel Integration（ACI）通过 `antom-channel-integration` 技能和配套 CLI，帮助外部开发者按照 AIS 平台标准和 SDK 的 SPI 契约实现机构协议适配。

它提供面向具体任务的指引，涵盖 SPI 选择、请求和响应字段映射、安全处理、由平台管理的 HTTP 与路由、标准结果码映射，以及测试和交付。以平台实际提供的 AIS SDK 为准；实现机构专属行为时，应使用已确认的协议规则。

### 技能和 CLI 资源

共享源文件位于 [`skills/antom-channel-integration/`](skills/antom-channel-integration/)。随附的 [`ACI CLI`](skills/antom-channel-integration/scripts/aci-cli/README.md) 包含 Java 源码、FreeMarker 模板、测试、AIS SDK 1.5.2 及供下游项目使用的独立 POM，并支持使用方向键进行交互选择：

- `aci init` 根据所选的卡类或非卡类能力、3DS 流程、通知和安全规则，生成一个独立的适配器项目。
- `aci package` 在本地执行构建，检查测试证据、依赖和普通 JAR，并生成交付报告。它不会上传产物或修改平台配置。
- 该技能可回答接入问题，并在指定的适配器项目中实现经用户确认的字段映射和安全规则。它不会部署平台或修改生产配置。

请完整加载或安装 `skills/antom-channel-integration/` 目录，包括参考资料、脚本和 SDK。Gemini CLI 和支持可移植插件的客户端会从共享 `skills/` 目录发现此技能。查阅离线资料和使用本地 CLI 均无需连接 Antom MCP。

### 快速开始

如果只需要接入指引，加载技能后即可提问，无需 Java 或平台 SDK。生成项目时，请在 macOS 或 Linux 上使用 Java 8 和 Maven 3.6.3 或更高版本。Windows 尚未验证。请在仓库根目录运行：

```sh
mvn -f skills/antom-channel-integration/scripts/aci-cli/pom.xml clean verify
sh skills/antom-channel-integration/scripts/aci-cli/bin/aci --help
```

AIS SDK 1.5.2 及供下游项目使用的独立 POM 已包含在技能的 `scripts/aci-cli/sdk/` 目录中。构建完成后即可运行 `init`，无需另行下载或配置 SDK。Maven 还会生成 `target/aci-cli-0.1.0.zip`，内含可执行 JAR 和 SDK，可独立使用。交互模式使用方向键和回车键，Agent 和 CI 使用文档所述的 JSON 配置模式。

```sh
sh skills/antom-channel-integration/scripts/aci-cli/bin/aci init --output ../my-channel-adapter
```

生成的项目包含基础组装代码和自定义扩展点。打包前，请实现机构所需的字段映射和安全规则，准备独立的测试数据，并通过实际 SPI 入口的测试。相关步骤见 [CLI 设置](skills/antom-channel-integration/scripts/aci-cli/README.md#build-and-usage)、[SPI 索引](skills/antom-channel-integration/references/guide/reference/spi/README.md)、[测试流程](skills/antom-channel-integration/references/TESTING.md)和[交付检查清单](skills/antom-channel-integration/references/delivery.md)。

### 提示词示例

```text
使用 $antom-channel-integration 解释 pay 和 notifyPayment 中平台与适配器各自的职责。请勿修改文件。
```

```text
在我的适配器目录中使用 $antom-channel-integration。根据下面已确认的字段映射和安全规则实现 pay、inquiryPayment 和 refund。通过实际 SPI 入口添加独立测试，并列出尚未确认的协议细节。
```

### 注意事项

1. 平台负责渠道标识、商户上下文、域名和路径配置、HTTP 传输、密钥查询及 iPay 转发。适配器通过平台提供的服务完成机构协议适配。
2. 请勿在公开 Issue 或提交中包含真实密钥、生产凭据或卡数据。分发技能和 CLI 时，请附带 SDK JAR 及供下游项目使用的独立 POM，并从技能源码包中排除本地构建产物。
3. 本地测试通过后，仍须完成平台组装验证、机构联调测试和发布审批。

</details>

## 可移植 Agent 插件

仓库根目录遵循 [Agent Plugins 1.0 规范](https://agent-plugins.org/)：

- [`plugin.json`](plugin.json) 声明可移植插件的信息。
- [`skills/`](skills/) 是随插件分发的 Agent 技能的统一维护目录。
- [`mcp.json`](mcp.json) 声明可选的 Antom MCP 服务连接。

各兼容客户端自行管理安装、权限和身份验证。请按客户端说明，将本仓库根目录作为 Agent 插件加载。

### Antom MCP 服务

可移植插件声明了由 Antom 托管的 MCP 服务：

- 服务地址：`https://mcp.antom.com`
- 传输协议：Streamable HTTP
- 配置文件：[`mcp.json`](mcp.json)
- 使用说明：[Antom MCP 文档](https://docs.antom.com/ac/ref_zh-cn/mcp)

MCP 服务为现有技能提供补充能力。如果 MCP 连接不可用，兼容客户端仍可加载随插件分发的技能。

> **访问权限**：Antom MCP 服务目前按白名单开放。申请方式请参阅 [Antom MCP 文档](https://docs.antom.com/ac/ref_zh-cn/mcp)。申请获批后，由客户端通过 OAuth 流程完成身份验证。请勿将凭据写入 `mcp.json`。

## 平台支持与安装

Antom 的 AI 工具可以帮你生成支付接入代码、在沙箱测试支付，以及分析结算报表。授权后，AI Agent 还可以通过 Antom MCP 调用 Antom API。

各平台支持的 Antom 支付能力和安装方式见 [Antom AI Tools 官方文档](https://docs.antom.com/ac/ref/ai-tools?lang=zh-cn&portal_channel=Antom_Website_WeChat_Owned&utm_campaign=product_innovation&utm_content=daiding&utm_medium=article&utm_source=wechat)。

| 平台 | 可用能力 | 安装入口 |
|------|----------|----------|
| Cursor | 官方 **Antom** 插件支持支付接入、结算对账，以及通过 Antom MCP 调用 Antom API（需 OAuth 授权）。 | [Cursor 官方市场](https://cursor.com/marketplace/antom)，或运行 `/add-plugin antom-integration` · [社区目录](https://cursor.directory/plugins/antom-2) |
| ChatGPT（Codex） | Antom Integration 和 Antom Reconciliation Expert 可分别安装。 | [支付接入插件](https://chatgpt.com/plugins/plugins_6a96e1a333088191a3d94d8e5d379c10) · [对账专家插件](https://chatgpt.com/plugins/plugins_6a979109d2ac8191b059c526f9303693) |
| Claude Code | `antom-integration` 插件提供支付接入指导和沙箱测试命令。 | [从 GitHub 安装](#从-github-安装) |
| Gemini CLI | `antom-ai-tools` 扩展提供 Antom 支付接入和结算对账技能。 | [Gemini CLI 官方扩展目录](https://geminicli.com/extensions/)（搜索 `antom-ai-tools`） · [从 GitHub 安装](#从-github-安装) |
| Qoder | 可分别安装 Antom CLI、支付接入和结算对账技能。 | [Antom CLI](https://qoder.cn/marketplace/skill?id=26d12b83-481d-4988-a7fc-0e9e6c442384) · [支付接入](https://qoder.cn/marketplace/skill?id=82012ef1-e8ac-4ded-965a-95f9dd4ee5e7) · [对账专家](https://qoder.cn/marketplace/skill?id=83b8dd88-6ccf-4d02-87bf-27664242e62d) |
| 兼容 Agent Plugins 1.0 的客户端 | `antom-ai-tools` 可移植插件提供共享技能，可按需连接 Antom MCP。 | [可移植插件安装说明](#可移植-agent-插件) |

### 从 GitHub 安装

在 **Claude Code** 中添加本仓库的插件市场并安装插件。

```text
/plugin marketplace add ant-intl/antom-ai-tools
/plugin install antom-integration@antom
```

在 **Gemini CLI** 官方扩展目录中搜索 `antom-ai-tools`，打开条目即可复制安装命令，也可以直接运行下面的命令。

```bash
gemini extensions install https://github.com/ant-intl/antom-ai-tools
```

<details>
<summary>本地开发与验证</summary>

在 **Cursor** 中调试插件时，从工作副本复制插件，再重启 Cursor（2.6 或更高版本）。仓库的市场配置见 [`.cursor-plugin/marketplace.json`](.cursor-plugin/marketplace.json)。

```bash
cp -R providers/cursor/plugin ~/.cursor/plugins/local/antom-integration
```

在 **Claude Code** 中将插件市场指向本地工作副本，再验证插件。市场配置见 [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)。

```text
/plugin marketplace add /absolute/path/to/antom-ai-tools
```

```bash
claude plugin validate .
```

在 **Codex** 中加载本地插件时，可参考仓库的[市场配置](.codex-plugin/marketplace.json)和[插件清单](providers/codex/plugins/antom-integration/.codex-plugin/plugin.json)。旧版导入器读取 [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json)。

在 **Gemini CLI** 中验证并链接本地工作副本。

```bash
gemini extensions validate .
gemini extensions link .
```

链接后重启 Gemini CLI，再确认扩展和技能是否可用。

```text
/extensions list
/skills list
```

</details>

## 社区与支持

- 阅读[安装和沙箱教程](https://github.com/ant-intl/antom-ai-tools/discussions/categories/tutorials-best-practices)。
- 在[问答区（Q&A）](https://github.com/ant-intl/antom-ai-tools/discussions/categories/q-a)提出接入问题。
- 在[建议区（Ideas）](https://github.com/ant-intl/antom-ai-tools/discussions/categories/ideas)提出新的技能或使用场景。
- 在[成果展示区（Show and tell）](https://github.com/ant-intl/antom-ai-tools/discussions/categories/show-and-tell)分享你的项目。
- 浏览全部 [Antom AI Tools 讨论](https://github.com/ant-intl/antom-ai-tools/discussions)。

使用微信或企业微信扫描下方二维码，加入「Antom 开发者」交流群。二维码在 11 月 17 日前有效。

<img src="assets/wechat-group-qr.png" alt="Antom 开发者交流群二维码" width="360" />


如需技术支持，请通过 `TechnicalService@antom.com` 联系 Antom 技术服务团队。

如果 Antom AI Tools 对你有帮助，欢迎为仓库点 Star，关注后续更新。

## 许可证

仓库采用 MIT 许可证，详见 [`LICENSE`](LICENSE)。

`antom-channel-integration` 技能及其 ACI CLI 保留原有的 [Apache-2.0 许可证](skills/antom-channel-integration/scripts/aci-cli/THIRD-PARTY-NOTICES.md#component-license)。CLI 依赖保留各自的[第三方声明](skills/antom-channel-integration/scripts/aci-cli/THIRD-PARTY-NOTICES.md)。AIS SDK 1.5.2 随技能和 CLI 一起分发。机构协议和其他平台库保留各自的权利。
