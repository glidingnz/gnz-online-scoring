---
name: version-release
description: Create a new version release following the release workflow
---

## What I do

When you ask me to create a new version release, I follow this workflow:

### Step 1: Check version state
- Run `git diff pyproject.toml` to check if version already changed
- If changed: Stop and ask what they're doing
- If not changed: Continue to Step 2

### Step 2: Commit code changes
- Run `git status` and `git diff` to see changes
- Ask user to confirm
- Propose commit message describing what was implemented (not version number)
- Run: `git commit -m "Description of what was implemented"`

### Step 3: Propose version
Analyze changes since last version:
- Bug fixes only: patch (0.2.0 → 0.2.1)
- New features: minor (0.2.0 → 0.3.0)
- Breaking changes: major (0.2.0 → 1.0.0)

Ask user: "Based on the changes since v0.2.0, I suggest [X.Y.Z]. Does that sound right?"

### Step 4: Update pyproject.toml
- Update version = "X.Y.Z"

### Step 5: Update docs
- CHANGELOG.md: Move [Unreleased] to [X.Y.Z] with date, add changes
- README.md: Update version in header
- STATUS.md: Update "Last updated" date

### Step 6: Build
- Run `python build.py`

### Step 7: Commit version bump
- `git add -A` and `git commit -m "Release vX.Y.Z"`

### Step 8: Tag (optional)
- `git tag vX.Y.Z`

## Source of truth
- pyproject.toml contains version = "X.Y.Z"
- build.py reads version from pyproject.toml
- CHANGELOG.md has [Unreleased] section to fill

## When to use me
Use this skill whenever you want to release a new version.