@echo off
title ModelBot - Pull Labels and Sort Photos
chcp 65001 > nul
echo.
echo =====================================================
echo   STEP 2: Pull Labels and Sort Photos
echo =====================================================
echo.
python "%~dp0pull_sort.py"
