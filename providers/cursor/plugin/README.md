# Antom Integration (Cursor)

Antom payment integration guidance for Cursor — product selection, integration
mode, code generation, and security validation.

## Contents

- `.cursor-plugin/plugin.json`: Cursor plugin manifest.
- `skills/antom-integration/SKILL.md`: Antom integration skill (Cursor will
  trigger this skill automatically based on the prompt).
- `assets/logo_antom.svg`: Plugin logo shown in the marketplace.

## Capabilities

The skill helps Cursor:

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

Copy this directory into `~/.cursor/plugins/local/antom-integration` and
restart Cursor (>= 2.6). Symlinks are not currently supported by the local
plugin loader.

## License

MIT — see repository root `LICENSE`.
