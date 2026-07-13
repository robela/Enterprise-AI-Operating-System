# Manual Git Cleanup & Deployment Guide

**Your Current Status**: Git is working but has untracked corrupted files preventing `git add .`

---

## Step-by-Step Instructions

### Step 1: Clean Corrupted Files

Open Terminal and run:
```bash
cd /c/Code/Enterprise-AI-Operating-System/Enterprise-AI-Operating-System
git clean -fd
```

**What this does**: Removes all untracked files (the corrupted files)

**Expected output**: Messages showing files being removed

---

### Step 2: Verify Cleanup

```bash
git status
```

**Expected output**: 
```
On branch develop
Your branch is up to date with 'origin/develop'.

nothing to commit, working tree clean
```

OR (if you have new files to commit):
```
On branch develop
Your branch is up to date with 'origin/develop'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   DEPLOYMENT_SUMMARY.md
        modified:   DEPLOYMENT_HISTORY_GUIDE.md
        ...

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        CLEANUP_GUIDE.md
        GIT_ISSUES.md
        ...
```

---

### Step 3: Stage All Changes

```bash
git add .
```

**Expected output**: No error message (success is silence)

**What this does**: Adds all modified and new files to git staging area

---

### Step 4: Commit Changes

```bash
git commit -m "Add deployment documentation and guides"
```

**Expected output**:
```
[develop a1b2c3d] Add deployment documentation and guides
 8 files changed, 500 insertions(+), 20 deletions(-)
 create mode 100644 CLEANUP_GUIDE.md
 create mode 100644 GIT_ISSUES.md
 ...
```

---

### Step 5: Push to Remote

```bash
git push origin develop
```

**Expected output**:
```
Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (8/8), 2.34 KiB | 2.34 MiB/s, done.
Total 8 (delta 4), reused 0 (delta 0), recycle bin entries
remote: Waiting for private key checker
remote: Waiting for new build to appear...
remote: Waiting for new build to appear...
To github.com:robela/Enterprise-AI-Operating-System.git
   a1b2c3d..xyz1234  develop -> develop
```

---

### Step 6: Monitor Cloud Build

**Cloud Build will automatically trigger!**

Option A: Watch in Web Console
```
https://console.cloud.google.com/cloud-build/builds?project=main-presence-500410-f8
```

Option B: Watch via CLI
```bash
gcloud builds list --project=main-presence-500410-f8 --limit=1

# When you see the build ID, get details:
gcloud builds log [BUILD_ID] --project=main-presence-500410-f8
```

---

## If You Get an Error

### Error: "unable to index file 'pan initialization step  '"
**Solution**: 
```bash
git clean -fd
# Try again
```

### Error: "Your branch and 'origin/develop' have diverged"
**Solution**:
```bash
git pull origin develop
git add .
git commit -m "Your message"
git push origin develop
```

### Error: "fatal: remote error: repository not found"
**Solution**: Check your GitHub authentication
```bash
# Try via HTTPS:
git remote set-url origin https://github.com/robela/Enterprise-AI-Operating-System.git
git push origin develop
```

---

## What Should Happen Next

1. ✅ `git clean -fd` removes corrupted files
2. ✅ `git add .` successfully stages all files
3. ✅ `git commit -m "..."` creates commit
4. ✅ `git push origin develop` pushes to GitHub
5. ✅ GitHub webhook triggers Cloud Build
6. ✅ Cloud Build starts new build (see "deploy-staging" trigger)
7. ✅ Build succeeds and deploys to staging
8. ✅ Backend service updates at: https://enterprise-ai-backend-staging-397980615504.us-central1.run.app/

---

## Success Checklist

After following all steps:

- [ ] `git clean -fd` completed without errors
- [ ] `git status` shows clean working directory
- [ ] `git add .` succeeded
- [ ] `git commit -m "..."` showed file changes
- [ ] `git push origin develop` succeeded  
- [ ] Cloud Build console shows new build (check in 30 seconds)
- [ ] New build completes successfully (green checkmark)
- [ ] Staging backend responds to: https://enterprise-ai-backend-staging-397980615504.us-central1.run.app/health

---

## Terminal Troubleshooting

If terminal shows alternate buffer/paging issues, try:

```bash
# Disable git paging
export GIT_PAGER=cat

# Then run git commands
git status
git add .
git commit -m "message"
git push origin develop
```

Or use PowerShell:
```powershell
cd 'c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System'
git status
git add .
git commit -m "message"
git push origin develop
```

---

## Files You've Created

All these files are ready to be committed:
- ✅ IMMEDIATE_ACTION_REQUIRED.md
- ✅ GIT_ISSUES.md
- ✅ CLEANUP_GUIDE.md
- ✅ cleanup.py
- ✅ cleanup.sh
- ✅ cleanup.ps1
- ✅ cleanup.bat
- ✅ DEPLOYMENT_SUMMARY.md
- ✅ DEPLOYMENT_HISTORY_GUIDE.md
- ✅ .deployment-status.md

---

## Quick Reference Commands

```bash
# Change to repo directory
cd /c/Code/Enterprise-AI-Operating-System/Enterprise-AI-Operating-System

# Clean corrupted files
git clean -fd

# Check status
git status

# Add everything
git add .

# Commit
git commit -m "Your message here"

# Push to GitHub
git push origin develop

# Check builds
gcloud builds list --project=main-presence-500410-f8 --limit=5
```

---

**Once you complete these steps, your deployment will automatically trigger and your staging environment will be updated!**

