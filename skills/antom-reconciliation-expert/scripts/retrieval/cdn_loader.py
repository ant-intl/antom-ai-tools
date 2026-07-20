"""CDN Document Loader

CDN loading strategy with in-memory caching, retry on transient errors,
and structured error reporting.

Rules Base URL: https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/rules
Wiki Base URL:  https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki
"""

import time
from typing import Dict

import requests

RULES_BASE_URL = "https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/rules"
WIKI_BASE_URL = "https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki"

# ── In-memory document cache (per-process) ──────────────────────────────────
# Key: full URL, Value: (timestamp, content_string, is_error)
_cache: Dict[str, tuple] = {}
_CACHE_TTL = 300       # seconds — for successful fetches
_ERROR_CACHE_TTL = 10  # seconds — for failed fetches (short, allows quick retry)

# ── Retry configuration ─────────────────────────────────────────────────────
_RETRY_COUNT = 2
_RETRY_DELAY = 1.0  # base delay in seconds; actual = base * 2^attempt

# HTTP status codes that are NOT transient — skip retry
_NON_TRANSIENT_STATUSES = frozenset({401, 403, 404})


def _fetch_from_url(base_url: str, relative_path: str, timeout: int = 10) -> str:
    """Fetch document content from the CDN with retry and caching.

    Returns the document text on success, or a ``[CDN_LOAD_ERROR]...[/CDN_LOAD_ERROR]``
    tagged string on failure so the caller can distinguish failure from an empty doc.
    """
    url = f"{base_url.rstrip('/')}/{relative_path.lstrip('/')}"

    # Check in-memory cache
    if url in _cache:
        ts, cached, is_error = _cache[url]
        ttl = _ERROR_CACHE_TTL if is_error else _CACHE_TTL
        if time.time() - ts < ttl:
            return cached
        del _cache[url]

    # Fetch with retry on transient errors
    last_error = ""
    for attempt in range(_RETRY_COUNT + 1):
        try:
            resp = requests.get(url, timeout=timeout)

            if resp.status_code >= 500 or resp.status_code == 429:
                # Transient server error — retry if attempts remain
                last_error = f"HTTP {resp.status_code} from CDN"
                if attempt < _RETRY_COUNT:
                    time.sleep(_RETRY_DELAY * (2 ** attempt))
                    continue
                break

            resp.raise_for_status()
            content = resp.text
            _cache[url] = (time.time(), content, False)
            return content

        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", 0) if e.response is not None else 0
            if status in _NON_TRANSIENT_STATUSES:
                last_error = f"HTTP {status} from CDN (non-transient)"
                break  # don't retry 404/403/401
            last_error = f"HTTP {status} from CDN"
            if attempt < _RETRY_COUNT:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
                continue
            break

        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = f"CDN request failed: {e}"
            if attempt < _RETRY_COUNT:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
                continue
            break

        except Exception as e:
            last_error = f"CDN fetch failed: {e}"
            break

    # All attempts exhausted — cache error with short TTL so transient
    # failures can be retried quickly (not blocked for 5 minutes).
    error_str = f"[CDN_LOAD_ERROR]{last_error}[/CDN_LOAD_ERROR]"
    _cache[url] = (time.time(), error_str, True)
    return error_str


# ── Public load functions ────────────────────────────────────────────────────

def load_doc(relative_path: str, timeout: int = 10) -> str:
    """Load a rules document (CDN with cache + retry)."""
    # Normalize: strip leading 'rules/' to prevent double-prefix with RULES_BASE_URL
    relative_path = relative_path.lstrip('/')
    if relative_path.startswith('rules/'):
        relative_path = relative_path[6:]
    return _fetch_from_url(RULES_BASE_URL, relative_path, timeout)


def load_workflow(name: str) -> str:
    """Load a workflow reference document.
    name: comprehensive-analysis / validation / transaction-tracing / fee-analysis"""
    return load_doc(f"workflows/{name}.md")


def load_capabilities() -> str:
    """Load the capability definitions document."""
    return load_doc("capabilities.md")


def load_constraints() -> str:
    """Load the detailed constraint rules document."""
    return load_doc("constraints/index.md")


def load_tools() -> str:
    """Load the tool parameter reference manual."""
    return load_doc("tools/index.md")


def load_guardrails() -> str:
    """Load the Guardrails case examples document."""
    return load_doc("guardrails/index.md")


# ── Version manifest loading ────────────────────────────────────────────────

def load_version_manifest(timeout: int = 10) -> str:
    """Load the version manifest JSON from CDN."""
    return load_doc("version-manifest.json", timeout)


# ── Version check ─────────────────────────────────────────────────────────────

def check_version() -> str:
    """Load the version manifest from CDN.

    Every session triggers a check. Within the same process the in-memory
    cache (300 s TTL) prevents duplicate network calls.

    Returns the manifest JSON string, or a ``[CDN_LOAD_ERROR]`` string on failure.
    """
    return load_version_manifest()


# ── Wiki knowledge base loading functions ─────────────────────────────────────

def load_wiki(relative_path: str, timeout: int = 10) -> str:
    """Load a Wiki knowledge base document (CDN with cache + retry).

    Path is relative to the wiki/ directory. A leading 'wiki/' prefix is
    automatically stripped to prevent double-prefix errors (the base URL
    already ends with /wiki).
    """
    # Normalize: strip leading 'wiki/' to prevent double-prefix with WIKI_BASE_URL
    relative_path = relative_path.lstrip('/')
    if relative_path.startswith('wiki/'):
        relative_path = relative_path[5:]
    return _fetch_from_url(WIKI_BASE_URL, relative_path, timeout)


def load_wiki_index(timeout: int = 10) -> str:
    """Load the Wiki knowledge base index page (scenario navigation)."""
    return load_wiki('index.md', timeout)


def load_report_template(timeout: int = 10) -> str:
    """Load the settlement analysis report content checklist.
    Must be called before generating any settlement analysis report."""
    return load_wiki('templates/report_template.md', timeout)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    _cli = argparse.ArgumentParser(
        description="Load CDN knowledge base documents",
    )
    _cli.add_argument("--doc", required=True,
                      help="Document to load: constraints, capabilities, guardrails, "
                           "wiki-index, report-template, tools, version-manifest, workflow:<name>, wiki:<path>")
    _args = _cli.parse_args()

    _doc_map = {
        "constraints": load_constraints,
        "capabilities": load_capabilities,
        "guardrails": load_guardrails,
        "wiki-index": load_wiki_index,
        "report-template": load_report_template,
        "tools": load_tools,
        "version-manifest": load_version_manifest,
    }

    if _args.doc.startswith("workflow:"):
        _content = load_workflow(_args.doc[9:])
    elif _args.doc.startswith("wiki:"):
        _content = load_wiki(_args.doc[5:])
    elif _args.doc in _doc_map:
        _content = _doc_map[_args.doc]()
    else:
        print(f"Unknown doc: {_args.doc}\nAvailable: {', '.join(_doc_map.keys())}, "
              f"workflow:<name>, wiki:<path>", file=sys.stderr)
        sys.exit(1)

    print(_content)
