@echo off
echo ============================================
echo   AVA OLO Database Test Tool
echo ============================================
echo.
echo This tool will:
echo 1. Test database connection
echo 2. Add test data (2 farmers)
echo 3. Verify data can be retrieved
echo 4. Test AI query functionality
echo.
echo Press any key to start testing...
pause >nul

python test_database.py

echo.
echo Press any key to exit...
pause >nul