
import QtQuick
import "../Components"

Rectangle {
    id: joystick

    property var navigator

    width: 1024
    height: 600
    color: "#070B12"

    Rectangle {
        width: 944
        height: 75
        x: 40
        y: 20
        radius: 22
        color: "#101925"

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 15
            text: "JOYSTICK CONTROL"
            color: "#FFFFFF"
            font.pixelSize: 32
            font.bold: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 50
            text: "ELECTRIC MOBILITY CONTROL"
            color: "#7187A5"
            font.pixelSize: 10
        }

        Rectangle {
            width: 150
            height: 40
            anchors.right: parent.right
            anchors.rightMargin: 20
            y: 18
            radius: 20
            color: "#083521"

            Text {
                anchors.centerIn: parent
                text: "● ONLINE"
                color: "#00E676"
                font.bold: true
                font.pixelSize: 17
            }
        }
    }

    Rectangle {
        width: 430
        height: 330
        x: 55
        y: 100
        radius: 25
        color: "#101925"

        Column {
            anchors.centerIn: parent
            spacing: 15

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "JOYSTICK POSITION"
                color: "#8EA1BB"
                font.pixelSize: 18
                font.bold: true
            }

            Rectangle {
                width: 210
                height: 210
                radius: 105
                color: "#0B1422"
                border.color: "#26384D"
                border.width: 4
                anchors.horizontalCenter: parent.horizontalCenter

                Rectangle {
                    width: 150
                    height: 150
                    radius: 75
                    anchors.centerIn: parent
                    color: "transparent"
                    border.color: "#172B40"
                    border.width: 2
                }

                Rectangle {
                    width: 130
                    height: 2
                    anchors.centerIn: parent
                    color: "#26384D"
                }

                Rectangle {
                    width: 2
                    height: 130
                    anchors.centerIn: parent
                    color: "#26384D"
                }

                Rectangle {
                    width: 70
                    height: 70
                    radius: 35
                    anchors.centerIn: parent
                    color: "#00E676"
                    border.color: "#064B32"
                    border.width: 5

                    Text {
                        anchors.centerIn: parent
                        text: "●"
                        color: "#FFFFFF"
                        font.pixelSize: 25
                    }
                }
            }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 35

                Text {
                    text: "X : 0"
                    color: "#7187A5"
                }

                Text {
                    text: "Y : 0"
                    color: "#7187A5"
                }
            }
        }
    }

    Rectangle {
        width: 360
        height: 330
        x: 610
        y: 100
        radius: 25
        color: "#101925"

        Column {
            anchors.fill: parent
            anchors.margins: 25
            spacing: 15

            Text {
                text: "MOTOR STATUS"
                color: "#8EA1BB"
                font.pixelSize: 18
                font.bold: true
            }

            Rectangle {
                width: 310
                height: 2
                color: "#26384D"
            }

            Rectangle {
                width: 310
                height: 105
                radius: 18
                color: "#0B1422"

                Row {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 18

                    Rectangle {
                        width: 45
                        height: 45
                        radius: 22
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#083521"

                        Text {
                            anchors.centerIn: parent
                            text: "L"
                            color: "#00E676"
                            font.pixelSize: 20
                            font.bold: true
                        }
                    }

                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 5

                        Text {
                            text: "LEFT MOTOR"
                            color: "#00E676"
                            font.bold: true
                            font.pixelSize: 17
                        }

                        Text {
                            text: "RPM     0"
                            color: "#FFFFFF"
                            font.pixelSize: 15
                        }

                        Text {
                            text: "PWM     0 %"
                            color: "#7187A5"
                            font.pixelSize: 13
                        }
                    }
                }
            }

            Rectangle {
                width: 310
                height: 105
                radius: 18
                color: "#0B1422"

                Row {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 18

                    Rectangle {
                        width: 45
                        height: 45
                        radius: 22
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#083521"

                        Text {
                            anchors.centerIn: parent
                            text: "R"
                            color: "#00E676"
                            font.pixelSize: 20
                            font.bold: true
                        }
                    }

                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 5

                        Text {
                            text: "RIGHT MOTOR"
                            color: "#00E676"
                            font.bold: true
                            font.pixelSize: 17
                        }

                        Text {
                            text: "RPM     0"
                            color: "#FFFFFF"
                            font.pixelSize: 15
                        }

                        Text {
                            text: "PWM     0 %"
                            color: "#7187A5"
                            font.pixelSize: 13
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        width: 850
        height: 70
        anchors.horizontalCenter: parent.horizontalCenter
        y: 435
        radius: 25
        color: "#101925"

        Row {
            anchors.centerIn: parent
            spacing: 100

            Column {
                Text {
                    text: "MODE"
                    color: "#7187A5"
                    font.pixelSize: 12
                }

                Text {
                    text: "ASSISTED"
                    color: "#00E676"
                    font.bold: true
                }
            }

            Column {
                Text {
                    text: "SPEED"
                    color: "#7187A5"
                    font.pixelSize: 12
                }

                Text {
                    text: "0.0 km/h"
                    color: "#FFFFFF"
                    font.bold: true
                }
            }

            Column {
                Text {
                    text: "STATUS"
                    color: "#7187A5"
                    font.pixelSize: 12
                }

                Text {
                    text: "ESP32 ONLINE"
                    color: "#00E676"
                    font.bold: true
                }
            }
        }
    }

    BottomMenu {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 515
        selected: currentMenu
        navigator: joystick.navigator
    }
}
