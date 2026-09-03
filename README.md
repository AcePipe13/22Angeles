# 22 Angeles Proyecto Diseño
Este repositorio trae todo lo que hicimos en nuestro proyecto de Diseño Mecatrónico para el programa Ingeniería en Mecatrónica de la Universidad Militar Nueva Granada de Colombia

# Si no quieren complicarse la vida

Este tutorial explica cómo usar los dos archivos `.bat` para trabajar con el repositorio sin tener que escribir todos los comandos de Git manualmente.

## Antes de empezar

Necesitas:

- Tener **Git** instalado:  
  - `https://git-scm.com/install/windows`
- Tener descargado/clonado el repositorio en tu PC.
  - `git clone https://github.com/AcePipe13/22Angeles/`
- Colocar estos dos archivos dentro de la carpeta del repositorio:
  - `crear_rama.bat`
  - `subir_cambios.bat`

La estructura puede quedar así:

```text
22Angeles/
├── crear_rama.bat
├── subir_cambios.bat
├── README.md
└── ...
```

## 1. Crear tu rama

Abre una terminal dentro de la carpeta del repositorio.

Puedes hacerlo entrando a la carpeta con:

```cmd
cd ruta\de\tu\repositorio
```

Después ejecuta:

```cmd
crear_rama.bat
```

También puedes usar:

```powershell
.\crear_rama.bat
```

El programa te pedirá tu apellido y área:

```text
Introduce tu Apellido-Area: Valderrama-Finanzas 
```

Al terminar, estarás trabajando en tu propia rama.

## 2. Subir tus cambios

Cuando hayas terminado tu trabajo, vuelve a abrir la terminal dentro de la carpeta del repositorio y ejecuta:

```cmd
subir_cambios.bat
```

El programa te pedirá dos datos:

```text
Introduce la descripcion del cambio: Añadido ejercicio 3
Introduce tu Apellido-Area: Valderrama-Finanzas
```

Tus cambios quedarán subidos a GitHub en la rama `Valderrama-Finanzas`.

## Resumen

La idea es sencilla:

```text
1. crear_rama.bat
   ↓
   Escribes tu apellido y área
   ↓
   Se crea tu rama

2. Haces tus cambios
   ↓

3. subir_cambios.bat
   ↓
   Escribes la descripción, tu apellido y área
   ↓
   Se crea el commit y se sube a GitHub
```

Así no hace falta escribir todos los comandos de Git a mano.

> **Importante:** ejecuta los `.bat` desde la carpeta del repositorio y asegúrate de tener Git configurado y acceso al repositorio de GitHub.
