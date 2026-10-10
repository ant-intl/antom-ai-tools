# From Generated Project to Callable Adapter

## 1. Prepare before starting

Confirm SDK/template versions, channel code, card or non-card integration, 3DS interaction mode, transaction/notification scope, institution protocol, field mappings, result-code rules, synthetic examples and the platform configuration owner.
Institution examples are not standard SDK protocols. Do not copy another channel's fields, success codes, headers or signatures.

For new-project creation, follow the authoritative [generation intake](../project-generation.md#confirm-the-generation-inputs): obtain a valid user-supplied institution code in a standalone question and wait for its answer before asking about other missing inputs or creating files. Detailed mappings, algorithms, order, computation mode and fixtures are implementation inputs, not prerequisites for merely creating a skeleton.

The default workflow uses CLI 0.1.0; see [project generation](../project-generation.md). The CLI includes the AIS SDK 1.5.2 JAR and standalone consumer POM in sdk/. Prerequisites: Java 8 and Maven 3.6.3+.
For a generic scaffold supplied directly by the platform, read [scaffold differences](../baseline-scaffold.md) first; do not assume identical class structures.

## 2. Select capabilities by business scope, not class names

| Integration choice | CLI and SDK constraints | Implementation |
| --- | --- | --- |
| Card, one payment call | Implement pay when selecting PaymentService | Select cancel/capture/query according to institution support |
| Card, separate authentication and authorization calls | pay + authenticateAuthorize | Use the two distinct request types; do not cast PayRequest |
| Non-card | Implement pay when selecting PaymentService; capture/notifyCapture unavailable | Select queries, refunds and notifications as needed |
| Refunds | Implement refund when selecting RefundService | Select inquiryRefund as needed |
| Notifications | Implement notifyPayment when selecting NotificationService | May add notifyCapture/notifyRefund; refund-notification-only generation is not supported |
| Online-bank/receive-payment notifications and URL callbacks | SDK declaration does not imply a connected entry point | CLI does not generate capabilities whose entry points are not connected |

Java abstract methods are required only when implementing their interface; not every channel must offer refunds or notifications. The interactive CLI wizard starts with pay. JSON generation requires pay when a payment-family method is selected, refund for a refund-family method, and notifyPayment for any notification; it can express refund-only or notification-only scopes. NotifyRefund does not itself require the refund transaction, and notifyCapture does not require the capture transaction.
Do not override unselected optional methods; preserve the SDK's default UnsupportedOperationException instead of returning null or fabricated success.
Capability changes must update configuration, implementation, tests and platform registration together. Do not rerun init over an existing project.

## 3. Default project structure

| Location | Generated content | Integrator work |
| --- | --- | --- |
| spi/Channel*Service | Selected methods delegate to the invocation template with an anonymous ChannelApiExtension or ChannelNotificationExtension | Validation, field conversion, path parameters and result mapping inside each SPI method; no customize/api helpers |
| customize/security/ChannelSecurityCustomization | Enabled signature/encryption features demonstrate typed platform calls; disabled features perform no computation | Complete fail-closed protocol hooks, choose computation mode, and confirm order, signing input, encoding, parameters and result placement |
| customize/transport/ChannelTransportCustomization | JSON/POST starting point | Set institution method, headers, Query/Form and Content-Type |
| src/test/java | GeneratedStructureTest; SecurityContractTest and DeliveryTest for each method | Distinguish synthetic template validation from real SPI acceptance; add institution scenarios |
| `src/test/resources/scenarios/<method>/<case-id>.json` | Independently confirmed input/context, HTTP/security/result-code expectations, and expected output or failure | Add cases without editing the test runner; generated `confirmed:false` placeholders intentionally fail |
| adapter-spec.json / generation-lock.json | Selections, SDK/template versions and SDK JAR/POM SHA-256 | Preserve provenance; do not edit lock values to bypass validation |

Transaction SPIs use executeDynamicUrl by default. Their anonymous ChannelApiExtension returns an empty Map when the path has no placeholders; otherwise it returns raw business values for platform encoding.
Notification SPIs use executeNotification and return a standard notification request, not an ACK or a direct iPay call. See the [implementation workflow](../implementation-workflow.md).

## 4. From local verification to platform integration

1. Complete the selected SPI methods' anonymous mapping extensions and security hooks; replace initially empty fixtures.
2. Run `mvn -Dtest=GeneratedStructureTest test` to check Spring wiring; this does not prove business completeness.
3. Run `mvn clean verify` for real SPI tests, including security failures, unknown business results and exceptions.
4. For a trusted project, run `aci package --project . --json` and inspect reports, dependencies and the plain JAR.
5. Ask the platform to configure bean scanning, uniqueId, capability registration, routes, iPay identity, keys and result codes.
6. Record host validation and institution integration separately. Local success does not mean routes, keys, notifications or ACK behavior are live.
