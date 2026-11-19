
import tkinter as tk


from LecturaADCJoystick0 import ADS1115


# =========================================================
# CONFIGURACIÓN
# =========================================================

ANCHO_CANVAS = 500
ALTO_CANVAS = 500

CENTRO_X = ANCHO_CANVAS // 2
CENTRO_Y = ALTO_CANVAS // 2

RADIO_JOYSTICK = 190
RADIO_PUNTO = 14


# =========================================================
# CREAR SENSOR
# =========================================================

joystick = ADS1115()


# =========================================================
# VENTANA
# =========================================================

ventana = tk.Tk()

ventana.title("CONTROL DE JOYSTICK")

ventana.geometry("700x850")

ventana.resizable(False, False)


# =========================================================
# TÍTULO
# =========================================================

titulo = tk.Label(
    ventana,
    text="CONTROL DE JOYSTICK",
    font=("Arial", 26, "bold")
)

titulo.pack(pady=(15, 10))


# =========================================================
# CANVAS
# =========================================================

canvas = tk.Canvas(
    ventana,
    width=ANCHO_CANVAS,
    height=ALTO_CANVAS,
    bg="white",
    highlightthickness=0
)

canvas.pack()


# =========================================================
# CÍRCULO PRINCIPAL
# =========================================================

canvas.create_oval(
    CENTRO_X - RADIO_JOYSTICK,
    CENTRO_Y - RADIO_JOYSTICK,
    CENTRO_X + RADIO_JOYSTICK,
    CENTRO_Y + RADIO_JOYSTICK,
    outline="black",
    width=3
)


# =========================================================
# EJES
# =========================================================

canvas.create_line(
    CENTRO_X - RADIO_JOYSTICK,
    CENTRO_Y,
    CENTRO_X + RADIO_JOYSTICK,
    CENTRO_Y,
    fill="gray",
    width=2
)

canvas.create_line(
    CENTRO_X,
    CENTRO_Y - RADIO_JOYSTICK,
    CENTRO_X,
    CENTRO_Y + RADIO_JOYSTICK,
    fill="gray",
    width=2
)


# =========================================================
# ETIQUETAS DE EJES
# =========================================================

canvas.create_text(
    CENTRO_X + RADIO_JOYSTICK - 5,
    CENTRO_Y - 15,
    text="X+",
    font=("Arial", 12, "bold")
)

canvas.create_text(
    CENTRO_X - RADIO_JOYSTICK + 5,
    CENTRO_Y - 15,
    text="X-",
    font=("Arial", 12, "bold")
)

canvas.create_text(
    CENTRO_X + 15,
    CENTRO_Y - RADIO_JOYSTICK + 5,
    text="Y+",
    font=("Arial", 12, "bold")
)

canvas.create_text(
    CENTRO_X + 15,
    CENTRO_Y + RADIO_JOYSTICK - 5,
    text="Y-",
    font=("Arial", 12, "bold")
)


# =========================================================
# CENTRO
# =========================================================

canvas.create_oval(
    CENTRO_X - 5,
    CENTRO_Y - 5,
    CENTRO_X + 5,
    CENTRO_Y + 5,
    fill="black"
)


# =========================================================
# PUNTO DEL JOYSTICK
# =========================================================

punto = canvas.create_oval(
    CENTRO_X - RADIO_PUNTO,
    CENTRO_Y - RADIO_PUNTO,
    CENTRO_X + RADIO_PUNTO,
    CENTRO_Y + RADIO_PUNTO,
    fill="red",
    outline="black",
    width=2
)


# =========================================================
# INFORMACIÓN
# =========================================================

frame_info = tk.Frame(ventana)

frame_info.pack(pady=10)


# ---------------------------------------------------------
# X
# ---------------------------------------------------------

label_x = tk.Label(
    frame_info,
    text="X: 0.000 V",
    font=("Arial", 16, "bold")
)

label_x.grid(
    row=0,
    column=0,
    padx=25
)


# ---------------------------------------------------------
# Y
# ---------------------------------------------------------

label_y = tk.Label(
    frame_info,
    text="Y: 0.000 V",
    font=("Arial", 16, "bold")
)

label_y.grid(
    row=0,
    column=1,
    padx=25
)


# ---------------------------------------------------------
# ADC X
# ---------------------------------------------------------

label_adc_x = tk.Label(
    frame_info,
    text="ADC X: 0",
    font=("Arial", 13)
)

label_adc_x.grid(
    row=1,
    column=0,
    padx=25,
    pady=5
)


# ---------------------------------------------------------
# ADC Y
# ---------------------------------------------------------

label_adc_y = tk.Label(
    frame_info,
    text="ADC Y: 0",
    font=("Arial", 13)
)

label_adc_y.grid(
    row=1,
    column=1,
    padx=25,
    pady=5
)


# =========================================================
# ESTADO
# =========================================================

label_estado = tk.Label(
    ventana,
    text="CENTRO",
    font=("Arial", 18, "bold")
)

label_estado.pack(pady=5)


# =========================================================
# ACTUALIZAR
# =========================================================

def actualizar():

    try:

        # -------------------------------------------------
        # Leer joystick
        # -------------------------------------------------

        x, y, adc_x, adc_y = joystick.update()


        # -------------------------------------------------
        # Mostrar datos
        # -------------------------------------------------

        label_x.config(
            text=f"X: {x:.3f} V"
        )

        label_y.config(
            text=f"Y: {y:.3f} V"
        )

        label_adc_x.config(
            text=f"ADC X: {adc_x}"
        )

        label_adc_y.config(
            text=f"ADC Y: {adc_y}"
        )


        # -------------------------------------------------
        # Conversión de voltaje a posición
        # -------------------------------------------------

        # ADS1115 gain = 1
        #
        # Rango aproximado utilizado:
        #
        # 0 V    -> -1
        # 2.048 V -> 0
        # 4.096 V -> +1

        CENTRO_V = 2.048
        RANGO_V = 2.048


        posicion_x = (
            (x - CENTRO_V)
            / RANGO_V
        )

        posicion_y = (
            (y - CENTRO_V)
            / RANGO_V
        )


        # -------------------------------------------------
        # Limitar rango
        # -------------------------------------------------

        posicion_x = max(
            -1,
            min(1, posicion_x)
        )

        posicion_y = max(
            -1,
            min(1, posicion_y)
        )


        # -------------------------------------------------
        # Coordenadas gráficas
        # -------------------------------------------------

        pantalla_x = (
            CENTRO_X
            + posicion_x * RADIO_JOYSTICK
        )

        pantalla_y = (
            CENTRO_Y
            - posicion_y * RADIO_JOYSTICK
        )


        # -------------------------------------------------
        # Mover punto
        # -------------------------------------------------

        canvas.coords(
            punto,

            pantalla_x - RADIO_PUNTO,
            pantalla_y - RADIO_PUNTO,

            pantalla_x + RADIO_PUNTO,
            pantalla_y + RADIO_PUNTO
        )


        # -------------------------------------------------
        # Determinar estado
        # -------------------------------------------------

        umbral = 0.15

        if (
            abs(posicion_x) < umbral
            and
            abs(posicion_y) < umbral
        ):

            estado = "CENTRO"

        elif abs(posicion_x) >= abs(posicion_y):

            if posicion_x > 0:
                estado = "DERECHA"
            else:
                estado = "IZQUIERDA"

        else:

            if posicion_y > 0:
                estado = "ARRIBA"
            else:
                estado = "ABAJO"


        label_estado.config(
            text=estado
        )


    except Exception as e:

        label_estado.config(
            text="ERROR"
        )

        print("Error:", e)


    # -----------------------------------------------------
    # Actualizar nuevamente
    # -----------------------------------------------------

    ventana.after(
        50,
        actualizar
    )


# =========================================================
# CERRAR
# =========================================================

def cerrar():

    try:
        joystick.close()
    except:
        pass

    ventana.destroy()


ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# =========================================================
# INICIAR
# =========================================================

actualizar()

ventana.mainloop()
