"""
Safe Excel file I/O with atomic writes and rotating backups.

Prevents corruption from interrupted writes, crashes, or concurrent access by
writing to a temporary file, validating it, optionally backing up the target,
and only then performing an atomic replace.
"""

import logging
import os
import shutil
import tempfile
from datetime import datetime
from zipfile import BadZipFile

import pandas as pd
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

MAX_BACKUPS = 3
BACKUP_SUFFIX = ".backup"


def safe_excel_save(file_path, write_func, backup=True):
    """
    Save an Excel file atomically.

    Writes to a temp file in the same directory, validates it, backs up the
    existing target (if any), and replaces the target in a single
    ``os.replace`` call.

    Args:
        file_path: Target Excel path.
        write_func: Callable ``(path) -> None`` that writes the Excel content.
        backup: If True (default), keep a rotated backup of the previous file.

    Returns:
        Tuple ``(success: bool, message: str)``.
    """
    directory = os.path.dirname(file_path) or '.'
    os.makedirs(directory, exist_ok=True)
    
    # --- Step 1: Write to temporary file in the same directory ---
    # Same directory ensures os.replace() is atomic (same filesystem)
    temp_fd, temp_path = tempfile.mkstemp(suffix='.xlsx', dir=directory)
    os.close(temp_fd)
    
    try:
        write_func(temp_path)
    except PermissionError:
        _cleanup_temp(temp_path)
        filename = os.path.basename(file_path)
        msg = (
            f"Cannot save '{filename}': file is open in another application. "
            f"Please close it and try again."
        )
        logger.error(msg)
        return False, msg
    except Exception as e:
        _cleanup_temp(temp_path)
        logger.error(f"Failed to write temp file: {e}")
        return False, f"Write failed: {e}"
    
    # --- Step 2: Validate the temp file is a valid Excel ---
    try:
        _validate_excel(temp_path)
    except Exception as e:
        _cleanup_temp(temp_path)
        logger.error(f"Validation failed for temp file: {e}")
        return False, f"File validation failed: {e}"
    
    # --- Step 3: Create backup of existing file ---
    if backup and os.path.exists(file_path):
        try:
            _create_backup(file_path)
        except Exception as e:
            # Non-fatal: log but continue with the save
            logger.warning(f"Backup creation failed: {e}")
    
    # --- Step 4: Atomic replace ---
    try:
        os.replace(temp_path, file_path)
        logger.info("Safely saved: %s", file_path)
        return True, "File saved successfully"
    except PermissionError:
        _cleanup_temp(temp_path)
        filename = os.path.basename(file_path)
        msg = (
            f"Cannot save '{filename}': file is open in another application. "
            f"Please close it and try again."
        )
        logger.error(msg)
        return False, msg
    except Exception as e:
        _cleanup_temp(temp_path)
        logger.error(f"Failed to replace file: {e}")
        return False, f"Replace failed: {e}"


def safe_excel_read(file_path):
    """
    Read an Excel file, falling back to the most recent valid backup on failure.

    If a backup is successfully loaded it is also copied over the corrupted
    main file.

    Returns:
        Tuple ``(df_or_None, message)``.
    """
    try:
        return pd.read_excel(file_path, engine="openpyxl"), "ok"
    except (BadZipFile, Exception) as e:
        logger.warning("Main file corrupted: %s - %s", file_path, e)

    for backup_path in _get_sorted_backups(file_path):
        try:
            df = pd.read_excel(backup_path, engine="openpyxl")
            logger.info("Recovered from backup: %s", backup_path)
            shutil.copy2(backup_path, file_path)
            logger.info("Restored backup to main file: %s", file_path)
            return df, "Recovered from backup (some recent changes may be lost)"
        except Exception:
            continue

    return None, f"File is corrupted and no valid backup found: {file_path}"


def _validate_excel(file_path):
    """Raise if ``file_path`` is not a loadable Excel workbook."""
    if os.path.getsize(file_path) == 0:
        raise ValueError("File is empty (0 bytes)")
    wb = load_workbook(file_path, read_only=True)
    wb.close()


def _create_backup(file_path):
    """Copy ``file_path`` into the ``.backups`` subdirectory and rotate old ones."""
    directory = os.path.dirname(file_path) or "."
    basename = os.path.basename(file_path)
    name, ext = os.path.splitext(basename)

    backup_dir = os.path.join(directory, ".backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{name}_{timestamp}{ext}{BACKUP_SUFFIX}")

    shutil.copy2(file_path, backup_path)
    _rotate_backups(file_path)


def _rotate_backups(file_path):
    """Delete all but the ``MAX_BACKUPS`` most recent backups."""
    for old_backup in _get_sorted_backups(file_path)[MAX_BACKUPS:]:
        try:
            os.remove(old_backup)
        except Exception:
            pass


def _get_sorted_backups(file_path):
    """Return backup paths for ``file_path``, newest first."""
    directory = os.path.dirname(file_path) or "."
    name, _ = os.path.splitext(os.path.basename(file_path))

    backup_dir = os.path.join(directory, ".backups")
    if not os.path.exists(backup_dir):
        return []

    backups = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.startswith(name) and f.endswith(BACKUP_SUFFIX)
    ]
    backups.sort(key=os.path.getmtime, reverse=True)
    return backups


def _cleanup_temp(temp_path):
    """Best-effort removal of a leftover temp file."""
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception:
        pass