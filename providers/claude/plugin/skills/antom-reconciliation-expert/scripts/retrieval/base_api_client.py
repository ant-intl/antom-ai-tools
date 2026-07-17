"""Base API Client

Abstracts common logic for antom CLI command execution:
subprocess invocation with retry, timeout, and JSON response parsing.

Subclasses build their own command lists and call _run_command().
The antom CLI handles authentication, endpoint resolution, and HTTPS transport.
"""

import json
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Friendly error messages are centralized in error_codes.py (single source of truth)
from ..io_modules.error_codes import get_friendly_message


class BaseAPIClient:
    """Base class for antom CLI command clients.

    Provides _run_command() which executes an antom subcommand with
    retry on transient errors and JSON response parsing.

    Subclasses only need to:
    - Set _API_NAME for logging
    - Build command lists and call _run_command()
    """

    _API_NAME: str = "API"

    # Retry defaults (can be overridden per subclass)
    _RETRY_COUNT: int = 2
    _RETRY_DELAY: float = 1.0  # base delay; actual = base * 2^attempt
    _cache_ttl: int = 300      # cache TTL in seconds (class-level)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Each subclass gets its own cache dict — shared across instances of
        # the same subclass, but isolated from sibling subclasses.
        cls._query_cache: Dict[str, tuple] = {}

    def __init__(self, skill_root: Optional[str] = None):
        self.skill_root = Path(skill_root) if skill_root else Path(__file__).parent.parent.parent
        self.last_error: Optional[str] = None          # technical detail for logging
        self.last_error_friendly: Optional[str] = None  # user-facing message

    def _run_command(self, cmd: List[str], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Run an antom CLI command with retry on transient errors.

        The CLI handles authentication, endpoint resolution, and HTTPS transport.
        This method manages subprocess execution, retry, and JSON parsing only.

        Args:
            cmd: Full command list, e.g.
                 ["antom", "report", "download-list", "--date", "20260601",
                  "--bill-type", "SETTLEMENT_DETAIL", "--json"]
            timeout: Subprocess timeout in seconds

        Returns:
            Parsed JSON dict from CLI stdout, or None on failure.
            On failure, self.last_error contains a human-readable error message.
        """
        self.last_error = None
        self.last_error_friendly = None

        for attempt in range(self._RETRY_COUNT + 1):
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                if attempt < self._RETRY_COUNT:
                    time.sleep(self._RETRY_DELAY * (2 ** attempt))
                    continue
                self.last_error = f"Command timed out ({timeout}s) after {self._RETRY_COUNT + 1} attempts"
                self.last_error_friendly = "The query timed out. Please retry later."
                print(f"Warning: {self._API_NAME} command timed out ({timeout}s) after {self._RETRY_COUNT + 1} attempts")
                return None
            except FileNotFoundError:
                self.last_error = "antom command not found; ensure antom-cli is installed and on PATH"
                self.last_error_friendly = ("Antom CLI is not installed. Please install it via "
                                            "'curl -fsSL https://mdn.alipayobjects.com/portal_4vwbay/uri/file/as/release/antom-cli-install.sh | bash' "
                                            "and log in with 'antom login'.")
                print(f"Warning: {self.last_error}")
                return None

            if proc.returncode == 2:
                # Usage error — not transient, don't retry
                self.last_error = f"Usage error: {proc.stderr.strip()}"
                self.last_error_friendly = "Invalid command parameters. Please check the date format and bill type."
                print(f"Warning: {self._API_NAME} usage error: {proc.stderr.strip()}")
                return None

            stdout_text = proc.stdout.strip()
            if not stdout_text:
                if attempt < self._RETRY_COUNT:
                    time.sleep(self._RETRY_DELAY * (2 ** attempt))
                    continue
                self.last_error = f"Empty response (exit={proc.returncode})"
                if proc.stderr.strip():
                    self.last_error += f": {proc.stderr.strip()}"
                self.last_error_friendly = "The server returned an empty response. Please retry later."
                print(f"Warning: {self._API_NAME} returned empty response (exit={proc.returncode})")
                if proc.stderr.strip():
                    print(f"  stderr: {proc.stderr.strip()}")
                return None

            try:
                response = json.loads(stdout_text)
            except json.JSONDecodeError as e:
                if attempt < self._RETRY_COUNT:
                    time.sleep(self._RETRY_DELAY * (2 ** attempt))
                    continue
                self.last_error = f"Failed to parse output: {e}"
                self.last_error_friendly = "Received an unparseable response from the server. Please retry later."
                print(f"Warning: {self._API_NAME} failed to parse output: {e}")
                return None

            # Check for CLI error response (non-zero exit code with error JSON)
            # The antom CLI returns JSON on stdout even for errors, but with a
            # non-zero exit code and an "error" key in the response body.
            # Without this check, error responses are silently treated as success.
            if proc.returncode != 0:
                error_info = response.get("error", {}) if isinstance(response, dict) else {}
                error_code = error_info.get("code", "UNKNOWN")
                error_msg = error_info.get("message", f"CLI exited with code {proc.returncode}")
                result_code = error_info.get("result_code", "")
                self.last_error = f"{error_code} - {error_msg}"
                if result_code:
                    self.last_error += f" (result_code={result_code})"
                self.last_error_friendly = get_friendly_message(result_code) if result_code else \
                    f"The query failed. Please retry later or contact Antom Support."
                print(f"Warning: {self._API_NAME} failed: {self.last_error}")
                return None

            return response

        return None

    # ── Cache ──

    def _get_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        if key in self._query_cache:
            ts, data = self._query_cache[key]
            if time.time() - ts < self._cache_ttl:
                return data
            del self._query_cache[key]
        return None

    def _set_cache(self, key: str, results: List[Dict[str, Any]]):
        self._query_cache[key] = (time.time(), results)
