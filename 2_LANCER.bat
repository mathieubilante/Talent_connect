@echo off
title TalentConnect - Lancement
echo Lancement de TalentConnect...
if not exist "%~dp0backend\venv\Scripts\activate.bat" goto pasinstalle
if not exist "%~dp0frontend\node_modules" goto pasinstalle

start "TalentConnect - API (ne pas fermer)" /D "%~dp0backend" cmd /k "venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload"
start "TalentConnect - Site (ne pas fermer)" /D "%~dp0frontend" cmd /k "npm run dev"

echo Patientez 10 secondes, le navigateur va s'ouvrir sur le site...
timeout /t 10 /nobreak >nul
start http://localhost:5173
echo.
echo Le site : http://localhost:5173
echo La documentation de l'API : http://localhost:8000/docs
echo Le code de verification (OTP) s'affiche dans la fenetre "API".
echo Pour arreter : fermez les deux fenetres noires.
pause
exit /b 0

:pasinstalle
echo Le projet n'est pas encore installe. Double-cliquez d'abord sur 1_INSTALLER.bat
pause
exit /b 1
