@echo off
echo ==========================================
echo    PUBLICAR NO GITHUB DE UPDATES
echo ==========================================
echo.

cd updates

echo Inicializando repositorio (se necessario)...
if not exist .git (
    "C:\Program Files\Git\cmd\git.exe" init -b main
    "C:\Program Files\Git\cmd\git.exe" config user.name "Antigravity Bot"
    "C:\Program Files\Git\cmd\git.exe" config user.email "bot@antigravity.local"
    "C:\Program Files\Git\cmd\git.exe" remote add origin https://github.com/juniorbatistamlk-stack/updates-bot
)

echo Adicionando arquivos...
"C:\Program Files\Git\cmd\git.exe" add .

echo Fazendo commit...
"C:\Program Files\Git\cmd\git.exe" commit -m "Nova versao publicada"

echo Enviando para GitHub...
"C:\Program Files\Git\cmd\git.exe" push origin main --force

cd ..

echo.
echo ==========================================
echo    PUBLICADO COM SUCESSO!
echo ==========================================
echo.
echo Seus clientes ja podem baixar a atualizacao!
echo.
pause
