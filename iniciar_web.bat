@echo off
chcp 65001 > nul
cd /d "%~dp0"
title LexQuest - Servidor Web Streamlit

echo ===============================================================================
echo            INICIANDO LEXQUEST WEB APP NO NAVEGADOR
echo ===============================================================================
echo.
echo Iniciando servidor Streamlit local em http://localhost:8501...
echo Seu navegador padrão abrirá automaticamente.
echo.
echo Para encerrar o servidor, feche esta janela ou pressione Ctrl+C.
echo ===============================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)

if errorlevel 1 pause
