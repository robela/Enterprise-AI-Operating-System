#!/usr/bin/env python3
"""Stage intended changes without traversing invalid root filenames."""
import subprocess
import os
import sys
from pathlib import Path

repo_dir = Path(r"c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System")
os.chdir(repo_dir)

files_to_stage = [
    "cleanup.py",
    "cleanup_and_add.bat",
    "test_backend.py",
]

print("=" * 70)
print("STAGING TRACKED CHANGES")
print("=" * 70)

# Set environment to disable paging
env = os.environ.copy()
env['GIT_PAGER'] = 'cat'
env['PAGER'] = 'cat'

result = subprocess.run(
    ['git', 'add', '-u'],
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

if result.returncode != 0:
    print(f"\n{'=' * 70}")
    print(f"✗ FAILED! git add -u returned error code {result.returncode}")
    print(f"{'=' * 70}\n")
    sys.exit(result.returncode)

print("\n" + "=" * 70)
print("STAGING EXPLICIT FILES")
print("=" * 70)

for file_name in files_to_stage:
    file_path = repo_dir / file_name
    if not file_path.exists():
        print(f"- Skipped missing file: {file_name}")
        continue

    add_result = subprocess.run(
        ['git', 'add', '--', file_name],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )

    if add_result.returncode != 0:
        print(f"✗ Failed to stage: {file_name}")
        if add_result.stderr:
            print(add_result.stderr)
        sys.exit(add_result.returncode)

    print(f"✓ Staged: {file_name}")

status_result = subprocess.run(
    ['git', 'status', '--short'],
    cwd=repo_dir,
    env=env,
    capture_output=True,
    text=True,
    timeout=30
)

print(f"\n{'=' * 70}")
if status_result.returncode == 0:
    print("✓ SUCCESS! targeted git add completed successfully")
    print(f"{'=' * 70}\n")
    if status_result.stdout:
        print(status_result.stdout)
else:
    print(f"✗ FAILED! git status returned error code {status_result.returncode}")
    print(f"{'=' * 70}\n")
    if status_result.stderr:
        print(status_result.stderr)
    sys.exit(status_result.returncode)
