"""  
CDN Document Loader

Pure CDN loading strategy: all documents are read directly from CDN without local caching.

Rules Base URL: https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/rules
Wiki Base URL: https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki
"""

import logging
import re
from typing import Optional

import requests

# CDN Base URLs
RULES_BASE_URL = "https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/rules"
WIKI_BASE_URL = "https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki"

# Skill version — must stay in sync with SKILL.md frontmatter `version`
SKILL_VERSION = "1.0.0"

# Skill source repository — metadata for agent to generate update commands
SKILL_REPO = "https://github.com/ant-intl/antom-ai-tools"
SKILL_REPO_PATH = "antom-reconciliation-expert"

# Logging configuration
logger = logging.getLogger(__name__)


def _fetch_from_cdn(relative_path: str, timeout: int = 5) -> str:
    """
    Fetch rules specification documents from CDN.

    Args:
        relative_path: Relative path, e.g., 'workflows/comprehensive-analysis.md'
        timeout: Request timeout in seconds

    Returns:
        Document content, empty string on failure
    """
    url = f"{RULES_BASE_URL.rstrip('/')}/{relative_path.lstrip('/')}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning(f"Rules CDN fetch failed {url}: {e}")
        return ""
    except Exception as e:
        logger.error(f"Rules CDN unknown error {url}: {e}")
        return ""


def _fetch_from_wiki(filename: str, timeout: int = 5) -> str:
    """
    Fetch content from CDN Wiki.

    Args:
        filename: Wiki filename, e.g., 'index.md', 'fee-and-amount.md'
        timeout: Request timeout in seconds

    Returns:
        Document content, empty string on failure
    """
    url = f"{WIKI_BASE_URL.rstrip('/')}/{filename.lstrip('/')}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning(f"Wiki CDN fetch failed {url}: {e}")
        return ""
    except Exception as e:
        logger.error(f"Wiki CDN unknown error {url}: {e}")
        return ""


def load_doc(relative_path: str, timeout: int = 5) -> str:
    """
    Load specification document: read entirely from CDN.

    Returns:
        Document content string, empty string on complete failure
    """
    return _fetch_from_cdn(relative_path, timeout)


def load_workflow(name: str) -> str:
    """
    Load workflow document.

    Args:
        name: Workflow name, e.g., 'comprehensive-analysis', 'validation', 'transaction-tracing', 'fee-analysis'

    Returns:
        Workflow document content
    """
    return load_doc(f"workflows/{name}.md")


def load_capabilities() -> str:
    """
    Load capability definition document.

    Returns:
        Capability definition document content
    """
    return load_doc("capabilities.md")


def load_constraints() -> str:
    """
    Load constraint specification details.

    Returns:
        Constraint specification document content
    """
    return load_doc("constraints/index.md")


def load_tools() -> str:
    """
    Load tool specification manual.

    Returns:
        Tool specification document content
    """
    return load_doc("tools/index.md")


def load_guardrails() -> str:
    """
    Load Guardrails specification cases.

    Returns:
        Guardrails specification document content
    """
    return load_doc("guardrails/index.md")


# ── Wiki knowledge base loading functions ─────────────────────────────────────

def load_wiki(relative_path: str, timeout: int = 5) -> str:
    """
    Load Wiki knowledge base document: read directly from CDN.

    Args:
        relative_path: Wiki relative path, e.g., 'index.md', 'entities/amount-fields.md'
        timeout: Request timeout in seconds

    Returns:
        Document content string, empty string on failure
    """
    return _fetch_from_wiki(relative_path, timeout)


def load_wiki_index(timeout: int = 5) -> str:
    """
    Load Wiki knowledge base index page (scenario navigation).

    Args:
        timeout: Request timeout in seconds

    Returns:
        Wiki index page content
    """
    return load_wiki('index.md', timeout)


# ── Version check ─────────────────────────────────────────────────────────────

def _parse_version(v: str) -> list:
    """Parse semver string into [major, minor, patch] integers.

    Tolerates non-numeric prefixes (e.g. 'v1.0.0') and suffixes
    (e.g. '1.0.0-beta'). Short versions (e.g. '1.0') are zero-padded
    to three segments so that '1.0' equals '1.0.0'.
    """
    parts = re.findall(r'\d+', v)
    if not parts:
        return [0, 0, 0]
    while len(parts) < 3:
        parts.append('0')
    return [int(x) for x in parts[:3]]


def _version_lt(v1: str, v2: str) -> bool:
    """Compare semver strings: True if v1 < v2."""
    return _parse_version(v1) < _parse_version(v2)


def check_version(timeout: int = 5) -> dict:
    """
    Check local SKILL_VERSION against the CDN version manifest.

    The manifest (``rules/version-manifest.json``) declares:
      - min_skill_version: minimum skill version required by current CDN rules
      - latest_skill_version: newest published skill version
      - release_notes: one-line summary of the latest release

    Returns:
        dict with keys:
          - current (str): local SKILL_VERSION
          - repo (str): skill source repository URL (for agent to generate update commands)
          - repo_path (str): skill directory path within the repository
          - min_required (str | None): min_skill_version from manifest
          - latest (str | None): latest_skill_version from manifest
          - release_notes (str): release summary from manifest (empty string if absent)
          - needs_update (bool): True when current < min_required
          - has_newer (bool): True when a newer version exists
          - message (str): human-readable upgrade notice (empty if up-to-date)
          - error (str | None): error message if manifest fetch failed
    """
    result = {
        "current": SKILL_VERSION,
        "repo": SKILL_REPO,
        "repo_path": SKILL_REPO_PATH,
        "min_required": None,
        "latest": None,
        "release_notes": "",
        "needs_update": False,
        "has_newer": False,
        "message": "",
        "error": None,
    }
    manifest_url = f"{RULES_BASE_URL}/version-manifest.json"
    try:
        resp = requests.get(manifest_url, timeout=timeout)
        resp.raise_for_status()
        manifest = resp.json()
    except Exception as e:
        logger.debug(f"Version manifest fetch failed: {e}")
        result["error"] = str(e)
        return result

    min_v = manifest.get("min_skill_version", "0.0.0")
    latest_v = manifest.get("latest_skill_version", SKILL_VERSION)
    notes = manifest.get("release_notes", "")
    result["min_required"] = min_v
    result["latest"] = latest_v
    result["release_notes"] = notes

    needs_update = _version_lt(SKILL_VERSION, min_v)
    has_newer = _version_lt(SKILL_VERSION, latest_v)
    result["needs_update"] = needs_update
    result["has_newer"] = has_newer

    notes_suffix = f" ({notes})" if notes else ""

    if needs_update:
        result["message"] = (
            f"Your Reconciliation Expert is v{SKILL_VERSION}, "
            f"but v{min_v}+ is required by the latest rules"
            f"{notes_suffix}. "
            f"Please update the skill to ensure accurate analysis."
        )
    elif has_newer:
        result["message"] = (
            f"Reconciliation Expert v{latest_v} is available"
            f"{notes_suffix} "
            f"(you have v{SKILL_VERSION}). "
            f"Consider updating for the latest improvements."
        )

    return result
