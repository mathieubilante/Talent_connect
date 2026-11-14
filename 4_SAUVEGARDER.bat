@echo off
title TalentConnect - Sauvegarde
cd /d "%~dp0backend"
if not exist venv\Scripts\activate.bat goto pasinstalle
call venv\Scripts\activate.bat
python -m tools.backup
echo.
echo Les sauvegardes sont dans le dossier backend\sauvegardes
pause
exit /b 0
:pasinstalle
echo Le projet n'est pas installe : lancez d'abord 1_INSTALLER.bat
pause
exit /b 1
