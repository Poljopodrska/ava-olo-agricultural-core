#!/bin/bash
# Automated Git Push Script for AVA OLO Project

echo "🚀 AVA OLO Git Push Helper"
echo "=========================="

# Check if token file exists
if [ ! -f .git-token ]; then
    echo "❌ No GitHub token found. Please run ./setup_git.sh first"
    exit 1
fi

# Get current branch
BRANCH=$(git branch --show-current)
echo "📌 Current branch: $BRANCH"

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Show status
echo -e "\n📊 Git Status:"
git status --short

# Add all changes
echo -e "\n📦 Adding all changes..."
git add .

# Commit with message
if [ -z "$1" ]; then
    # Auto-generate commit message based on changed files
    CHANGED_FILES=$(git diff --cached --name-only | head -5 | xargs basename -a | tr '\n' ', ' | sed 's/,$//')
    COMMIT_MSG="Update $CHANGED_FILES

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
else
    # Use provided message
    COMMIT_MSG="$1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
fi

echo -e "\n💬 Committing with message:"
echo "$COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# Push to remote
echo -e "\n📤 Pushing to GitHub..."
git push

if [ $? -eq 0 ]; then
    echo -e "\n✅ Successfully pushed to GitHub!"
    echo "🔄 AWS App Runner will automatically deploy the changes"
else
    echo -e "\n❌ Push failed. Please check your connection and token"
fi