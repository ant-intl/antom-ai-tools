"""  
CDN Document Loader

Pure CDN loading strategy: all documents are read directly from CDN without local caching.

Rules Base URL: https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/rules
Wiki Base URL: https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki
"""

import logging
from typing import Optional

import requests

# CDN Base URLs
RULES_BASE_URL = "https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/rules"
WIKI_BASE_URL = "https://cdn.marmot-cloud.com/page/antom_bill_reconciliation_doc/wiki"

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
