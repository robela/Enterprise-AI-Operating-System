#!/usr/bin/env python3
"""Commit and push changes using subprocess to bypass terminal issues."""
import subprocess
import sys
import os

os.chdir(r"C:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System")

# Step 1: Check git status
print("=" * 80)
print("Step 1: Checking git status...")
print("=" * 80)
result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}\n")

# Step 2: Add changes
print("=" * 80)
print("Step 2: Adding changes...")
print("=" * 80)
result = subprocess.run(["git", "add", "backend/app/main.py", "cloudbuild.yaml"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}\n")

# Step 3: Check status again
print("=" * 80)
print("Step 3: Checking git status after add...")
print("=" * 80)
result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}\n")

# Step 4: Commit
print("=" * 80)
print("Step 4: Committing changes...")
print("=" * 80)
result = subprocess.run(
    ["git", "commit", "-m", "fix: enhance startup diagnostics and add /status endpoint"],
    capture_output=True,
    text=True
)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}\n")

# Step 5: Push
print("=" * 80)
print("Step 5: Pushing to develop branch...")
print("=" * 80)
result = subprocess.run(["git", "push", "origin", "develop"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}\n")

# Step 6: Show current HEAD
print("=" * 80)
print("Step 6: Showing current HEAD...")
print("=" * 80)
result = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}\n")

print("=" * 80)
print("DONE!")
print("=" * 80)
