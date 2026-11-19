from __future__ import annotations
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import serial
from serial.tools import list_ports

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# =====================================================
# CONFIGURACION DE LA PRUEBA
# =====================================================

BAUDIOS = 57600

# Deja None para seleccionar el puerto al ejecutar.
# Tambien puedes escribir, por ejemplo: PUERTO = "COM3"
PUERTO: Optional[str] = None

# Ambos motores reciben la misma magnitud:
#   +PWM_PRUEBA hacia adelante
#   -PWM_PRUEBA hacia atras
PWM_PRUEBA = 30.0

TIEMPO_REPOSO_INICIAL_S = 2.0
TIEMPO_ADELANTE_S = 3.0
TIEMPO_ATRAS_S = 3.0

# Antes de invertir el sentido se manda PWM = 0 y se comprueba
# con los encoders que ambos motores esten practicamente detenidos.
TIEMPO_MINIMO_PARADA_S = 1.0
TIEMPO_MAXIMO_PARADA_S = 5.0
UMBRAL_RPM_PARADA = 5.0
MUESTRAS_PARADA_CONSECUTIVAS = 3

INTERVALO_KEEP_S = 0.4

# Cambiar a True si se desea invertir inmediatamente sin esperar parada.
CAMBIO_DIRECCION_INSTANTANEO = True

TIMEOUT_RESPUESTA_S = 3.0

DIRECTORIO_DATOS = (
    Path(__file__).resolve().parent / "datos_caracterizacion"
)


def validar_configuracion() -> None:
    """Evita iniciar una prueba con parametros peligrosos o invalidos."""
    if not 0.0 < PWM_PRUEBA <= 100.0:
        raise ValueError("PWM_PRUEBA debe estar entre 0 y 100.")

    tiempos = [
        TIEMPO_REPOSO_INICIAL_S,
        TIEMPO_ADELANTE_S,
        TIEMPO_ATRAS_S,
        TIEMPO_MINIMO_PARADA_S,
        TIEMPO_MAXIMO_PARADA_S,
    ]

    if any(valor <= 0.0 for valor in tiempos):
        raise ValueError("Todos los tiempos deben ser mayores que cero.")

    if TIEMPO_MAXIMO_PARADA_S < TIEMPO_MINIMO_PARADA_S:
        raise ValueError(
            "TIEMPO_MAXIMO_PARADA_S no puede ser menor que "
            "TIEMPO_MINIMO_PARADA_S."
        )

    if UMBRAL_RPM_PARADA < 0.0:
        raise ValueError("UMBRAL_RPM_PARADA no puede ser negativo.")

    if MUESTRAS_PARADA_CONSECUTIVAS < 1:
        raise ValueError(
            "MUESTRAS_PARADA_CONSECUTIVAS debe ser al menos 1."
        )


def seleccionar_puerto() -> str:
    """Selecciona el puerto configurado o pregunta al usuario."""
    if PUERTO:
        return PUERTO

    puertos = list(list_ports.comports())

    if not puertos:
        raise RuntimeError(
            "No se encontraron puertos seriales. "
            "Conecta la ESP32 e intenta nuevamente."
        )

    print("\nPuertos seriales disponibles:")

    for indice, puerto in enumerate(puertos, start=1):
        descripcion = puerto.description or "Sin descripcion"
        print(f"  {indice}. {puerto.device} - {descripcion}")

    while True:
        respuesta = input("\nSelecciona el numero del puerto: ").strip()

        try:
            seleccion = int(respuesta)
        except ValueError:
            print("Escribe un numero valido.")
            continue

        if 1 <= seleccion <= len(puertos):
            return puertos[seleccion - 1].device

        print("Seleccion fuera de rango.")


def enviar(ser: serial.Serial, comando: str) -> None:
    """Envia una linea completa a la ESP32."""
    ser.write((comando + "\n").encode("ascii"))
    ser.flush()


def leer_linea(ser: serial.Serial) -> str:
    """Lee una linea sin fallar por caracteres incompletos."""
    datos = ser.readline()

    if not datos:
        return ""

    return datos.decode("utf-8", errors="replace").strip()


def esperar_respuesta(
    ser: serial.Serial,
    prefijo: str,
    timeout_s: float = TIMEOUT_RESPUESTA_S,
) -> str:
    """Espera una respuesta determinada de la ESP32."""
    limite = time.monotonic() + timeout_s

    while time.monotonic() < limite:
        linea = leer_linea(ser)

        if not linea:
            continue

        if linea.startswith("ERR,"):
            raise RuntimeError(f"ESP32 respondio: {linea}")

        if linea.startswith(prefijo):
            return linea

    raise TimeoutError(
        f"No se recibio la respuesta esperada: {prefijo}"
    )


def comprobar_comunicacion(ser: serial.Serial) -> None:
    """Comprueba que la ESP32 tenga el firmware correcto."""
    ser.reset_input_buffer()
    enviar(ser, "PING")
    respuesta = esperar_respuesta(ser, "ACK,PONG")
    print(f"Comunicacion confirmada: {respuesta}")


def interpretar_data(linea: str) -> Optional[dict]:
    """Convierte una linea DATA de la ESP32 en un registro."""
    if not linea.startswith("DATA,"):
        return None

    partes = linea.split(",")

    if len(partes) != 8:
        return None

    try:
        tiempo_us = int(partes[1])

        return {
            "tiempo_us": tiempo_us,
            "tiempo_s": tiempo_us / 1_000_000.0,
            "duty_izquierdo": float(partes[2]),
            "cuentas_izquierdo": int(partes[3]),
            "rpm_izquierdo": float(partes[4]),
            "duty_derecho": float(partes[5]),
            "cuentas_derecho": int(partes[6]),
            "rpm_derecho": float(partes[7]),
        }
    except ValueError:
        return None


def agregar_registro(
    registros: list[dict],
    registro: dict,
    numero_etapa: int,
    etapa: str,
) -> None:
    """Agrega la etapa de la rutina a una muestra de la ESP32."""
    registro["numero_etapa"] = numero_etapa
    registro["etapa"] = etapa
    registros.append(registro)


def procesar_linea(
    linea: str,
    registros: list[dict],
    numero_etapa: int,
    etapa: str,
) -> Optional[dict]:
    """Valida una linea y guarda su muestra si contiene telemetria."""
    if linea.startswith("ERR,"):
        raise RuntimeError(f"ESP32 respondio: {linea}")

    registro = interpretar_data(linea)

    if registro is not None:
        agregar_registro(
            registros,
            registro,
            numero_etapa,
            etapa,
        )

    return registro


def cambiar_pwm(
    ser: serial.Serial,
    duty_izquierdo: float,
    duty_derecho: float,
    registros: list[dict],
    numero_etapa_anterior: int,
    etapa_anterior: str,
) -> None:
    """Cambia el PWM y espera confirmacion sin perder muestras previas."""
    enviar(
        ser,
        f"PWM,{duty_izquierdo:.3f},{duty_derecho:.3f}",
    )

    limite = time.monotonic() + TIMEOUT_RESPUESTA_S

    while time.monotonic() < limite:
        linea = leer_linea(ser)

        if not linea:
            continue

        if linea.startswith("ACK,PWM,"):
            return

        procesar_linea(
            linea,
            registros,
            numero_etapa_anterior,
            etapa_anterior,
        )

    raise TimeoutError("La ESP32 no confirmo el nuevo valor de PWM.")


def capturar_durante(
    ser: serial.Serial,
    duracion_s: float,
    registros: list[dict],
    numero_etapa: int,
    etapa: str,
) -> None:
    """Captura datos durante un tiempo manteniendo vivo el enlace."""
    inicio = time.monotonic()
    ultimo_keep = inicio

    while time.monotonic() - inicio < duracion_s:
        ahora = time.monotonic()

        if ahora - ultimo_keep >= INTERVALO_KEEP_S:
            enviar(ser, "KEEP")
            ultimo_keep = ahora

        linea = leer_linea(ser)

        if linea:
            procesar_linea(
                linea,
                registros,
                numero_etapa,
                etapa,
            )


def esperar_detencion(
    ser: serial.Serial,
    registros: list[dict],
    numero_etapa: int,
    etapa: str,
) -> bool:
    """Espera hasta confirmar por encoder que ambos motores se detuvieron."""
    inicio = time.monotonic()
    ultimo_keep = inicio
    muestras_detenidas = 0

    while time.monotonic() - inicio < TIEMPO_MAXIMO_PARADA_S:
        ahora = time.monotonic()
        tiempo_parada = ahora - inicio

        if ahora - ultimo_keep >= INTERVALO_KEEP_S:
            enviar(ser, "KEEP")
            ultimo_keep = ahora

        linea = leer_linea(ser)

        if not linea:
            continue

        registro = procesar_linea(
            linea,
            registros,
            numero_etapa,
            etapa,
        )

        if registro is None:
            continue

        motores_detenidos = (
            abs(registro["rpm_izquierdo"]) <= UMBRAL_RPM_PARADA
            and abs(registro["rpm_derecho"]) <= UMBRAL_RPM_PARADA
        )

        if (
            tiempo_parada >= TIEMPO_MINIMO_PARADA_S
            and motores_detenidos
        ):
            muestras_detenidas += 1
        else:
            muestras_detenidas = 0

        if muestras_detenidas >= MUESTRAS_PARADA_CONSECUTIVAS:
            print(
                f"  Detencion confirmada en {tiempo_parada:.2f} s "
                f"(|RPM| <= {UMBRAL_RPM_PARADA:g})."
            )
            return True

    return False


def guardar_csv(
    registros: list[dict],
    ruta_pwm: Path,
    ruta_rpm_izq: Path,
    ruta_rpm_der: Path,
) -> None:
    """Genera tres archivos CSV para MATLAB System Identification.

    PWM.csv -> entrada u(t)
    RPM_IZQUIERDO.csv -> salida motor izquierdo
    RPM_DERECHO.csv -> salida motor derecho
    """
    ruta_pwm.parent.mkdir(parents=True, exist_ok=True)

    with ruta_pwm.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=["tiempo_s", "PWM"],
        )
        escritor.writeheader()

        for fila in registros:
            escritor.writerow({
                "tiempo_s": fila["tiempo_s"],
                "PWM": fila["duty_izquierdo"],
            })

    with ruta_rpm_izq.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=["tiempo_s", "RPM"],
        )
        escritor.writeheader()

        for fila in registros:
            escritor.writerow({
                "tiempo_s": fila["tiempo_s"],
                "RPM": fila["rpm_izquierdo"],
            })

    with ruta_rpm_der.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=["tiempo_s", "RPM"],
        )
        escritor.writeheader()

        for fila in registros:
            escritor.writerow({
                "tiempo_s": fila["tiempo_s"],
                "RPM": fila["rpm_derecho"],
            })


def guardar_grafica(registros: list[dict], ruta: Path) -> None:
    """Genera una grafica de duty y velocidad si matplotlib esta instalado."""
    if plt is None or not registros:
        return

    tiempo = [fila["tiempo_s"] for fila in registros]
    duty_izquierdo = [
        fila["duty_izquierdo"] for fila in registros
    ]
    duty_derecho = [
        fila["duty_derecho"] for fila in registros
    ]
    rpm_izquierdo = [
        fila["rpm_izquierdo"] for fila in registros
    ]
    rpm_derecho = [
        fila["rpm_derecho"] for fila in registros
    ]

    figura, ejes = plt.subplots(
        2,
        1,
        figsize=(10, 7),
        sharex=True,
    )

    ejes[0].step(
        tiempo,
        duty_izquierdo,
        where="post",
        label="Duty izquierdo",
    )
    ejes[0].step(
        tiempo,
        duty_derecho,
        where="post",
        label="Duty derecho",
    )
    ejes[0].set_ylabel("Duty (%)")
    ejes[0].grid(True)
    ejes[0].legend()

    ejes[1].plot(
        tiempo,
        rpm_izquierdo,
        label="RPM izquierdo",
    )
    ejes[1].plot(
        tiempo,
        rpm_derecho,
        label="RPM derecho",
    )
    ejes[1].axhline(0.0, color="black", linewidth=0.8)
    ejes[1].set_xlabel("Tiempo de la ESP32 (s)")
    ejes[1].set_ylabel("Velocidad (RPM)")
    ejes[1].grid(True)
    ejes[1].legend()

    figura.suptitle(
        "Ambos motores: mismo PWM hacia adelante y hacia atras"
    )
    figura.tight_layout()
    figura.savefig(ruta, dpi=150)
    plt.close(figura)


def ejecutar_rutina(
    ser: serial.Serial,
) -> tuple[list[dict], bool]:
    """Ejecuta adelante, parada comprobada y atras en una captura."""
    registros: list[dict] = []
    rutina_completa = False

    # Reinicio seguro antes de iniciar la caracterizacion
    enviar(ser, "RESET")
    esperar_respuesta(ser, "ACK,RESET")

    time.sleep(1.0)

    enviar(ser, "START")
    esperar_respuesta(ser, "ACK,START")

    numero_etapa = 1
    etapa = "reposo_inicial"

    try:
        print(
            f"\nEtapa 1: reposo inicial durante "
            f"{TIEMPO_REPOSO_INICIAL_S:.1f} s."
        )
        capturar_durante(
            ser,
            TIEMPO_REPOSO_INICIAL_S,
            registros,
            numero_etapa,
            etapa,
        )

        cambiar_pwm(
            ser,
            PWM_PRUEBA,
            PWM_PRUEBA,
            registros,
            numero_etapa,
            etapa,
        )
        numero_etapa = 2
        etapa = "adelante"
        print(
            f"Etapa 2: ambos motores al +{PWM_PRUEBA:g} % "
            f"durante {TIEMPO_ADELANTE_S:.1f} s."
        )
        capturar_durante(
            ser,
            TIEMPO_ADELANTE_S,
            registros,
            numero_etapa,
            etapa,
        )

        cambiar_pwm(
            ser,
            0.0,
            0.0,
            registros,
            numero_etapa,
            etapa,
        )
        numero_etapa = 3
        etapa = "parada_antes_de_invertir"
        print("Etapa 3: PWM 0 %, esperando que ambos se detengan.")

        if not CAMBIO_DIRECCION_INSTANTANEO:
            if not esperar_detencion(
                ser,
                registros,
                numero_etapa,
                etapa,
            ):
                print(
                    "  SEGURIDAD: no se confirmo la detencion. "
                    "No se aplicara el movimiento hacia atras."
                )
                return registros, False

        else:
            print("  Cambio de direccion inmediato habilitado.")

        cambiar_pwm(
            ser,
            -PWM_PRUEBA,
            -PWM_PRUEBA,
            registros,
            numero_etapa,
            etapa,
        )
        numero_etapa = 4
        etapa = "atras"
        print(
            f"Etapa 4: ambos motores al -{PWM_PRUEBA:g} % "
            f"durante {TIEMPO_ATRAS_S:.1f} s."
        )
        capturar_durante(
            ser,
            TIEMPO_ATRAS_S,
            registros,
            numero_etapa,
            etapa,
        )

        cambiar_pwm(
            ser,
            0.0,
            0.0,
            registros,
            numero_etapa,
            etapa,
        )
        numero_etapa = 5
        etapa = "reposo_final"
        print("Etapa 5: PWM 0 %, esperando la detencion final.")

        rutina_completa = esperar_detencion(
            ser,
            registros,
            numero_etapa,
            etapa,
        )

        if not rutina_completa:
            print(
                "  Advertencia: no se confirmo la detencion final "
                "dentro del tiempo maximo."
            )

        return registros, rutina_completa
    finally:
        enviar(ser, "STOP")

        try:
            esperar_respuesta(ser, "ACK,STOP", timeout_s=1.5)
        except (TimeoutError, RuntimeError):
            pass


def mostrar_rutina() -> None:
    """Muestra exactamente lo que se enviara a los motores."""
    print("\nRutina programada:")
    print(
        f"  1. Reposo inicial: 0 % durante "
        f"{TIEMPO_REPOSO_INICIAL_S:.1f} s"
    )
    print(
        f"  2. Adelante: ambos motores a +{PWM_PRUEBA:g} % "
        f"durante {TIEMPO_ADELANTE_S:.1f} s"
    )
    print(
        "  3. Parada: 0 % hasta confirmar velocidad cercana a cero"
    )
    print(
        f"  4. Atras: ambos motores a -{PWM_PRUEBA:g} % "
        f"durante {TIEMPO_ATRAS_S:.1f} s"
    )
    print(
        "  5. Parada final: 0 % hasta confirmar velocidad cercana a cero"
    )


def main() -> int:
    validar_configuracion()
    puerto = seleccionar_puerto()
    mostrar_rutina()

    print(
        "\nLos motores tienen velocidades nominales diferentes, por lo que "
        "el mismo PWM no producira las mismas RPM."
    )
    print(
        "Levanta las ruedas o deja libres los ejes y mantente listo "
        "para desconectar la alimentacion."
    )

    confirmacion = input(
        "Escribe INICIAR para ejecutar la rutina: "
    ).strip()

    if confirmacion != "INICIAR":
        print("Rutina cancelada.")
        return 0

    DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)

    print(f"\nAbriendo {puerto} a {BAUDIOS} baudios...")

    with serial.Serial(
        puerto,
        BAUDIOS,
        timeout=0.05,
        write_timeout=1.0,
    ) as ser:


        time.sleep(4)

        ser.reset_input_buffer()
        ser.reset_output_buffer()

        comprobar_comunicacion(ser)

        try:
            registros, rutina_completa = ejecutar_rutina(ser)
        except KeyboardInterrupt:
            print("\nInterrupcion solicitada. Deteniendo motores...")
            enviar(ser, "STOP")
            return 1
        except Exception:
            enviar(ser, "STOP")
            raise

    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = (
        f"{marca_tiempo}_ambos_adelante_atras_"
        f"pwm_{PWM_PRUEBA:g}"
    )

    ruta_pwm = DIRECTORIO_DATOS / f"{nombre_base}_PWM.csv"
    ruta_rpm_izq = DIRECTORIO_DATOS / f"{nombre_base}_RPM_IZQUIERDO.csv"
    ruta_rpm_der = DIRECTORIO_DATOS / f"{nombre_base}_RPM_DERECHO.csv"
    ruta_rpm = DIRECTORIO_DATOS / f"{nombre_base}_VELOCIDAD.csv"
    ruta_png = DIRECTORIO_DATOS / f"{nombre_base}.png"

    guardar_csv(
        registros,
        ruta_pwm,
        ruta_rpm_izq,
        ruta_rpm_der,
    )
    guardar_grafica(registros, ruta_png)

    print(
        f"\n{len(registros)} muestras guardadas en:"
        f"\n  PWM: {ruta_pwm}"
        f"\n  Velocidad: {ruta_rpm}"
    )

    if plt is not None:
        print(f"Grafica guardada en:\n  {ruta_png}")
    else:
        print(
            "No se genero grafica porque matplotlib no esta instalado."
        )

    if not rutina_completa:
        print(
            "Rutina terminada antes de completar todas las etapas "
            "por seguridad. Los datos obtenidos si fueron guardados."
        )
        return 1

    print("Rutina terminada correctamente.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except serial.SerialException as error:
        print(f"Error serial: {error}", file=sys.stderr)
        raise SystemExit(1)
    except (RuntimeError, TimeoutError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
