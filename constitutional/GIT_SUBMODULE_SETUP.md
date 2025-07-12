# 🔗 GIT SUBMODULE SETUP FOR CONSTITUTIONAL FRAMEWORK

## 📋 Prerequisites

1. Create `ava-olo-shared-constitutional` repository on GitHub
2. Move all constitutional documents to that repository
3. Ensure all documents are AWS-compliant

## 🚀 Setting Up Submodules

### For New Repositories

```bash
# Clone your service repository
git clone https://github.com/Poljopodrska/ava-olo-[service-name].git
cd ava-olo-[service-name]

# Add constitutional submodule
git submodule add https://github.com/Poljopodrska/ava-olo-shared-constitutional.git constitutional

# Commit the submodule addition
git add .gitmodules constitutional
git commit -m "CONSTITUTIONAL: Add shared constitutional framework as submodule"
git push origin main
```

### For Existing Repositories (like monitoring-dashboards)

```bash
cd ava-olo-monitoring-dashboards

# Backup current constitutional folder
mv constitutional constitutional_backup

# Add as submodule
git submodule add https://github.com/Poljopodrska/ava-olo-shared-constitutional.git constitutional

# Remove backup after verifying
rm -rf constitutional_backup

# Commit changes
git add .gitmodules constitutional
git commit -m "CONSTITUTIONAL: Migrate to shared constitutional submodule"
git push origin main
```

## 📖 Working with Submodules

### Cloning a Repository with Submodules

```bash
# Clone with submodules initialized
git clone --recursive https://github.com/Poljopodrska/ava-olo-monitoring-dashboards.git

# Or if already cloned
git submodule init
git submodule update
```

### Updating Constitutional Documents

```bash
# Navigate to shared constitutional repo
cd ava-olo-shared-constitutional

# Make your changes
vim AVA_OLO_CONSTITUTION.md

# Commit and push
git add .
git commit -m "CONSTITUTIONAL: Update principle X for clarity"
git push origin main

# Now update each service repository
cd ../ava-olo-monitoring-dashboards/constitutional
git pull origin main
cd ..
git add constitutional
git commit -m "CONSTITUTIONAL: Update to latest shared constitution"
git push origin main
```

### Checking Submodule Status

```bash
# See current submodule commit
git submodule status

# Update all submodules to latest
git submodule update --remote --merge
```

## 🎯 Benefits of This Approach

1. **Version Control**: Track exactly which constitutional version each service uses
2. **Independence**: Services can update at their own pace
3. **Consistency**: Guarantees all services reference same source
4. **History**: Full git history of constitutional changes
5. **Rollback**: Easy to revert to previous constitutional versions

## ⚠️ Important Notes

1. **Always commit submodule updates** - When constitutional repo updates, each service must explicitly update
2. **Use --recursive** - When cloning repositories with submodules
3. **Check .gitmodules** - Ensures correct submodule URLs
4. **Test before pushing** - Verify submodule links work correctly

## 📋 Migration Checklist for Each Repository

- [ ] Backup existing constitutional folder (if any)
- [ ] Add shared constitutional as submodule
- [ ] Update any hardcoded paths to constitutional docs
- [ ] Test that constitutional documents are accessible
- [ ] Commit with "CONSTITUTIONAL:" prefix
- [ ] Update CI/CD to handle submodules
- [ ] Document in repository README

## 🔄 Automated Updates (Optional)

Create a GitHub Action to check for constitutional updates:

```yaml
name: Check Constitutional Updates
on:
  schedule:
    - cron: '0 0 * * 1' # Weekly on Monday
  workflow_dispatch:

jobs:
  update-constitutional:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true
      
      - name: Update constitutional submodule
        run: |
          git submodule update --remote --merge
          
      - name: Check for changes
        id: check
        run: |
          if [[ -n $(git status --porcelain) ]]; then
            echo "changes=true" >> $GITHUB_OUTPUT
          fi
          
      - name: Create Pull Request
        if: steps.check.outputs.changes == 'true'
        uses: peter-evans/create-pull-request@v5
        with:
          title: "CONSTITUTIONAL: Update to latest shared constitution"
          body: "This PR updates the constitutional submodule to the latest version."
          branch: constitutional-update
```

This architectural change will ensure constitutional governance across the entire AVA OLO ecosystem! 🏗️