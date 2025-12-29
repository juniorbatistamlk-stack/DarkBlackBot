@echo off
title Instalador Dark Black Bot
color 0B
echo ==================================================
echo      INSTALANDO DARK BLACK BOT - AI POWERED
echo ==================================================
echo.

echo [1/3] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.10+ do site python.org lembrando de marcar "Add to PATH"
    pause
    exit
)
echo [OK] Python encontrado!

echo.
echo [2/3] Instalando bibliotecas...
pip install -r requirements.txt --quiet
echo [OK] Bibliotecas instaladas!

echo.
echo [3/3] Criando atalho na area de trabalho...
set SCRIPT="%TEMP%\CreateShortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Dark Black Bot.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%CD%\INICIAR_BOT.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%" >> %SCRIPT%
echo oLink.IconLocation = "%CD%\darkblackbot.ico" >> %SCRIPT%
echo oLink.Description = "Dark Black Bot - Trading Automatico com IA" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript //nologo %SCRIPT%
del %SCRIPT%
echo [OK] Atalho criado na area de trabalho!

echo.
echo ==================================================
echo      INSTALACAO CONCLUIDA COM SUCESSO!
echo ==================================================
echo.
echo Voce pode iniciar o bot de duas formas:
echo   1. Clique no atalho "Dark Black Bot" na area de trabalho
echo   2. Execute o arquivo INICIAR_BOT.bat
echo.
pause
