#!/usr/bin/env python3
"""Remove corrupted untracked files from git repository."""
import os
import sys
from pathlib import Path

# Change to repo directory
repo_dir = Path(r"c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System")
os.chdir(repo_dir)

# List of corrupted files identified in directory listing
corrupted_files = [
    "describe b9771968-3d86-41e3-acc1-4a88e978c338 --project=main-presence-500410-f8 2&1",
    "e",
    "ervices describe enterprise-ai-frontend-staging --region us-central1 --format=value(spec.template.spec.containers[0].env)",
    "h",
    "h origin develop",
    "how --stat HEAD",
    "jq parse error Invalid numeric literal at line 1, column 5",
    "leep 10 && echo Waiting for new build to appear...",
    "leep 15",
    "pan initialization step  ",
    "s -File CTempgit_push.ps1",
    "sage' in build",
    "t",
    "t --format=value(core.project)",
    "tatus",
    "tatus --porcelain",
    "ubprocess",
    "ult = subprocess.run(['git', 'commit', '-m', 'fix simplify Dockerfile and remove error handling'],",
    "ult.stderr}),",
    " {result.stderr})",
]

print("=" * 70)
print("REMOVING CORRUPTED FILES")
print("=" * 70)

removed_count = 0
error_count = 0

for filename in corrupted_files:
    file_path = repo_dir / filename
    if file_path.exists():
        try:
            if file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            print(f"✓ REMOVED: {filename}")
            removed_count += 1
        except Exception as e:
            print(f"✗ ERROR:   {filename}")
            print(f"           {e}")
            error_count += 1
    else:
        print(f"⊘ SKIP:    {filename} (not found)")

print("=" * 70)
print(f"Summary: Removed {removed_count} files, {error_count} errors")
print("=" * 70)
