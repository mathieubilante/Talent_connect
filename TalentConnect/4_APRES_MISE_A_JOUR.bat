@echo off
title TalentConnect - Apres mise a jour
echo Installation des nouveaux paquets (rapide, vos donnees sont conservees)...
cd /d "%~dp0backend"
if not exist venv\Scripts\activate.bat goto pasinstalle
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto erreur
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 goto erreur
echo.
echo Mise a jour terminee. Lancez 2_LANCER.bat
pause
exit /b 0
:pasinstalle
echo Le projet n'est pas encore installe : lancez d'abord 1_INSTALLER.bat
pause
exit /b 1
:erreur
echo ERREUR : copiez les lignes rouges ci-dessus et envoyez-les pour obtenir de l'aide.
pause
exit /b 1
