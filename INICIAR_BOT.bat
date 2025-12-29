@echo off
title Dark Black Bot - AI Powered
color 0A
echo ==================================================
echo      INICIANDO DARK BLACK BOT - AI POWERED
echo ==================================================
echo.
echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.10 ou superior.
    echo Baixe em: python.org
    pause
    exit
)

echo Iniciando sistema...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O bot fechou com erro.
    pause
)
pause
