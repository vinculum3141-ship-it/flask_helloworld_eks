# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## Development Log

> **Purpose**: Track development changes, refactorings, and improvements not captured in production releases.  
> **Audience**: Developers working on this project.  
> **Format**: Manual entries for significant work; auto-generated entries archived below.

### Guidelines for Development Entries

**When to add manual entries**:
- Significant refactoring or architectural changes
- Breaking changes affecting developers
- New testing strategies or patterns
- Documentation consolidation efforts

**What to include**:
- Clear context and rationale
- Before/after comparisons
- Impact on workflows
- Related file changes

**Auto-generated entries**: Run `make changelog-dev` or `make changelog-dev-since TAG=v1.0.0` to append auto-generated changelog entries below.

---

---

## Templates

### Production Release Template

```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security updates
```

### Development Entry Template

```markdown
## [Dev] YYYY-MM-DD - Description

**Context**: Why this change was needed

**Changes**:
- List of specific changes
- Impact on workflows

**Related Files**:
- `path/to/file1.md`
- `path/to/file2.py`
```
