#!/bin/sh
# Backup Ombre Brain memories to a git repo
# Usage: BACKUP_REPO=https://github.com/Yvine34/ombre-backup.git ./scripts/backup_to_git.sh
#
# Environment variables:
#   BACKUP_REPO     - git remote URL (required)
#   OMBRE_BUCKETS_DIR - buckets directory (default: /data or ./buckets)
#   BACKUP_BRANCH   - branch name (default: main)

BUCKETS_DIR="${OMBRE_BUCKETS_DIR:-./buckets}"
BRANCH="${BACKUP_BRANCH:-main}"
BACKUP_DIR="/tmp/ombre-backup-$$"

if [ -z "$BACKUP_REPO" ]; then
    echo "Error: BACKUP_REPO not set"
    exit 1
fi

if [ ! -d "$BUCKETS_DIR" ]; then
    echo "Error: buckets dir not found: $BUCKETS_DIR"
    exit 1
fi

echo "Backing up $BUCKETS_DIR to $BACKUP_REPO ..."

git clone --depth 1 -b "$BRANCH" "$BACKUP_REPO" "$BACKUP_DIR" 2>/dev/null || {
    mkdir -p "$BACKUP_DIR"
    cd "$BACKUP_DIR"
    git init
    git checkout -b "$BRANCH"
}

# Sync bucket markdown files
cp -r "$BUCKETS_DIR"/* "$BACKUP_DIR"/ 2>/dev/null

cd "$BACKUP_DIR"
git add -A
if git diff --cached --quiet; then
    echo "No changes to backup."
else
    git commit -m "backup: $(date '+%Y-%m-%d %H:%M')"
    git push origin "$BRANCH" 2>/dev/null || git push --set-upstream origin "$BRANCH"
    echo "Backup complete."
fi

rm -rf "$BACKUP_DIR"
