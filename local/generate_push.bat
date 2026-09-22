@echo off
title ModelBot - Encrypt ^& Push Reference Photo
chcp 65001 > nul
python "%~dp0generate_push.py"
