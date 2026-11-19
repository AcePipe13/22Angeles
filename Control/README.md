# Control — motores y movimiento

Esta área reúne el firmware de motores, las mediciones de caracterización, las simulaciones y las herramientas de prueba de la silla de ruedas eléctrica.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `firmware/esp32/CodigoControlFinal/` | Programa de referencia para controlar la velocidad de dos motores con ESP32, controlador Cytron y encoders. |
| `pruebas/movimiento/` | Programa de comprobación de movimiento con Cytron. |
| `caracterizacion/cytron/` | Código ESP32, MATLAB y Simulink para caracterización de motores. |
| `caracterizacion/primera_etapa/` | Código de captura y mediciones CSV de la primera campaña de caracterización. |
| `simulaciones/teoria_control/` | Cálculos y modelo de Simulink. |
| `herramientas/bluetooth/` | Programa e interfaces de pruebas por Bluetooth. |
| `versiones_anteriores/` | Código anterior, con otra asignación de pines y parámetros. |

## Programa de referencia

`firmware/esp32/CodigoControlFinal/CodigoControlFinal.ino` es la variante más reciente encontrada en esta área. Implementa el control PI de velocidad de cada motor, lectura de encoders, comandos por puerto serie y telemetría. Usa la biblioteca `CytronMotorDriver` y los pines y baudios definidos al inicio del archivo. La versión de `versiones_anteriores/` se conserva para comparar cambios; no debe combinarse con el cableado actual sin revisar esas diferencias.

Antes de mover la silla, confirmar en el montaje real el sentido de giro, los canales del Cytron, los encoders, la alimentación, el protocolo serie y la parada de los motores. Las ganancias PI del código requieren validación con mediciones; el nombre `CodigoControlFinal` no equivale a una validación completa del sistema.

## Datos y relación con otras áreas

Los CSV en `caracterizacion/primera_etapa/datos_caracterizacion/` son mediciones originales. Los archivos temporales de MATLAB y Simulink se excluyen mediante `.gitignore`. El dimensionamiento mecánico del motor está en [`Calculos_Motores/`](../Calculos_Motores/), los esquemas en [Electrónica](../Electronica_PCB/README.md) y las pruebas GPS en [`IaDatos/GPS/`](../IaDatos/GPS/).
