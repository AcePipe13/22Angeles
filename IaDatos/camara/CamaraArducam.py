import tkinter as tk
from PIL import Image, ImageTk
from picamera2 import Picamera2
import time


# ==========================================================
# CONFIGURACIÓN DE LA CÁMARA
# ==========================================================

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (640, 480),
        "format": "RGB888"
    }
)

picam2.configure(config)

picam2.start()

# Esperar a que la cámara se inicialice
time.sleep(2)


# ==========================================================
# INTERFAZ
# ==========================================================

ventana = tk.Tk()

ventana.title("Arducam - Raspberry Pi 5")
ventana.geometry("700x580")
ventana.resizable(False, False)


titulo = tk.Label(
    ventana,
    text="CÁMARA ARDUCAM",
    font=("Arial", 24, "bold")
)

titulo.pack(pady=10)


# ==========================================================
# ÁREA DE VIDEO
# ==========================================================

label_video = tk.Label(ventana)

label_video.pack()


# ==========================================================
# ACTUALIZAR VIDEO
# ==========================================================

def actualizar_video():

    frame = picam2.capture_array()

    # Convertir imagen de NumPy a PIL
    imagen = Image.fromarray(frame)

    # Mostrar en Tkinter
    imagen_tk = ImageTk.PhotoImage(imagen)

    label_video.configure(image=imagen_tk)

    # Mantener referencia para evitar que Python la elimine
    label_video.image = imagen_tk

    # Actualizar aproximadamente cada 30 ms
    ventana.after(30, actualizar_video)


# ==========================================================
# CERRAR
# ==========================================================

def cerrar():

    picam2.stop()
    ventana.destroy()


boton_salir = tk.Button(
    ventana,
    text="SALIR",
    font=("Arial", 14, "bold"),
    command=cerrar
)

boton_salir.pack(pady=10)


# ==========================================================
# INICIAR
# ==========================================================

ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)

actualizar_video()

ventana.mainloop()