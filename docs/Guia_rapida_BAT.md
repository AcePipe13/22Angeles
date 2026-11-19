# Guía rápida para subir cambios con los `.bat`

Esta guía es para quienes trabajan en Windows y quieren usar los archivos `crear_rama.bat` y `subir_cambios.bat` de la raíz del repositorio. La [guía de Git y pull requests](Flujo_Git_y_PR.md) explica el proceso con comandos.

## Antes de empezar

1. Instala Git y configura tu nombre, correo y acceso a este repositorio.
2. Clona `https://github.com/AcePipe13/22Angeles` y abre una terminal dentro de la carpeta `22Angeles`.
3. Ejecuta `git status --short`. Si aparecen cambios que aún no guardaste, revísalos antes de crear otra rama. Los `.bat` no resuelven conflictos automáticamente.

## 1. Crear o abrir tu rama

Ejecuta:

```cmd
crear_rama.bat
```

Cuando pida `Introduce tu Apellido-Area`, escribe un nombre como `Valderrama-Control`. El script se detiene si hay cambios locales pendientes o si falla un comando de Git. Después descarga las referencias de GitHub, actualiza `main` y crea o abre la rama indicada. Si esa rama existe solo en GitHub, también puede recuperarla. Comprueba el resultado con:

```cmd
git branch --show-current
```

Debe aparecer el mismo nombre que escribiste. Si Git mostró un error durante el proceso, resuélvelo antes de continuar.

## 2. Hacer y subir los cambios

Trabaja en tu área, guarda los archivos y comprueba qué cambió:

```cmd
git status --short
```

Después ejecuta:

```cmd
subir_cambios.bat
```

El script muestra la rama activa y los cambios; confirma con `S` solo si quieres incluirlos todos. No permite subir directamente desde `main` y no pide que vuelvas a escribir el nombre de la rama. Ejecuta `git add --all`, comprueba el contenido preparado, pide una descripción si hay cambios nuevos, crea el commit y hace `git push -u origin HEAD`. Como agrega todos los cambios no ignorados, revisa la lista antes de confirmar.

Al terminar, revisa tu rama en GitHub. Si algún comando falla, el script se detiene y muestra un error; puede haber completado pasos anteriores, así que comprueba `git status --short --branch` antes de reintentarlo.

## 3. Abrir un pull request

En GitHub, abre un pull request desde tu rama hacia `main` para que el equipo revise e integre los cambios. Subir una rama no cambia `main` automáticamente.
