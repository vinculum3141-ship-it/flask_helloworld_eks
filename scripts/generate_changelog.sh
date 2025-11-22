#!/bin/bash
# Auto-generate changelog from git commits
# Usage: bash scripts/generate_changelog.sh [from_tag] [to_tag] [--markdown-only]
#
# Examples:
#   bash scripts/generate_changelog.sh                    # All commits (with colors)
#   bash scripts/generate_changelog.sh v1.0.0             # From v1.0.0 to HEAD
#   bash scripts/generate_changelog.sh v1.0.0 v2.0.0      # Between two tags
#   bash scripts/generate_changelog.sh --markdown-only    # Clean markdown (no colors)

set -euo pipefail

# Note: This script defines its own colors for --markdown-only mode compatibility
# It does not source common.sh to keep it standalone and flexible

# Check for markdown-only mode
MARKDOWN_ONLY=false
if [[ "${1:-}" == "--markdown-only" ]] || [[ "${2:-}" == "--markdown-only" ]] || [[ "${3:-}" == "--markdown-only" ]]; then
    MARKDOWN_ONLY=true
fi

# Filter out --markdown-only from args
ARGS=()
for arg in "$@"; do
    if [[ "$arg" != "--markdown-only" ]]; then
        ARGS+=("$arg")
    fi
done

FROM_REF="${ARGS[0]:-}"
TO_REF="${ARGS[1]:-HEAD}"

# Color codes (only used when not in markdown-only mode)
if [ "$MARKDOWN_ONLY" = false ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Header (skip decorative elements in markdown-only mode)
if [ "$MARKDOWN_ONLY" = false ]; then
    echo "=========================================="
    echo "Git Changelog Generator"
    echo "=========================================="
    echo ""
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Determine the range
if [ -z "$FROM_REF" ]; then
    RANGE=""
    RANGE_TEXT="All commits"
else
    RANGE="$FROM_REF..$TO_REF"
    RANGE_TEXT="From $FROM_REF to $TO_REF"
fi

if [ "$MARKDOWN_ONLY" = false ]; then
    echo -e "${BLUE}Range:${NC} $RANGE_TEXT"
    echo ""
fi

# Function to categorize commit
categorize_commit() {
    local msg="$1"
    
    # Convert to lowercase for matching
    local msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if echo "$msg_lower" | grep -qE "^(feat|feature|add)"; then
        echo "Added"
    elif echo "$msg_lower" | grep -qE "^(fix|bugfix)"; then
        echo "Fixed"
    elif echo "$msg_lower" | grep -qE "^(change|update|modify)"; then
        echo "Changed"
    elif echo "$msg_lower" | grep -qE "^(remove|delete)"; then
        echo "Removed"
    elif echo "$msg_lower" | grep -qE "^(deprecate)"; then
        echo "Deprecated"
    elif echo "$msg_lower" | grep -qE "^(security|sec)"; then
        echo "Security"
    elif echo "$msg_lower" | grep -qE "^(doc|docs)"; then
        echo "Documentation"
    elif echo "$msg_lower" | grep -qE "^(test)"; then
        echo "Tests"
    elif echo "$msg_lower" | grep -qE "^(refactor)"; then
        echo "Refactored"
    else
        echo "Other"
    fi
}

# Generate changelog
echo "## Changelog"
echo ""
echo "Generated on: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Create temporary file for categorized commits
TEMP_FILE=$(mktemp)

# Get all commits and categorize them
if [ -z "$RANGE" ]; then
    git log --pretty=format:"%s|%h|%an|%ad" --date=short --no-merges
else
    git log "$RANGE" --pretty=format:"%s|%h|%an|%ad" --date=short --no-merges
fi | while IFS='|' read -r subject hash author date; do
    category=$(categorize_commit "$subject")
    echo "$category|$subject|$hash|$author|$date" >> "$TEMP_FILE"
done

# Print categorized commits
for category in "Added" "Changed" "Fixed" "Removed" "Deprecated" "Security" "Documentation" "Tests" "Refactored" "Other"; do
    # Check if category has commits
    if grep -q "^$category|" "$TEMP_FILE" 2>/dev/null; then
        echo "### $category"
        echo ""
        grep "^$category|" "$TEMP_FILE" | while IFS='|' read -r cat subject hash author date; do
            # Clean up conventional commit prefixes
            clean_subject=$(echo "$subject" | sed -E 's/^(feat|feature|add|fix|bugfix|change|update|modify|remove|delete|deprecate|security|sec|doc|docs|test|refactor):?\s*//i')
            echo "- $clean_subject (\`$hash\`) - $author, $date"
        done
        echo ""
    fi
done

# Cleanup
rm -f "$TEMP_FILE"

# Footer (skip in markdown-only mode)
if [ "$MARKDOWN_ONLY" = false ]; then
    echo "=========================================="
    echo ""
    echo -e "${GREEN}Tip:${NC} Save this output to CHANGELOG.md:"
    echo -e "  ${YELLOW}bash scripts/generate_changelog.sh > CHANGELOG_AUTO.md${NC}"
    echo ""
    echo -e "${GREEN}Tip:${NC} Generate changelog between tags:"
    echo -e "  ${YELLOW}bash scripts/generate_changelog.sh v1.0.0 v2.0.0${NC}"
    echo ""
fi

# Show statistics
if [ "$MARKDOWN_ONLY" = true ]; then
    echo "---"
    echo ""
fi

echo "Statistics:"
if [ -z "$RANGE" ]; then
    COMMIT_COUNT=$(git rev-list --count --no-merges HEAD)
else
    COMMIT_COUNT=$(git rev-list --count --no-merges "$RANGE")
fi

echo "  Total commits: $COMMIT_COUNT"

# Files changed
if [ -z "$RANGE" ]; then
    FILES_CHANGED=$(git diff --name-only $(git rev-list --max-parents=0 HEAD) HEAD | wc -l)
else
    FILES_CHANGED=$(git diff --name-only "$FROM_REF" "$TO_REF" | wc -l)
fi

echo "  Files changed: $FILES_CHANGED"

# Contributors
if [ -z "$RANGE" ]; then
    CONTRIBUTORS=$(git log --format='%an' --no-merges | sort -u | wc -l)
else
    CONTRIBUTORS=$(git log "$RANGE" --format='%an' --no-merges | sort -u | wc -l)
fi

echo "  Contributors: $CONTRIBUTORS"
echo ""
