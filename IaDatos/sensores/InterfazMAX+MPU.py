import tkinter as tk
import math
import threading
import time

from LecturaMAX30102 import MAX30102
from LecturaMPU6050 import MPU6050
from Config4TOFVL531X import VL53L1X_4Sensores
from LecturaADCJoystick import ADS1115


# ==========================================================
# SENSORES
# ==========================================================

max_sensor = MAX30102()
mpu_sensor = MPU6050()
tof_sensor = VL53L1X_4Sensores()
joystick_sensor = ADS1115()


# ==========================================================
# VARIABLES TOF
# ==========================================================

distancias_tof = [None, None, None, None]


# ==========================================================
# VENTANA
# ==========================================================

root = tk.Tk()

root.title("Monitoreo")

root.geometry("1500x700")

root.resizable(False, False)


# ==========================================================
# TÍTULO
# ==========================================================

titulo = tk.Label(
    root,
    text="MONITOREO",
    font=("Arial", 30, "bold")
)

titulo.pack(pady=20)


# ==========================================================
# CONTENEDOR PRINCIPAL
# ==========================================================

contenedor = tk.Frame(root)

contenedor.pack(
    fill="both",
    expand=True,
    padx=20
)


# ==========================================================
# COLUMNAS
# ==========================================================

columna_bpm = tk.Frame(
    contenedor,
    width=340
)

columna_mpu = tk.Frame(
    contenedor,
    width=420
)

columna_tof = tk.Frame(
    contenedor,
    width=320
)

columna_joystick = tk.Frame(
    contenedor,
    width=340
)


columna_bpm.grid(
    row=0,
    column=0,
    padx=10,
    sticky="n"
)

columna_mpu.grid(
    row=0,
    column=1,
    padx=10,
    sticky="n"
)

columna_tof.grid(
    row=0,
    column=2,
    padx=10,
    sticky="n"
)

columna_joystick.grid(
    row=0,
    column=3,
    padx=10,
    sticky="n"
)


# ==========================================================
# FRECUENCIA CARDÍACA
# ==========================================================

cardio_titulo = tk.Label(
    columna_bpm,
    text="FRECUENCIA\nCARDÍACA",
    font=("Arial", 21, "bold")
)

cardio_titulo.pack(
    pady=10
)


bpm_label = tk.Label(
    columna_bpm,
    text="--",
    font=("Arial", 65, "bold")
)

bpm_label.pack(
    pady=10
)


bpm_unidad = tk.Label(
    columna_bpm,
    text="BPM",
    font=("Arial", 20)
)

bpm_unidad.pack()


bpm_estado = tk.Label(
    columna_bpm,
    text="Coloca el dedo\nsobre el sensor",
    font=("Arial", 15)
)

bpm_estado.pack(
    pady=25
)


bpm_indicador = tk.Label(
    columna_bpm,
    text="●",
    font=("Arial", 60),
    fg="gray"
)

bpm_indicador.pack(
    pady=10
)


# ==========================================================
# INCLINACIÓN
# ==========================================================

inclinacion_titulo = tk.Label(
    columna_mpu,
    text="INCLINACIÓN",
    font=("Arial", 21, "bold")
)

inclinacion_titulo.pack(
    pady=10
)


# ==========================================================
# BALANZA
# ==========================================================

canvas_balanza = tk.Canvas(
    columna_mpu,
    width=420,
    height=200,
    highlightthickness=0
)

canvas_balanza.pack(
    pady=5
)


# ==========================================================
# DIBUJAR BALANZA
# ==========================================================

def dibujar_balanza(angulo):

    canvas_balanza.delete("all")

    centro_x = 210
    centro_y = 85

    longitud = 170

    angulo_visual = max(
        -45,
        min(45, angulo)
    )

    rad = math.radians(
        angulo_visual
    )

    # Soporte
    canvas_balanza.create_line(
        centro_x,
        centro_y + 5,
        centro_x,
        centro_y + 75,
        width=5
    )

    # Base
    canvas_balanza.create_line(
        centro_x - 55,
        centro_y + 75,
        centro_x + 55,
        centro_y + 75,
        width=6
    )

    # Barra
    x1 = (
        centro_x
        - longitud * math.cos(rad)
    )

    y1 = (
        centro_y
        + longitud * math.sin(rad)
    )

    x2 = (
        centro_x
        + longitud * math.cos(rad)
    )

    y2 = (
        centro_y
        - longitud * math.sin(rad)
    )

    canvas_balanza.create_line(
        x1,
        y1,
        x2,
        y2,
        width=8
    )

    # Centro
    canvas_balanza.create_oval(
        centro_x - 10,
        centro_y - 10,
        centro_x + 10,
        centro_y + 10,
        fill="black"
    )

    # Izquierda
    canvas_balanza.create_oval(
        x1 - 10,
        y1 - 10,
        x1 + 10,
        y1 + 10,
        fill="black"
    )

    # Derecha
    canvas_balanza.create_oval(
        x2 - 10,
        y2 - 10,
        x2 + 10,
        y2 + 10,
        fill="black"
    )


dibujar_balanza(0)


# ==========================================================
# ÁNGULO X
# ==========================================================

angulo_label = tk.Label(
    columna_mpu,
    text="0.0°",
    font=("Arial", 45, "bold")
)

angulo_label.pack(
    pady=5
)


eje_label = tk.Label(
    columna_mpu,
    text="Eje X",
    font=("Arial", 16)
)

eje_label.pack()


# ==========================================================
# ÁNGULO Y
# ==========================================================

angulo_y_label = tk.Label(
    columna_mpu,
    text="Y: 0.0°",
    font=("Arial", 17)
)

angulo_y_label.pack(
    pady=15
)


# ==========================================================
# DISTANCIA - 4 TOF
# ==========================================================

distancia_titulo = tk.Label(
    columna_tof,
    text="DISTANCIA",
    font=("Arial", 21, "bold")
)

distancia_titulo.pack(
    pady=5
)


# ==========================================================
# FRAME DE LOS 4 SENSORES
# ==========================================================

frame_tof = tk.Frame(
    columna_tof
)

frame_tof.pack(
    pady=5
)


tof_widgets = []


direcciones_tof = [
    "0x30",
    "0x31",
    "0x32",
    "0x33"
]


for i in range(4):

    sensor_frame = tk.Frame(
        frame_tof,
        relief="groove",
        borderwidth=2,
        width=300,
        height=115
    )

    sensor_frame.pack(
        pady=4,
        fill="x"
    )

    sensor_frame.pack_propagate(False)

    # ------------------------------------------------------
    # Nombre
    # ------------------------------------------------------

    nombre = tk.Label(
        sensor_frame,
        text=f"TOF {i + 1}   ({direcciones_tof[i]})",
        font=("Arial", 14, "bold")
    )

    nombre.pack(
        pady=2
    )

    # ------------------------------------------------------
    # Distancia
    # ------------------------------------------------------

    distancia = tk.Label(
        sensor_frame,
        text="-- cm",
        font=("Arial", 22, "bold")
    )

    distancia.pack(
        side="left",
        padx=15
    )

    # ------------------------------------------------------
    # Estado
    # ------------------------------------------------------

    estado = tk.Label(
        sensor_frame,
        text="ESPERANDO",
        font=("Arial", 13, "bold"),
        width=9
    )

    estado.pack(
        side="right",
        padx=10
    )

    tof_widgets.append(
        {
            "distancia": distancia,
            "estado": estado
        }
    )


# ==========================================================
# RANGOS
# ==========================================================

rango_label = tk.Label(
    columna_tof,
    text="CERCA < 50 cm\n"
         "MEDIO 50 - 150 cm\n"
         "LEJOS > 150 cm",
    font=("Arial", 11),
    justify="left"
)

rango_label.pack(
    pady=5
)


# ==========================================================
# JOYSTICK
# ==========================================================

joystick_titulo = tk.Label(
    columna_joystick,
    text="JOYSTICK",
    font=("Arial", 21, "bold")
)

joystick_titulo.pack(
    pady=10
)


# ==========================================================
# CANVAS JOYSTICK
# ==========================================================

TAMANO = 280

canvas_joystick = tk.Canvas(
    columna_joystick,
    width=TAMANO,
    height=TAMANO,
    bg="white",
    highlightthickness=2
)

canvas_joystick.pack(
    pady=5
)


CX = TAMANO // 2
CY = TAMANO // 2


# Eje vertical
canvas_joystick.create_line(
    CX,
    0,
    CX,
    TAMANO,
    fill="gray",
    width=2
)


# Eje horizontal
canvas_joystick.create_line(
    0,
    CY,
    TAMANO,
    CY,
    fill="gray",
    width=2
)


# Círculo exterior
canvas_joystick.create_oval(
    20,
    20,
    TAMANO - 20,
    TAMANO - 20,
    outline="gray",
    width=3
)


# Centro
canvas_joystick.create_oval(
    CX - 8,
    CY - 8,
    CX + 8,
    CY + 8,
    fill="black"
)


# Punto
RADIO = 12

punto_joystick = canvas_joystick.create_oval(
    CX - RADIO,
    CY - RADIO,
    CX + RADIO,
    CY + RADIO,
    fill="blue"
)


# ==========================================================
# INFORMACIÓN JOYSTICK
# ==========================================================

valor_x = tk.Label(
    columna_joystick,
    text="X: 0.000 V",
    font=("Arial", 15)
)

valor_x.pack(
    pady=5
)


valor_y = tk.Label(
    columna_joystick,
    text="Y: 0.000 V",
    font=("Arial", 15)
)

valor_y.pack(
    pady=5
)


adc_x_label = tk.Label(
    columna_joystick,
    text="ADC X: 0",
    font=("Arial", 12)
)

adc_x_label.pack()


adc_y_label = tk.Label(
    columna_joystick,
    text="ADC Y: 0",
    font=("Arial", 12)
)

adc_y_label.pack()


# ==========================================================
# LECTURA DE LOS 4 TOF
# ==========================================================

def actualizar_tof():

    global distancias_tof

    try:

        nuevas_distancias = tof_sensor.leer_todos()

        if nuevas_distancias is not None:

            distancias_tof = nuevas_distancias

    except Exception as e:

        print(
            "Error TOF:",
            e
        )

    root.after(
        50,
        actualizar_tof
    )


# ==========================================================
# ACTUALIZAR INTERFAZ
# ==========================================================

def actualizar():

    try:

        # ==================================================
        # MAX30102
        # ==================================================

        bpm = max_sensor.update()

        if bpm > 0:

            bpm_label.config(
                text=f"{bpm:.0f}"
            )

            bpm_estado.config(
                text="Dedo detectado"
            )

            bpm_indicador.config(
                fg="red"
            )

        else:

            bpm_label.config(
                text="--"
            )

            bpm_estado.config(
                text="Calculando..."
            )

            bpm_indicador.config(
                fg="gray"
            )


        # ==================================================
        # MPU6050
        # ==================================================

        angle_x, angle_y = mpu_sensor.update()

        angulo_label.config(
            text=f"{angle_x:.1f}°"
        )

        angulo_y_label.config(
            text=f"Y: {angle_y:.1f}°"
        )

        dibujar_balanza(
            angle_x
        )


        # ==================================================
        # VL53L1X - 4 SENSORES
        # ==================================================

        for i in range(4):

            distancia = distancias_tof[i]

            widget = tof_widgets[i]

            if distancia is not None:

                widget["distancia"].config(
                    text=f"{distancia:.1f} cm"
                )

                # ------------------------------------------
                # CERCA
                # ------------------------------------------

                if distancia < 50:

                    widget["estado"].config(
                        text="CERCA",
                        bg="red",
                        fg="white"
                    )

                # ------------------------------------------
                # MEDIO
                # ------------------------------------------

                elif distancia < 150:

                    widget["estado"].config(
                        text="MEDIO",
                        bg="orange",
                        fg="black"
                    )

                # ------------------------------------------
                # LEJOS
                # ------------------------------------------

                else:

                    widget["estado"].config(
                        text="LEJOS",
                        bg="green",
                        fg="white"
                    )

            else:

                widget["distancia"].config(
                    text="-- cm"
                )

                widget["estado"].config(
                    text="SIN DATO",
                    bg="gray",
                    fg="white"
                )


        # ==================================================
        # ADS1115 / JOYSTICK
        # ==================================================

        x, y, adc_x, adc_y = joystick_sensor.update()


        # Valores
        valor_x.config(
            text=f"X: {x:.3f} V"
        )

        valor_y.config(
            text=f"Y: {y:.3f} V"
        )


        adc_x_label.config(
            text=f"ADC X: {adc_x}"
        )

        adc_y_label.config(
            text=f"ADC Y: {adc_y}"
        )


        # ==================================================
        # POSICIÓN DEL JOYSTICK
        # ==================================================

        # X invertido
        posicion_x = 1 - (x / 3.3)

        # Y normal
        posicion_y = y / 3.3


        # Limitar
        posicion_x = max(
            0,
            min(1, posicion_x)
        )

        posicion_y = max(
            0,
            min(1, posicion_y)
        )


        # ==================================================
        # COORDENADAS
        # ==================================================

        margen = 30

        px = (
            margen
            + posicion_x
            * (TAMANO - 2 * margen)
        )

        py = TAMANO - (
            margen
            + posicion_y
            * (TAMANO - 2 * margen)
        )


        # ==================================================
        # MOVER JOYSTICK
        # ==================================================

        canvas_joystick.coords(
            punto_joystick,
            px - RADIO,
            py - RADIO,
            px + RADIO,
            py + RADIO
        )


    except Exception as e:

        print(
            "Error:",
            e
        )


    # ======================================================
    # PRÓXIMA ACTUALIZACIÓN
    # ======================================================

    root.after(
        50,
        actualizar
    )


# ==========================================================
# CERRAR
# ==========================================================

def cerrar():

    try:
        tof_sensor.cerrar()
    except:
        pass

    try:
        joystick_sensor.close()
    except:
        pass

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# ==========================================================
# INICIAR
# ==========================================================

actualizar_tof()

actualizar()

root.mainloop()