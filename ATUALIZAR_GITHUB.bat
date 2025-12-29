@echo off
echo ==========================================
echo    PUBLICAR LICENCAS NO GITHUB
echo ==========================================
echo.

REM ===================================================
REM PASSO 0: Copiar license_database.json para raiz
REM (resolve problema de pasta separada do Git)
REM ===================================================
echo 0. Sincronizando banco de licencas...
if exist "license_database.json" (
    copy /Y "license_database.json" "..\..\license_database.json" >nul 2>&1
    if %errorlevel%==0 (
        echo    [OK] Banco copiado para raiz do projeto
    ) else (
        echo    [AVISO] Nao foi possivel copiar para raiz
    )
)

REM Muda para a raiz do projeto Git
cd /d "%~dp0..\.."

echo 1. Buscando novidades (Pull)...
"C:\Program Files\Git\cmd\git.exe" pull origin main

echo 2. Salvando suas mudancas...
"C:\Program Files\Git\cmd\git.exe" add license_database.json
"C:\Program Files\Git\cmd\git.exe" commit -m "Sync: Atualizacao de licencas"

echo 3. Enviando...
"C:\Program Files\Git\cmd\git.exe" push origin main

echo.
echo ==========================================
echo    CONCLUIDO! Licencas publicadas.
echo ==========================================
pause
