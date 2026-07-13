#!/usr/bin/env python3
"""
Direct git operations bypassing terminal paging issues.
This script removes corrupted files and stages them for commit.
"""
import subprocess
import os
import sys
from pathlib import Path

repo_dir = Path(r"c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System")
os.chdir(repo_dir)

# Corrupted files to remove
corrupted = [
    "pan initialization step  ",
    "tatus",
    "t",
    "e",
    "h",
    "leep 15",
    "leep 10 && echo Waiting for new build to appear...",
    "sage' in build",
    "ubprocess",
    "how --stat HEAD",
    "s -File CTempgit_push.ps1",
    "t --format=value(core.project)",
    "describe b9771968-3d86-41e3-acc1-4a88e978c338 --project=main-presence-500410-f8 2&1",
    "ervices describe enterprise-ai-frontend-staging --region us-central1 --format=value(spec.template.spec.containers[0].env)",
    "tatus --porcelain",
    "h origin develop",
    "jq parse error Invalid numeric literal at line 1, column 5",
    "ult = subprocess.run(['git', 'commit', '-m', 'fix simplify Dockerfile and remove error handling'],",
    "ult.stderr}),",
    " {result.stderr})",
]

print("=" * 70)
print("REMOVING CORRUPTED FILES")
print("=" * 70)

for f in corrupted:
    p = repo_dir / f
    if p.exists():
        try:
            p.unlink()
            print(f"✓ Removed: {f}")
        except Exception as e:
            print(f"✗ Error removing {f}: {e}")

print("\n" + "=" * 70)
print("RUNNING: git add .")
print("=" * 70 + "\n")

# Set environment to disable paging
env = os.environ.copy()
env['GIT_PAGER'] = 'cat'
env['PAGER'] = 'cat'

# Run git add without terminal
result = subprocess.run(
    ['git', 'add', '.'],
    cwd=repo_dir,
    env=env,
    capture_output=True,
    text=True,
    timeout=30
)

if result.stdout:
    print("STDOUT:")
    print(result.stdout)

if result.stderr:
    print("STDERR:")
    print(result.stderr)

print(f"\n{'=' * 70}")
if result.returncode == 0:
    print("✓ SUCCESS! git add completed successfully")
    print(f"{'=' * 70}\n")
    print("Next steps:")
    print("  1. git commit -m 'Add deployment documentation and cleanup'")
    print("  2. git push origin develop")
    print("  3. Cloud Build will automatically trigger")
else:
    print(f"✗ FAILED! Git add returned error code {result.returncode}")
    print(f"{'=' * 70}\n")
    if result.stderr:
        print("Error details:")
        print(result.stderr)

sys.exit(result.returncode)
