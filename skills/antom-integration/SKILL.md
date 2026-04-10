---
name: antom-integration
description: >-
  A skill dedicated to Antom payment integration, helping merchants select the right product and integration approach based on business needs, and build production-grade code.
  Supported products: One-time Payments, Tokenized Payment (recurring auto-debit), Subscription Payment, Scan to Link.
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


# Product Categories

This Skill only provides the following product integrations to merchants. Do not reveal other products:

| Product | Use Case | Integration Mode | Key Features | Reference Doc |
|---------|----------|-----------------|--------------|---------------|
| **One-time Payments** | Single-transaction payments for goods purchases, service fees, etc. | Element integration, Checkout integration (fully hosted / embedded), API-only (APM / bank card) | 3 integration modes available; supports Apple Pay / Google Pay express checkout; bank card payments; card tokenization | `https://cdn.marmot-cloud.com/page/antom-integration-doc/references/one-time-payments.md` |
| **Tokenized Payment** | Recurring auto-debit with a one-time authorization that remains valid long-term | Two-step flow: authorization → payment | No repeated authorization needed after initial consent; supports 31 countries/regions and 16 local currency settlements; settlement cycle T+2 to T+25 | `https://cdn.marmot-cloud.com/page/antom-integration-doc/references/tokenized-payment.md` |
| **Subscription Payment** | Subscription renewals and membership services with automatic periodic billing | Payment Element, Checkout Page (fully hosted), API-only (hosted card / merchant-collected card) | Supports yearly / monthly / weekly / daily / custom cycles; first payment requires 3DS verification; supports pause / resume / cancel; automatic retry on payment failure | `https://cdn.marmot-cloud.com/page/antom-integration-doc/references/subscription-payment.md` |



# SDK Resources

Can leverage these SDKs to assist your development.

| SDK      | Documentation                                                                                       |
|----------|-----------------------------------------------------------------------------------------------------|
| Java     | [Java SDK](https://cdn.marmot-cloud.com/page/antom-integration-doc/library/java.md)           |
| Python   | [Python SDK](https://cdn.marmot-cloud.com/page/antom-integration-doc/library/python.md)       |
| Embedded Element WEB SDK | [Element WEB SDK](https://cdn.marmot-cloud.com/page/antom-integration-doc/web-sdk/web-sdk.md) |