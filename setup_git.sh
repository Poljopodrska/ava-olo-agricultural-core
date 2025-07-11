#!/bin/bash
# Git Setup and Configuration Script for AVA OLO Project

echo "🔧 Git Setup for AVA OLO Monitoring Dashboards"
echo "=============================================="

# Current repository information
echo -e "\n📦 Current Repository:"
echo "Repository: ava-olo-monitoring-dashboards"
echo "Owner: Poljopodrska"
echo "URL: https://github.com/Poljopodrska/ava-olo-monitoring-dashboards.git"

# Check if .env file exists for token storage
if [ ! -f .git-token ]; then
    echo -e "\n🔑 GitHub Token Setup:"
    echo "Please enter your GitHub Personal Access Token:"
    read -s GITHUB_TOKEN
    echo $GITHUB_TOKEN > .git-token
    chmod 600 .git-token
    echo "✅ Token saved to .git-token (this file is gitignored)"
else
    GITHUB_TOKEN=$(cat .git-token)
    echo -e "\n✅ GitHub token found in .git-token"
fi

# Configure Git with token
echo -e "\n⚙️ Configuring Git..."

# Set remote URL with token embedded
git remote set-url origin https://${GITHUB_TOKEN}@github.com/Poljopodrska/ava-olo-monitoring-dashboards.git

# Configure credential helper to cache for 24 hours
git config credential.helper 'cache --timeout=86400'

# Verify user configuration
echo -e "\n👤 Git User Configuration:"
git config user.name "Poljopodrska"
git config user.email "noreply@avaolo.com"
echo "Name: $(git config user.name)"
echo "Email: $(git config user.email)"

# Set default branch
git config init.defaultBranch main

# Enable automatic upstream setup
git config push.autoSetupRemote true

echo -e "\n✅ Git configuration complete!"
echo -e "\n📝 Quick Reference Commands:"
echo "- Regular push: ./git_push.sh"
echo "- Push with message: ./git_push.sh \"Your commit message\""
echo "- Manual push: git push"
echo "- Check status: git status"

# Create .gitignore entry for token file
if ! grep -q ".git-token" .gitignore 2>/dev/null; then
    echo -e "\n# Git token file\n.git-token" >> .gitignore
    echo "✅ Added .git-token to .gitignore"
fi