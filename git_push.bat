@echo off
REM Windows Batch Script for Git Push
REM This makes it easy to push from Windows

echo =====================================
echo   AVA OLO Git Push Helper (Windows)
echo =====================================

REM Check if .git-token exists
if not exist .git-token (
    echo ERROR: No GitHub token found!
    echo Please create a .git-token file with your GitHub Personal Access Token
    echo.
    echo Steps:
    echo 1. Create a file named .git-token in this directory
    echo 2. Paste your GitHub token in the file
    echo 3. Save and close the file
    echo 4. Run this script again
    pause
    exit /b 1
)

REM Read token
set /p GITHUB_TOKEN=<.git-token

REM Configure remote with token
git remote set-url origin https://%GITHUB_TOKEN%@github.com/Poljopodrska/ava-olo-monitoring-dashboards.git

REM Check for changes
git status --porcelain >nul
if %errorlevel% equ 0 (
    echo No changes to commit
    pause
    exit /b 0
)

echo.
echo Current Status:
git status --short

echo.
echo Adding all changes...
git add .

REM Commit
if "%~1"=="" (
    git commit -m "Update project files"
) else (
    git commit -m "%~1"
)

echo.
echo Pushing to GitHub...
git push

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! Pushed to GitHub
    echo AWS App Runner will automatically deploy the changes
) else (
    echo.
    echo ERROR: Push failed
)

pause