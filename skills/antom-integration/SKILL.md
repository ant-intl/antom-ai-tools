---
name: antom-integration
description: >-
  A skill dedicated to Antom payment integration, helping merchants select the right product and integration approach based on business needs, and build code.
  Supported products: One-time Payments, Tokenized Payment (recurring auto-debit), Subscription Payment.
  Supported integration modes: Payment Element, Checkout Page (fully hosted / embedded), API-only integration (APM / bank card).
---

**All Antom product documentation is available via online dynamic links. Before integration, make sure to read the corresponding product's online documentation to get the latest API parameters and code examples.**

# Document Access Guidelines

To access Antom online documentation, fetch content directly using curl:

```bash
# Example: Get One-time Payments CKP documentation
curl -sL "https://****/****.md" 
```

**Important**: Before writing code, make sure to read the corresponding product's online documentation via curl. The documentation contains the latest API parameters, code examples, and important notes.



# Get Integration Documentation

## SDK Selection
- **SDK Selection**: To help developers call open interfaces, Alipay provides open platform server-side SDKs, including Java, PHP, Node.js, Python and .NET languages, encapsulating signature and verification, HTTP interface requests and other basic functions. Please download the latest version of the server-side SDK for your language and import it into your development project. [SDK Description](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/select-sdk.md)

## Product Selection
Read [Product Decision](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/product-decision.md), match keywords based on user input, and only recommend payment products and integration solutions. Always use [Clarification Template](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/product-decision.md) for product and integration solution confirmation.


> ⛔ **Blocking Checkpoint**: Product Categories step completion criteria (all of the following must be satisfied before proceeding to subsequent steps)
- [ ] SDK Selection has been read
- [ ] Product documentation has been read (required recursive reading items: Quick Start, API List, Asynchronous Notification, SampleCode Instructions)

# FAQ

Read [FAQ (Coding)](https://cdn.marmot-cloud.com/page/antom-integration-doc/troubleshoot/faq-coding.md) BEFORE writing code. Scan items matching the user's product. Your code response MUST include a brief FAQ compliance note confirming how each applicable item is handled (e.g., "FAQ checked: gateway=correct region, settlementCurrency=omitted, subscriptionExpiryTime=default").


# Debug Logs

**Write logs to a file** named `antom_debug.log` in the project root directory, in addition to console output. All generated integration code MUST log the API endpoint, complete request and response for each API call. Mask sensitive fields (card numbers, CVV, private keys).

**Use exactly this format:**
- Outgoing request/response: `[Antom][{timestamp}][{API endpoint}] {request/response body}`
- Incoming async notification: `[Antom][{timestamp}][{API name}] {notification body}`

> The logging code is for **development & debugging only** — remove or reduce once integration is stable.

# Troubleshooting

When an error occurs or users report issues, follow this sequence:

1. **Get error details** — from user input, console output, or debug log file (antom_debug.log)

2. **Analyze error** — read resultCode + resultMessage
  - Matches a known error pattern → check [FAQ (Errors)](https://cdn.marmot-cloud.com/page/antom-integration-doc/troubleshoot/faq-errors.md), fix per Action
  - resultCode/resultMessage states clear cause → look up API endpoint or API name in [API Troubleshooting Index](https://cdn.marmot-cloud.com/page/antom-integration-doc/troubleshoot/api-troubleshooting-index.md), find the corresponding API doc, match resultCode in its Result/Error codes section, follow Further action to fix
  - Above cannot resolve → proceed to step 3

3. **Dashboard diagnosis** — guide user to:
  - Search by paymentRequestId in [Request Log](https://dashboard.antom.com/global-payments/developers/requestLog)
  - Paste request ID into Copilot on [Antom Dashboard](https://dashboard.antom.com/) (right panel or top-right icon) for AI diagnosis
  - If unresolved, advise user to contact Antom support with requestId and log snippet


# Integration Companion Guides

- **Post-code guidance (mandatory)**: After code is written, guidance must be provided. Tell users what conditions must be met to go live. Never output bare URLs as user guidance. never stop at "code is done". Proactively guide the user through the remaining stages by reading the corresponding companion docs and presenting key actions inline:
  1. **Credentials & config** → read [Onboarding Guide](https://cdn.marmot-cloud.com/page/antom-integration-doc/integration-guides/onboarding.md), ensure user has sandbox ClientId/keys configured and project is runnable. **Ask user to confirm settlement currencies**: how many are contracted? If multiple, `settlementCurrency` must be set in code. User can check at Dashboard → Finance (switch to Test mode for sandbox).
  2. **Sandbox testing** → read [Sandbox Guide](https://cdn.marmot-cloud.com/page/antom-integration-doc/integration-guides/sandbox-guide.md), walk user through first end-to-end payment (cards/wallets/APMs) and disclose sandbox limitations
  3. **self-check** → read [Self-Check List](https://cdn.marmot-cloud.com/page/antom-integration-doc/integration-guides/self-check.md), guide users on items that sandbox cannot cover but must be verified.
  4. **Error diagnosis** → Must guide users on how to handle integration issues, see Troubleshooting decision tree above.

- **On-demand trigger**: If the user asks about credentials/registration, sandbox testing, check list, or go-live readiness at any point (even before code is written), read the matching doc above and respond inline.


# Integration Validation

Perform validation during integration and before production launch to ensure signature verification, asynchronous notifications, and exception handling meet specifications. Validation results are for reference only; developers must check against the latest Antom Open Platform documentation. See: [Integration Checklist](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/checklist.md)


# Security Red Lines
> ⛔ The following rules are **security red lines** for Antom payment integration. Violations may lead to financial loss or security incidents and must be strictly adhered to.
- **Private Key Must NOT Be Stored on the Client Side**: Transaction data construction and signing must be completed on the merchant's server. The private key must absolutely NOT be stored in the merchant's APP client.
- **Private Key Must NOT Be Logged**: The private key must not appear in any logs.
- **Private Key Must NOT Be Committed to Public Repositories**: The private key must not be uploaded to public code repositories like GitHub or GitLab.
- **Client-side Payment Results Are Untrustworthy**: The synchronous redirect result on the client side is untrustworthy. The result must be confirmed via Antom's asynchronous notification (Notify) or by calling the transaction query API.
- **No Repayment Before Confirmation**: Before the payment result is confirmed, the user must not be asked to pay again. The payment result must first be confirmed via asynchronous notification or the query API.
- **Asynchronous Notifications Must Be Verified First**: Upon receiving an asynchronous notification, signature verification must be performed first to ensure the notification is from Antom.