@echo off
echo ==========================================
echo    ATUALIZAR BOT NO GITHUB (SIMPLES)
echo ==========================================
echo.

echo 1. Buscando novidades (Pull)...
"C:\Program Files\Git\cmd\git.exe" pull origin main

echo 2. Salvando suas mudancas...
"C:\Program Files\Git\cmd\git.exe" add .
set /p msg="Escreva o que mudou (ou aperte ENTER para 'Atualizacao'): "
if "%msg%"=="" set msg=Atualizacao
"C:\Program Files\Git\cmd\git.exe" commit -m "%msg%"

echo 3. Enviando...
"C:\Program Files\Git\cmd\git.exe" push origin main

echo.
echo ==========================================
echo    FIM! Se nao deu erro vermelho, foi.
echo ==========================================
pause
