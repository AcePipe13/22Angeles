# 🚀 Flujo de trabajo con Git y GitHub

Esta guía explica el proceso recomendado para crear una rama de trabajo, realizar cambios, subirlos a GitHub y abrir un Pull Request.

---

# 📌 1. Preparar la rama principal (`main`)

Antes de comenzar cualquier tarea, asegúrate de tener la versión más reciente del proyecto.

```bash
git checkout main
```

Cambia a la rama principal.

```bash
git pull origin main
```

Descarga los últimos cambios del repositorio remoto.

---

# 🔎 2. Verificar la rama actual

Comprueba que estás trabajando desde `main`:

```bash
git status
```

Debe aparecer:

```
On branch main
```

Si no estás en `main`, cambia con:

```bash
git checkout main
```

---

# 🌱 3. Crear una rama para tu tarea

Crea una nueva rama usando siempre el mismo nombre durante todo el proceso:

```bash
git checkout -b Apellido
```

Ejemplo:

```bash
git checkout -b Perez
```

Esto crea la rama y cambia automáticamente hacia ella.

> ⚠️ Si la rama ya existe (por ejemplo, porque continuas una sesión anterior), utiliza:

```bash
git checkout Apellido
```

---

# 🛠️ 4. Realizar los cambios

Ahora puedes trabajar normalmente en tu código:

- Crear archivos nuevos.
- Modificar archivos existentes.
- Eliminar archivos innecesarios.
- Probar tu solución.

Cuando termines, guarda todos los cambios.

---

# 📦 5. Agregar cambios al área de staging

Prepara todos los archivos modificados:

```bash
git add .
```

Esto incluye:

✅ Archivos nuevos  
✅ Archivos modificados  
✅ Archivos eliminados  

---

# 💾 6. Crear un commit

Guarda tus cambios en el historial de Git:

```bash
git commit -m "Descripción del cambio - Tu Apellido"
```

Ejemplo:

```bash
git commit -m "Agregue validacion del formulario - Perez"
```

Un buen mensaje de commit debe explicar claramente qué cambiaste.

---

# ☁️ 7. Subir la rama a GitHub

Envía tu rama al repositorio remoto:

```bash
git push -u origin Apellido
```

Ejemplo:

```bash
git push -u origin Perez
```

Después de esta primera subida, solo será necesario usar:

```bash
git push
```

---

# 🔀 8. Crear un Pull Request

Cuando tu código esté en GitHub:

1. Entra al repositorio.
2. Selecciona tu rama.
3. Haz clic en:

```
Compare & pull request
```

4. Describe los cambios realizados.
5. Presiona:

```
Create pull request
```

🎉 Tu tarea queda lista para revisión.

---

<br>

# 🔄 Ciclo para iniciar una nueva tarea

Después de que tu Pull Request sea aprobado y unido (`Merged`) a `main`, sigue estos pasos para comenzar una nueva tarea.

---

# 1. Revisar cambios pendientes

Primero verifica que no tengas cambios sin guardar:

```bash
git status
```

Si aparecen archivos modificados:

- Haz commit si deseas conservarlos.
- Descártalos si ya no los necesitas.

---

# 2. Volver a la rama principal

```bash
git checkout main
```

Regresa a la rama principal.

---

# 3. Actualizar `main`

Descarga los cambios aprobados:

```bash
git pull origin main
```

Ahora tienes las últimas tareas fusionadas por el equipo.

---

# 4. Eliminar la rama anterior

Cuando la tarea ya está guardada en `main`, elimina la rama antigua:

```bash
git branch -d apellido
```

Ejemplo:

```bash
git branch -d Perez
```

> ⚠️ Si Git muestra:

```
not fully merged
```

puedes forzar la eliminación:

```bash
git branch -D apellido
```

---

# 5. Crear la nueva rama

Comienza la siguiente tarea desde la versión actualizada:

```bash
git checkout -b apellido
```

Ejemplo:

```bash
git checkout -b Perez
```

Ahora estás listo para comenzar un nuevo ejercicio 🚀

---

# 📚 Resumen rápido

| Acción | Comando |
|---|---|
| Ir a main | `git checkout main` |
| Actualizar proyecto | `git pull origin main` |
| Crear rama | `git checkout -b nombre` |
| Preparar cambios | `git add .` |
| Crear commit | `git commit -m "mensaje"` |
| Subir rama | `git push -u origin nombre` |
| Ver estado | `git status` |
| Eliminar rama | `git branch -d nombre` |

---

## ✅ Buenas prácticas

- Trabaja siempre en ramas, nunca directamente en `main`.
- Usa nombres claros para tus ramas.
- Haz commits pequeños y descriptivos.
- Actualiza `main` antes de comenzar una nueva tarea.
- Abre un Pull Request para que los cambios sean revisados.

¡Feliz programación! 🚀