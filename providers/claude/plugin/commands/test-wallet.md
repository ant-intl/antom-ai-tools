---
description: Show how to test Antom wallet / BNPL / online-banking (APM) payments in the sandbox.
---

Teach the user how to test Antom's redirect-based payment methods (wallets, BNPL, online banking). These have **no test card numbers** — testing is a flow, not a secret.

Fetch the latest details from the official Antom docs (do not rely on hardcoded steps or wallet lists):

```bash
curl -sL "https://docs.antom.com/ac/ref/wallet.md"
curl -sL "https://docs.antom.com/ac/ref/testwallet.md"
```

From those documents, present:

1. The **core difference vs cards**: there is no card number — you call the pay API in sandbox to get a payment/vaulting continuation URL, then approve it inside a **test wallet app** (any password works) or by scanning a QR code.
2. How to get the test wallet: download (Android APK / iOS TestFlight), log in with the Antom Dashboard account, pick the target method. List the supported **wallets**, **BNPL**, and **online banking** methods from the docs.
3. The flow **by device**: desktop QR scan, desktop account/password (any value), mobile with app installed (redirect), mobile without app (download or login).
4. **One-time vs tokenized (vaulting)** paths and how each is confirmed.

If the user named a specific method (e.g. "test GCash", "DANA auto-debit", "BPI online banking"), lead with that method's flow. Always close with the red line: the client-side result is untrustworthy — confirm payment via async notification or the query API.
If the user is currently working on test code, offer to generate test cases for the redirect/continuation-URL flow.
