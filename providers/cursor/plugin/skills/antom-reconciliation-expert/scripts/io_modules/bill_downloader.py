"""
Bill Downloader

Downloads bill files atomically, extracts ZIPs recursively, and verifies
integrity via a per-ZIP manifest (.{zip}.manifest.json) that records the
ZIP's SHA256 hash and per-extracted-file sizes.

Two-layer integrity-aware reuse:
  L1 — Extracted XLSX files exist + size matches manifest
       → reuse (no download, no unzip)
  L2 — ZIP exists + SHA256 matches manifest
       → reuse ZIP (extract again only if extraction is stale)
       → otherwise: download, verify, unzip, save manifest

Header: Referer: https://dashboard.antom.com
"""

import os
import re
import json
import shutil
import hashlib
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import requests

from ..core.constants import DOWNLOAD_REFERER


# Regex to extract the 18-digit batchId from an XLSX inner filename
_BATCH_ID_RE = re.compile(r'_(\d{18})_')


# ---------------------------------------------------------------------------
# Hashing & Manifest
# ---------------------------------------------------------------------------

def _sha256(file_path: Path) -> str:
    """Compute the SHA256 hex digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _manifest_path(zip_path: Path) -> Path:
    """Manifest sidecar file path: .{zip_name}.manifest.json"""
    return zip_path.parent / f".{zip_path.name}.manifest.json"


def _save_manifest(zip_path: Path, zip_hash: str, extracted_files: List[str]) -> None:
    """Save manifest with ZIP hash and per-extracted-file sizes."""
    file_sizes: Dict[str, int] = {}
    for p in extracted_files:
        try:
            file_sizes[p] = Path(p).stat().st_size
        except Exception:
            file_sizes[p] = 0
    manifest = {
        "zip_hash": zip_hash,
        "zip_size": zip_path.stat().st_size if zip_path.exists() else 0,
        "extracted_files": extracted_files,
        "file_sizes": file_sizes,
        "extraction_time": datetime.now().isoformat(),
    }
    try:
        with open(_manifest_path(zip_path), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: failed to save manifest: {e}")


def _load_manifest(zip_path: Path) -> Optional[Dict[str, Any]]:
    """Load manifest dict if present and parseable, else None."""
    mp = _manifest_path(zip_path)
    if not mp.exists():
        return None
    try:
        with open(mp, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _delete_quietly(p: Path) -> None:
    """Best-effort delete; ignore errors."""
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def peek_zip_main_xlsx_name(zip_path: Path) -> Optional[str]:
    """Read the ZIP central directory only (no extraction) and return the main
    inner filename (XLSX/CSV/nested ZIP). Filters out macOS junk."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                base = name.split('/')[-1]
                if not base or base.startswith('._') or '__MACOSX' in name:
                    continue
                lower = base.lower()
                if lower.endswith('.xlsx') or lower.endswith('.csv') or lower.endswith('.zip'):
                    return base
    except zipfile.BadZipFile:
        print(f"Warning: {zip_path.name} is not a valid ZIP file")
        return None
    except Exception as e:
        print(f"Warning: failed to peek ZIP {zip_path.name}: {e}")
        return None
    return None


def parse_batch_id_from_xlsx_name(xlsx_name: str) -> Optional[str]:
    """Extract the 18-digit batchId from a SettlementDetailReport main filename."""
    m = _BATCH_ID_RE.search(xlsx_name)
    return m.group(1) if m else None


def _pick_main_file(file_list: List[str]) -> Optional[str]:
    """Pick the main file from extracted files — XLSX preferred over CSV."""
    csv_fallback = None
    for f in file_list:
        if f.endswith('.xlsx'):
            return f
        if f.endswith('.csv') and csv_fallback is None:
            csv_fallback = f
    return csv_fallback


@dataclass
class DownloadContext:
    """Parameter container for _build_file_info, replacing 11 positional args."""
    date_str: str
    batch_id: Optional[str]
    url: str
    zip_path: Optional[str]
    file_size: int
    is_duplicate: bool
    file_hash: Optional[str]
    all_extracted_files: List[str]
    extracted_iterations: int
    already_extracted: bool
    dedup_level: Optional[str] = None


def _build_file_info(ctx: DownloadContext) -> Dict[str, Any]:
    """Build a standardized file-info dict from a DownloadContext."""
    main_file = _pick_main_file(ctx.all_extracted_files)
    return {
        "date": ctx.date_str,
        "batch_id": ctx.batch_id,
        "original_url": ctx.url,
        "zip_path": ctx.zip_path,
        "file_size": ctx.file_size,
        "download_time": datetime.now().isoformat(),
        "is_duplicate": ctx.is_duplicate,
        "file_hash": ctx.file_hash,
        "all_extracted_files": ctx.all_extracted_files,
        "extracted_iterations": ctx.extracted_iterations,
        "already_extracted": ctx.already_extracted,
        "final_file_path": main_file,
        "file_type": "XLSX" if main_file and main_file.endswith('.xlsx') else ("CSV" if main_file else None),
        "dedup_level": ctx.dedup_level,
    }


# ---------------------------------------------------------------------------
# L1: integrity-verified reuse of already-extracted XLSX
# ---------------------------------------------------------------------------

def _try_l1_reuse(
    target_dir: Path,
    date_str: str,
    expected_count: int,
) -> Optional[List[Path]]:
    """Verify whether enough XLSX files for the given date already exist
    locally AND are integrity-verified by some manifest in target_dir.

    Returns the verified XLSX paths if all checks pass; otherwise None.
    XLSX files without a corresponding manifest entry, or with a size
    mismatch, are deleted to force a fresh download in subsequent steps.
    """
    existing_xlsx = sorted(
        p for p in target_dir.glob(
            f"A_SettlementDetailReport_{date_str}_{date_str}_*.xlsx"
        )
        if not p.name.startswith('._')
    )
    if not existing_xlsx or len(existing_xlsx) < expected_count:
        return None

    # Aggregate size map from all manifests in this directory
    size_map: Dict[str, int] = {}
    for mp in target_dir.glob('.*.manifest.json'):
        try:
            with open(mp, 'r', encoding='utf-8') as f:
                m = json.load(f)
            size_map.update(m.get('file_sizes', {}) or {})
        except (json.JSONDecodeError, IOError):
            continue

    if not size_map:
        # No manifests at all — cannot verify, treat as untrusted
        return None

    verified: List[Path] = []
    for p in existing_xlsx:
        expected = size_map.get(str(p.absolute()))
        if expected is None:
            print(f"L1 miss: no manifest entry for {p.name}, treating as untrusted")
            return None
        actual = p.stat().st_size
        if actual != expected:
            print(f"L1 miss: size mismatch for {p.name} (expected {expected}, got {actual}), deleting")
            _delete_quietly(p)
            return None
        verified.append(p)

    return verified


# ---------------------------------------------------------------------------
# Download (atomic write)
# ---------------------------------------------------------------------------

def download_file_atomic(
    url: str,
    target_dir: Path,
    target_filename: str,
    timeout: int = 30,
    log_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Download a file atomically (temp + rename).

    Returns: {success, local_path, file_size, file_hash, reused, error_message}
    - reused=True means file was already on disk (caller verifies via manifest)
    - reused=False means freshly downloaded
    """
    if log_path is None:
        log_path = Path.home() / "antom" / "logs" / "downloader.log"
    else:
        log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    final_path = target_dir / target_filename

    # If file already on disk, return it (caller does manifest verification)
    if final_path.exists():
        return {
            "success": True,
            "local_path": str(final_path.absolute()),
            "file_size": final_path.stat().st_size,
            "file_hash": _sha256(final_path),
            "reused": True,
        }

    # Download with Content-Length verification
    try:
        headers = {"Referer": DOWNLOAD_REFERER}
        response = requests.get(url, headers=headers, stream=True, timeout=timeout)
        response.raise_for_status()

        expected_length = int(response.headers.get('Content-Length', 0))
        temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', dir=target_dir)
        os.close(temp_fd)

        try:
            actual_length = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        actual_length += len(chunk)

            # Content-Length verification (if server provided it)
            if expected_length and actual_length != expected_length:
                os.unlink(temp_path)
                return {
                    "success": False,
                    "error_message": f"Download truncated: expected {expected_length} bytes, got {actual_length}"
                }

            os.rename(temp_path, final_path)

            # ZIP integrity check: verify magic bytes (PK\x03\x04)
            # AFS may return HTTP 200 + error JSON instead of a real ZIP
            try:
                with open(final_path, 'rb') as f:
                    header = f.read(4)
                if header[:2] != b'PK':
                    # Not a ZIP — try to parse AFS error response
                    afs_error = None
                    try:
                        with open(final_path, 'r', encoding='utf-8-sig') as f:
                            error_body = json.load(f)
                        afs_error = error_body.get('resultMessage', str(error_body))
                    except Exception:
                        pass
                    os.unlink(final_path)
                    _log_download_error(log_path, url, target_filename,
                                        ValueError(afs_error or "Not a valid ZIP file"))
                    return {
                        "success": False,
                        "error_message": afs_error or "Downloaded file is not a valid ZIP"
                    }
            except Exception as e:
                # If we can't read the file back, something is very wrong
                _delete_quietly(final_path)
                return {"success": False, "error_message": f"Post-download validation failed: {e}"}

            return {
                "success": True,
                "local_path": str(final_path.absolute()),
                "file_size": final_path.stat().st_size,
                "file_hash": _sha256(final_path),
                "reused": False,
            }
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except requests.RequestException as e:
        _log_download_error(log_path, url, target_filename, e)
        return {"success": False, "error_message": f"Download failed: {str(e)}"}
    except Exception as e:
        _log_download_error(log_path, url, target_filename, e)
        return {"success": False, "error_message": f"Unknown error: {str(e)}"}


def _log_download_error(log_path: Path, url: str, target_filename: str, err: Exception) -> None:
    """Append a compact error entry to the download log (only on failure)."""
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[Download Error] {datetime.now().isoformat()}\n")
            f.write(f"URL: {url}  Target: {target_filename}\n")
            f.write(f"Error: {err}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Recursive unzip (with ZipSlip + macOS junk filtering)
# ---------------------------------------------------------------------------

def recursive_unzip(zip_path: str, keep_zip: bool = True, max_iterations: int = 5) -> Dict[str, Any]:
    """Recursively unzip a ZIP file until no ZIPs remain.
    Preserves original inner filenames and applies ZipSlip + macOS junk filtering."""
    zip_path = Path(zip_path)

    if not zip_path.exists():
        return {
            "success": False,
            "error_message": f"ZIP file not found: {zip_path}",
            "final_files": []
        }

    current_zips = [zip_path]
    all_final_files: List[str] = []
    iterations = 0

    while current_zips and iterations < max_iterations:
        iterations += 1
        next_zips = []

        for zp in current_zips:
            try:
                with zipfile.ZipFile(zp, 'r') as zf:
                    file_list = zf.namelist()
                    temp_dir = tempfile.mkdtemp(suffix='.extract', dir=zp.parent)

                    # ZipSlip + macOS junk filtering
                    temp_dir_resolved = Path(temp_dir).resolve()
                    safe_members: List[str] = []
                    for member in file_list:
                        if member.endswith('/'):
                            continue
                        if '__MACOSX' in member:
                            continue
                        parts = member.split('/')
                        if any(p.startswith('._') for p in parts):
                            continue
                        if any(p.startswith('.') and len(p) > 1 for p in parts[:-1]):
                            continue
                        member_path = (Path(temp_dir) / member).resolve()
                        if not str(member_path).startswith(str(temp_dir_resolved)):
                            print(f"Warning: skipping ZIP entry with path traversal: {member}")
                            continue
                        safe_members.append(member)

                    zf.extractall(temp_dir, members=safe_members)

                    # Classify extracted files
                    csv_files: List[Path] = []
                    nested_zips: List[Path] = []
                    for f in safe_members:
                        f_lower = f.lower()
                        file_path = Path(temp_dir) / f
                        if not file_path.exists():
                            continue
                        if f_lower.endswith('.csv') or f_lower.endswith('.xlsx'):
                            csv_files.append(file_path)
                        elif f_lower.endswith('.zip'):
                            nested_zips.append(file_path)

                    # Move CSV/XLSX files to final location
                    for csv_path in csv_files:
                        final_csv_path = zp.parent / csv_path.name
                        if not final_csv_path.exists():
                            shutil.move(str(csv_path), str(final_csv_path))
                        all_final_files.append(str(final_csv_path.absolute()))

                    # Handle nested ZIPs
                    for nested_zip in nested_zips:
                        final_zip_path = zp.parent / nested_zip.name
                        if not final_zip_path.exists():
                            shutil.move(str(nested_zip), str(final_zip_path))
                        next_zips.append(final_zip_path)

                    shutil.rmtree(temp_dir, ignore_errors=True)

                    if not keep_zip:
                        _delete_quietly(zp)

            except zipfile.BadZipFile as e:
                return {
                    "success": False,
                    "error_message": f"Corrupt ZIP file: {zp.name} - {str(e)}",
                    "final_files": all_final_files,
                    "total_iterations": iterations
                }
            except Exception as e:
                return {
                    "success": False,
                    "error_message": f"Extraction failed: {zp.name} - {str(e)}",
                    "final_files": all_final_files,
                    "total_iterations": iterations
                }

        current_zips = next_zips

    if iterations >= max_iterations and current_zips:
        return {
            "success": False,
            "error_message": f"Reached maximum extraction depth ({max_iterations})",
            "final_files": all_final_files,
            "total_iterations": iterations,
            "remaining_zips": [str(z) for z in current_zips]
        }

    return {
        "success": True,
        "final_files": all_final_files,
        "total_iterations": iterations
    }


# ---------------------------------------------------------------------------
# Main entry: download_bills (two-layer integrity-aware reuse)
# ---------------------------------------------------------------------------

def download_bills(
    bill_list_response: Dict[str, Any],
    base_dir: Optional[str] = None,
    auto_unzip: bool = True,
    keep_zip: bool = False
) -> Dict[str, Any]:
    """Download and unzip bills by date.

    Two-layer integrity-aware reuse:
      L1 — XLSX files exist + manifest size matches → reuse
      L2 — ZIP exists + manifest hash matches → reuse ZIP, re-extract only if stale
           Otherwise → download, verify, unzip, save manifest
    """
    bill_urls = bill_list_response.get('bill_download_urls', [])
    if not bill_urls:
        return {
            "success": True,
            "errorCode": "NO_BILL_DATA",
            "downloaded_files": [],
            "skipped_dates": [],
            "failed_downloads": []
        }

    if base_dir is None:
        base_dir = Path.home() / "antom" / "bills"
    else:
        base_dir = Path(base_dir)

    downloaded_files: List[Dict[str, Any]] = []
    failed_downloads: List[Dict[str, Any]] = []

    for url_info in bill_urls:
        url = url_info.get('download_url', '')
        bill_type = url_info.get('bill_type', 'SETTLEMENT_DETAIL')
        metadata = url_info.get('metadata', {})
        batch_id = url_info.get('file_token')
        merchant_account_id = metadata.get('merchant_account_id') or 'unknown'
        date_str = url_info.get('bill_date', 'unknown')

        target_dir = base_dir / merchant_account_id / bill_type / date_str
        target_dir.mkdir(parents=True, exist_ok=True)

        # === L1: integrity-verified reuse of extracted XLSX ===
        # expected_count=1: per-URL check; each URL only needs 1 matching XLSX
        l1_files = _try_l1_reuse(target_dir, date_str, expected_count=1)
        if l1_files:
            _bm = _BATCH_ID_RE.search(l1_files[0].name)
            _existing_batch = _bm.group(1) if _bm else batch_id
            print(f"L1 hit: reusing verified XLSX {l1_files[0].name}")
            downloaded_files.append(_build_file_info(DownloadContext(
                date_str=date_str,
                batch_id=_existing_batch,
                url=url,
                zip_path=None,
                file_size=l1_files[0].stat().st_size,
                is_duplicate=True,
                file_hash=None,
                all_extracted_files=[str(p.absolute()) for p in l1_files],
                extracted_iterations=0,
                already_extracted=True,
                dedup_level="L1_manifest_size",
            )))
            continue

        # Build ZIP filename
        if batch_id:
            target_filename = f"{bill_type}_{batch_id}_{date_str}.zip"
        else:
            url_token = url.rsplit('token=', 1)[-1][:8] if 'token=' in url else hashlib.md5(url.encode()).hexdigest()[:8]
            target_filename = f"{bill_type}_{url_token}_{date_str}.zip"

        local_path = target_dir / target_filename

        # === L2: integrity-verify existing ZIP via manifest ===
        if local_path.exists():
            manifest = _load_manifest(local_path)
            current_hash = _sha256(local_path)

            if manifest is None:
                # No manifest — untrusted ZIP, delete and re-download
                print(f"L2 miss: no manifest for {target_filename}, deleting")
                _delete_quietly(local_path)
            elif manifest.get('zip_hash') != current_hash:
                # ZIP tampered/corrupted — delete and re-download
                print(f"L2 miss: ZIP hash mismatch for {target_filename}, deleting")
                _delete_quietly(local_path)
                _delete_quietly(_manifest_path(local_path))
            else:
                # ZIP integrity verified — check extraction state
                extracted = manifest.get('extracted_files', [])
                file_sizes = manifest.get('file_sizes', {}) or {}
                extraction_intact = (
                    bool(extracted)
                    and all(Path(p).exists() for p in extracted)
                    and all(Path(p).stat().st_size == file_sizes.get(p, -1) for p in extracted)
                )
                if extraction_intact:
                    # Full L2 reuse — ZIP + extraction both verified
                    print(f"L2 hit: ZIP + extraction verified, reusing {target_filename}")
                    downloaded_files.append(_build_file_info(DownloadContext(
                        date_str=date_str,
                        batch_id=batch_id,
                        url=url,
                        zip_path=str(local_path.absolute()),
                        file_size=local_path.stat().st_size,
                        is_duplicate=True,
                        file_hash=current_hash,
                        all_extracted_files=extracted,
                        extracted_iterations=0,
                        already_extracted=True,
                        dedup_level="L2_zip_verified",
                    )))
                    continue
                # ZIP OK but extraction stale → fall through to re-extract
                print(f"L2 partial: ZIP verified but extraction stale, will re-extract: {target_filename}")

        # === Download (or file was just deleted above) ===
        result = download_file_atomic(url, target_dir, target_filename)
        if not result['success']:
            failed_downloads.append({
                "date": date_str,
                "url": url,
                "error": result.get('error_message', 'Unknown error')
            })
            continue

        local_path = Path(result['local_path'])
        zip_hash = result['file_hash']

        # === L2 namelist dedup: real batchId may match existing XLSX ===
        _inner = peek_zip_main_xlsx_name(local_path)
        if _inner:
            _real_batch = parse_batch_id_from_xlsx_name(_inner)
            if _real_batch:
                _existing = [
                    p for p in target_dir.glob(f"*_{_real_batch}_*.xlsx")
                    if not p.name.startswith('._') and p.name != _inner
                ]
                if _existing:
                    _delete_quietly(local_path)
                    _save_manifest(local_path, zip_hash, [str(p.absolute()) for p in _existing])
                    print(f"L2 namelist hit: deleted ZIP, reusing {_existing[0].name}")
                    downloaded_files.append(_build_file_info(DownloadContext(
                        date_str=date_str,
                        batch_id=_real_batch,
                        url=url,
                        zip_path=None,
                        file_size=_existing[0].stat().st_size,
                        is_duplicate=True,
                        file_hash=zip_hash,
                        all_extracted_files=[str(p.absolute()) for p in _existing],
                        extracted_iterations=0,
                        already_extracted=True,
                        dedup_level="L2_namelist",
                    )))
                    continue
                # Rename ZIP to use the real batchId
                if not batch_id:
                    new_zip_name = f"{bill_type}_{_real_batch}_{date_str}.zip"
                    new_zip_path = local_path.parent / new_zip_name
                    if local_path.name != new_zip_name and not new_zip_path.exists():
                        try:
                            local_path.rename(new_zip_path)
                            local_path = new_zip_path
                            batch_id = _real_batch
                        except Exception:
                            pass

        # === Extract + save manifest ===
        if auto_unzip:
            unzip_result = recursive_unzip(str(local_path), keep_zip=keep_zip)
            if unzip_result['success']:
                final_files = unzip_result['final_files']
                _save_manifest(local_path, zip_hash, final_files)
                downloaded_files.append(_build_file_info(DownloadContext(
                    date_str=date_str,
                    batch_id=batch_id,
                    url=url,
                    zip_path=str(local_path.absolute()) if local_path.exists() else None,
                    file_size=result['file_size'],
                    is_duplicate=result.get('reused', False),
                    file_hash=zip_hash,
                    all_extracted_files=final_files,
                    extracted_iterations=unzip_result.get('total_iterations', 0),
                    already_extracted=False,
                )))
            else:
                # Unzip failed — clean up and report as failed download
                _delete_quietly(local_path)
                _delete_quietly(_manifest_path(local_path))
                failed_downloads.append({
                    "date": date_str,
                    "url": url,
                    "error": f"Unzip failed: {unzip_result['error_message']}"
                })
        else:
            downloaded_files.append({
                "date": date_str,
                "batch_id": batch_id,
                "original_url": url,
                "zip_path": str(local_path.absolute()),
                "file_size": result['file_size'],
                "download_time": datetime.now().isoformat(),
                "is_duplicate": result.get('reused', False),
                "file_hash": zip_hash,
                "final_file_path": str(local_path.absolute()),
                "file_type": "ZIP",
            })

    partial_success = len(failed_downloads) > 0
    return {
        "success": len(downloaded_files) > 0 or not partial_success,
        "partial_success": partial_success,
        "downloaded_files": downloaded_files,
        "failed_downloads": failed_downloads,
        "skipped_dates": [],
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    _cli = argparse.ArgumentParser(
        description="Download and unzip bill files from bill list JSON",
    )
    _cli.add_argument("--input", required=True,
                      help="JSON file path from bill_list_api output")
    _cli.add_argument("--base-dir", default=None,
                      help="Base directory for downloads (default: ~/antom/bills)")
    _cli.add_argument("--no-unzip", action="store_true",
                      help="Skip automatic unzip")
    _cli.add_argument("--keep-zip", action="store_true",
                      help="Keep ZIP files after extraction")
    _args = _cli.parse_args()

    with open(_args.input) as _f:
        _bill_list = json.load(_f)

    _result = download_bills(
        _bill_list,
        base_dir=_args.base_dir,
        auto_unzip=not _args.no_unzip,
        keep_zip=_args.keep_zip,
    )
    print(json.dumps(_result, indent=2, ensure_ascii=False, default=str))
    sys.exit(0 if _result.get("success") else 1)
