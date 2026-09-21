@echo off
title ModelBot - Encrypt and Push Photos
chcp 65001 > nul
echo.
echo =====================================================
echo   STEP 1: Encrypt and Push Photos to GitHub
echo =====================================================
echo.
echo Put your photos in the to_upload folder first.
echo Then press any key to continue.
pause > nul
python "%~dp0encrypt_push.py"
