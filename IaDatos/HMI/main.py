
import sys
import time
import threading
import signal
from pathlib import Path

from PySide6.QtCore import (
    QObject, Signal, Slot, Property, QThread, QTimer,
    QUrl, Qt
)
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QApplication


BASE_DIR = Path(__file__).resolve().parent
QML_FILE = BASE_DIR / "Main.qml"

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
TARGET_FPS = 60


class CameraImageProvider(QQuickImageProvider):

    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self._image = QImage()
        self._lock = threading.Lock()

    def update_image(self, image):
        with self._lock:
            self._image = image.copy()

    def requestImage(self, image_id, size, requested_size):
        with self._lock:
            image = self._image.copy()

        if image.isNull():
            return QImage()

        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())

        if requested_size.isValid():
            image = image.scaled(
                requested_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )

        return image


class CameraWorker(QThread):

    frame_ready = Signal(QImage)
    camera_error = Signal(str)

    def run(self):
        camera = None

        try:
            from picamera2 import Picamera2

            camera = Picamera2()

            config = camera.create_video_configuration(
                main={
                    "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
                    "format": "RGB888"
                },
                controls={
                    "FrameRate": float(TARGET_FPS)
                },
                buffer_count=4
            )

            camera.configure(config)
            camera.start()

            time.sleep(0.5)

            print(
                f"Cámara iniciada. Objetivo: {TARGET_FPS} FPS "
                f"({CAMERA_WIDTH}x{CAMERA_HEIGHT})"
            )

            while not self.isInterruptionRequested():
                frame = camera.capture_array("main")

                if frame is None:
                    continue

                height, width = frame.shape[:2]
                channels = frame.shape[2] if frame.ndim == 3 else 1

                if channels == 3:
                    image_format = QImage.Format.Format_BGR888
                elif channels == 4:
                    image_format = QImage.Format.Format_RGBX8888
                else:
                    raise ValueError(
                        f"Formato de imagen no compatible: {frame.shape}"
                    )

                image = QImage(
                    frame.data,
                    width,
                    height,
                    frame.strides[0],
                    image_format
                ).copy()

                self.frame_ready.emit(image)

        except Exception as error:
            self.camera_error.emit(str(error))

        finally:
            if camera is not None:
                try:
                    camera.stop()
                except Exception:
                    pass

                try:
                    camera.close()
                except Exception:
                    pass

            print("Captura de cámara finalizada.")


class CameraController(QObject):

    statusChanged = Signal()
    runningChanged = Signal()
    fpsChanged = Signal()
    frameChanged = Signal()

    def __init__(self, provider):
        super().__init__()

        self.provider = provider
        self.worker = None

        self._status = "READY"
        self._running = False
        self._fps = 0
        self._frame_count = 0
        self._closing = False

        self.fps_timer = QTimer(self)
        self.fps_timer.setInterval(1000)
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start()

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._running

    @Property(int, notify=fpsChanged)
    def fps(self):
        return self._fps

    def set_status(self, value):
        if self._status != value:
            self._status = value
            self.statusChanged.emit()

    def set_running(self, value):
        if self._running != value:
            self._running = value
            self.runningChanged.emit()

    @Slot()
    def startCamera(self):
        if self._closing:
            return

        if self.worker is not None and self.worker.isRunning():
            return

        self._frame_count = 0

        if self._fps != 0:
            self._fps = 0
            self.fpsChanged.emit()

        self.set_status("STARTING")
        self.set_running(True)

        self.worker = CameraWorker()
        self.worker.frame_ready.connect(self.on_frame)
        self.worker.camera_error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    @Slot()
    def stopCamera(self):
        if self.worker is not None and self.worker.isRunning():
            self.set_status("STOPPING")
            self.worker.requestInterruption()
        else:
            self.set_running(False)
            self.set_status("READY")

    @Slot(QImage)
    def on_frame(self, image):
        self.provider.update_image(image)
        self._frame_count += 1

        if self._status != "ONLINE":
            self.set_status("ONLINE")

        self.frameChanged.emit()

    @Slot(str)
    def on_error(self, message):
        print("ERROR DE CÁMARA:", message)
        self.set_status("CAMERA ERROR")

    @Slot()
    def on_finished(self):
        self.set_running(False)

        if self._status not in ("CAMERA ERROR", "READY"):
            self.set_status("READY")

    @Slot()
    def update_fps(self):
        measured_fps = self._frame_count
        self._frame_count = 0

        if measured_fps != self._fps:
            self._fps = measured_fps
            self.fpsChanged.emit()

    def shutdown(self):
        self._closing = True
        self.fps_timer.stop()

        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

        self.set_running(False)


def main():
    app = QApplication(sys.argv)

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: app.quit()
    )

    if not QML_FILE.exists():
        print(f"ERROR: No se encuentra el archivo: {QML_FILE}")
        return 1

    provider = CameraImageProvider()
    controller = CameraController(provider)
    engine = QQmlApplicationEngine()

    engine.addImageProvider("camera", provider)

    engine.rootContext().setContextProperty(
        "cameraController",
        controller
    )

    engine.load(QUrl.fromLocalFile(str(QML_FILE)))

    if not engine.rootObjects():
        print(f"ERROR: No se pudo cargar {QML_FILE}")
        controller.shutdown()
        return 1

    app.aboutToQuit.connect(controller.shutdown)

    app._camera_engine = engine
    app._camera_controller = controller
    app._camera_provider = provider

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
