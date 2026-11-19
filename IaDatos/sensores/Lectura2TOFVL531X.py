import time
import board
import busio
import serial
from gpiozero import DigitalOutputDevice
import adafruit_vl53l1x

# ============================================================
# CONFIGURACIÓN
# ============================================================
PINES_XSHUT = [17, 27]
DIRECCIONES = [0x30, 0x31]

# ============================================================
# CONFIGURAR XSHUT
# ============================================================
xshut = []
for pin in PINES_XSHUT:
    salida = DigitalOutputDevice(pin, initial_value=False)
    xshut.append(salida)

print("Sensores apagados.")
time.sleep(0.2)

# ============================================================
# INICIALIZAR I2C
# ============================================================
i2c = busio.I2C(board.SCL, board.SDA)
sensores = []

# ============================================================
# INICIALIZAR LOS DOS VL53L1X
# ============================================================
print("\nInicializando sensores...\n")

for i in range(2):
    print(f"Inicializando Sensor {i + 1}...")
    
    # Encender sensor individualmente
    xshut[i].on()
    time.sleep(0.2)

    try:
        # El sensor arranca en la dirección por defecto (0x29)
        sensor = adafruit_vl53l1x.VL53L1X(i2c, address=0x29)
        print(f"Sensor {i + 1} detectado en 0x29")

        # Cambiar dirección I2C
        sensor.set_address(DIRECCIONES[i])
        print(f"Sensor {i + 1} -> 0x{DIRECCIONES[i]:02X}")

        # Configuración del sensor
        sensor.distance_mode = 2  # 2 = LONG (hasta 4 metros)
        sensor.timing_budget = 50  # Tiempo de integración en ms

        # Iniciar medición continua
        sensor.start_ranging()
        sensores.append(sensor)
        print(f"Sensor {i + 1} listo.")

    except Exception as e:
        print(f"ERROR en Sensor {i + 1}: {e}")
        sensores.append(None)

print("\n================================")
print("Sensores inicializados")
print("================================")

for i, sensor in enumerate(sensores):
    if sensor is not None:
        print(f"S{i + 1} -> 0x{DIRECCIONES[i]:02X} OK")
    else:
        print(f"S{i + 1} -> ERROR")

# ============================================================
# PUERTO SERIAL
# ============================================================
puerto_serial = serial.Serial(
    port="/dev/serial0",
    baudrate=9600,
    timeout=1
)

print("\nSerial iniciado:")
print("/dev/serial0 @ 9600\n")

# ============================================================
# BUCLE PRINCIPAL (Sin valores N/A)
# ============================================================
# Memoria interna para guardar la última distancia leída de cada sensor
ultimas_distancias = {0: "0.0", 1: "0.0"}

try:
    while True:
        lecturas = []

        for index, sensor in enumerate(sensores):
            if sensor is None:
                lecturas.append(f"S{index + 1}:ERR")
                continue

            try:
                # Actualizar el valor guardado únicamente cuando el sensor tenga datos listos
                if sensor.data_ready:
                    distancia = sensor.distance
                    if distancia is not None:
                        ultimas_distancias[index] = f"{distancia:.1f}"
                    else:
                        ultimas_distancias[index] = "ERR"
                    
                    sensor.clear_interrupt()

                # Siempre reportar la última distancia leída en lugar de N/A
                lecturas.append(f"S{index + 1}:{ultimas_distancias[index]}cm")

            except Exception as e:
                lecturas.append(f"S{index + 1}:ERR")

        # Crear mensaje delimitado
        mensaje = " | ".join(lecturas) + "\n"

        # Enviar por UART
        puerto_serial.write(mensaje.encode("utf-8"))

        # Mostrar en terminal
        print(f"Enviado: {mensaje.strip()}")

        time.sleep(0.05)

# ============================================================
# SALIDA LIMPIA AL INTERRUMPIR (CTRL+C)
# ============================================================
except KeyboardInterrupt:
    print("\nDeteniendo sensores...")

finally:
    # Detener mediciones en los sensores
    for sensor in sensores:
        if sensor is not None:
            try:
                sensor.stop_ranging()
            except:
                pass

    # Cerrar puerto serial
    try:
        puerto_serial.close()
    except:
        pass

    # Apagar y liberar pines XSHUT
    for pin in xshut:
        try:
            pin.off()
            pin.close()
        except:
            pass

    print("Programa terminado.")