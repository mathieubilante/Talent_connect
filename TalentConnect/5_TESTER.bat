@echo off
title TalentConnect - Tests automatiques
cd /d "%~dp0backend"
if not exist venv\Scripts\activate.bat goto pasinstalle
call venv\Scripts\activate.bat
echo Lancement des tests (environ 1 minute)...
python -m pytest
echo.
echo Si tout est vert (passed), le systeme fonctionne. Sinon copiez les lignes rouges et envoyez-les pour obtenir de l'aide.
pause
exit /b 0
:pasinstalle
echo Le projet n'est pas installe : lancez d'abord 1_INSTALLER.bat
pause
exit /b 1
