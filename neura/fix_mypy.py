#!/usr/bin/env python3
"""
Fix common MyPy errors automatically.

Fixes:
1. Optional[T] → T | None (already done by Ruff)
2. Missing return type annotations
3. Implicit Optional parameters
"""

import re
import sys
from pathlib import Path


def fix_implicit_optional(content: str) -> str:
    """Fix implicit Optional in function signatures."""
    # Pattern: def func(param: Type = None)
    # Replace with: def func(param: Type | None = None)
    
    patterns = [
        # voice: str = None → voice: str | None = None
        (r'(\w+):\s*str\s*=\s*None', r'\1: str | None = None'),
        # rate: int = None → rate: int | None = None
        (r'(\w+):\s*int\s*=\s*None', r'\1: int | None = None'),
        # language: str = None → language: str | None = None
        (r'language:\s*str\s*=\s*None', r'language: str | None = None'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content


def fix_missing_return_types(file_path: Path) -> None:
    """Add missing return type annotations."""
    content = file_path.read_text()
    original = content
    
    # Fix implicit Optional
    content = fix_implicit_optional(content)
    
    # Add -> None for __init__ methods without return type
    content = re.sub(
        r'(def __init__\([^)]+\)):\s*\n',
        r'\1 -> None:\n',
        content
    )
    
    if content != original:
        file_path.write_text(content)
        print(f"✅ Fixed: {file_path}")
        return True
    
    return False


def main():
    """Fix MyPy errors in neura/ directory."""
    neura_dir = Path("neura")
    
    if not neura_dir.exists():
        print("❌ neura/ directory not found")
        sys.exit(1)
    
    print("🔧 Fixing MyPy errors...\n")
    
    fixed_count = 0
    
    # Fix Python files
    for py_file in neura_dir.rglob("*.py"):
        if fix_missing_return_types(py_file):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
    print("\nRun: poetry run mypy neura/ --ignore-missing-imports")


if __name__ == "__main__":
    main()
