# Version Release Workflow

## Step 1: Check version state

```bash
git diff pyproject.toml  # Check if version changed
```

- **If version changed**: Ask user - is this a continued release or should we reset?
  - If continuing: use the changed version as-is
  - If reset: revert pyproject.toml and start fresh
- **If not changed**: Continue to Step 2

## Step 2: Commit code changes

```bash
git status
git diff
```

- Ask user to confirm
- Propose commit message describing what was implemented (not version number)
- Run: `git commit -m "Description of what was implemented"`

## Step 3: Propose version

Analyze changes since last version:
- Bug fixes only → patch (0.2.0 → 0.2.1)
- New features → minor (0.2.0 → 0.3.0)
- Breaking changes → major (0.2.0 → 1.0.0)

Propose to user: "Based on the changes since v0.2.0, I suggest [X.Y.Z]. Does that sound right?"

## Step 4: Update version in pyproject.toml

```bash
# Update version = "X.Y.Z"
```

## Step 5: Update docs

```bash
# CHANGELOG.md - Move [Unreleased] to [X.Y.Z] with date, add your changes UNDER the version heading
# README.md - Update version in header
# STATUS.md - Update "Last updated" date
```

### CHANGELOG.md Format Rules:
- Entries are ordered newest to oldest (0.4.0 → 0.3.0 → ... → 0.1.0)
- **Never delete old version sections** - they stay there for historical record
- Under each version heading, use three subsections:
  - `### Added` - for new features
  - `### Changed` - for modifications to existing functionality
  - `### Fixed` - for bug fixes
- If a version has no entries in a category, omit that category
- Write entries as: `- concise description of change`

## Step 6: Build

```bash
python build.py
```

## Step 7: Commit version bump

```bash
git add -A
git commit -m "Release vX.Y.Z"
```

## Step 8: Tag (optional)

```bash
git tag vX.Y.Z
```