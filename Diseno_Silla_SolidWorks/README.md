# Mecánica — diseño de la silla

Esta carpeta contiene los modelos de SolidWorks de la silla de ruedas eléctrica, sus iteraciones, accesorios y archivos de estudio mecánico. El dimensionamiento de motores está en la carpeta hermana [`Calculos_Motores/`](../Calculos_Motores/).

## Estructura

| Ruta | Contenido |
| --- | --- |
| `Silla_V8.0/` | Iteración más reciente identificada por nombre de carpeta. Incluye el ensamble general `TODO.SLDASM`, estructura, ruedas, transmisión, cojinería, electrónica y accesorios. |
| `Silla_V4.0/`, `Silla_V6.0/`, `Silla_V6.1/`, `Silla_V7.0/` | Iteraciones anteriores conservadas para consultar la evolución del diseño. |
| `Estudios_Mecanicos/` | Modelo de estructura soldada y archivos de análisis. |
| `Pruebas_de_Control/` | Modelos de montaje, motor, encoder y acople usados en pruebas. |

En `Silla_V8.0/Accesorios/` hay modelos de batería, joystick, pantalla, sensor cardíaco y sensor de distancia TOF. La carpeta `Silla_V8.0/Electronica/` contiene representaciones mecánicas de componentes electrónicos. Los esquemas eléctricos están documentados por el área de [Electrónica](../Electronica_PCB/README.md).

## Archivo de referencia y cálculos

Para explorar el conjunto de la silla, empezar por `Silla_V8.0/TODO.SLDASM`. Sus piezas y subensambles se encuentran dentro de la misma versión; se recomienda mantener esa estructura de carpetas al abrirlo en SolidWorks.

[`Calculos_Motores/dimensionarSilla.m`](../Calculos_Motores/dimensionarSilla.m) calcula fuerzas, torque, potencia, velocidad y reducción a partir de una estructura de parámetros `P`. `Motores.mlx` conserva cálculos en formato Live Script de MATLAB. Comprobar que masa, radio de rueda, pendiente, eficiencias y características del motor correspondan al prototipo antes de usar los resultados.

## Estado

Los nombres de versión indican iteraciones del modelo, no una certificación del ensamble. Los archivos CAD y de estudio se conservaron como material de diseño; la fabricación, el montaje y las pruebas físicas deben documentarse por separado.
