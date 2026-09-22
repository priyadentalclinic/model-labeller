@echo off
title ModelBot - Individual Photo Reports (Qwen 2.5-VL)
cd /d "%~dp0\.."
python local\pull_report.py
pause
