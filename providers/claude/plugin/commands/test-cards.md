---
description: Show Antom sandbox test cards and payment-testing scenarios.
---

Surface the Antom sandbox test cards for the user.

Fetch the latest cards from the official Antom docs (do not rely on hardcoded numbers):

```bash
curl -sL "https://docs.antom.com/ac/ref/card.md"
```

From that document, present:

1. A short table of the most useful **successful** test cards (brand, number, region).
2. The **failure** cards for testing the decline path.
3. The **3DS**, **risk-control (by amount)**, and **invalid-input** scenarios.
4. A reminder of the sandbox input rules (any CVC/expiry/postal code) and that these only work in the sandbox gateway.

If the user named a specific scenario (e.g. "a card that fails", "test 3DS", "a Brazilian Visa"), lead with the matching card. Always close with the red line: the client-side result is untrustworthy — confirm payment via async notification or the query API.
If the user is currently working on test code, offer to generate test cases using these cards.