# 22 Ángeles — silla de ruedas eléctrica

Proyecto de Diseño Mecatrónico del programa de Ingeniería en Mecatrónica de la Universidad Militar Nueva Granada (Colombia). El repositorio reúne el diseño de una silla de ruedas eléctrica y los prototipos de sus sistemas mecánicos, electrónicos, de control, interfaz y adquisición de datos.

## Áreas del proyecto

| Área | Contenido | Documentación |
| --- | --- | --- |
| Mecánica | Ensambles de SolidWorks, accesorios, estudios y dimensionamiento de motores. | [Diseño mecánico](Diseno_Silla_SolidWorks/README.md) y [cálculos](Calculos_Motores/) |
| Electrónica | Esquemas eléctricos, imágenes y modelos 3D de las placas. | [Electrónica](Electronica_PCB/README.md) |
| Control | Firmware para motores y encoders, caracterización, simulaciones y herramientas de prueba. | [Control](Control/README.md) |
| IA y Datos | Pruebas ESP32, sensores, cámara, GPS, aplicación celular e interfaz de usuario. | [IA y Datos](IaDatos/README.md) |

## Cómo se relacionan los módulos

El diseño mecánico define la estructura, las ruedas, la transmisión y los soportes de los accesorios. La electrónica documenta las placas y conexiones. Control contiene el programa que regula la velocidad de los motores con realimentación de encoders. IA y Datos agrupa la lectura de sensores, la presentación de información y las pruebas de comunicación y GPS.

Estas carpetas incluyen diseños y pruebas en diferentes etapas. La presencia de un modelo o una pantalla no demuestra por sí sola que el accesorio esté integrado y validado en la silla. Cada README de área indica qué archivo usar como referencia y qué queda por comprobar en el hardware.

## Por dónde empezar

1. Abrir el README del área de interés en la tabla anterior.
2. Identificar allí el ensamble, esquema o programa de referencia y sus dependencias.
3. Revisar el cableado, la alimentación y los parámetros del equipo real antes de ejecutar firmware o conectar motores.
4. Para colaborar mediante ramas y pull requests, seguir la [guía de Git](main/Tutorial_Git.md). En Windows también están disponibles `crear_rama.bat` y `subir_cambios.bat` en la raíz.

Los archivos de compilación y los entornos locales se excluyen mediante `.gitignore` en las áreas correspondientes. Las credenciales Wi-Fi de las pruebas GPS se guardan en un archivo local ignorado por Git; el [README de IA y Datos](IaDatos/README.md) explica cómo configurarlo.
