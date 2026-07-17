#!/usr/bin/env python3
"""CLI launcher for antom-reconciliation-expert skill modules.

Avoids PYTHONPATH issues by inserting the skill root into sys.path
before delegating to the target module's __main__ block.

Usage:
  python3 scripts/cli.py <module> [args...]

Examples:
  python3 scripts/cli.py scripts.core.parser --files xxx.csv
  python3 scripts/cli.py scripts.core.validators --mode summary --input /tmp/parsed.json
  python3 scripts/cli.py scripts.io_modules.bill_list_api --start 20260315 --end 20260325
  python3 scripts/cli.py scripts.io_modules.bill_downloader --input /tmp/bills.json
  python3 scripts/cli.py scripts.retrieval.cdn_loader --doc constraints
  python3 scripts/cli.py scripts.retrieval.transaction_detail_query --tx-id xxx
"""
import sys
import os

# Insert skill root into sys.path (absolute path, never relative)
# cli.py is in scripts/, so skill root is one level up
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(_scripts_dir)
sys.path.insert(0, skill_root)

# Dependency check — only when a module is actually invoked
_MODULE_DEPS = {
    "scripts.core.parser":                 ["openpyxl"],
    "scripts.io_modules.bill_downloader":   ["requests"],
    "scripts.retrieval.cdn_loader":        ["requests"],
    "scripts.io_modules.bill_list_api":    [],  # uses antom CLI, not pip
    "scripts.retrieval.transaction_detail_query": [],  # uses antom CLI
    "scripts.core.validators":             [],  # pure stdlib
}


def _check_deps(module_name):
    deps = _MODULE_DEPS.get(module_name, [])
    missing = []
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    if missing:
        print(f"Error: module '{module_name}' requires: {', '.join(missing)}", file=sys.stderr)
        print(f"Install with: pip3 install {' '.join(missing)}", file=sys.stderr)
        sys.exit(2)


if len(sys.argv) < 2:
    print("Usage: python3 scripts/cli.py <module> [args...]\n")
    print("Available modules:")
    print("  scripts.core.parser                        Parse settlement detail reports")
    print("  scripts.core.validators                    Validate and compute summaries")
    print("  scripts.io_modules.bill_list_api           Query bill download URLs")
    print("  scripts.io_modules.bill_downloader         Download bill files")
    print("  scripts.retrieval.cdn_loader               Load CDN knowledge documents")
    print("  scripts.retrieval.transaction_detail_query Query transaction detail")
    sys.exit(1)

module = sys.argv[1]
sys.argv = [sys.argv[0]] + sys.argv[2:]

_check_deps(module)

import runpy
runpy.run_module(module, run_name="__main__")
