"""
Antom Reconciliation Report Constant Definitions

All enumerable structured rules are centrally managed here to reduce the
degree of freedom an agent has when recalling rules from natural language.
"""

import re as _re


# ============================================================
# Settlement Detail filename regex
# Purpose: Layer-1 detection — only accept Settlement Detail report filenames.
#          Directory path is NEVER part of the detection.
#
# Rule: basename (case-insensitive) must contain both "SETTLEMENT" and "DETAIL"
# as keywords (in any order / position), and end with .csv or .xlsx.
# Accepted examples:
#   - SETTLEMENT_DETAIL_202604271985548486_20260428.xlsx
#   - Settlement_Detail_Report.csv
#   - A_SettlementDetailReport_xxx.xlsx
# Rejected examples:
#   - SETTLEMENT_SUMMARY_xxx.xlsx   (missing DETAIL)
#   - TRANSACTION_DETAIL_xxx.xlsx   (missing SETTLEMENT)
# ============================================================
SETTLEMENT_DETAIL_FILENAME_RE = _re.compile(
    r"^(?=.*SETTLEMENT)(?=.*DETAIL).+\.(csv|xlsx)$",
    _re.IGNORECASE,
)


# ============================================================
# Settlement Detail header content sanity check (positive + negative signals)
# Purpose: After the filename gate passes, verify the header structure is
#          actually a Settlement Detail report — not a Transaction Detail or
#          Settlement Summary file that was renamed to SETTLEMENT_DETAIL_*.
#          Catches obvious renaming/spoofing.
#
# Two-layer rule:
#   1. Positive (POSITIVE): the header must match at least
#      SETTLEMENT_DETAIL_MIN_CORE_MATCH columns from SETTLEMENT_DETAIL_CORE_COLUMNS.
#      These columns exist in Settlement Detail but not in Settlement Summary,
#      so a renamed Summary file will be rejected here.
#   2. Negative (NEGATIVE): the header must not contain any column from
#      SETTLEMENT_DETAIL_FORBIDDEN_COLUMNS. These columns are exclusive to
#      Transaction Detail reports, so a renamed TX Detail file will be rejected here.
#
# Threshold rationale: 6 / 10 tolerates Antom schema evolution (minor column
# renames / removals) while reliably rejecting Settlement Summary
# (which shares only ~3 core columns).
# ============================================================
SETTLEMENT_DETAIL_CORE_COLUMNS = {
    "settlementBatchId",
    "transactionId",
    "transactionRequestId",
    "transactionType",
    "paymentMethodType",
    "transactionAmountValue",
    "transactionCurrency",
    "settlementAmountValue",
    "settlementCurrency",
    "settlementInitiatedDate",
}

SETTLEMENT_DETAIL_MIN_CORE_MATCH = 6

SETTLEMENT_DETAIL_FORBIDDEN_COLUMNS = {
    "status",                          # transaction status (TX only)
    "3DAuthentication",                # TX only
    "3DOffered",                       # TX only
    "accountHolderName",               # TX only
    "originalCardSummary",             # TX only
    "cardNumber(Last 4 digits)",       # TX only
    "issuer",                          # TX only
    "liabilityShift",                  # TX only
    "reason",                          # TX only
}


# ============================================================
# Fee field constants (all 20 fee amount fields)
# Source: bill-schema.md Section 9 / amount-fields.md Section 3
# Purpose: Ensure full coverage during fee aggregation; inferring field
#          selection from sample data is prohibited
# ============================================================
ALL_FEE_FIELDS = [
    "paymentMethodFeeAmountValue",       # Payment method fee (Blended Rate)
    "interchangeFeeAmountValue",         # IC fee (issuing bank)
    "schemeFeeAmountValue",              # SF fee (card scheme)
    "acquirerMarkupAmountValue",         # Markup fee (PSP markup)
    "processingFeeAmountValue",          # Fixed processing fee
    "taxFeeAmountValue",                 # Tax
    "refundFeeAmountValue",              # Refund handling fee
    "disputeHandlingFee",                # Dispute handling fee
    "financingFeeAmountValue",           # Installment fee
    "rdrFeeAmountValue",                 # RDR dispute fee
    "anticipationFeeAmountValue",        # Anticipation fee
    "riskDecisionServiceFeeAmountValue", # Risk decision fee
    "riskManagementFeeAmountValue",      # Risk management fee
    "cdrnFeeAmountValue",                # CDRN fee
    "iofFeeAmountValue",                 # Brazil IOF tax
    "withholdingTaxAmountValue",         # Withholding tax
    "fxFeeAmountValue",                  # FX exchange fee
    "rtauServiceFeeAmountValue",         # AU (Account Updater) service fee
    "ntServiceFeeAmountValue",           # Network Token service fee
    "revenueBoosterServiceFeeAmountValue",  # Card Revenue Booster service fee
]


# ============================================================
# Fee field pairing: amount field → corresponding currency field
# Source: bill-schema.md Section 10
# Purpose: Validate fee currency consistency (all fee currencies
#          are typically equal to settlementCurrency)
# ============================================================
FEE_FIELD_PAIRS = {
    "paymentMethodFeeAmountValue":       "paymentMethodFeeCurrency",
    "interchangeFeeAmountValue":         "interchangeFeeCurrency",
    "schemeFeeAmountValue":              "schemeFeeCurrency",
    "acquirerMarkupAmountValue":         "acquirerMarkupCurrency",
    "processingFeeAmountValue":          "processingFeeCurrency",
    "taxFeeAmountValue":                 "taxFeeCurrency",
    "refundFeeAmountValue":              "refundFeeCurrency",
    "disputeHandlingFee":                "disputeHandlingFeeCurrency",
    "financingFeeAmountValue":           "financingFeeCurrency",
    "rdrFeeAmountValue":                 "rdrFeeCurrency",
    "anticipationFeeAmountValue":        "anticipationFeeCurrency",
    "riskDecisionServiceFeeAmountValue": "riskDecisionServiceFeeCurrency",
    "riskManagementFeeAmountValue":      "riskManagementFeeCurrency",
    "cdrnFeeAmountValue":                "cdrnFeeCurrency",
    "iofFeeAmountValue":                 "iofFeeCurrency",
    "withholdingTaxAmountValue":         "withholdingTaxFeeCurrency",
    "fxFeeAmountValue":                  "fxFeeAmountCurrency",
    "rtauServiceFeeAmountValue":         "rtauServiceFeeCurrency",
    "ntServiceFeeAmountValue":           "ntServiceFeeCurrency",
    "revenueBoosterServiceFeeAmountValue": "revenueBoosterServiceFeeCurrency",
}


# ============================================================
# Transaction type enumeration (17 types)
# Source: transaction-types.md / id-fields.md
# Purpose: Structured rule lookup table, replacing agent inference from
#          natural language
#
# Attribute descriptions:
#   has_original_txn_request_id: whether originalTransactionRequestId is present
#   has_txn_request_id: whether transactionRequestId is present
#   description: English description
#
# Design decisions:
#   - fee_sign excluded: whatever is written on the report is what it is,
#     not determined by transaction type
#   - category excluded: no practical use
#   - needs_formula_validation excluded: determined automatically from data,
#     not hardcoded
# ============================================================
TRANSACTION_TYPES = {
    "PAYMENT": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": True,
        "description": "Payment processing",
    },
    "REFUND": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": True,
        "description": "Refund processing",
    },
    "CANCEL": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": True,
        "description": "Cancel order/payment",
    },
    "AUTHORIZATION": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": True,
        "description": "Pre-authorization fund freeze",
    },
    "CAPTURE": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": True,
        "description": "Capture after pre-authorization",
    },
    "DISPUTE": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": False,
        "description": "Dispute handling",
    },
    "ADJUSTMENT_FEE": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": False,
        "description": "Fee adjustment",
    },
    "PAYMENT_REVERSAL": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": True,
        "description": "Payment reversal, fund return",
    },
    "REFUND_REVERSAL": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": True,
        "description": "Refund reversal, fund return",
    },
    "SETTLEMENT_FEE": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": False,
        "description": "Settlement fee",
    },
    "DISPUTE_REVERSAL": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": False,
        "description": "Dispute won, fund return",
    },
    "COLLATERAL_WITHHELD": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": False,
        "description": "Collateral withheld",
    },
    "RESERVE": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": False,
        "description": "Reserve held",
    },
    "RESERVE_RELEASED": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": False,
        "description": "Reserve released",
    },
    "COLLATERAL_RELEASED": {
        "has_original_txn_request_id": False,
        "has_txn_request_id": False,
        "description": "Collateral released",
    },
    "RAPID_DISPUTE_RESOLUTION": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": False,
        "description": "RDR rapid dispute resolution",
    },
    "CDRN": {
        "has_original_txn_request_id": True,
        "has_txn_request_id": False,
        "description": "CDRN cardholder dispute network",
    },
}


# ============================================================
# Download configuration
# ============================================================
DOWNLOAD_REFERER = "https://dashboard.antom.com"
