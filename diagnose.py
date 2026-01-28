"""
Diagnostic Script for MET GUI
Helps identify where solvents/bases lists are hardcoded
"""

import os
import re
import sys

print("=" * 70)
print("🔍 MET GUI DIAGNOSTIC TOOL")
print("=" * 70)

# Check if descriptor files are available
print("\n📦 Checking descriptor files...")
try:
    from bofire_solvent_descriptors import BOFIRE_SOLVENT_DESCRIPTORS
    print(f"✓ bofire_solvent_descriptors.py found ({len(BOFIRE_SOLVENT_DESCRIPTORS)} solvents)")
except ImportError as e:
    print(f"✗ bofire_solvent_descriptors.py NOT FOUND")
    print(f"  Error: {e}")
    BOFIRE_SOLVENT_DESCRIPTORS = {}

try:
    from bofire_base_descriptors import BOFIRE_BASE_DESCRIPTORS
    print(f"✓ bofire_base_descriptors.py found ({len(BOFIRE_BASE_DESCRIPTORS)} bases)")
except ImportError as e:
    print(f"✗ bofire_base_descriptors.py NOT FOUND")
    print(f"  Error: {e}")
    BOFIRE_BASE_DESCRIPTORS = {}

# List available compounds
if BOFIRE_SOLVENT_DESCRIPTORS:
    print("\n📋 Available Solvents:")
    for i, solvent in enumerate(sorted(BOFIRE_SOLVENT_DESCRIPTORS.keys()), 1):
        print(f"  {i:2d}. {solvent}")

if BOFIRE_BASE_DESCRIPTORS:
    print("\n📋 Available Bases:")
    for i, base in enumerate(sorted(BOFIRE_BASE_DESCRIPTORS.keys()), 1):
        print(f"  {i:2d}. {base}")

# Search for hardcoded lists in Python files
print("\n" + "=" * 70)
print("🔎 Searching for hardcoded lists in Python files...")
print("=" * 70)

# Common solvent names to search for
common_solvents = ["Water", "Ethanol", "Acetone", "DMSO", "DMF"]
common_bases = ["Triethylamine", "Pyridine", "DBU"]

# Files to check
files_to_check = []
for root, dirs, files in os.walk('.'):
    # Skip common non-relevant directories
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
    for file in files:
        if file.endswith('.py') and not file.startswith('bofire_'):
            files_to_check.append(os.path.join(root, file))

print(f"\nFound {len(files_to_check)} Python files to check\n")

suspicious_files = []

for filepath in files_to_check:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Check for hardcoded solvent lists
            solvent_patterns = [
                r'\[.*["\']Water["\'].*["\']Ethanol["\'].*\]',  # List with Water and Ethanol
                r'options\s*=\s*\[.*["\']Water["\']',  # Dropdown options with Water
                r'categories\s*=\s*\[.*["\']Water["\']',  # BoFire categories with Water
            ]
            
            # Check for hardcoded base lists
            base_patterns = [
                r'\[.*["\']Triethylamine["\'].*["\']Pyridine["\'].*\]',
                r'options\s*=\s*\[.*["\']Triethylamine["\']',
                r'categories\s*=\s*\[.*["\']Triethylamine["\']',
            ]
            
            found_issues = []
            
            for i, line in enumerate(lines, 1):
                # Check solvent patterns
                for pattern in solvent_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        found_issues.append((i, line.strip(), "Potential hardcoded SOLVENT list"))
                
                # Check base patterns
                for pattern in base_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        found_issues.append((i, line.strip(), "Potential hardcoded BASE list"))
                
                # Check for specific dropdown definitions
                if 'dcc.Dropdown' in line or 'CategoricalInput' in line:
                    # Check next few lines for hardcoded options
                    context = '\n'.join(lines[max(0, i-1):min(len(lines), i+10)])
                    if any(solv in context for solv in common_solvents):
                        found_issues.append((i, line.strip(), "Dropdown/Feature definition (check nearby lines)"))
            
            if found_issues:
                suspicious_files.append((filepath, found_issues))
    
    except Exception as e:
        print(f"⚠️  Error reading {filepath}: {e}")

# Report findings
if suspicious_files:
    print("\n🚨 FOUND POTENTIAL HARDCODED LISTS:\n")
    for filepath, issues in suspicious_files:
        print(f"\n📄 {filepath}")
        print("─" * 70)
        for line_num, line, issue_type in issues:
            print(f"  Line {line_num}: {issue_type}")
            print(f"    → {line[:80]}{'...' if len(line) > 80 else ''}")
else:
    print("\n✓ No obvious hardcoded lists found!")
    print("  If dropdowns still don't show new compounds, check:")
    print("  - Are the descriptor files in the correct location?")
    print("  - Did you restart the server after changes?")
    print("  - Are the imports correct in your app file?")

# Provide recommendations
print("\n" + "=" * 70)
print("💡 RECOMMENDATIONS")
print("=" * 70)

if suspicious_files:
    print("\n1. Review the files listed above")
    print("2. Replace hardcoded lists with dynamic imports:")
    print("\n   from bofire_solvent_descriptors import BOFIRE_SOLVENT_DESCRIPTORS")
    print("   from bofire_base_descriptors import BOFIRE_BASE_DESCRIPTORS")
    print("\n   # For Dash dropdowns:")
    print("   options=[{'label': s, 'value': s} for s in BOFIRE_SOLVENT_DESCRIPTORS.keys()]")
    print("\n   # For BoFire features:")
    print("   categories=list(BOFIRE_SOLVENT_DESCRIPTORS.keys())")

print("\n3. After making changes, restart your application server")
print("4. Clear browser cache if needed (Ctrl+Shift+R or Cmd+Shift+R)")

# Check for common files
print("\n" + "=" * 70)
print("📁 CHECKING COMMON FILES")
print("=" * 70)

common_files = ['app.py', 'layout.py', 'callbacks.py', 'domain.py', 'features.py', 'config.py']
for filename in common_files:
    if os.path.exists(filename):
        print(f"  ✓ {filename} exists - CHECK THIS FILE")
    else:
        print(f"  ✗ {filename} not found")

print("\n" + "=" * 70)
print("Done! Review the findings above.")
print("=" * 70)