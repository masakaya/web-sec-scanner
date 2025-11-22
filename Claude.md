# Project Rules for Claude Code

## Branch Protection Policy

**IMPORTANT: Direct push to the following branches is PROHIBITED:**

- `main` - Main branch (stable code)
- `staging` - Staging environment branch
- `production` - Production environment branch

### Branch Naming Convention

Branch names should follow Conventional Commits types:

- `feat/` - New features (e.g., `feat/add-user-auth`)
- `fix/` - Bug fixes (e.g., `fix/login-error`)
- `chore/` - Maintenance tasks (e.g., `chore/update-deps`)
- `docs/` - Documentation (e.g., `docs/update-readme`)
- `refactor/` - Refactoring (e.g., `refactor/simplify-api`)
- `test/` - Tests (e.g., `test/add-unit-tests`)
- `ci/` - CI/CD changes (e.g., `ci/add-workflow`)

### Workflow

1. Create a branch from `main` following the naming convention above
2. Make changes and commit
3. Create a Pull Request to `main`
4. After review and merge to `main`, auto-promotion PRs will be created:
   - `main` → `staging` (automatic PR)
   - `staging` → `production` (automatic PR after staging merge)
5. Production merge triggers automatic release creation (version tag + CHANGELOG)

**Always work through Pull Requests. Never push directly to protected branches.**

### ⚠️ Important: GitHub Actions Auto-Commits

**GitHub Actions may create commits automatically (e.g., Ruff auto-formatting).**

This can cause conflicts if you continue working locally while the action is running.

#### To avoid conflicts:

```bash
# Before continuing work, rebase with the latest remote branch
git fetch origin
git rebase origin/<your-branch-name>

# If conflicts occur during rebase, resolve them and continue
git rebase --continue
```

#### Example workflow:

```bash
# 1. Push your changes
git push origin feature/my-feature

# 2. GitHub Actions runs and may add auto-format commits

# 3. Before making more changes, rebase first
git fetch origin
git rebase origin/feature/my-feature

# 4. Now safe to continue working
git add .
git commit -m "feat: continue work"
git push origin feature/my-feature
```

**Always rebase before continuing work on a branch with an open PR.**

## Pull Request Guidelines

When creating a Pull Request, follow the PR template format:

```markdown
## 概要
<!-- 変更内容を簡潔に -->

## テスト
- [ ] ローカルで動作確認済み
```

**Always fill in the template sections when creating PRs.**

## Code Quality Standards

This project adheres to strict code quality standards:

### Ruff (Linting & Formatting)

- **All code must pass Ruff checks** before merging
- Ruff automatically formats code on PR creation
- Configuration: `ruff.toml`
- Run locally: `poe lint` or `poe format`

### mypy (Type Checking)

- **All code must pass mypy type checks** before merging
- Type annotations are required for all functions
- Configuration: `pyproject.toml` (`[tool.mypy]` section)
- Run locally: `poe typecheck`

### Enforcement

- GitHub Actions automatically runs Ruff and mypy on all PRs
- reviewdog posts inline comments for any violations
- PRs cannot be merged until all checks pass

**When writing code, ensure it complies with both Ruff and mypy standards.**

## Commit Message Convention

**IMPORTANT: This project uses Conventional Commits for automatic versioning and CHANGELOG generation.**

All commit messages MUST follow the Conventional Commits format:

```
<type>: <description>

[optional body]

[optional footer]
```

### Required Types

- **feat**: A new feature (triggers MINOR version bump: 0.1.0 → 0.2.0)
- **fix**: A bug fix (triggers PATCH version bump: 0.1.0 → 0.1.1)
- **chore**: Maintenance tasks (no version bump)
- **docs**: Documentation changes (no version bump)
- **refactor**: Code refactoring (no version bump)
- **test**: Adding or updating tests (no version bump)
- **ci**: CI/CD changes (no version bump)

### Breaking Changes

For breaking changes (triggers MAJOR version bump: 0.1.0 → 1.0.0):

```
feat!: remove deprecated API

BREAKING CHANGE: The old API has been removed
```

### Examples

```bash
# Feature (0.1.0 → 0.2.0)
feat: add user authentication

# Bug fix (0.1.0 → 0.1.1)
fix: resolve memory leak in parser

# Breaking change (0.1.0 → 1.0.0)
feat!: redesign configuration API

BREAKING CHANGE: Configuration format has changed
```

### Why This Matters

- **Automatic versioning**: release-please analyzes commits to determine version
- **CHANGELOG generation**: Commits are automatically organized into CHANGELOG
- **Production releases**: Only properly formatted commits trigger correct versioning

**Always use Conventional Commits format. Incorrect format will result in improper versioning.**

### Enforcement with Git Hooks

This project uses **gitlint** with **pre-commit** to enforce Conventional Commits format.

#### Setup (First Time Only)

```bash
# Install git hooks
poe setup-hooks

# Or manually
uv run pre-commit install --hook-type commit-msg
```

#### How It Works

When you commit, gitlint automatically validates your commit message:

```bash
# ✅ Valid commit - will succeed
git commit -m "feat: add user authentication"

# ❌ Invalid commit - will be rejected
git commit -m "Added new feature"
# Error: Commit message does not follow Conventional Commits format
```

#### Validation Commands

```bash
# Validate last commit message
poe validate-commit

# Uninstall hooks (if needed)
poe uninstall-hooks
```

#### Configuration

- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `.gitlint` - Gitlint rules and format enforcement

## Package Management

This project uses **uv** for package management. **DO NOT use pip**.

### Installing Dependencies

- Use `uv sync` to install all dependencies from pyproject.toml
- Use `uv add <package>` to add a new runtime dependency
- Use `uv add --dev <package>` to add a new development dependency
- Use `uv remove <package>` to remove a dependency

### Running Python

- Use `uv run python <script>` to run Python scripts
- Use `uv run <command>` to run commands in the virtual environment

### Why uv?

uv is a fast Python package installer and resolver written in Rust. It provides:
- Faster dependency resolution and installation
- Better reproducibility
- Built-in virtual environment management
- Compatibility with pip and pyproject.toml standards
