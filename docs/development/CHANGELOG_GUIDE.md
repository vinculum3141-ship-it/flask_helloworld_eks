# Changelog Management Guide

This project uses a unified changelog that includes both manual and automated changelog generation.

## Files

- **`CHANGELOG.md`** - Unified changelog containing both production releases and development logs
- **`scripts/generate_changelog.sh`** - Auto-generate changelog from git commits
- **`.github/workflows/changelog.yml`** - GitHub Actions workflow for automatic changelog updates

## Production Releases (Manual)

The top of `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) format with categories:

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security updates

## Development Log (Manual & Auto-generated)

The Development Log section in `CHANGELOG.md` tracks development changes, refactorings, and improvements not captured in production releases. This section supports both manual entries and auto-generated entries from git commits.

### Updating CHANGELOG.md Manually

1. Open `CHANGELOG.md`
2. Add your changes under `## [Unreleased]` section
3. When releasing, move changes to a new version section:

```markdown
## [1.0.0] - 2025-11-14

### Added
- Ingress support for Minikube
- Automated ingress setup script

### Changed
- Service type from NodePort to ClusterIP
```

## Auto-Generated Changelog

Use the script to quickly generate a changelog from git commit messages.

### Basic Usage

```bash
# Generate changelog from all commits (with colors for terminal)
bash scripts/generate_changelog.sh

# Generate changelog in clean markdown (no colors, for files)
bash scripts/generate_changelog.sh --markdown-only

# Generate changelog from a specific tag to HEAD
bash scripts/generate_changelog.sh v1.0.0

# Generate changelog between two tags
bash scripts/generate_changelog.sh v1.0.0 v2.0.0

# Save to file (use --markdown-only for clean output)
bash scripts/generate_changelog.sh --markdown-only > CHANGELOG_AUTO.md
```

### Commit Message Conventions

The script categorizes commits based on prefixes:

| Prefix | Category | Example |
|--------|----------|---------|
| `feat:`, `feature:`, `add:` | Added | `feat: add ingress support` |
| `fix:`, `bugfix:` | Fixed | `fix: resolve 404 error` |
| `change:`, `update:` | Changed | `update: service to ClusterIP` |
| `remove:`, `delete:` | Removed | `remove: deprecated script` |
| `deprecate:` | Deprecated | `deprecate: old API endpoint` |
| `security:`, `sec:` | Security | `security: update dependencies` |
| `doc:`, `docs:` | Documentation | `docs: update README` |
| `test:` | Tests | `test: add ingress tests` |
| `refactor:` | Refactored | `refactor: simplify logic` |

**Examples:**
```bash
# Good commit messages for auto-changelog
git commit -m "feat: add Ingress support for Minikube"
git commit -m "fix: resolve 404 error when using Minikube IP"
git commit -m "docs: update README with Ingress instructions"
git commit -m "test: add test_ingress.py for validation"

# Without prefix (categorized as "Other")
git commit -m "minor changes"
```

### Output Format

**Terminal Output (with colors):**
```bash
bash scripts/generate_changelog.sh
```

```
==========================================
Git Changelog Generator
==========================================

Range: All commits

## Changelog

Generated on: 2025-11-14 10:30:45

### Added

- add Ingress support for Minikube (`a1b2c3d`) - John Doe, 2025-11-14
...
```

**Clean Markdown Output:**
```bash
bash scripts/generate_changelog.sh --markdown-only
```

```markdown
## Changelog

Generated on: 2025-11-14 10:30:45

### Added

- add Ingress support for Minikube (`a1b2c3d`) - John Doe, 2025-11-14
- add ingress setup script (`b2c3d4e`) - Jane Smith, 2025-11-14

### Fixed

- resolve 404 error when using Minikube IP (`c3d4e5f`) - John Doe, 2025-11-14

### Documentation

- update README with Ingress instructions (`d4e5f6g`) - Jane Smith, 2025-11-14

---

Statistics:
  Total commits: 45
  Files changed: 23
  Contributors: 2
```

## GitHub Actions Automation

The workflow `.github/workflows/changelog.yml` automatically generates changelogs.

### Automatic Triggers

1. **On Release Creation**
   - Automatically generates changelog between previous and current tag
   - Creates a Pull Request with the updated CHANGELOG.md

2. **Manual Trigger**
   - Go to Actions → "Generate Changelog" → "Run workflow"
   - Optionally specify from/to tags

### Manual Trigger in GitHub UI

1. Navigate to **Actions** tab
2. Select **"Generate Changelog"** workflow
3. Click **"Run workflow"**
4. (Optional) Enter tag range:
   - **From tag**: `v1.0.0` (leave empty for all commits)
   - **To tag**: `v2.0.0` or `HEAD`
5. Click **"Run workflow"**

### View Generated Changelog

After the workflow completes:

1. Go to the workflow run
2. Download the **"changelog"** artifact
3. Extract and view `CHANGELOG_AUTO.md`

## Best Practices

### For Contributors

1. **Use conventional commit messages** for better auto-changelog:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug"
   git commit -m "docs: update documentation"
   ```

2. **Update CHANGELOG.md manually** for significant releases:
   - Add context that git commits don't capture
   - Group related changes
   - Add migration guides if needed

### For Maintainers

1. **Before each release:**
   ```bash
   # Generate auto-changelog to see what changed
   bash scripts/generate_changelog.sh v1.0.0 > /tmp/auto.md
   
   # Review and manually update CHANGELOG.md
   # Add context, group changes, add breaking changes section
   ```

2. **Version the changelog:**
   ```markdown
   ## [2.0.0] - 2025-11-14
   
   ### Breaking Changes
   - Changed service from NodePort to ClusterIP (requires Ingress setup)
   
   ### Added
   - Ingress support for Minikube
   ```

3. **Create git tag:**
   ```bash
   git tag -a v2.0.0 -m "Release version 2.0.0"
   git push origin v2.0.0
   ```

## Workflow Comparison

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Manual** | Releases, major changes | Full control, add context | Takes time |
| **Auto-generated script** | Quick overview, between tags | Fast, comprehensive | Less context |
| **GitHub Actions** | CI/CD, automatic updates | Automated, consistent | Requires good commit messages |

## Recommended Workflow

1. **During development**: Use conventional commit messages
2. **Before release**: Run auto-changelog script to see what changed
3. **Manual curation**: Update CHANGELOG.md with context and grouping
4. **Create release**: GitHub Actions can auto-update if configured
5. **Review**: Ensure changelog accurately reflects changes

## Example: Complete Release Process

```bash
# 1. Generate auto-changelog to review changes
bash scripts/generate_changelog.sh v1.0.0 > /tmp/changes.md
cat /tmp/changes.md

# 2. Manually update CHANGELOG.md
vim CHANGELOG.md
# Move items from [Unreleased] to [2.0.0]
# Add breaking changes, migration guides, etc.

# 3. Commit changelog
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v2.0.0"

# 4. Create and push tag
git tag -a v2.0.0 -m "Release version 2.0.0 - Ingress support"
git push origin main
git push origin v2.0.0

# 5. Create GitHub release
# Go to GitHub → Releases → Create release
# Use CHANGELOG.md content for release notes
```

## Tips

1. **Reference commits in changelog:**
   ```markdown
   - Fixed 404 error with Ingress ([#123](link), `abc1234`)
   ```

2. **Link to issues:**
   ```markdown
   - Resolved ingress routing issue ([#45](link))
   ```

3. **Add migration guides:**
   ```markdown
   ### Migration Guide
   
   If upgrading from v1.x:
   1. Run `bash scripts/setup_ingress.sh`
   2. Update service type to ClusterIP
   ```

4. **Use semantic versioning:**
   - **Major** (2.0.0): Breaking changes
   - **Minor** (1.1.0): New features, backward compatible
   - **Patch** (1.0.1): Bug fixes

## Resources

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
