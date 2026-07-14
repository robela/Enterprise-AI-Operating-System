#!/usr/bin/env python3
"""Preview or remove corrupted command-fragment files from the repo root."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


EXACT_CANDIDATES = {
    "describe b9771968-3d86-41e3-acc1-4a88e978c338 --project=main-presence-500410-f8 2&1",
    "e",
    "ervices describe enterprise-ai-frontend-staging --region us-central1 --format=value(spec.template.spec.containers[0].env)",
    "e",
    "h",
    "h origin develop",
    "how --stat HEAD",
    "jq parse error Invalid numeric literal at line 1, column 5",
    "leep 10 && echo Waiting for new build to appear...",
    "leep 15",
    "nuke_corrupted.py",
    "pan initialization step  ",
    "s -File CTempgit_push.ps1",
    "sage' in build",
    "t",
    "t --format=value(core.project)",
    "tatus",
    "tatus --porcelain",
    "ubprocess",
    "ult = subprocess.run(['git', 'commit', '-m', 'fix simplify Dockerfile and remove error handling']",
    "ult.stderr}),",
    " {result.stderr})",
}

COMMAND_MARKERS = (
    "&&",
    "--format=",
    "2&1",
    "subprocess.run(",
    "gcloud",
    "git', 'commit'",
    "origin develop",
    "enterprise-ai-frontend-staging",
    "Waiting for new build",
)

PREFIX_MARKERS = (
    "describe ",
    "ervices describe ",
    "how --stat",
    "jq",
    "leep ",
    "pan initialization",
    "sage' in build",
    "s -File ",
    "t --format=",
    "tatus",
    "ult = subprocess.run(",
    "ult.stderr",
    "ubprocess",
    " {result.stderr}",
)

SAFE_ROOT_NAMES = {
    ".deployment-status.md",
    ".env",
    ".env.example",
    ".git",
    ".gitignore",
    ".pytest_cache",
    ".venv",
    ".venv-wsl",
    "ARCHITECTURE.md",
    "backend",
    "cleanup.bat",
    "cleanup.ps1",
    "cleanup.py",
    "cleanup.sh",
    "cleanup_and_add.bat",
    "CLEANUP_GUIDE.md",
    "cloudbuild.yaml",
    "commit_and_push.py",
    "DEPLOYMENT_HISTORY_GUIDE.md",
    "DEPLOYMENT_READY.md",
    "DEPLOYMENT_SUMMARY.md",
    "dev.db",
    "direct_git_add.py",
    "docker-compose.yml",
    "frontend",
    "GIT_ISSUES.md",
    "IMMEDIATE_ACTION_REQUIRED.md",
    "MANUAL_DEPLOYMENT_STEPS.md",
    "pyproject.toml",
    "README.md",
    "test_backend.py",
}


def resolve_repo_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=script_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return script_dir
    return Path(result.stdout.strip())


def looks_corrupted(name: str) -> bool:
    if name in EXACT_CANDIDATES:
        return True
    if name in SAFE_ROOT_NAMES:
        return False
    if name.strip() != name:
        return True
    if name in {"e", "h", "t"}:
        return True
    if any(name.startswith(prefix) for prefix in PREFIX_MARKERS):
        return True
    if any(marker in name for marker in COMMAND_MARKERS):
        return True
    if any(char in name for char in ("", "", "")):
        return True
    return False


def collect_candidates(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for entry in sorted(repo_root.iterdir(), key=lambda path: path.name.lower()):
        if looks_corrupted(entry.name):
            candidates.append(entry)
    return candidates


def remove_candidate(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or remove corrupted command-fragment files from the repo root."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete the detected corrupted files. Default is preview only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root()
    candidates = collect_candidates(repo_root)

    print("=" * 70)
    print("Repository Cleanup Tool")
    print("=" * 70)
    print(f"Repository root: {repo_root}")
    print(f"Mode: {'APPLY' if args.apply else 'PREVIEW'}")
    print()

    if not candidates:
        print("No corrupted root-level files detected.")
        return 0

    print("Detected corrupted files:")
    for candidate in candidates:
        kind = "DIR " if candidate.is_dir() else "FILE"
        print(f"  [{kind}] {candidate.name}")

    if not args.apply:
        print()
        print("Preview only. Re-run with --apply to delete these files.")
        return 0

    print()
    removed = 0
    failed = 0
    for candidate in candidates:
        try:
            remove_candidate(candidate)
            print(f"Removed: {candidate.name}")
            removed += 1
        except OSError as exc:
            print(f"Failed : {candidate.name} -> {exc}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Summary: {removed} removed, {failed} failed")
    print("=" * 70)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
