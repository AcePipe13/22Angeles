@echo off
setlocal

set /p "apellido=Introduce tu Apellido-Area: "

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
echo Verificando rama %apellido%...

git show-ref --verify --quiet refs/heads/%apellido%

if %errorlevel%==0 (
    echo La rama %apellido% ya existe.
    echo Cambiando a la rama...
    git checkout %apellido%
) else (
    echo Creando rama %apellido%...
    git checkout -b %apellido%
)

echo.
echo Rama actual:
git branch --show-current

pause