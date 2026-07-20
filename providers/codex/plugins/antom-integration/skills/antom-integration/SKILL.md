---
name: antom-integration
description: >-
  Antom payment integration skill for product and integration-mode selection, integration Q&A, code implementation, troubleshooting, sandbox testing, and go-live guidance.
  Use for One-time Payments, Tokenized Payment (recurring auto-debit), Subscription Payment, Payment Element, Checkout Page, and API-only integration.
---

# Scope

Use this skill to:
- locate relevant Antom product, integration, SDK, notification, checklist, and troubleshooting knowledge
- write or modify Antom payment integration code for the selected product, integration mode, and tech stack
- diagnose integration issues from result codes, API names, request IDs, logs, asynchronous notifications, and sandbox or go-live symptoms

# Document Access Guidelines

Fetch Antom online docs with curl:

```bash
curl -sL "https://****/****.md"
```

# Get Integration Documentation

Use this section as the shared knowledge lookup for product advice, Q&A, code implementation, and troubleshooting.

## SDK Selection

Read [SDK Description](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/select-sdk.md) when choosing an SDK, when the implementation language is known, or before writing code.

## Product Selection

Read [Product Decision](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/product-decision.md) for product or integration-mode advice. Use its clarification template only when needed.

Prefer Checkout Page (CKP) when the user wants rapid integration and broad payment-method coverage, if it fits the scenario.

## Integration Documentation Select

Based on the user's selected product and integration mode, locate the corresponding product integration documentation:

- [One-time Payments](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/one-time-payments.md)
- [Tokenized Payment](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/tokenized-payment.md)
- [Subscription Payment](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/subscription-payment.md)

Read the most specific sections available in the matched product doc.

- After selecting One-time Payments, Tokenized Payment, or Subscription Payment, do not load other product docs unless comparison or migration is requested.
- For Q&A or product advice: infer what you can, read the closest relevant docs, and state assumptions when useful.
- For troubleshooting: route by resultCode/resultMessage, API name, requestId, debug log, or error text first.

# Writing Code

Before writing or modifying code, first confirm the user's selected product, integration mode, and tech stack.

Blocking list before coding:

Do not write or modify integration code until all applicable items below are complete.

- [ ] Read [Product Decision](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/product-decision.md) to confirm the product category and integration mode, even when the user's request appears specific. Skip only if the user explicitly asks to skip product selection.
- [ ] Read [SDK Description](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/select-sdk.md) when a backend language or SDK is involved.
- [ ] Read the matched product overview from `Integration Documentation Select`:
  - One-time Payments
  - Tokenized Payment
  - Subscription Payment
- [ ] From the matched product overview, route by the selected integration mode and read the linked implementation docs needed for that flow, such as Quick Start, API list, frontend SDK, native SDK, Element, Checkout Page, or API-only guides.
- [ ] For coding tasks, route by the requested language or platform and read the matching product sample-code document from the same product overview before writing code. Inline examples in Quick Start, API reference, or integration guides are useful references, but they do not replace the product sample-code document.
- [ ] From the matched product overview, read the asynchronous notification document or section that matches the selected product and integration mode.
- [ ] Read [FAQ (Coding)](https://cdn.marmot-cloud.com/page/antom-integration-doc/troubleshoot/faq-coding.md), scanning items that match the selected product, integration mode, payment method, and market.

Generated code must:
- keep signing and private keys on the server side
- verify asynchronous notifications before trusting them
- not treat client-side redirect results as final payment status
- confirm uncertain payment status through asynchronous notification or query API
- include development debug logging guidance when useful, masking card numbers, CVV, private keys, and secrets
- include a brief FAQ compliance note confirming how each applicable item is handled, such as `gateway=correct region`, `settlementCurrency=omitted`, or `subscriptionExpiryTime=default`
- include a brief note about the docs and validation assumptions used
- include next-step guidance for credentials, sandbox testing, self-check, and go-live readiness when the user is building a full integration

## Debug Logs

**Write logs to a file** named `antom_debug.log` in the project root directory, in addition to console output. All generated integration code MUST log the API endpoint, complete request and response for each API call. Mask sensitive fields (card numbers, CVV, private keys).

**Use exactly this format:**
- Outgoing request/response: `[Antom][{timestamp}][{API endpoint}] {request/response body}`
- Incoming async notification: `[Antom][{timestamp}][{API name}] {notification body}`

> The logging code is for **development & debugging only** — remove or reduce once integration is stable.

## Validation and Post-code Guidance

Read [Integration Checklist](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/checklist.md) before finalizing code or launch-readiness guidance.

When guiding credentials and config, include credential locations:
- API domain, Client ID, and Antom public key can be found in [Quick Start](https://dashboard.antom.com/global-payments/developers/quickStart).
- The merchant private key can be generated or managed in [iKeys](https://dashboard.antom.com/global-payments/developers/iKeys); keep it server-side and never log, expose, or commit it.

After code is written, do not stop at "code is done". Guide the user through:
- credentials and config: [Onboarding Guide](https://cdn.marmot-cloud.com/page/antom-integration-doc/integration-guides/onboarding.md)
- sandbox testing: [Sandbox Guide](https://cdn.marmot-cloud.com/page/antom-integration-doc/integration-guides/sandbox-guide.md)
- self-check and go-live readiness: [Self-Check List](https://cdn.marmot-cloud.com/page/antom-integration-doc/integration-guides/self-check.md)
- error diagnosis: use `Troubleshooting`

If the user asks about credentials, registration, sandbox testing, checklist, self-check, or go-live readiness at any point, read the matching companion doc and answer inline.

# Troubleshooting

- **Error diagnosis (mandatory)**: When an Antom API call fails or the user reports an integration issue, read [Troubleshooting Guide](https://cdn.marmot-cloud.com/page/antom-integration-doc/troubleshoot/troubleshooting-guide.md) BEFORE diagnosing. Never skip directly to diagnosis CLI, Dashboard, or support.

  Follow the guide's order:
  1. **Evidence** → collect evidence from user input, console output, `antom_debug.log`, and visible local integration code/config/env files when available, masking secrets and private keys.
  2. **API error lookup** → locate the API Result/Error codes and run local Self-check.
  3. **Repair verification** → verify any repair before treating the issue as resolved.
  4. **Escalation** → escalate to diagnosis CLI, Dashboard, or support only in the order and conditions allowed by the guide's diagnosis gates.
  5. **Diagnosis Ledger** → return the compact Diagnosis Ledger defined in the guide.

- **On-demand trigger**: If the user asks about an integration error, API failure, request/response issue, result code, Dashboard diagnosis, diagnosis CLI, or troubleshooting at any point, read the Troubleshooting Guide and respond inline.

# Security Red Lines

- Private keys must never be stored on the client side, logged, or committed to public repositories.
- Asynchronous notifications must be signature-verified before being trusted.
- Client-side redirect results are not final payment status.
- Do not ask the user to pay again before confirming payment status through asynchronous notification or query API.
