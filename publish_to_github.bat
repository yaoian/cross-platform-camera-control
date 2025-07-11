@echo off
echo ========================================
echo Publishing Cross-Platform Camera Control Tool to GitHub
echo ========================================

echo.
echo Step 1: Checking Git status...
git status

echo.
echo Step 2: Checking remote repository...
git remote -v

echo.
echo Step 3: Pushing to GitHub...
echo Note: You may need to authenticate with GitHub
echo.
git push -u origin main

echo.
echo Step 4: Checking if push was successful...
git log --oneline -5

echo.
echo ========================================
echo Publish process completed!
echo.
echo If the push was successful, your repository should be available at:
echo https://github.com/yaoian/cross-platform-camera-control
echo.
echo Next steps:
echo 1. Visit the repository on GitHub
echo 2. Add topics/tags for better discoverability
echo 3. Create a release (optional)
echo 4. Update repository settings if needed
echo ========================================

pause
