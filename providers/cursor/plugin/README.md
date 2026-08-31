# Antom Integration (Cursor)

Antom payment integration guidance for Cursor — product selection, integration
mode, code generation, and security validation.

## Contents

- `.cursor-plugin/plugin.json`: Cursor plugin manifest.
- `mcp.json`: Hosted Antom MCP server connection.
- `skills/antom-integration/SKILL.md`: Antom integration skill (Cursor will
  trigger this skill automatically based on the prompt).
- `skills/antom-reconciliation-expert/SKILL.md`: Antom settlement report
  retrieval, parsing, validation, and reconciliation skill.
- `assets/logo_antom.svg`: Plugin logo shown in the marketplace.

## Capabilities

The plugin helps Cursor:

- Choose the right Antom payment product (One-time Payments, Tokenized Payment,
  Subscription Payment).
- Select an integration mode: Payment Element, Checkout Page (hosted /
  embedded), or API-only (APM / bank card).
- Fetch the latest Antom online documentation before generating code.
- Validate signature, asynchronous notification, and exception handling against
  Antom integration security red lines.
- Retrieve, parse, validate, and analyze Antom settlement reports.
- Connect to the hosted Antom MCP server for additional tools and data sources.

## MCP Access

The plugin connects to the hosted Antom MCP endpoint at
`https://mcp.antom.com`.

Antom MCP is currently available to selected allowlisted merchants.

- Request MCP access: `pub_antom_integration_service@antom.com`
- Setup guide: [Antom MCP documentation](https://docs.antom.com/ac/ref/mcp)

After access is approved, an Antom account administrator must enable MCP access
in Antom Dashboard under **Settings > Team > MCP Access**. Test and Live mode
access are managed separately.

Cursor then handles authentication through the standard OAuth flow. Do not add
credentials or secrets to `mcp.json`.

## Example Prompts

```text
Help me choose the right Antom payment integration.
```

```text
Review my Antom payment flow for security issues.
```

```text
Generate Antom checkout integration code.
```

## Local Test

Copy this directory into `~/.cursor/plugins/local/antom-integration` and
restart Cursor (>= 2.6). Symlinks are not currently supported by the local
plugin loader.

## License

MIT — see repository root `LICENSE`.
