"""
Parsing of online-analysis result files.

Result file format (``key = value`` lines, experiments separated by blank lines)::

    Yield = 78.5
    STY = 12.3

    Yield = 92.1
    STY = 15.6

Rules:
- Each experiment is a block of ``key = value`` lines.
- Blocks are separated by one or more blank lines.
- Lines starting with ``#`` are comments (ignored).
- File keys are mapped to objective names via a user-provided mapping.
- Works with any number of objectives.
"""

import os
from typing import Optional


def parse_result_file(filepath: str) -> list[dict]:
    """Parse ``filepath`` into a list of ``{key: float}`` experiment dicts."""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Online analysis: error reading file {filepath}: {e}")
        return []

    experiments: list[dict] = []
    current_block: dict = {}

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#"):
            continue

        if not stripped:
            if current_block:
                experiments.append(current_block)
                current_block = {}
            continue

        if "=" not in stripped:
            print(f"Online analysis: skipping line without '=': '{stripped}'")
            continue

        key, value_str = (part.strip() for part in stripped.split("=", 1))
        try:
            current_block[key] = float(value_str)
        except ValueError:
            print(f"Online analysis: could not parse value '{value_str}' for key '{key}'")

    if current_block:
        experiments.append(current_block)

    return experiments


def get_file_keys(filepath: str) -> list[str]:
    """Return the keys present in the first experiment block of ``filepath``."""
    experiments = parse_result_file(filepath)
    return list(experiments[0].keys()) if experiments else []


def map_results_to_objectives(experiments: list[dict], key_mapping: dict) -> list[dict]:
    """Remap file keys to domain objective names using ``key_mapping``."""
    mapped = []
    for exp in experiments:
        mapped_exp = {
            obj_name: exp[file_key]
            for file_key, obj_name in key_mapping.items()
            if file_key in exp
        }
        mapped.append(mapped_exp)
    return mapped


def get_new_results(filepath: str, already_processed: int, key_mapping: dict) -> list[dict]:
    """Return mapped results that are past index ``already_processed``."""
    all_experiments = parse_result_file(filepath)
    if len(all_experiments) <= already_processed:
        return []
    return map_results_to_objectives(all_experiments[already_processed:], key_mapping)


def count_results_in_file(filepath: str) -> int:
    """Count complete experiment blocks in ``filepath``."""
    return len(parse_result_file(filepath))


def get_file_modification_time(filepath: str) -> Optional[float]:
    """Return ``os.path.getmtime(filepath)`` or ``None`` if the file is missing."""
    if os.path.exists(filepath):
        return os.path.getmtime(filepath)
    return None


def validate_result_file(filepath: str) -> dict:
    """
    Return diagnostic info about ``filepath``.

    The returned dict has keys ``valid``, ``exists``, ``n_results``, ``keys``,
    and a human-readable ``message``.
    """
    info = {
        "valid": False,
        "exists": False,
        "n_results": 0,
        "keys": [],
        "message": "",
    }

    if not os.path.exists(filepath):
        info["message"] = "File not found"
        return info

    info["exists"] = True

    try:
        experiments = parse_result_file(filepath)
        info["n_results"] = len(experiments)
        info["keys"] = list(experiments[0].keys()) if experiments else []
        info["valid"] = True

        if experiments:
            keys_str = ", ".join(info["keys"])
            info["message"] = f"{len(experiments)} experiment(s) found — keys: {keys_str}"
        else:
            info["message"] = "File exists but no complete experiment blocks found"
    except Exception as e:
        info["message"] = f"Error reading file: {e}"

    return info
