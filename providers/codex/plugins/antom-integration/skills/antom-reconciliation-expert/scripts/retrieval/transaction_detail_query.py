"""Transaction Detail Query

Query a transaction detail via the antom CLI command:
  antom report transaction-detail --transaction-id <id> --json --live

The CLI handles authentication, endpoint resolution, and HTTPS transport.
Python is responsible only for constructing the command flags and
parsing the JSON response.

CLI JSON output schema (returned directly to caller):
  {
    "profile": "default",
    "environment": "test",
    "merchant_id": "2188120258646856",
    "transaction_id": "20260122194010800100188010245005460",
    "merchant_request_id": "PAYMENT_...",
    "reference_transaction_id": "ORDER_...",
    "amount": {"value": "0.15", "currency": "CNY"},
    "status": "TO_BE_SETTLED",
    "transaction_type": "PAYMENT",
    "payment_method": {"type": "ALIPAY_CN", "psp_name": "AlipayCN"},
    "risk_decision": null,
    "payment_lifecycle": [
      {"time": "2026-01-22T19:36:04+08:00", "transaction_type": "PAYMENT", "transaction_status": "PROCESSING"}
    ]
  }

Usage within a Skill:
    from scripts.retrieval.transaction_detail_query import query_transaction_detail
    result = query_transaction_detail("20260518993030096600502796446525944")
"""

from typing import List, Dict, Any, Optional

from .base_api_client import BaseAPIClient


class TransactionDetailQuerier(BaseAPIClient):
    """Transaction detail query client via antom report transaction-detail command."""
    _API_NAME = "Transaction Detail"

    def query(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Query a single transaction detail.

        Args:
            transaction_id: Transaction ID

        Returns:
            CLI JSON response dict, or None on failure
        """
        if not transaction_id or not transaction_id.strip():
            return None

        cmd = [
            "antom", "report", "transaction-detail",
            "--transaction-id", transaction_id.strip(),
            "--json",
            "--live",
        ]
        return self._run_command(cmd)

    def query_batch(self, transaction_ids: List[str]) -> List[Dict[str, Any]]:
        """Query multiple transaction details sequentially.

        Args:
            transaction_ids: List of transaction IDs

        Returns:
            List of query results, one per transaction ID (failed queries are skipped)
        """
        results = []
        for tid in transaction_ids:
            cache_key = tid
            cached = self._get_cache(cache_key)
            if cached is not None:
                results.extend(cached)
                continue

            result = self.query(tid)
            if result is not None:
                results.append(result)
                self._set_cache(cache_key, [result])
        return results


def query_transaction_detail(
    transaction_id: str,
    skill_root: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Query a single transaction detail.

    Args:
        transaction_id: Transaction ID
        skill_root: Skill root directory (optional)

    Returns:
        CLI JSON response dict, or None on failure
    """
    querier = TransactionDetailQuerier(skill_root)
    return querier.query(transaction_id)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import json as _json
    import sys

    _cli = argparse.ArgumentParser(
        description="Query transaction detail via antom CLI",
    )
    _cli.add_argument("--tx-id", required=True, help="Transaction ID")
    _args = _cli.parse_args()

    _result = query_transaction_detail(_args.tx_id)
    if _result is not None:
        print(_json.dumps(_result, indent=2, ensure_ascii=False, default=str))
    else:
        print(_json.dumps({"error": "Query returned None"}, indent=2), file=sys.stderr)
        sys.exit(1)
