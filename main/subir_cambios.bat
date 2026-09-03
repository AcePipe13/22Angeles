@echo off
setlocal

set /p "descripcion=Introduce la descripcion del cambio: "
set /p "apellido=Introduce tu apellido: "

if "%descripcion%"=="" (
    echo Debes introducir una descripcion.
    pause
    exit /b 1
)

if "%apellido%"=="" (
    echo Debes introducir un apellido.
    pause
    exit /b 1
)

echo.
echo Añadiendo cambios...
git add .

echo.
echo Creando commit...
git commit -m "%descripcion% - %apellido%"

echo.
echo Subiendo rama a GitHub...
git push -u origin "%apellido%"

echo.
echo Proceso terminado.
pause