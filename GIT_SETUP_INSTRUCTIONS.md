# Git Setup Instructions for AVA OLO Project

## 🎯 Active Repositories (2)

### 1. Monitoring Dashboards (THIS REPO)
- **Repository Name**: ava-olo-monitoring-dashboards
- **Owner**: Poljopodrska
- **URL**: https://github.com/Poljopodrska/ava-olo-monitoring-dashboards.git
- **Purpose**: All dashboards and database interfaces

### 2. Agricultural Core
- **Repository Name**: ava-olo-agricultural-core
- **Owner**: Poljopodrska  
- **URL**: https://github.com/Poljopodrska/ava-olo-agricultural-core.git
- **Purpose**: Core agricultural logic and WhatsApp integration

## 🚀 Quick Setup (One-Time)

### For Windows Users:
1. Create a file named `.git-token` in your project directory
2. Paste your GitHub Personal Access Token in the file
3. Save the file

### For Linux/WSL Users:
1. Run: `./setup_git.sh`
2. Enter your GitHub token when prompted

## 📤 How to Push Changes

### Windows (Easiest):
Double-click `git_push.bat` or run in CMD:
```cmd
git_push.bat "Your commit message"
```

### Linux/WSL:
```bash
./git_push.sh "Your commit message"
```

### Manual Method:
```bash
git add .
git commit -m "Your message"
git push
```

## 🔑 GitHub Token
Your token needs these permissions:
- repo (Full control of private repositories)
- workflow (Update GitHub Action workflows)

Create a token at: https://github.com/settings/tokens/new

## 🗑️ Cleanup Other Repositories
If you have other unused repositories, you can delete them from:
https://github.com/Poljopodrska?tab=repositories

## ⚡ Automatic Deployment
Every push automatically triggers AWS ECS deployment (takes ~3-5 minutes)

## 🆘 Troubleshooting
- **"Authentication failed"**: Check your token in `.git-token`
- **"No upstream branch"**: The scripts handle this automatically
- **"Permission denied"**: Make scripts executable: `chmod +x *.sh`