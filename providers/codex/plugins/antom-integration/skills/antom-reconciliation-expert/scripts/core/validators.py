"""
Antom Reconciliation Report Validation Functions

Uses Decimal + ROUND_HALF_EVEN to ensure financial precision.
Settlement formula: settlementAmountValue = grossSettleAmount + sum(ALL_FEE_FIELDS)
"""

from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Dict, Any, Optional, List, Tuple

from .constants import ALL_FEE_FIELDS


# Special fee line types: fees reflected in settlementAmountValue rather than 17 fee fields
_SPECIAL_FEE_TYPES = {"SETTLEMENT_FEE", "ADJUSTMENT_FEE"}


# ============================================================
# Basic utility functions
# ============================================================

def safe_decimal(val: Any) -> Decimal:
    """Safely convert to Decimal, empty values/invalid strings return 0."""
    if val is None:
        return Decimal('0')
    s = str(val).strip()
    if not s or s.lower() in ('none', 'null', ''):
        return Decimal('0')
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal('0')


def parse_currency_pair(pair_str: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse quoteCurrencyPair string (e.g., "USD/SGD"), return (left, right)."""
    if not pair_str or '/' not in pair_str:
        return (None, None)
    parts = pair_str.strip().split('/')
    if len(parts) != 2:
        return (None, None)
    left = parts[0].strip()
    right = parts[1].strip()
    if not left or not right:
        return (None, None)
    return (left, right)


# ============================================================
# Currency conversion
# ============================================================

def compute_gross_settle_amount(row: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate grossSettleAmount (total transaction amount in settlement currency, excluding fees), with cross-validation."""
    txn_amount = safe_decimal(row.get('transactionAmountValue'))
    txn_currency = str(row.get('transactionCurrency', '')).strip()
    settle_currency = str(row.get('settlementCurrency', '')).strip()
    pair_str = str(row.get('quoteCurrencyPair', '')).strip()
    quote_price = safe_decimal(row.get('quotePrice'))

    result = {
        "gross": Decimal('0'),
        "method": "",
        "success": False,
        "error": None,
        "cross_validation": {
            "converted_value": None,
            "diff": None,
            "match": None,
        }
    }

    # Same currency
    if not pair_str or txn_currency == settle_currency:
        result["gross"] = txn_amount
        result["method"] = "same_currency"
        result["success"] = True
        return result

    # Cross-currency: need quotePrice
    if quote_price == 0:
        result["error"] = "quotePrice is 0 or missing"
        return result

    left, right = parse_currency_pair(pair_str)
    if left is None:
        result["error"] = f"cannot parse quoteCurrencyPair: {pair_str}"
        return result

    if txn_currency == left:
        # txn in left currency, settle in right currency → multiply
        gross = (txn_amount * quote_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        result["method"] = "multiply"
    elif txn_currency == right:
        # txn in right currency, settle in left currency → divide
        gross = (txn_amount / quote_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        result["method"] = "divide"
    else:
        result["error"] = (
            f"transactionCurrency '{txn_currency}' not in "
            f"quoteCurrencyPair '{pair_str}'"
        )
        return result

    result["gross"] = gross
    result["success"] = True

    # Cross-validation: convertedTransactionAmountValue
    converted_raw = row.get('convertedTransactionAmountValue')
    if converted_raw is not None:
        converted = safe_decimal(converted_raw)
        if converted != 0:
            diff = abs(gross - converted)
            result["cross_validation"] = {
                "converted_value": converted,
                "diff": diff,
                "match": diff <= Decimal('0.02'),
            }

    return result


# ============================================================
# Single-row settlement amount validation
# ============================================================

def validate_row_formula(
    row: Dict[str, Any],
    tolerance: Decimal = Decimal('0.02'),
) -> Dict[str, Any]:
    """Validate single-row settlement amount: settlement = gross + sum(fees). Auto-identifies non_formula_row."""
    settle_amount = safe_decimal(row.get('settlementAmountValue'))
    txn_type = str(row.get('transactionType', '')).strip()

    # Calculate gross
    gross_result = compute_gross_settle_amount(row)
    gross = gross_result["gross"] if gross_result["success"] else Decimal('0')

    # Calculate total fees
    total_fees = Decimal('0')
    for field in ALL_FEE_FIELDS:
        total_fees += safe_decimal(row.get(field))
    total_fees = total_fees.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)

    result = {
        "row_type": "",
        "valid": None,
        "settlement_amount": settle_amount,
        "gross": gross,
        "total_fees": total_fees,
        "expected": None,
        "diff": None,
        "gross_detail": gross_result,
        "transaction_type": txn_type,
    }

    # Auto-detect: gross=0, fees=0, settle!=0 → non_formula_row
    if gross == 0 and total_fees == 0 and settle_amount != 0:
        result["row_type"] = "non_formula_row"
        return result

    # gross calculation failed but doesn't match non_formula_row characteristics
    if not gross_result["success"]:
        result["row_type"] = "formula_row"
        result["valid"] = False
        result["diff"] = None
        return result

    # Normal validation
    expected = gross + total_fees
    diff = abs(expected - settle_amount)

    result["row_type"] = "formula_row"
    result["expected"] = expected
    result["diff"] = diff
    result["valid"] = diff <= tolerance

    return result


# ============================================================
# Batch/cross-batch settlement amount validation
# ============================================================

def validate_batch_formula(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Batch-level settlement amount validation. Validates each row then aggregates net_settlement, returns failures and statistics."""
    net_settlement = Decimal('0')
    formula_rows = 0
    non_formula_rows = 0
    formula_valid = 0
    formula_invalid = 0
    failures = []
    non_formula_total = Decimal('0')
    non_formula_by_type: Dict[str, Decimal] = {}

    for i, row in enumerate(rows):
        result = validate_row_formula(row)
        settle = result["settlement_amount"]
        net_settlement += settle

        if result["row_type"] == "non_formula_row":
            non_formula_rows += 1
            non_formula_total += settle
            txn_type = result["transaction_type"]
            non_formula_by_type[txn_type] = non_formula_by_type.get(txn_type, Decimal('0')) + settle

        elif result["row_type"] == "formula_row":
            formula_rows += 1
            if result["valid"]:
                formula_valid += 1
            else:
                formula_invalid += 1
                failures.append({
                    "row_index": i,
                    "transaction_type": result["transaction_type"],
                    "expected": result["expected"],
                    "actual": settle,
                    "diff": result["diff"],
                    "gross": result["gross"],
                    "total_fees": result["total_fees"],
                    "gross_detail": result["gross_detail"],
                })

    return {
        "net_settlement": net_settlement.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN),
        "total_rows": len(rows),
        "formula_row_count": formula_rows,
        "non_formula_row_count": non_formula_rows,
        "formula_valid_count": formula_valid,
        "formula_invalid_count": formula_invalid,
        "all_valid": formula_invalid == 0,
        "validation_failures": failures,
        "non_formula_summary": {
            "total_amount": non_formula_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN),
            "by_type": {k: v.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
                        for k, v in non_formula_by_type.items()},
        },
    }


# ============================================================
# Fee model identification
# ============================================================

def detect_fee_model(row: Dict[str, Any]) -> str:
    """Identify single-row fee model: IC++ vs BLENDED_RATE vs UNKNOWN."""
    has_interchange = safe_decimal(row.get('interchangeFeeAmountValue')) != 0
    has_scheme = safe_decimal(row.get('schemeFeeAmountValue')) != 0
    has_markup = safe_decimal(row.get('acquirerMarkupAmountValue')) != 0
    has_blended = safe_decimal(row.get('paymentMethodFeeAmountValue')) != 0

    if has_interchange or has_scheme or has_markup:
        return "IC++"
    elif has_blended:
        return "BLENDED_RATE"
    else:
        return "UNKNOWN"


# ============================================================
# Financial breakdown view
# ============================================================

def compute_settlement_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build financial breakdown view: decompose rows into gross revenue + fees + special fee rows + OTHERS, with formula_check self-validation."""
    Q = Decimal('0.01')

    net_settlement = Decimal('0')

    # Gross revenue
    gross_total = Decimal('0')
    gross_by_type: Dict[str, Dict] = {}

    # Fees
    fees_total = Decimal('0')
    fees_by_field: Dict[str, Decimal] = {}

    # Special fee rows
    special_total = Decimal('0')
    special_by_type: Dict[str, Dict] = {}

    # OTHERS
    others_total = Decimal('0')
    others_by_type: Dict[str, Dict] = {}

    for row in rows:
        settle = safe_decimal(row.get('settlementAmountValue'))
        txn_type = str(row.get('transactionType', '')).strip()
        net_settlement += settle

        # Calculate grossSettleAmount
        gross_result = compute_gross_settle_amount(row)
        gross = gross_result["gross"] if gross_result["success"] else Decimal('0')

        # Calculate inline fees
        inline_fees = Decimal('0')
        for field in ALL_FEE_FIELDS:
            val = safe_decimal(row.get(field))
            inline_fees += val
            if val != 0:
                fees_by_field[field] = fees_by_field.get(field, Decimal('0')) + val

        # Classification
        if gross != 0 or inline_fees != 0:
            # Normal transaction row: contributes gross revenue and fees
            gross_total += gross
            fees_total += inline_fees
            if txn_type not in gross_by_type:
                gross_by_type[txn_type] = {"count": 0, "amount": Decimal('0')}
            gross_by_type[txn_type]["count"] += 1
            gross_by_type[txn_type]["amount"] += gross

        elif settle != 0:
            # gross=0, fees=0, settle!=0
            if txn_type in _SPECIAL_FEE_TYPES:
                # Special fee row
                special_total += settle
                if txn_type not in special_by_type:
                    special_by_type[txn_type] = {"count": 0, "amount": Decimal('0')}
                special_by_type[txn_type]["count"] += 1
                special_by_type[txn_type]["amount"] += settle
            else:
                # OTHERS
                others_total += settle
                if txn_type not in others_by_type:
                    others_by_type[txn_type] = {"count": 0, "amount": Decimal('0')}
                others_by_type[txn_type]["count"] += 1
                others_by_type[txn_type]["amount"] += settle
        else:
            # All-zero row (gross=0, fees=0, settle=0): count in gross statistics but amount is 0
            if txn_type not in gross_by_type:
                gross_by_type[txn_type] = {"count": 0, "amount": Decimal('0')}
            gross_by_type[txn_type]["count"] += 1

    # Self-validation
    reconstructed = gross_total + fees_total + special_total + others_total
    diff = net_settlement - reconstructed

    def _quantize_by_type(d):
        return {k: {"count": v["count"], "amount": v["amount"].quantize(Q, rounding=ROUND_HALF_EVEN)}
                for k, v in sorted(d.items())}

    return {
        "net_settlement": net_settlement.quantize(Q, rounding=ROUND_HALF_EVEN),
        "total_rows": len(rows),
        "gross_revenue": {
            "total": gross_total.quantize(Q, rounding=ROUND_HALF_EVEN),
            "by_type": _quantize_by_type(gross_by_type),
        },
        "fees": {
            "total": fees_total.quantize(Q, rounding=ROUND_HALF_EVEN),
            "by_field": {k: v.quantize(Q, rounding=ROUND_HALF_EVEN)
                         for k, v in sorted(fees_by_field.items())},
        },
        "special_fee_rows": {
            "total": special_total.quantize(Q, rounding=ROUND_HALF_EVEN),
            "by_type": _quantize_by_type(special_by_type),
        },
        "others": {
            "total": others_total.quantize(Q, rounding=ROUND_HALF_EVEN),
            "by_type": _quantize_by_type(others_by_type),
        },
        "formula_check": {
            "reconstructed": reconstructed.quantize(Q, rounding=ROUND_HALF_EVEN),
            "diff": diff.quantize(Q, rounding=ROUND_HALF_EVEN),
            "balanced": abs(diff) < Decimal('1.00'),
        },
    }
