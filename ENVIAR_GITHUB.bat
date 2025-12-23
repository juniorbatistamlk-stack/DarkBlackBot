@echo off
set GCM_INTERACTIVE=always
echo ==========================================
echo    CORRECAO DEFINITIVA - LIMPEZA TOTAL
echo ==========================================
echo.

echo 1. Apagando historico antigo (com erro)...
rmdir /s /q .git

echo 2. Iniciando novo repositorio...
"C:\Program Files\Git\cmd\git.exe" init -b main
"C:\Program Files\Git\cmd\git.exe" config user.name "Antigravity Bot"
"C:\Program Files\Git\cmd\git.exe" config user.email "bot@antigravity.local"

echo 3. Vinculando ao GitHub...
"C:\Program Files\Git\cmd\git.exe" remote add origin https://github.com/juniorbatistamlk-stack/updates-bot

echo 4. Adicionando arquivos (agora limpos)...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Fixed: Removed all secrets and updated icon"

echo 5. ENVIANDO AGORA...
echo.
echo    [ATENCAO]
echo    Se pedir login, faca novamente.
echo    Isso vai apagar o historico ruim e enviar o limpo.
echo.
"C:\Program Files\Git\cmd\git.exe" push origin main --force

echo.
echo ==========================================
echo    Se apareceu "Writing objects 100", DEU CERTO!
echo ==========================================
pause
