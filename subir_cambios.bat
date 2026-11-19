@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
if errorlevel 1 goto :error

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ERROR: ejecuta este archivo dentro de la copia del repositorio.
    goto :error
)

for /f "delims=" %%B in ('git branch --show-current') do set "ramaActual=%%B"
if not defined ramaActual (
    echo ERROR: no hay una rama activa. Comprueba si Git esta en detached HEAD.
    goto :error
)
if /I "!ramaActual!"=="main" (
    echo ERROR: no subas cambios directamente a main. Crea una rama de trabajo.
    goto :error
)

echo Rama activa: !ramaActual!
echo Cambios detectados:
git status --short
if errorlevel 1 goto :error

set /p "confirmar=Agregar todos estos cambios y continuar? [S/N]: "
if /I not "!confirmar!"=="S" (
    echo Operacion cancelada. No se agregaron archivos ni se hizo push.
    pause
    exit /b 0
)

git add --all
if errorlevel 1 goto :error
git diff --cached --check
if errorlevel 1 goto :error

git diff --cached --quiet
set "estadoDiff=!errorlevel!"
if !estadoDiff! GTR 1 goto :error

if !estadoDiff! EQU 1 (
    set /p "descripcion=Introduce la descripcion del cambio: "
    if not defined descripcion (
        echo ERROR: debes escribir una descripcion para el commit.
        goto :error
    )
    git commit -m "!descripcion! - !ramaActual!"
    if errorlevel 1 goto :error
) else (
    echo No hay cambios nuevos para crear un commit. Se intentara subir cualquier commit pendiente.
)

echo Subiendo la rama activa a GitHub...
git push -u origin HEAD
if errorlevel 1 goto :error

echo.
git status --short --branch
echo Rama publicada. Abre un pull request hacia main para integrarla.
pause
exit /b 0

:error
echo.
echo Proceso detenido. Revisa el error anterior; no se continuara automaticamente.
pause
exit /b 1
