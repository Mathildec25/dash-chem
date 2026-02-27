"""
Safe Excel file operations with atomic writes and automatic backups.
Prevents file corruption from interrupted writes, crashes, or concurrent access.
"""

import os
import shutil
import tempfile
import logging
from datetime import datetime
from zipfile import BadZipFile

import pandas as pd
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

# Maximum number of backups to keep per file
MAX_BACKUPS = 3
BACKUP_SUFFIX = ".backup"


def safe_excel_save(file_path, write_func, backup=True):
    """
    Safely save an Excel file using atomic write pattern.
    
    1. Write to a temporary file in the same directory
    2. Validate the temp file is a valid Excel
    3. Create a backup of the current file (if it exists)
    4. Atomically replace the original with the temp file
    
    Parameters
    ----------
    file_path : str
        Path to the target Excel file.
    write_func : callable
        Function that takes a file path and writes the Excel content.
        Example: lambda path: df.to_excel(path, index=False, engine='openpyxl')
    backup : bool
        Whether to create a backup of the existing file before overwriting.
    
    Returns
    -------
    tuple (bool, str)
        (success, message)
    
    Usage
    -----
    # Simple save:
    safe_excel_save(
        "data.xlsx",
        lambda path: df.to_excel(path, index=False, engine='openpyxl')
    )
    
    # With ExcelWriter formatting:
    def write_formatted(path):
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Experiments')
            # ... formatting code ...
    
    safe_excel_save("data.xlsx", write_formatted)
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
        logger.info(f"✅ Safely saved: {file_path}")
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
    Safely read an Excel file with automatic recovery from corruption.
    
    If the main file is corrupted, attempts to read from the most recent backup.
    
    Parameters
    ----------
    file_path : str
        Path to the Excel file.
    
    Returns
    -------
    tuple (pd.DataFrame, str)
        (dataframe, message) - message indicates if backup was used
    """
    # Try reading the main file
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df, "ok"
    except (BadZipFile, Exception) as e:
        logger.warning(f"Main file corrupted: {file_path} - {e}")
    
    # Try backups in reverse chronological order
    backups = _get_sorted_backups(file_path)
    for backup_path in backups:
        try:
            df = pd.read_excel(backup_path, engine='openpyxl')
            logger.info(f"✅ Recovered from backup: {backup_path}")
            
            # Restore the backup as the main file
            shutil.copy2(backup_path, file_path)
            logger.info(f"✅ Restored backup to main file: {file_path}")
            
            return df, f"Recovered from backup (some recent changes may be lost)"
        except Exception:
            continue
    
    # No valid backup found
    return None, f"File is corrupted and no valid backup found: {file_path}"


def _validate_excel(file_path):
    """Validate that a file is a valid Excel file by opening it."""
    # Check file size > 0
    if os.path.getsize(file_path) == 0:
        raise ValueError("File is empty (0 bytes)")
    
    # Try to open with openpyxl (validates ZIP structure + Excel format)
    wb = load_workbook(file_path, read_only=True)
    wb.close()


def _create_backup(file_path):
    """Create a timestamped backup, rotate old backups."""
    directory = os.path.dirname(file_path) or '.'
    basename = os.path.basename(file_path)
    name, ext = os.path.splitext(basename)
    
    backup_dir = os.path.join(directory, '.backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{name}_{timestamp}{ext}{BACKUP_SUFFIX}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    shutil.copy2(file_path, backup_path)
    
    # Rotate: keep only MAX_BACKUPS most recent
    _rotate_backups(file_path)


def _rotate_backups(file_path):
    """Keep only the most recent MAX_BACKUPS backups for a given file."""
    backups = _get_sorted_backups(file_path)
    
    for old_backup in backups[MAX_BACKUPS:]:
        try:
            os.remove(old_backup)
        except Exception:
            pass


def _get_sorted_backups(file_path):
    """Get backup files sorted by modification time (newest first)."""
    directory = os.path.dirname(file_path) or '.'
    basename = os.path.basename(file_path)
    name, _ = os.path.splitext(basename)
    
    backup_dir = os.path.join(directory, '.backups')
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for f in os.listdir(backup_dir):
        if f.startswith(name) and f.endswith(BACKUP_SUFFIX):
            full_path = os.path.join(backup_dir, f)
            backups.append(full_path)
    
    # Sort by modification time, newest first
    backups.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return backups


def _cleanup_temp(temp_path):
    """Remove temporary file, ignoring errors."""
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception:
        pass