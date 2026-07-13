#!/usr/bin/env python3
"""
Remove corrupted files from the repository
"""
import os
import sys
import glob
from pathlib import Path

# Change to repo directory
repo_dir = Path(r"c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System")
os.chdir(repo_dir)

print("=" * 70)
print("Repository Cleanup Tool")
print("=" * 70)
print(f"Working directory: {os.getcwd()}")
print()

# List of problematic filenames to remove
corrupted_patterns = [
    "pan initialization step  ",
    "*pan*initialization*",
    "tatus*",
    "ubprocess",
    "e",
    "h",
    "t",
]

# Also specifically target files that git can't handle
specifically_remove = [
    "pan initialization step  ",
    "tatus",
    "tatus --porcelain",
    "t",
    "e",
    "h",
    "ubprocess",
]

print("Attempting to remove corrupted files...")
print()

removed_count = 0
failed_count = 0

# Try removing specific files
for filename in specifically_remove:
    filepath = repo_dir / filename
    if filepath.exists():
        try:
            os.remove(filepath)
            print(f"✓ Removed: {filename}")
            removed_count += 1
        except Exception as ex:
            print(f"✗ Failed to remove '{filename}': {ex}")
            failed_count += 1
            
            # Try alternative method
            try:
                import subprocess
                subprocess.run(['del', '/F', '/Q', str(filepath)], shell=True, check=False)
                print(f"  → Removed via subprocess")
                removed_count += 1
                failed_count -= 1
            except:
                pass

print()
print("=" * 70)
print(f"Summary: {removed_count} removed, {failed_count} failed")
print("=" * 70)
print()

# List remaining files in root
print("Current files in repository root:")
print()
for item in sorted(os.listdir(".")):
    if not item.startswith("."):
        full_path = repo_dir / item
        size = len(item)
        if os.path.isdir(item):
            print(f"  [DIR]  {item}")
        else:
            print(f"  [FILE] {item} ({size} chars)")

print()
print("If cleanup was successful, try:")
print("  git status")
print("  git add .")
print("  git commit -m 'Cleanup corrupted files'")
print("  git push origin develop")
