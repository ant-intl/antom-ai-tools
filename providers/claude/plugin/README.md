# Antom Integration (Claude Code)

Antom payment integration guidance for Claude Code — product selection,
integration mode, code generation, and security validation.

## Contents

- `.claude-plugin/plugin.json`: Claude Code plugin manifest.
- `skills/antom-integration/SKILL.md`: Antom integration skill (Claude will
  trigger this skill automatically based on the prompt).

## Capabilities

The skill helps Claude Code:

- Choose the right Antom payment product (One-time Payments, Tokenized Payment,
  Subscription Payment).
- Select an integration mode: Payment Element, Checkout Page (hosted /
  embedded), or API-only (APM / bank card).
- Fetch the latest Antom online documentation before generating code.
- Validate signature, asynchronous notification, and exception handling against
  Antom integration security red lines.

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

From the repository root, register this repo as a local marketplace and
install the plugin:

```text
/plugin marketplace add /absolute/path/to/ai-antom
/plugin install antom-integration@antom
```

Validate the marketplace metadata with the official CLI:

```bash
claude plugin validate .
```

The plugin cache lives under `~/.claude/plugins/cache`.

## License

MIT — see repository root `LICENSE`.
