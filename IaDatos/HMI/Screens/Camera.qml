
import QtQuick
import "../Components"

Rectangle {
    id: camera

    property var navigator
    property int currentMenu: 1
    property int frameRefresh: 0

    width: 1024
    height: 600
    color: "#070B12"

    Timer {
        interval: 16
        running: cameraController.status === "ONLINE"
        repeat: true
        onTriggered: camera.frameRefresh += 1
    }

    Rectangle {
        width: 944
        height: 80
        x: 40
        y: 20
        radius: 25
        color: "#101925"

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 10
            text: "CAMERA SYSTEM"
            color: "#FFFFFF"
            font.pixelSize: 34
            font.bold: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 52
            text: "INTELLIGENT VISION MODULE"
            color: "#7187A5"
            font.pixelSize: 11
        }

        Rectangle {
            width: 150
            height: 42
            x: 20
            y: 19
            radius: 21
            color: cameraController.status === "ONLINE"
                   ? "#083521" : "#302B20"

            Text {
                anchors.centerIn: parent
                text: cameraController.status === "ONLINE"
                      ? "● ACTIVE" : "● STANDBY"
                color: cameraController.status === "ONLINE"
                       ? "#00E676" : "#F2B95D"
                font.bold: true
                font.pixelSize: 16
            }
        }

        Rectangle {
            width: 150
            height: 42
            anchors.right: parent.right
            anchors.rightMargin: 20
            y: 19
            radius: 21
            color: "#17283A"

            Text {
                anchors.centerIn: parent
                text: "AI VISION"
                color: "#8EA1BB"
                font.bold: true
                font.pixelSize: 15
            }
        }
    }

    Rectangle {
        id: videoPanel
        x: 110
        y: 135
        width: 440
        height: 310
        radius: 28
        color: "#101925"
        border.color: "#26384D"
        border.width: 2
        clip: true

        Rectangle {
            id: videoBackground
            anchors.fill: parent
            anchors.margins: 12
            radius: 20
            color: "#070B12"
            clip: true

            Image {
                id: liveCamera
                anchors.fill: parent
                anchors.margins: 2

                source: cameraController.status === "ONLINE"
                        ? "image://camera/live?frame=" + camera.frameRefresh
                        : ""

                cache: false
                asynchronous: false
                fillMode: Image.PreserveAspectFit
                smooth: false
                visible: cameraController.status === "ONLINE"

                onStatusChanged: {
                    if (status === Image.Error)
                        console.log("No se pudo cargar la imagen:", source)
                }
            }

            Column {
                anchors.centerIn: parent
                spacing: 15
                visible: cameraController.status !== "ONLINE"

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: cameraController.status === "CAMERA ERROR"
                          ? "CAMERA ERROR"
                          : cameraController.status === "STARTING"
                            ? "STARTING CAMERA"
                            : cameraController.status === "STOPPING"
                              ? "STOPPING CAMERA"
                              : "LIVE CAMERA"

                    color: cameraController.status === "CAMERA ERROR"
                           ? "#FF5252" : "#7187A5"
                    font.pixelSize: 30
                    font.bold: true
                }

                Rectangle {
                    width: 80
                    height: 3
                    color: "#00E676"
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: cameraController.status === "CAMERA ERROR"
                          ? "CHECK CAMERA CONNECTION"
                          : cameraController.status === "STARTING"
                            ? "INITIALIZING VIDEO..."
                            : "WAITING SIGNAL"

                    color: cameraController.status === "CAMERA ERROR"
                           ? "#FF5252" : "#00E676"
                    font.pixelSize: 13
                }
            }
        }
    }

    Rectangle {
        x: 630
        y: 135
        width: 240
        height: 310
        radius: 28
        color: "#101925"

        Column {
            anchors.fill: parent
            anchors.margins: 25
            spacing: 18

            Text {
                text: "VISION STATUS"
                color: "#8EA1BB"
                font.pixelSize: 17
                font.bold: true
            }

            Text {
                text: cameraController.status
                color: cameraController.status === "ONLINE"
                       ? "#00E676"
                       : cameraController.status === "CAMERA ERROR"
                         ? "#FF5252" : "#F2B95D"
                font.pixelSize: 24
                font.bold: true
            }

            Rectangle {
                width: 185
                height: 1
                color: "#26384D"
            }

            Text {
                text: cameraController.status === "ONLINE"
                      ? "● CAMERA ONLINE"
                      : "● CAMERA OFFLINE"
                color: cameraController.status === "ONLINE"
                       ? "#00E676" : "#F2B95D"
                font.pixelSize: 15
            }

            Text {
                text: "FPS        " + cameraController.fps
                color: "white"
                font.pixelSize: 18
            }

            Text {
                text: "OBJECTS     0"
                color: "#8EA1BB"
                font.pixelSize: 18
            }

            Text {
                text: "DISTANCE   1.0 m"
                color: "#8EA1BB"
                font.pixelSize: 18
            }
        }
    }

    Rectangle {
        width: 240
        height: 50
        anchors.horizontalCenter: parent.horizontalCenter
        y: 455
        radius: 25
        color: "#101925"

        border.color: cameraController.running
                      ? "#FF5252" : "#00E676"
        border.width: 1

        Text {
            anchors.centerIn: parent
            text: cameraController.running
                  ? "■  STOP CAMERA"
                  : "▶  START CAMERA"
            color: cameraController.running
                   ? "#FF5252" : "#00E676"
            font.pixelSize: 17
            font.bold: true
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor

            onClicked: {
                if (cameraController.running)
                    cameraController.stopCamera()
                else
                    cameraController.startCamera()
            }
        }
    }

    BottomMenu {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 515
        selected: camera.currentMenu
        navigator: camera.navigator
    }
}
