@echo off
title TalentConnect - Reinitialisation
echo ATTENTION : cela efface tous les comptes et toutes les donnees, puis recree les comptes de demonstration.
echo Fermez d'abord les fenetres "API" et "Site" (2_LANCER) si elles sont ouvertes.
set /p OK=Tapez O pour continuer : 
if /i not "%OK%"=="O" goto fin
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
if exist talentconnect.db del talentconnect.db
python -m app.seed
echo.
echo Termine. Relancez avec 2_LANCER.bat
:fin
pause
