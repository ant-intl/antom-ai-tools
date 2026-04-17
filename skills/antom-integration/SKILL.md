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


# Integration Validation

Perform validation during integration and before production launch to ensure signature verification, asynchronous notifications, and exception handling meet specifications. Validation results are for reference only; developers must check against the latest Antom Open Platform documentation. See: [Integration Checklist](https://cdn.marmot-cloud.com/page/antom-integration-doc/references/checklist.md)


# Information Retrieval
Keys, gateway URL selection, ClientId and all other content retrieval: [Antom Official Website](https://www.antom.com/)


# Security Red Lines
> ⛔ The following rules are **security red lines** for Antom payment integration. Violations may lead to financial loss or security incidents and must be strictly adhered to.
- **Private Key Must NOT Be Stored on the Client Side**: Transaction data construction and signing must be completed on the merchant's server. The private key must absolutely NOT be stored in the merchant's APP client.
- **Private Key Must NOT Be Logged**: The private key must not appear in any logs.
- **Private Key Must NOT Be Committed to Public Repositories**: The private key must not be uploaded to public code repositories like GitHub or GitLab.
- **Client-side Payment Results Are Untrustworthy**: The synchronous redirect result on the client side is untrustworthy. The result must be confirmed via Antom's asynchronous notification (Notify) or by calling the transaction query API.
- **No Repayment Before Confirmation**: Before the payment result is confirmed, the user must not be asked to pay again. The payment result must first be confirmed via asynchronous notification or the query API.
- **Asynchronous Notifications Must Be Verified First**: Upon receiving an asynchronous notification, signature verification must be performed first to ensure the notification is from Antom.