# AIS Channel Adapter Integration Rules

Supply this to a developer or Agent. Reference specific institution protocol sections instead of repeating rules already documented there. Mark unknowns as "To confirm + impact" rather than guessing. Do not attach real keys or complete card credentials.

## Integration scope

| Item | Details |
| --- | --- |
| Institution code explicitly supplied by the user; required before other generation questions | |
| Institution display name; optional, cannot replace the code | |
| Adapter project path and allowed change scope | |
| Maven groupId, artifactId, project version and Java package: explicit or derived from the code | |
| Platform/SDK version | |
| SDK JAR / consumer POM SHA-256; ChannelRequestContext availability | |
| Platform-assigned channelCode, or code-derived identifier pending platform registration | |
| Card / non-card; one-call / two-call / inapplicable 3DS | |
| Selected transaction methods | |
| Refund transaction / refund inquiry included or excluded | |
| Selected notification methods | |
| Scaffold signature handling needed: yes / no | |
| Scaffold encryption handling needed: yes / no | |
| Protocol name, version and source sections | |
| Platform configuration and integration owners | |

For new-project creation, follow the authoritative [generation intake](../references/project-generation.md#confirm-the-generation-inputs): obtain the user's valid institution code first, waiting for it before asking any other generation questions; then collect only the remaining missing inputs.

This is a recording form, not another questionnaire or CLI JSON schema. Detailed security rules, mappings and acceptance fixtures belong to implementation; no real keys belong here.

## Per-method field mappings

Method: ; direction: standard request → institution request / institution response → standard response / institution notification → standard notification.

| Source field path | Target field path | Types on both sides | Required condition | Conversion, amount units, timezone | Missing/null behavior | Synthetic input and expectation | Protocol evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

## Transport and results

| Item | Details |
| --- | --- |
| HTTP method / Content-Type | |
| Header, Query and Form sources/rules | |
| Dynamic-path placeholders and raw-value sources; domain configured by platform | |
| Normal / non-2xx / empty-response handling | |
| Institution success, rejection and processing states | |
| Institution primary/secondary/tertiary code → platform resultStatus/resultCode | |
| Standard code catalog API / parameter-center api / SPI method relationship | |
| Notification ACK status, headers, body, deadline and redelivery rules | |

## Implementation-stage security rules for each direction

Complete after scaffold creation, separately for request signing/encryption, response verification/decryption and notification verification/decryption. The two scaffold booleans do not settle these rules or the platform/custom computation choice.

| Item | Details |
| --- | --- |
| Computation mode: platform / adapter after queryKey | |
| Exact algorithm, output format, padding/curve and other protocol requirements | |
| Platform-context merchantId relationship to institution Client-Id | |
| Key purpose, material type/format/length; do not include value | |
| Signing-input fields, order, separators, null handling and trailing newline | |
| Character encoding and digest/encryption/signing order | |
| Query inclusion in Request-Target and URL encoding rules | |
| Signature placement, header prefix and case | |
| Verification/key-query failure handling | |
| Independent test vectors and non-production test-material source | |

## Acceptance scenarios

Prepare synthetic channel, merchant and runtime environment independently in each scenario's context object. Cover absent context, missing merchant and cleanup after exceptions. A null runtimeEnv must not implicitly skip security or select a sandbox destination. Prepare expected values before code; see the [scenario format](../references/TESTING.md#3-add-independent-protocol-cases).

| SPI/scenario | Standard input | Simulated institution response | Expected outbound request/standard result | Expected invocation count or exception | Owner |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Open questions

| Question | Affected methods/fields | Known evidence | Required confirmer |
| --- | --- | --- | --- |
| | | | |
