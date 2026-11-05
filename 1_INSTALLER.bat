@echo off
title TalentConnect - Installation
echo ==================================================
echo   TalentConnect - Installation (a faire une seule fois)
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 goto nopython
where node >nul 2>nul
if errorlevel 1 goto nonode

echo [1/4] Creation de l'environnement Python...
cd /d "%~dp0backend"
if not exist venv python -m venv venv
if errorlevel 1 goto erreur
call venv\Scripts\activate.bat

echo.
echo [2/4] Installation des paquets Python (quelques minutes)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto erreur

echo.
echo [3/4] Creation des comptes de demonstration...
python -m app.seed
if errorlevel 1 goto erreur

echo.
echo [4/4] Installation du site web (quelques minutes)...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 goto erreur

echo.
echo ==================================================
echo   Installation terminee !
echo   Double-cliquez maintenant sur 2_LANCER.bat
echo ==================================================
pause
exit /b 0

:nopython
echo ERREUR : Python n'est pas installe.
echo Installez-le depuis https://www.python.org/downloads/
echo Cochez bien "Add Python to PATH" pendant l'installation, puis relancez ce fichier.
pause
exit /b 1

:nonode
echo ERREUR : Node.js n'est pas installe.
echo Installez la version LTS depuis https://nodejs.org puis relancez ce fichier.
pause
exit /b 1

:erreur
echo.
echo ERREUR pendant l'installation. Faites une capture ou copiez les lignes rouges
echo ci-dessus et envoyez-les pour obtenir de l'aide.
pause
exit /b 1
