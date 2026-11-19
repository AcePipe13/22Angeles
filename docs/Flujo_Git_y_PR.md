# Flujo de trabajo con Git y GitHub

Esta guía explica cómo crear una rama, registrar cambios y abrir un pull request usando comandos. Si prefieres los scripts de Windows, consulta la [guía rápida de los `.bat`](Guia_rapida_BAT.md).

Ejecuta los comandos desde la raíz del repositorio `22Angeles`.

## 1. Revisar y actualizar `main`

Comprueba primero que no tengas cambios pendientes:

```bash
git status --short
```

Si el resultado está vacío, actualiza la rama principal:

```bash
git switch main
git pull --ff-only origin main
```

Si hay cambios pendientes, guárdalos en la rama correspondiente antes de cambiar de rama. Si `git pull` falla, revisa el mensaje de Git; no continúes sobre una versión desactualizada sin resolverlo.

## 2. Crear una rama para la tarea

Usa un nombre que identifique a la persona y el área o la tarea:

```bash
git switch -c Valderrama-Control
git branch --show-current
```

Si continúas una rama local ya existente, usa `git switch Valderrama-Control` en vez de crearla de nuevo.

## 3. Preparar y registrar cambios

Después de editar y probar tus archivos, revisa qué vas a incluir:

```bash
git status --short
git add ruta/del/archivo
git diff --cached --check
git diff --cached --stat
git commit -m "Describe el cambio - Apellido-Area"
```

Sustituye `ruta/del/archivo` por las rutas reales. Puedes añadir varias rutas. `git add .` añade todos los cambios no ignorados del directorio actual; úsalo solo si ya revisaste la lista completa.

## 4. Subir la rama y solicitar revisión

```bash
git push -u origin HEAD
```

En GitHub, abre un pull request de tu rama hacia `main`, describe los cambios y espera su revisión. El push publica la rama; el pull request es el paso que permite integrar el trabajo en `main`.

## 5. Comenzar otra tarea

Cuando el pull request anterior esté integrado y tu directorio de trabajo esté limpio:

```bash
git switch main
git pull --ff-only origin main
git switch -c Apellido-NuevaTarea
```

Comprueba la rama activa con `git branch --show-current` antes de volver a editar archivos.
