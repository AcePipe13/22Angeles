@echo off
setlocal

set /p "apellido=Introduce tu apellido: "

if "%apellido%"=="" (
    echo Debes introducir un apellido.
    pause
    exit /b 1
)

echo.
echo Actualizando main...
git checkout main
git pull origin main

echo.
echo Creando rama %apellido%...
git checkout -b "%apellido%"

echo.
echo Rama creada correctamente: %apellido%
pause