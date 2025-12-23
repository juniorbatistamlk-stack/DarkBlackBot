@echo off
chcp 65001 >nul
title Dark Black Bot - Instalador Simples
color 0A

REM Muda para o diretório onde está o bat
cd /d "%~dp0"

echo.
echo ═══════════════════════════════════════════════════════════
echo     🤖 DARK BLACK BOT PRO - INSTALADOR AUTOMÁTICO
echo ═══════════════════════════════════════════════════════════
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo.
    echo 📥 Baixando Python...
    echo Por favor, aguarde...
    
    REM Baixar Python
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile 'python_installer.exe'"
    
    echo.
    echo 📦 Instalando Python...
    echo IMPORTANTE: Marque a opção "Add Python to PATH"!
    echo.
    pause
    
    start /wait python_installer.exe
    del python_installer.exe
    
    echo.
    echo ✅ Python instalado!
    echo ⚠️  REINICIE este instalador agora.
    pause
    exit
)

echo ✅ Python encontrado!
echo.

REM Instalar dependências
echo 📦 Instalando dependências...
echo Isso pode demorar alguns minutos...
echo.

python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo.
    echo ❌ Erro ao instalar dependências!
    echo Tente executar manualmente: pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Dependências instaladas!
echo.

REM Criar atalho na área de trabalho
echo 🔗 Criando atalho...

set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop

REM Criar arquivo .bat para executar o bot
echo @echo off > "%SCRIPT_DIR%ABRIR_BOT.bat"
echo cd /d "%SCRIPT_DIR%" >> "%SCRIPT_DIR%ABRIR_BOT.bat"
echo python main.py >> "%SCRIPT_DIR%ABRIR_BOT.bat"
echo pause >> "%SCRIPT_DIR%ABRIR_BOT.bat"

REM Criar atalho com ícone usando PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\Dark Black Bot.lnk'); $s.TargetPath = '%SCRIPT_DIR%ABRIR_BOT.bat'; $s.IconLocation = '%SCRIPT_DIR%icon.ico'; $s.Save()"

echo ✅ Atalho criado na área de trabalho com ícone personalizado!
echo.
echo ═══════════════════════════════════════════════════════════
echo     ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ═══════════════════════════════════════════════════════════
echo.
echo 📌 Para abrir o bot:
echo    - Clique 2x em "Dark Black Bot.bat" na área de trabalho
echo    - Ou execute "ABRIR_BOT.bat" nesta pasta
echo.
echo 🔐 Na primeira vez, você precisará inserir sua chave de licença.
echo.
echo 💬 Suporte: https://t.me/magoTrader_01
echo.
pause
