@echo off
title ModelBot - Pull ^& Decrypt Generated UGC Ads
chcp 65001 > nul
python "%~dp0pull_generated.py"
