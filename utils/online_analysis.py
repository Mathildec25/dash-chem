"""
Online Analysis Utilities
Handles parsing result files from online analysis tools and detecting new results.

Result file format (key = value, experiments separated by blank lines):

    Yield = 78.5
    STY = 12.3

    Yield = 92.1
    STY = 15.6

    Yield = 65.3
    STY = 9.8

Rules:
- Each experiment is a block of "key = value" lines
- Blocks are separated by one or more blank lines
- Lines starting with '#' are comments (ignored)
- Keys in the file are mapped to objective names via a user-defined mapping
- Works with any number of objectives (1, 2, 3, ...)
"""

import os
from typing import Optional


def parse_result_file(filepath: str) -> list[dict]:
    """
    Parse a result file into a list of experiment result dicts.
    
    Each experiment is a block of key=value lines separated by blank lines.
    
    Args:
        filepath: Path to the result text file
        
    Returns:
        List of dicts, e.g.:
        [
            {'Yield': 78.5, 'STY': 12.3},
            {'Yield': 92.1, 'STY': 15.6},
        ]
    """
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Online Analysis: Error reading file {filepath}: {e}")
        return []
    
    experiments = []
    current_block = {}
    
    for line in lines:
        stripped = line.strip()
        
        # Skip comments
        if stripped.startswith('#'):
            continue
        
        # Empty line = end of block
        if not stripped:
            if current_block:
                experiments.append(current_block)
                current_block = {}
            continue
        
        # Parse key = value
        if '=' in stripped:
            parts = stripped.split('=', 1)
            key = parts[0].strip()
            value_str = parts[1].strip()
            
            try:
                value = float(value_str)
                current_block[key] = value
            except ValueError:
                print(f"⚠️ Online Analysis: Could not parse value '{value_str}' for key '{key}'")
        else:
            print(f"⚠️ Online Analysis: Skipping line without '=': '{stripped}'")
    
    # Don't forget last block if file doesn't end with blank line
    if current_block:
        experiments.append(current_block)
    
    return experiments


def get_file_keys(filepath: str) -> list[str]:
    """
    Detect the keys present in the result file (from the first experiment block).
    Useful for auto-populating the key mapping UI.
    
    Args:
        filepath: Path to the result text file
        
    Returns:
        List of key names found in the first block, e.g. ['Yield', 'STY']
    """
    experiments = parse_result_file(filepath)
    if experiments:
        return list(experiments[0].keys())
    return []


def map_results_to_objectives(experiments: list[dict], key_mapping: dict) -> list[dict]:
    """
    Remap file keys to domain objective names using the user-defined mapping.
    
    Args:
        experiments: Raw parsed experiments from parse_result_file()
        key_mapping: Dict mapping file keys to objective names
                     e.g. {'Yield': 'Yield', 'STY': 'SpaceTimeYield'}
    
    Returns:
        List of dicts with objective names as keys, e.g.:
        [{'Yield': 78.5, 'SpaceTimeYield': 12.3}, ...]
    """
    mapped = []
    for exp in experiments:
        mapped_exp = {}
        for file_key, obj_name in key_mapping.items():
            if file_key in exp:
                mapped_exp[obj_name] = exp[file_key]
        mapped.append(mapped_exp)
    return mapped


def get_new_results(filepath: str, already_processed: int, key_mapping: dict) -> list[dict]:
    """
    Get only the new results that haven't been processed yet,
    already mapped to objective names.
    
    Args:
        filepath: Path to the result text file
        already_processed: Number of experiments already integrated
        key_mapping: Dict mapping file keys to objective names
        
    Returns:
        List of new mapped result dicts
    """
    all_experiments = parse_result_file(filepath)
    
    if len(all_experiments) > already_processed:
        new_raw = all_experiments[already_processed:]
        return map_results_to_objectives(new_raw, key_mapping)
    
    return []


def count_results_in_file(filepath: str) -> int:
    """Count how many complete experiment blocks are in the file."""
    return len(parse_result_file(filepath))


def get_file_modification_time(filepath: str) -> Optional[float]:
    """Get the last modification time of the result file."""
    if os.path.exists(filepath):
        return os.path.getmtime(filepath)
    return None


def validate_result_file(filepath: str) -> dict:
    """
    Validate a result file and return diagnostic information.
    
    Returns:
        Dict with:
        {
            'valid': bool,
            'exists': bool,
            'n_results': int,
            'keys': list[str],       # keys found in first block
            'message': str
        }
    """
    info = {
        'valid': False,
        'exists': False,
        'n_results': 0,
        'keys': [],
        'message': ''
    }
    
    if not os.path.exists(filepath):
        info['message'] = 'File not found'
        return info
    
    info['exists'] = True
    
    try:
        experiments = parse_result_file(filepath)
        info['n_results'] = len(experiments)
        info['keys'] = list(experiments[0].keys()) if experiments else []
        info['valid'] = True
        
        if experiments:
            keys_str = ', '.join(info['keys'])
            info['message'] = f"{len(experiments)} experiment(s) found — keys: {keys_str}"
        else:
            info['message'] = "File exists but no complete experiment blocks found"
    
    except Exception as e:
        info['message'] = f'Error reading file: {e}'
    
    return info