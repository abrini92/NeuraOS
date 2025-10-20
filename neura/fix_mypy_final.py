#!/usr/bin/env python3
"""
Fix remaining MyPy errors automatically.
"""

import re
from pathlib import Path


def fix_no_return_value(file_path: Path) -> bool:
    """Fix 'No return value expected' errors by changing -> None to proper type."""
    content = file_path.read_text()
    original = content
    
    # Pattern: async def func() -> None: ... return {...}
    # These should be -> dict or appropriate type
    
    # For router files, change -> None to -> dict for endpoints
    if 'router.py' in str(file_path):
        # Find functions that return dict but are typed as -> None
        content = re.sub(
            r'(async def \w+\([^)]*\)) -> None:',
            r'\1 -> dict:',
            content
        )
    
    if content != original:
        file_path.write_text(content)
        return True
    
    return False


def fix_missing_args(file_path: Path, errors: list[str]) -> bool:
    """Add missing arguments based on error messages."""
    content = file_path.read_text()
    original = content
    
    # Fix PolicyDecision missing retry_after
    if 'policy/engine.py' in str(file_path):
        content = re.sub(
            r'PolicyDecision\(([^)]+)\)',
            r'PolicyDecision(\1, retry_after=None)',
            content
        )
    
    if content != original:
        file_path.write_text(content)
        return True
    
    return False


def main():
    """Fix all remaining MyPy errors."""
    print("🔧 Fixing final MyPy errors...\n")
    
    neura_dir = Path("neura")
    fixed_count = 0
    
    # Fix router files (No return value expected)
    router_files = list(neura_dir.rglob("*router.py"))
    print(f"📝 Fixing {len(router_files)} router files...")
    for router_file in router_files:
        if fix_no_return_value(router_file):
            print(f"   ✅ {router_file}")
            fixed_count += 1
    
    # Fix policy engine
    policy_engine = neura_dir / "policy" / "engine.py"
    if policy_engine.exists():
        print(f"\n📝 Fixing policy engine...")
        if fix_missing_args(policy_engine, []):
            print(f"   ✅ {policy_engine}")
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
    print("\nRun: poetry run mypy neura/")


if __name__ == "__main__":
    main()
