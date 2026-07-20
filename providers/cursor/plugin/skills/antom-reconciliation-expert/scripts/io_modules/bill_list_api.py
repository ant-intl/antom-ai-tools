"""Bill List API

Query bill download URLs via the antom CLI command:
  antom report download-list --date <YYYYMMDD|YYYYMMDD-YYYYMMDD> --bill-type <TYPE> --json --live

The CLI handles authentication, endpoint resolution, and HTTPS transport.
Python is responsible only for constructing the command flags and
parsing the JSON response.

Supports batch querying across multiple dates by grouping contiguous
dates into ranges and merging results from multiple CLI calls.

CLI JSON output schema (returned directly to caller):
  {
    "profile": "default",
    "environment": "test",
    "merchant_id": "2188120258646856",
    "date": {"start": "20260401", "end": "20260630"},
    "total": 2,
    "bill_download_urls": [
      {
        "bill_date": "20260428",
        "bill_type": "SETTLEMENT_DETAIL",
        "download_url": "https://...",
        "file_token": "...",
        "metadata": {"merchant_account_id": "...", "settle_date": "20260428"}
      }
    ]
  }
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from ..retrieval.base_api_client import BaseAPIClient


class BillListClient(BaseAPIClient):
    """Bill list API client via antom report download-list command."""
    _API_NAME = "Bill List"

    def query(self, date_str: str, bill_type: str) -> Optional[Dict[str, Any]]:
        """Query bills for a single date or date range.

        Args:
            date_str: Single date 'YYYYMMDD' or range 'YYYYMMDD-YYYYMMDD'
            bill_type: Bill type, e.g. SETTLEMENT_DETAIL

        Returns:
            CLI JSON response dict, or None on failure
        """
        cmd = [
            "antom", "report", "download-list",
            "--date", date_str,
            "--bill-type", bill_type,
            "--json",
            "--live",
        ]
        return self._run_command(cmd, timeout=65)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def validate_date_format(date: str) -> bool:
    """Validate date format (yyyyMMdd)."""
    try:
        datetime.strptime(date, "%Y%m%d")
        return True
    except ValueError:
        return False


def _group_dates_to_ranges(dates: List[str]) -> List[str]:
    """Sort dates and group contiguous ones into ranges.

    Returns:
        List of strings, each either 'YYYYMMDD' or 'YYYYMMDD-YYYYMMDD'.
    """
    sorted_dates = sorted(set(dates))
    if not sorted_dates:
        return []

    ranges: List[str] = []
    start = sorted_dates[0]
    end = sorted_dates[0]

    for i in range(1, len(sorted_dates)):
        prev_dt = datetime.strptime(end, "%Y%m%d")
        curr_dt = datetime.strptime(sorted_dates[i], "%Y%m%d")
        if (curr_dt - prev_dt).days == 1:
            end = sorted_dates[i]
        else:
            ranges.append(f"{start}-{end}" if start != end else start)
            start = sorted_dates[i]
            end = sorted_dates[i]

    ranges.append(f"{start}-{end}" if start != end else start)
    return ranges


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def get_bill_list(
    dates: List[str],
    bill_type: str = "SETTLEMENT_DETAIL",
) -> Dict[str, Any]:
    """Query bill download URLs for multiple dates.

    Groups contiguous dates into ranges to minimize CLI calls, then
    merges the results into a single response.

    Args:
        dates: List of dates in yyyyMMdd format, e.g. ['20260504', '20260505']
        bill_type: Bill type, e.g. SETTLEMENT_DETAIL, SETTLEMENT_SUMMARY

    Returns:
        CLI JSON response (merged if multiple ranges):
        {
          "profile": "...",
          "environment": "...",
          "merchant_id": "...",
          "date": {"start": "...", "end": "..."},
          "total": N,
          "bill_download_urls": [...]
        }
        On failure: {"success": false, "error": "...", "bill_download_urls": []}
    """
    if not dates:
        return {
            "success": False,
            "error": "Date list cannot be empty",
            "bill_download_urls": [],
        }

    # Validate date formats
    for date in dates:
        if not validate_date_format(date):
            return {
                "success": False,
                "error": f"Invalid date format: {date} (expected yyyyMMdd)",
                "bill_download_urls": [],
            }

    # Normalize bill type (backward compat: settlementDetail -> SETTLEMENT_DETAIL)
    if bill_type == "settlementDetail":
        bill_type = "SETTLEMENT_DETAIL"

    # Group contiguous dates into ranges
    ranges = _group_dates_to_ranges(dates)

    # Check max 90 days per range (CLI constraint)
    for r in ranges:
        if '-' in r:
            start_str, end_str = r.split('-')
            start_dt = datetime.strptime(start_str, "%Y%m%d")
            end_dt = datetime.strptime(end_str, "%Y%m%d")
            if (end_dt - start_dt).days > 89:
                return {
                    "success": False,
                    "error": f"Date range {r} exceeds 90 days maximum",
                    "bill_download_urls": [],
                }

    client = BillListClient()

    # Single range — return CLI output directly
    if len(ranges) == 1:
        result = client.query(ranges[0], bill_type)
        if result is None:
            return {
                "success": False,
                "error": client.last_error_friendly or client.last_error or "The query failed. Please retry later.",
                "error_detail": client.last_error,
                "bill_download_urls": [],
            }
        return result

    # Multiple ranges — call CLI for each and merge
    all_urls: List[Dict[str, Any]] = []
    first_result: Optional[Dict[str, Any]] = None
    min_start = min(dates)
    max_end = max(dates)

    for r in ranges:
        result = client.query(r, bill_type)
        if result is None:
            return {
                "success": False,
                "error": client.last_error_friendly or client.last_error or "The query failed. Please retry later.",
                "error_detail": client.last_error,
                "bill_download_urls": all_urls,
            }
        if first_result is None:
            first_result = result
        all_urls.extend(result.get("bill_download_urls", []))

    # Sort by bill_date
    all_urls.sort(key=lambda x: x.get("bill_date", ""))

    return {
        "profile": first_result.get("profile") if first_result else None,
        "environment": first_result.get("environment") if first_result else None,
        "merchant_id": first_result.get("merchant_id") if first_result else None,
        "date": {"start": min_start, "end": max_end},
        "total": len(all_urls),
        "bill_download_urls": all_urls,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import json as _json
    import sys
    from datetime import datetime, timedelta

    _cli = argparse.ArgumentParser(
        description="Query bill download URLs via antom CLI",
    )
    _cli.add_argument("--start", required=True, help="Start date (yyyyMMdd)")
    _cli.add_argument("--end", required=True, help="End date (yyyyMMdd)")
    _cli.add_argument("--bill-type", default="SETTLEMENT_DETAIL",
                      help="Bill type (default: SETTLEMENT_DETAIL)")
    _args = _cli.parse_args()

    _start_dt = datetime.strptime(_args.start, "%Y%m%d")
    _end_dt = datetime.strptime(_args.end, "%Y%m%d")
    _dates = []
    _cur = _start_dt
    while _cur <= _end_dt:
        _dates.append(_cur.strftime("%Y%m%d"))
        _cur += timedelta(days=1)

    _result = get_bill_list(_dates, _args.bill_type)
    print(_json.dumps(_result, indent=2, ensure_ascii=False, default=str))
    sys.exit(0 if _result.get("success", True) else 1)
