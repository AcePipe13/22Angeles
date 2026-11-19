import tkinter as tk
import threading
import time

from Config4TOFVL531X import VL53L1X_4Sensores


# =========================================================
# SENSOR
# =========================================================

tof = VL53L1X_4Sensores()


# =========================================================
# VARIABLES
# =========================================================

distancias = [
    None,
    None,
    None,
    None
]

estados = [
    "INICIANDO",
    "INICIANDO",
    "INICIANDO",
    "INICIANDO"
]

ejecutando = True


# =========================================================
# DISTANCIAS
# =========================================================

CERCA = 30
MEDIO = 100


# =========================================================
# CLASIFICACIÓN
# =========================================================

def clasificar(distancia):

    if distancia is None:

        return "ESPERANDO"


    if distancia < CERCA:

        return "CERCA"


    elif distancia <= MEDIO:

        return "MEDIO"


    else:

        return "LEJOS"


# =========================================================
# ADQUISICIÓN
# =========================================================

def adquirir_datos():

    global distancias
    global estados


    while ejecutando:

        try:

            datos = tof.leer_todos()


            for i in range(4):

                if datos[i] is not None:

                    distancias[i] = datos[i]

                    estados[i] = clasificar(
                        datos[i]
                    )


        except Exception as e:

            print(
                "Error adquisición:",
                e
            )


        time.sleep(0.05)


# =========================================================
# VENTANA
# =========================================================

root = tk.Tk()

root.title(
    "Monitoreo - 4 VL53L1X"
)

root.geometry(
    "800x700"
)

root.resizable(
    False,
    False
)


# =========================================================
# TÍTULO
# =========================================================

titulo = tk.Label(
    root,
    text="MONITOREO VL53L1X",
    font=("Arial", 28, "bold")
)

titulo.pack(
    pady=20
)


subtitulo = tk.Label(
    root,
    text="4 sensores de distancia | I2C-0",
    font=("Arial", 14)
)

subtitulo.pack(
    pady=(0, 15)
)


# =========================================================
# FRAME
# =========================================================

frame_sensores = tk.Frame(
    root
)

frame_sensores.pack()


labels_distancia = []
labels_estado = []


# =========================================================
# CREAR LOS 4 PANELES
# =========================================================

for i in range(4):

    panel = tk.Frame(
        frame_sensores,
        width=340,
        height=220,
        relief="ridge",
        borderwidth=3
    )

    panel.grid(
        row=i // 2,
        column=i % 2,
        padx=15,
        pady=15
    )

    panel.grid_propagate(
        False
    )


    # -----------------------------------------------------
    # SENSOR
    # -----------------------------------------------------

    nombre = tk.Label(
        panel,
        text=f"SENSOR {i + 1}",
        font=("Arial", 20, "bold")
    )

    nombre.pack(
        pady=(15, 3)
    )


    # -----------------------------------------------------
    # DIRECCIÓN
    # -----------------------------------------------------

    direccion = tk.Label(
        panel,
        text=(
            f"I2C: "
            f"{hex(tof.DIRECCIONES[i])}"
        ),
        font=("Arial", 12)
    )

    direccion.pack()


    # -----------------------------------------------------
    # DISTANCIA
    # -----------------------------------------------------

    distancia = tk.Label(
        panel,
        text="--- cm",
        font=("Arial", 30, "bold")
    )

    distancia.pack(
        pady=10
    )

    labels_distancia.append(
        distancia
    )


    # -----------------------------------------------------
    # ESTADO
    # -----------------------------------------------------

    estado = tk.Label(
        panel,
        text="INICIANDO",
        font=("Arial", 20, "bold")
    )

    estado.pack()

    labels_estado.append(
        estado
    )


# =========================================================
# REFERENCIA
# =========================================================

referencia = tk.Label(
    root,
    text=(
        "CERCA < 30 cm   |   "
        "MEDIO 30-100 cm   |   "
        "LEJOS > 100 cm"
    ),
    font=("Arial", 12)
)

referencia.pack(
    pady=10
)


# =========================================================
# ACTUALIZAR INTERFAZ
# =========================================================

def actualizar():

    for i in range(4):

        distancia = distancias[i]

        estado = estados[i]


        # -----------------------------------------------
        # DISTANCIA
        # -----------------------------------------------

        if distancia is not None:

            labels_distancia[i].config(
                text=f"{distancia:.1f} cm"
            )


        # -----------------------------------------------
        # ESTADO
        # -----------------------------------------------

        labels_estado[i].config(
            text=estado
        )


        # -----------------------------------------------
        # COLOR
        # -----------------------------------------------

        if estado == "CERCA":

            labels_estado[i].config(
                fg="red"
            )


        elif estado == "MEDIO":

            labels_estado[i].config(
                fg="orange"
            )


        elif estado == "LEJOS":

            labels_estado[i].config(
                fg="green"
            )


        else:

            labels_estado[i].config(
                fg="black"
            )


    if ejecutando:

        root.after(
            100,
            actualizar
        )


# =========================================================
# HILO DE ADQUISICIÓN
# =========================================================

hilo = threading.Thread(
    target=adquirir_datos,
    daemon=True
)

hilo.start()


# =========================================================
# ACTUALIZAR GUI
# =========================================================

actualizar()


# =========================================================
# CERRAR
# =========================================================

def cerrar():

    global ejecutando

    ejecutando = False

    tof.cerrar()

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# =========================================================
# EJECUTAR
# =========================================================

root.mainloop()