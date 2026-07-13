# Cleanup script for corrupted files in Enterprise AI OS repository
# Run this script in PowerShell to remove all invalid/corrupted filenames

cd 'c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System'

Write-Host "======================================"
Write-Host "Repository Cleanup Script (PowerShell)"
Write-Host "======================================"
Write-Host ""

# Corrupted files to remove
$corruptedFiles = @(
    "pan initialization step  ",
    "tatus",
    "tatus --porcelain",
    "t",
    "t --format=value(core.project)",
    "e",
    "ervices describe enterprise-ai-frontend-staging --region us-central1 --format=value(spec.template.spec.containers[0].env)",
    "h",
    "h origin develop",
    "how --stat HEAD",
    "leep 10 && echo Waiting for new build to appear...",
    "leep 15",
    "s -File CTempgit_push.ps1",
    "ubprocess",
    "describe b9771968-3d86-41e3-acc1-4a88e978c338 --project=main-presence-500410-f8 2&1",
    "jq parse error Invalid numeric literal at line 1, column 5",
    "ult = subprocess.run(['git', 'commit', '-m', 'fix simplify Dockerfile and remove error handling'],",
    " {result.stderr}",
    "sage' in build"
)

Write-Host "Removing corrupted files..."
$removed = 0
$notFound = 0

foreach ($file in $corruptedFiles) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force -ErrorAction Stop
            Write-Host "✓ Removed: $file" -ForegroundColor Green
            $removed++
        } catch {
            Write-Host "✗ Failed to remove: $file" -ForegroundColor Red
            Write-Host "  Error: $_"
        }
    } else {
        $notFound++
    }
}

Write-Host ""
Write-Host "======================================"
Write-Host "Cleanup Summary"
Write-Host "======================================"
Write-Host "Removed: $removed files"
Write-Host "Not found: $notFound files"
Write-Host ""

# Verify cleanup
Write-Host "Current directory contents:"
Write-Host ""
Get-ChildItem -Name | Sort-Object | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "======================================"
Write-Host "Cleanup Complete!"
Write-Host "======================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  git status          # Verify cleanup"
Write-Host "  git add .           # Stage changes"
Write-Host "  git commit -m '...' # Commit"
Write-Host "  git push            # Push to remote"
