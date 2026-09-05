@echo off
chcp 65001 > nul
cd /d "%~dp0"
title LexQuest - Gerador de Questões

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m lexquest.menu
) else (
    python -m lexquest.menu
)

if errorlevel 1 pause
