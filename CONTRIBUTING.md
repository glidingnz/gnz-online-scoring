# Contributing to GNZ Online Scoring

## Quick Start

```bash
# Clone the repo
git clone https://github.com/brunoTAG/WeGlideClient.git
cd WeGlideClient

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run the app
python main.py
```

## Reporting Issues

- Search existing issues first
- Use issue templates if available
- Include:
  - Clear title
  - Steps to reproduce
  - Expected vs actual behavior
  - Python version, OS

## Feature Requests

- Explain the use case
- Describe alternative solutions
- Consider scope (MVP vs extended)

## Pull Requests

1. Branch from `master`
2. Follow conventional commits
3. Include tests for new features
4. Update docs if needed
5. PR description template:
   ```
   ## Summary
   
   ## Changes
   
   ## Testing
   ```

## Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/)
- **Linting**: Run `ruff check .`
- **Formatting**: Run `ruff format .`
- **Type hints**: Use where possible (Python 3.9+)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Building

```bash
python build.py
# Output: release/gnz-online-scoring-vX.Y.Z.exe
```

## Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| **feat** | New feature |
| **fix** | Bug fix |
| **docs** | Documentation only |
| **style** | Code style (formatting, no logic) |
| **refactor** | Code refactoring |
| **test** | Adding/updating tests |
| **chore** | Build, tooling, dependencies |

### Examples

```
fix(csv): handle pilots with fewer than 5 flights
feat(gui): add hide invalid flights checkbox
docs(readme): update CLI options table
refactor(api): extract flight parsing to separate function
```

### Rules

- Commit message describes what changed, not what was done
- Use imperative mood (add, not added / adding)
- All commits are required for release workflow
- Scope is optional but recommended when applicable

## Pull Requests

1. Create a feature branch from `master`
2. Make commits following conventional commits
3. Push and create PR
4. PR title should follow conventional commits format