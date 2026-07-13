# Repository Cleanup Guide

## Problem
Your repository has corrupted/invalid filenames that are preventing git operations:

```
pan initialization step  
tatus
tatus --porcelain
t
t --format=value(core.project)
e
ervices describe enterprise-ai-frontend-staging --region us-central1 --format=value(spec.template.spec.containers[0].env)
h
h origin develop
how --stat HEAD
leep 10 && echo Waiting for new build to appear...
leep 15
s -File CTempgit_push.ps1
ubprocess
describe b9771968-3d86-41e3-acc1-4a88e978c338 --project=main-presence-500410-f8 2&1
jq parse error Invalid numeric literal at line 1, column 5
ult = subprocess.run(['git', 'commit', '-m', 'fix simplify Dockerfile and remove error handling'],
 {result.stderr}
sage' in build
```

These appear to be fragments of command-line operations that were accidentally created as files.

---

## Solution: Use git clean

The easiest way to remove these untracked files is:

### Option 1: Remove Only These Corrupted Files (Recommended)

```bash
cd /c/Code/Enterprise-AI-Operating-System/Enterprise-AI-Operating-System

# Remove all untracked files (these corrupted files are untracked)
git clean -fd
```

### Option 2: Remove Untracked Files and Directories

```bash
# More aggressive (removes untracked files AND directories)
git clean -fdx

# Note: Don't use -x if you have .env or other important untracked files
```

### Option 3: Preview What Will Be Removed

```bash
# See what git clean will remove without actually removing it
git clean -fdn
```

---

## After Cleanup

Once cleaned, you should be able to:

```bash
# Add changes
git add .

# Commit changes
git commit -m "Your commit message"

# Push to remote
git push origin develop
```

---

## Manual File Deletion (If Above Doesn't Work)

If `git clean` doesn't work, manually delete these files:

**In VS Code Explorer:**
1. Show hidden files (Ctrl+Shift+.)
2. Sort by name
3. Look for single-letter files and odd filenames
4. Delete them one by one

**In PowerShell:**
```powershell
cd 'c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System'

# Remove specific corrupted files
Remove-Item 'pan initialization step  ' -Force -ErrorAction SilentlyContinue
Remove-Item 'tatus' -Force -ErrorAction SilentlyContinue
Remove-Item 'tatus --porcelain' -Force -ErrorAction SilentlyContinue
Remove-Item 't' -Force -ErrorAction SilentlyContinue
Remove-Item 'e' -Force -ErrorAction SilentlyContinue
Remove-Item 'h' -Force -ErrorAction SilentlyContinue
# ... etc

# List remaining files to verify
Get-ChildItem | Sort-Object Name
```

**In Bash:**
```bash
cd /c/Code/Enterprise-AI-Operating-System/Enterprise-AI-Operating-System

# Remove corrupted files one at a time
rm -f "pan initialization step  "
rm -f "tatus"
rm -f "t"
rm -f "e"
rm -f "h"
rm -f "ubprocess"
# ... etc
```

---

## Verify Cleanup

```bash
# Check git status - should show only real files
git status

# List directory - should show only valid files
ls -la

# Try adding files again
git add .
```

---

## Preventing This in the Future

These files were likely created by:
- Accidentally running shell commands with output redirection to wrong location
- Pasting multi-line commands into the terminal incorrectly
- Issues with script execution

**Best practices:**
1. ✅ Use clear working directories before running commands
2. ✅ Test git commands with `git status` first
3. ✅ Review files before `git add .` (use `git add` selectively)
4. ✅ Use `.gitignore` for temporary files

---

## Next Steps

1. Run: `git clean -fdn` to preview what will be removed
2. Run: `git clean -fd` to actually remove the files
3. Verify: `git status` should be clean
4. Then: `git add .` and commit normally

