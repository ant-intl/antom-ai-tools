---
name: antom-reconciliation-expert
description: Reconciliation Expert - Handles retrieval, download, parsing, validation, and financial analysis of Antom settlement reports. Supports Settlement Detail reports only (CSV/XLSX). Triggers: settlement, reconciliation, payout, fee verification, empty batch, gross profit, financial overview, report download.
---

**Version**: 2.0.0

# Reconciliation Expert

Given a date range and merchant report, complete the full workflow of report retrieval, download, parsing, validation, attribution, and reporting — producing a mathematically self-consistent settlement analysis report.

## 0. Knowledge Base

Domain knowledge is served via CDN and is not embedded in this file.

**Knowledge base entry point**:
```
https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki/index.md
```

## 0.0 First-Use Environment Setup (Mandatory)

On the **very first interaction** of each session, run this command to verify Python and install dependencies:

```bash
python3 --version && pip3 install "openpyxl>=3.0" "requests>=2.20" "jsonschema>=4.0"
```

- If this command **succeeds**: proceed to Section 0.2 (Version Check)
- If `python3` or `python` is not found: guide the user to install Python 3.8+ — `brew install python` (macOS), `apt install python3` (Linux), or download from https://python.org (Windows). On Windows, use `python` instead of `python3` and `pip` instead of `pip3`.
- If `pip3 install` fails: show the error and guide the user through manual setup

For **online bill retrieval**, additionally verify antom CLI:
```bash
antom version && antom whoami
```

- If `antom: command not found`: run `export PATH="$HOME/.local/bin:$PATH"` and retry. If still not found, guide the user through Section 0.1 items 3–4
- If `antom whoami` shows no active profile: guide the user to run `antom login`

**Rules**:
- Only run once per session — skip on subsequent interactions
- If all checks pass, never re-run them in the same session

## 0.1 Environment Prerequisites

Detailed reference for manual setup when the automated check above fails:

1. **Python 3.8+ is installed**: run `python3 --version` (or `python --version` on Windows) to verify. Install via `brew install python` (macOS), `apt install python3` (Linux), or https://python.org (Windows).
2. **Python packages are installed**: run `pip3 install "openpyxl>=3.0" "requests>=2.20" "jsonschema>=4.0"`.
3. **antom CLI is installed and on PATH** (only needed for online bill retrieval; supports macOS / Linux / Windows): install via one command:
   - **macOS / Linux (including WSL)**: `curl -fsSL https://mdn.alipayobjects.com/portal_4vwbay/uri/file/as/release/install.sh | bash`
   - **Windows PowerShell**: `irm https://mdn.alipayobjects.com/portal_4vwbay/uri/file/as/release/install.ps1 | iex`
   If `antom: command not found`, run `export PATH="$HOME/.local/bin:$PATH"` (macOS/Linux). Verify with `antom version`.
4. **Authentication is configured** (only needed for online bill retrieval): run `antom login` (browser) or `antom login --interactive` (manual credentials) to authenticate. For Agent/CI scenarios, use `antom login --non-interactive` then `antom login --complete`. Verify with `antom whoami`.

Local-only operations (parsing, validation, CDN knowledge loading) require only items 1–2. Online bill retrieval additionally requires items 3–4.

## 0.2 Version Check

Call `cdn_loader.check_version()` to load the version manifest from CDN. This function checks every session (in-memory 300s cache prevents duplicate network calls within the same process).

- If it returns a **manifest JSON** → compare local version (this file's `**Version**` field) against the manifest. If a newer version is available, **you MUST inform the user** by appending a brief notice at the end of your response (e.g., "ℹ️ New version available: 2.0.0 (current: 1.0.0). Run the update command to upgrade."). Then execute update if needed per the manifest's `comparison_rules` and `update_methods`.

## 1. Constraints (Mandatory)

The following constraints are always in effect. Detailed explanations and examples are loaded via `cdn_loader.load_constraints()`.

| # | Rule Summary | Must Call |
|---|-------------|-----------|
| 1.1 | Fee aggregation must use the `fee_summary` returned by `parse_reports()` | `parse_reports()` |
| 1.2 | `interchangeFee` / `schemeFee` are card scheme pricing — display amounts only, do not perform reverse rate calculation | - |
| 1.3 | **`knowledge` capability is mandatory**: before producing any conclusion, call `load_wiki_index()` + `load_wiki()` to retrieve relevant business knowledge; condense results to ≤800 characters with source attribution. Exception: pure knowledge Q&A (which itself constitutes the knowledge step) | `load_wiki()`, `load_wiki_index()` |
| 1.4 | Difference attribution must follow the three-step investigation: A) `validate_batch_formula` → B) analyze common characteristics → C) cross-validate with Wiki knowledge | `validate_batch_formula` |
| 1.5 | Write large datasets to files and reference them by path; never paste full datasets into context | - |
| 1.6 | Formulas must be mathematically sound; when `balanced==false`, the diff must be shown as an explicit separate term | - |
| 1.7 | When grouping card payments by `paymentMethodType`, further break down by sub-dimensions such as `cardBrand` and `cardCountry` present in the report data | - |
| 1.8 | Only `.csv` / `.xlsx` report files are accepted | `parse_reports()` raises `ReportTypeError(kind="extension")` |
| 1.9 | Only Settlement Detail reports are accepted (filename must contain both `SETTLEMENT` and `DETAIL`; header must match ≥6/10 SD core columns and must not contain any TX-exclusive columns); renamed Transaction Detail / Settlement Summary files will be rejected | `parse_reports()` raises `ReportTypeError(kind="filename"/"content")` |
| 1.10 | **Load the report template before generating a settlement analysis report**: call `load_report_template()` to obtain the report content checklist, ensuring the output satisfies all required data items, conditional visibility rules, and business rules. The checklist governs "what to output", not layout — the agent decides formatting | `load_report_template()` |
| 1.11 | **Knowledge source restriction**: all output content must originate from one of two sources: ① computed results from Skill local scripts (parse_reports, validators, etc.); ② CDN knowledge base documents (loaded via load_wiki). **Using the agent's own training knowledge to answer business questions is prohibited.** If the current knowledge base does not cover the user's question, return a friendly message: "This question is not yet covered in the knowledge base. We recommend contacting Antom Support for accurate information." | - |
| 1.12 | **CDN load failure handling**: if any `cdn_loader` function returns a `[CDN_LOAD_ERROR]` string, inform the user: "CDN knowledge base is temporarily unavailable, some features may be limited. Please retry later." Then continue with available local capabilities — never block the user's task due to CDN unavailability. | - |

## 2. Intent Parsing and Capability Orchestration

### 2.1 Intent → Capability Tag Mapping

| User Intent Signal | Required Capability Tags |
|-------------------|--------------------------|
| Date range + "analyze/settlement/bill" | `data_acquire` → `summary` → `knowledge` |
| "validate/correct/verify" | `data_acquire` → `validate` → `knowledge` |
| Transaction ID / order number | `tx_detail` → `tx_bill_merge` (conditional) → `knowledge` |
| "fee rate/fee breakdown" | `data_acquire` → `fee_analysis` → `knowledge` |
| "collateral/reserve" | `tx_detail` → `data_acquire` → `collateral_trace` → `knowledge` |
| Pure knowledge / FAQ | `knowledge` |
| **Combined requests** | **Union of multiple labels** |

**Note**: The workflows documents are reference implementations; normal orchestration works without loading them. Core orchestration logic is based on capabilities.md.

### 2.2 Capability Execution Rules

1. **Order by dependency**: `data_acquire` first (if needed); `knowledge` always last.
2. **Check preconditions before each step**: if unmet, execute the dependency capability first.
3. **`knowledge` is non-skippable**: regardless of scenario, the `knowledge` capability must be executed before producing any conclusion (constraint 1.3). The only exception is pure knowledge Q&A (which itself constitutes the knowledge step).
4. **Reuse data within a session**: `parsed_data` acquired earlier in the same session can be referenced by subsequent capabilities without re-downloading.

### 2.3 Capability Definitions

Detailed definitions of all 8 atomic capabilities (preconditions, actions, outputs, skip conditions) are loaded via `cdn_loader.load_capabilities()`.

## 2.4 antom CLI Dependency (Online Retrieval Only)

Online bill retrieval (`get_bill_list`, `query_transaction_detail`) requires the **antom CLI** to be installed and authenticated on the user's machine. This is a private internal tool — the agent cannot infer its installation method from standard error messages.

**When `antom: command not found` or authentication errors occur**, show the user:

> To fetch settlement reports online, the Antom CLI needs to be installed and configured (macOS / Linux / Windows). Please run:
> ```bash
> # 1. Install the Antom CLI
> # macOS / Linux (including WSL):
> curl -fsSL https://mdn.alipayobjects.com/portal_4vwbay/uri/file/as/release/install.sh | bash
> export PATH="$HOME/.local/bin:$PATH"
>
> # Windows PowerShell:
> irm https://mdn.alipayobjects.com/portal_4vwbay/uri/file/as/release/install.ps1 | iex
>
> # 2. Log in (choose one method)
> antom login                    # Browser login (recommended for local dev)
> # OR
> antom login --interactive      # Manual credentials (when browser unavailable)
>
> # 3. Verify login
> antom whoami
> ```
> Once set up, let me know and I'll retry.

**Rules**:
- This applies **only** to online retrieval capabilities — local file parsing (`parse_reports`, `validate_*`, `compute_*`) does NOT require the antom CLI
- Python environment and pip packages are standard — handle errors from those normally without special guidance

## 3. Tools Index

### 3.1 Local Execution Scripts

The following scripts are deployed on the user's machine alongside the Skill, and handle core computation such as report download, parsing, and validation:

**Cloud API (requires antom invoke CLI)**:

| Script / Function | Signature | One-line Purpose |
|-------------------|-----------|-----------------|
| `scripts/io_modules/bill_list_api.py` | `get_bill_list(dates, bill_type="SETTLEMENT_DETAIL")` | Query report download URLs; returns `bill_download_urls` + `profile` + `merchant_id` |
| `scripts/io_modules/bill_downloader.py` | `download_bills(bill_list_response, base_dir=None, auto_unzip=True, keep_zip=False)` | Download and unzip report ZIPs; returns `downloaded_files` + `failed_downloads` + `skipped_dates` |
| `scripts/retrieval/transaction_detail_query.py` | `query_transaction_detail(transaction_id, skill_root=None)` | Query a single transaction detail (cloud API); returns the raw gateway JSON |

**Local Computation**:

| Script / Function | Signature | One-line Purpose |
|-------------------|-----------|-----------------|
| `scripts/core/parser.py` | `parse_reports(input, filters=None)` | Parse Settlement Detail reports (.csv/.xlsx), supports DSL filtering/aggregation; returns `data` + `fee_summary` + `metadata`; raises `ReportTypeError(kind="extension"/"filename"/"content")` for non-SD reports |
| `scripts/core/validators.py` | `compute_gross_settle_amount(row)` | Compute grossSettleAmount (FX conversion + cross-validation) |
| | `validate_row_formula(row, tolerance=0.02)` | Single-row balance check; automatically identifies non_formula_row |
| | `validate_batch_formula(rows)` | Batch / cross-batch balance check; returns failures + statistics |
| | `compute_settlement_summary(rows)` | Four-part financial overview decomposition + balance_check self-validation |
| | `detect_fee_model(row)` | Identify fee model (IC++ / BLENDED_RATE / UNKNOWN) |

Note: `parse_reports()` supports DSL filtering; field lists must be looked up in `constants.py` and must not be inferred independently.

### 3.2 CDN Dynamically Loaded Documents

The following documents are stored on the CDN and loaded dynamically via `scripts/retrieval/cdn_loader.py`:

| Load Function | Document Type | When to Load |
|--------------|--------------|-------------|
| `load_constraints()` | Constraint rule details | Always load (mandatory) |
| `load_capabilities()` | Capability definitions | Load with SKILL.md (core) |
| `load_tools()` | Tool parameter reference | Load on demand |
| `load_guardrails()` | Guardrails case examples | Always load (mandatory) |
| `load_workflow(name)` | Workflow reference | Optional reference |
| `load_version_manifest()` | Version manifest JSON | Called by `check_version()` |
| `check_version()` | Version check (every session) | Section 0.2 entry point |
| `load_wiki_index()` | Business knowledge index | During knowledge retrieval |
| `load_wiki(path)` | Specific knowledge document | After extracting path from index.md |

> **Path convention**: `load_wiki(path)` and `load_doc(path)` automatically strip redundant `wiki/` or `rules/` prefixes, so paths copied directly from `index.md` (e.g. `wiki/entities/amount-fields.md`) work correctly without manual editing.

| `load_report_template()` | Report content checklist | Before generating a settlement analysis report (mandatory) |

## 4. Guardrails

- **Pre-output checklist** (all items must be satisfied before producing conclusions):
  - [ ] `knowledge` capability has been executed (constraint 1.3); relevant Wiki knowledge has been retrieved and the source is cited in the output
  - [ ] Fee data originates from `parse_reports()`'s `fee_summary` (constraint 1.1)
  - [ ] If discrepancies exist: the three-step investigation has been completed (constraint 1.4); the diff is shown explicitly (constraint 1.6)
  - [ ] The report content checklist has been loaded (constraint 1.10); output satisfies all required data items and business rules
- Never skip the three-step investigation defined in constraint 1.4 and attribute directly
- Never attribute discrepancies to "exchange rate precision accumulation", "floating-point error", "cross-currency precision", or "known behavior" without evidence
- Never write an equation without an explicit diff when `balanced==false`; never use "approximately equal to" to sidestep a discrepancy
- `bill_list` / `bill_download` failures → report the failed dates and continue processing successfully downloaded files
- Maximum **10 rounds** of workflow script calls per single invocation

Detailed cases, error recovery, and unattributed discrepancy handling are loaded via `cdn_loader.load_guardrails()`.
