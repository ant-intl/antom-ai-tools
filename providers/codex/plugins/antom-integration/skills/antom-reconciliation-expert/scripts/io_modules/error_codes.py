"""
Error Code Constants

Based on actual API response formats; uses string error codes.
"""

from typing import Dict

# Error code dictionary (string format)
ERROR_CODES = {
    # Success
    "SUCCESS": "Operation succeeded",
    
    # 1xx - Merchant / account related
    "MERCHANT_NOT_REGISTERED": "Merchant has not enrolled in the 2.0 standard after-sales portal",
    "MERCHANT_MID_INVALID": "Merchant MID is invalid",
    "MERCHANT_MID_MISSING": "Merchant MID is missing",
    "ACCOUNT_NOT_FOUND": "Account not found",
    
    # 2xx - Network / system errors
    "NETWORK_ERROR": "Network error",
    "API_UNAVAILABLE": "API temporarily unavailable",
    "RATE_LIMIT_EXCEEDED": "Request rate limit exceeded",
    "HTTP_ERROR": "HTTP request error",
    "TIMEOUT": "Request timed out",
    
    # 3xx - Parse / system errors
    "PARSE_ERROR": "Response parse error",
    "SYSTEM_ERROR": "System error",
    "CONFIG_ERROR": "Configuration error",
    
    # 4xx - Business data related (not exceptional)
    "NO_BILL_DATA": "No bill data for the requested date",
    "BILL_NOT_FOUND": "Specified bill file not found",
    "BILL_TYPE_NOT_SUPPORTED": "Bill type not supported",
    "INVALID_DATE_FORMAT": "Invalid date format",
    "INVALID_TIMEZONE": "Invalid timezone format",
    "EMPTY_BATCH": "Empty batch (pending settlement balance has not reached the settlement threshold)",
    "BILL_FILE_NOT_FOUND": "Specified bill file was not found on the server",

    # 5xx - Server / parameter / auth errors
    "UNKNOWN_EXCEPTION": "Unknown server exception",
    "PARAM_ILLEGAL": "Invalid request parameters",
    "AUTH_REQUIRED": "Authentication required",
}

# Error code categories (frozenset for O(1) lookup and immutability)
BUSINESS_ERROR_CODES = frozenset({
    "NO_BILL_DATA",
    "BILL_NOT_FOUND",
    "BILL_FILE_NOT_FOUND",  # Actual error code returned by the API
    "BILL_TYPE_NOT_SUPPORTED",
    "INVALID_DATE_FORMAT",
    "INVALID_TIMEZONE",
    "EMPTY_BATCH",
})

SYSTEM_ERROR_CODES = frozenset({
    "NETWORK_ERROR",
    "API_UNAVAILABLE",
    "RATE_LIMIT_EXCEEDED",
    "HTTP_ERROR",
    "TIMEOUT",
    "PARSE_ERROR",
    "SYSTEM_ERROR",
    "CONFIG_ERROR",
    "UNKNOWN_EXCEPTION",
    "PARAM_ILLEGAL",
})

MERCHANT_ERROR_CODES = frozenset({
    "MERCHANT_NOT_REGISTERED",
    "MERCHANT_MID_INVALID",
    "MERCHANT_MID_MISSING",
    "ACCOUNT_NOT_FOUND",
    "AUTH_REQUIRED",
})


def get_error_message(code: str) -> str:
    """Return the description for an error code."""
    return ERROR_CODES.get(code, f"Unknown error: {code}")


# ============================================================
# User-friendly error messages (for agent-facing output)
# Single source of truth — base_api_client.py imports from here.
# ============================================================

FRIENDLY_MESSAGES: Dict[str, str] = {
    # Server-side errors
    "UNKNOWN_EXCEPTION":       "The query service is temporarily unavailable. Please retry later.",
    "SYSTEM_ERROR":            "A system error occurred on the server. Please retry later.",
    "API_UNAVAILABLE":         "The API is temporarily unavailable. Please retry later.",
    # Network errors
    "NETWORK_ERROR":           "A network error occurred. Please check your connection and retry later.",
    "HTTP_ERROR":              "An HTTP request error occurred. Please retry later.",
    "TIMEOUT":                 "The request timed out. Please retry later.",
    # Rate limiting
    "RATE_LIMIT_EXCEEDED":     "Request rate limit exceeded. Please wait a moment and retry.",
    # Parse / config errors
    "PARSE_ERROR":             "Failed to parse the server response. Please retry later.",
    "CONFIG_ERROR":            "Configuration error. Please check your CLI setup and try again.",
    # Parameter errors
    "PARAM_ILLEGAL":           "Invalid request parameters. Please verify the date range and bill type.",
    "INVALID_DATE_FORMAT":     "Invalid date format. Please use YYYYMMDD.",
    "INVALID_TIMEZONE":        "Invalid timezone format. Please check the timezone parameter.",
    # Auth errors
    "AUTH_REQUIRED":           "Authentication required. Please run 'antom login' to configure credentials.",
    "MERCHANT_NOT_REGISTERED": "The merchant is not enrolled in the billing service.",
    "MERCHANT_MID_INVALID":    "The merchant ID is invalid. Please check your CLI configuration.",
    "MERCHANT_MID_MISSING":    "Merchant ID is missing. Please check your CLI configuration.",
    "ACCOUNT_NOT_FOUND":       "The specified account was not found. Please verify your merchant configuration.",
    # Data errors (not real errors — no data available)
    "NO_BILL_DATA":            "No bill data available for the requested date.",
    "BILL_NOT_FOUND":          "The specified bill file was not found.",
    "BILL_FILE_NOT_FOUND":     "The specified bill file was not found.",
    "BILL_TYPE_NOT_SUPPORTED": "This bill type is not supported for the current merchant.",
    "EMPTY_BATCH":             "No settlement batch for the requested date (settlement threshold not reached).",
}


def get_friendly_message(
    code: str,
    default: str = "An unexpected error occurred. Please retry later.",
) -> str:
    """Return a user-friendly message for an error code.

    Falls back to ``default`` if the code is not in FRIENDLY_MESSAGES.
    """
    return FRIENDLY_MESSAGES.get(code, default)


def is_business_error(code: str) -> bool:
    """Return True if the error code represents a business data condition (not exceptional)."""
    return code in BUSINESS_ERROR_CODES


def is_system_error(code: str) -> bool:
    """Return True if the error code represents a system or network error."""
    return code in SYSTEM_ERROR_CODES


def is_merchant_error(code: str) -> bool:
    """Return True if the error code represents a merchant or account error."""
    return code in MERCHANT_ERROR_CODES
