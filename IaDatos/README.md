# IA y Datos — sensores, interfaz y GPS

Esta área reúne pruebas de adquisición y comunicación, una interfaz de usuario y prototipos de cámara, sensores y GPS para la silla de ruedas eléctrica.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `Codigos_Pruebas_ESP32/` | Proyectos PlatformIO ya existentes para comunicación con Raspberry Pi, GPS y sensor de distancia TOF. |
| `HMI/` | Interfaz Qt/QML con pantallas, componentes y recursos. |
| `sensores/` | Lecturas y prototipos Tkinter para joystick ADS1115, distancia VL53L1X, pulso MAX30102 y orientación MPU6050. |
| `camara/` | Prueba independiente de cámara Arducam/Picamera2. |
| `GPS/` | Programa ESP32, receptor e interfaz de Raspberry Pi y aplicación Flutter para celular. |

## HMI

`HMI/main.py` inicia la interfaz QML mediante PySide6 y aporta el controlador de cámara usado por `HMI/Screens/Camera.qml`. Requiere PySide6; la captura en Raspberry Pi usa Picamera2. `HMI/main.cpp` con `HMI/CMakeLists.txt` ofrece una ruta Qt/C++ alternativa, pero no aporta ese mismo controlador de cámara.

La HMI contiene también pantallas y valores de demostración. `HMI/Screens/VoiceAI.qml` es todavía un marcador sin implementación. Los textos de estado, posición o mediciones que aparecen en las pantallas deben conectarse y verificarse con los datos reales antes de considerarlos telemetría operativa.

## Sensores y GPS

Los scripts de `sensores/` permanecen juntos para conservar sus importaciones entre archivos. Cada prueba requiere las bibliotecas y conexiones del sensor correspondiente. `GPS/` conserva por separado el código ESP32, el programa de Raspberry Pi y la app Flutter, porque cada uno cumple una función distinta.

Para usar la prueba `GPS/ESP32_GPS/`, copiar `gps_secrets.example.h` como `gps_secrets.h` en esa misma carpeta y completar allí la red y la contraseña Wi-Fi. `gps_secrets.h` está ignorado por Git; no se deben publicar credenciales reales. `gps_input_wifi.h` conserva la lógica de conexión y lectura UDP.

Los entornos Python, las carpetas `build/`, `.dart_tool/` y otras cachés locales están excluidos mediante `.gitignore`. El firmware de movimiento está documentado en [Control](../Control/README.md).
