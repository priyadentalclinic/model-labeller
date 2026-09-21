@echo off
title ModelBot - One-Time Setup
chcp 65001 > nul
echo.
echo =====================================================
echo   ModelBot Labeler - One-Time Setup
echo =====================================================
echo.
python "%~dp0setup_labeler.py"
