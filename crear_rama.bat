@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
if errorlevel 1 goto :error

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ERROR: ejecuta este archivo dentro de la copia del repositorio.
    goto :error
)

git status --porcelain >nul 2>&1
if errorlevel 1 goto :error
for /f "delims=" %%L in ('git status --porcelain') do set "hayCambios=1"
if defined hayCambios (
    echo ERROR: hay cambios sin guardar. Haz commit o revisalos antes de cambiar de rama.
    git status --short
    goto :error
)

set /p "rama=Introduce tu Apellido-Area: "
if not defined rama (
    echo ERROR: debes escribir un nombre de rama.
    goto :error
)

git check-ref-format --branch "!rama!" >nul 2>&1
if errorlevel 1 (
    echo ERROR: el nombre de rama no es valido para Git.
    goto :error
)
if /I "!rama!"=="main" (
    echo ERROR: trabaja en una rama propia, no directamente en main.
    goto :error
)

echo.
echo Descargando referencias de GitHub...
git fetch origin
if errorlevel 1 goto :error

echo Actualizando main sin crear un merge...
git switch main
if errorlevel 1 goto :error
git merge --ff-only origin/main
if errorlevel 1 goto :error

git show-ref --verify --quiet "refs/heads/!rama!"
if not errorlevel 1 (
    echo Abriendo rama local !rama!...
    git switch "!rama!"
    if errorlevel 1 goto :error
) else (
    git show-ref --verify --quiet "refs/remotes/origin/!rama!"
    if not errorlevel 1 (
        echo Recuperando rama !rama! desde GitHub...
        git switch --track -c "!rama!" "origin/!rama!"
        if errorlevel 1 goto :error
    ) else (
        echo Creando rama !rama! desde main...
        git switch -c "!rama!"
        if errorlevel 1 goto :error
    )
)

echo.
echo Rama activa:
git branch --show-current
echo Proceso terminado.
pause
exit /b 0

:error
echo.
echo Proceso detenido. Revisa el error anterior; no se continuara automaticamente.
pause
exit /b 1
