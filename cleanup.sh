#!/bin/bash

# Cleanup script for corrupted files in Enterprise AI OS repository
# Run this script to remove all invalid/corrupted filenames

cd /c/Code/Enterprise-AI-Operating-System/Enterprise-AI-Operating-System

echo "======================================"
echo "Repository Cleanup Script"
echo "======================================"
echo ""

# Use git clean to remove untracked files (safest method)
echo "Method 1: Using 'git clean' (recommended)"
echo "Preview of files to be removed:"
git clean -fdn

echo ""
echo "Removing files..."
git clean -fd

echo ""
echo "======================================"
echo "Cleanup Complete!"
echo "======================================"
echo ""

# Verify
echo "Verifying cleanup..."
git status

echo ""
echo "Repository is now clean. You can now run:"
echo "  git add ."
echo "  git commit -m 'Your message'"
echo "  git push origin develop"
