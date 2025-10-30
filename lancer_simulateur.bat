@echo off
echo ========================================
echo Simulateur de Trajectoire d'Avion P21
echo ========================================
echo.
echo Lancement du simulateur...
echo.

cd /d "%~dp0"
python main.py

if errorlevel 1 (
    echo.
    echo Erreur lors du lancement du simulateur!
    pause
)
