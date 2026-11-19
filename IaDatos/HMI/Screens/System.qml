
import QtQuick
import QtQuick.Controls
import "../Components"

Rectangle {
    id: systemScreen

    property var navigator
    property int currentMenu: 5

    property real brightness: 100
    property string language: "ES"

    width: 1024
    height: 600
    color: "#070B12"

    Rectangle {
        x: 40
        y: 20
        width: 944
        height: 75
        radius: 22
        color: "#101925"

        Text {
            x: 24
            anchors.verticalCenter: parent.verticalCenter
            text: language === "ES" ? "CONFIGURACIÓN" : "SETTINGS"
            color: "#FFFFFF"
            font.pixelSize: 27
            font.bold: true
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            text: "● " + (language === "ES" ? "SISTEMA ACTIVO" : "SYSTEM ONLINE")
            color: "#00E676"
            font.pixelSize: 14
            font.bold: true
        }
    }

    Rectangle {
        x: 40
        y: 115
        width: 455
        height: 175
        radius: 22
        color: "#101925"
        border.color: "#203047"
        border.width: 1

        Text {
            x: 22
            y: 18
            text: "☼  " + (language === "ES" ? "Brillo de pantalla" : "Screen brightness")
            color: "#FFFFFF"
            font.pixelSize: 20
            font.bold: true
        }

        Text {
            x: 22
            y: 58
            text: language === "ES"
                  ? "Ajusta la intensidad visual de la interfaz"
                  : "Adjust the interface visual intensity"
            color: "#7187A5"
            font.pixelSize: 12
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 24
            y: 88
            text: Math.round(brightness) + "%"
            color: "#00E676"
            font.pixelSize: 24
            font.bold: true
        }

        Slider {
            id: brightnessSlider
            x: 22
            y: 112
            width: 410
            from: 20
            to: 100
            value: systemScreen.brightness

            onValueChanged: systemScreen.brightness = value

            background: Rectangle {
                x: brightnessSlider.leftPadding
                y: brightnessSlider.topPadding
                     + brightnessSlider.availableHeight / 2 - height / 2
                width: brightnessSlider.availableWidth
                height: 6
                radius: 3
                color: "#26364A"

                Rectangle {
                    width: brightnessSlider.visualPosition * parent.width
                    height: parent.height
                    radius: 3
                    color: "#00E676"
                }
            }

            handle: Rectangle {
                x: brightnessSlider.leftPadding
                   + brightnessSlider.visualPosition
                   * (brightnessSlider.availableWidth - width)
                y: brightnessSlider.topPadding
                   + brightnessSlider.availableHeight / 2 - height / 2
                width: 20
                height: 20
                radius: 10
                color: "#00E676"
                border.color: "#FFFFFF"
                border.width: 2
            }
        }
    }

    Rectangle {
        x: 515
        y: 115
        width: 469
        height: 175
        radius: 22
        color: "#101925"
        border.color: "#203047"
        border.width: 1

        Text {
            x: 22
            y: 18
            text: "文  " + (language === "ES" ? "Idioma" : "Language")
            color: "#FFFFFF"
            font.pixelSize: 20
            font.bold: true
        }

        Text {
            x: 22
            y: 58
            text: language === "ES"
                  ? "Selecciona el idioma de configuración"
                  : "Choose the settings language"
            color: "#7187A5"
            font.pixelSize: 12
        }

        Row {
            x: 22
            y: 94
            spacing: 15

            Repeater {
                model: [
                    { code: "ES", label: "ESPAÑOL" },
                    { code: "EN", label: "ENGLISH" }
                ]

                delegate: Rectangle {
                    width: 195
                    height: 52
                    radius: 14

                    color: systemScreen.language === modelData.code
                           ? "#173B2B" : "#172333"

                    border.color: systemScreen.language === modelData.code
                                  ? "#00E676" : "#26364A"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: (systemScreen.language === modelData.code ? "✓  " : "")
                              + modelData.label
                        color: systemScreen.language === modelData.code
                               ? "#00E676" : "#A8B8CC"
                        font.pixelSize: 14
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: systemScreen.language = modelData.code
                    }
                }
            }
        }
    }

    Rectangle {
        x: 40
        y: 310
        width: 290
        height: 150
        radius: 22
        color: "#101925"
        border.color: "#203047"
        border.width: 1

        Text {
            x: 20
            y: 18
            text: language === "ES" ? "ESTADO DEL SISTEMA" : "SYSTEM STATUS"
            color: "#FFFFFF"
            font.pixelSize: 15
            font.bold: true
        }

        Text {
            x: 20
            y: 58
            text: "●  " + (language === "ES" ? "Interfaz activa" : "Interface active")
            color: "#00E676"
            font.pixelSize: 14
        }

        Text {
            x: 20
            y: 88
            text: language === "ES" ? "Versión de interfaz: 1.0" : "Interface version: 1.0"
            color: "#7187A5"
            font.pixelSize: 12
        }
    }

    Rectangle {
        x: 350
        y: 310
        width: 290
        height: 150
        radius: 22
        color: "#101925"
        border.color: "#203047"
        border.width: 1

        Text {
            x: 20
            y: 18
            text: language === "ES" ? "APARIENCIA" : "APPEARANCE"
            color: "#FFFFFF"
            font.pixelSize: 15
            font.bold: true
        }

        Rectangle {
            x: 20
            y: 60
            width: 34
            height: 34
            radius: 10
            color: "#00E676"
        }

        Text {
            x: 65
            y: 60
            text: language === "ES" ? "Verde neón" : "Neon green"
            color: "#FFFFFF"
            font.pixelSize: 14
            font.bold: true
        }

        Text {
            x: 65
            y: 82
            text: "#00E676"
            color: "#7187A5"
            font.pixelSize: 12
        }

        Text {
            x: 20
            y: 112
            text: language === "ES" ? "Tema oscuro" : "Dark theme"
            color: "#7187A5"
            font.pixelSize: 12
        }
    }

    Rectangle {
        x: 660
        y: 310
        width: 324
        height: 150
        radius: 22
        color: "#101925"
        border.color: "#203047"
        border.width: 1

        Text {
            x: 20
            y: 18
            text: language === "ES" ? "CÁMARA" : "CAMERA"
            color: "#FFFFFF"
            font.pixelSize: 15
            font.bold: true
        }

        Text {
            x: 20
            y: 60
            text: "●  " + (typeof cameraController !== "undefined"
                           ? cameraController.status : "READY")
            color: "#00E676"
            font.pixelSize: 14
        }

        Text {
            x: 20
            y: 88
            text: language === "ES"
                  ? "Frecuencia de captura"
                  : "Capture frame rate"
            color: "#7187A5"
            font.pixelSize: 12
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 20
            y: 108
            text: (typeof cameraController !== "undefined"
                   ? cameraController.fps : 0) + " FPS"
            color: "#00E676"
            font.pixelSize: 18
            font.bold: true
        }
    }

    Rectangle {
        x: 40
        y: 480
        width: 944
        height: 1
        color: "#203047"
    }

    Text {
        x: 42
        y: 488
        text: language === "ES"
              ? "SMART CHAIR  •  CONFIGURACIÓN"
              : "SMART CHAIR  •  SETTINGS"
        color: "#526780"
        font.pixelSize: 10
    }

    BottomMenu {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 515
        selected: systemScreen.currentMenu
        navigator: systemScreen.navigator
    }

    Rectangle {
        anchors.fill: parent
        z: 1000
        color: "#000000"
        opacity: (100 - systemScreen.brightness) / 100
        visible: opacity > 0
    }
}
