
import QtQuick
import QtLocation
import QtPositioning
import "../Components"

Rectangle {
    id: gps

    property var navigator
    property int currentMenu: 3

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
            y: 12
            text: "GPS NAVIGATION"
            color: "#FFFFFF"
            font.pixelSize: 32
            font.bold: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 48
            text: "SMART POSITIONING SYSTEM"
            color: "#7187A5"
            font.pixelSize: 11
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
                text: "● GPS READY"
                color: "#00E676"
                font.bold: true
                font.pixelSize: 15
            }
        }
    }

    Rectangle {
        x: 45
        y: 125
        width: 590
        height: 300
        radius: 30
        color: "#101925"

        Text {
            x: 25
            y: 18
            text: "LIVE TRACKING"
            color: "#8EA1BB"
            font.pixelSize: 17
            font.bold: true
        }

        Rectangle {
            x: 20
            y: 55
            width: 550
            height: 220
            radius: 22
            clip: true

            Plugin {
                id: mapPlugin
                name: "osm"
            }

            Map {
                anchors.fill: parent
                plugin: mapPlugin

                center: QtPositioning.coordinate(4.7110, -74.0721)
                zoomLevel: 16

                MapQuickItem {
                    coordinate: QtPositioning.coordinate(4.7110, -74.0721)
                    anchorPoint.x: 30
                    anchorPoint.y: 30

                    sourceItem: Item {
                        width: 60
                        height: 60

                        Rectangle {
                            anchors.centerIn: parent
                            width: 60
                            height: 60
                            radius: 30
                            color: "#00E676"
                            opacity: 0.25
                        }

                        Rectangle {
                            anchors.centerIn: parent
                            width: 38
                            height: 38
                            radius: 19
                            color: "#00E676"
                            border.color: "#FFFFFF"
                            border.width: 3

                            Text {
                                anchors.centerIn: parent
                                text: "♿"
                                font.pixelSize: 22
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        x: 665
        y: 125
        width: 315
        height: 300
        radius: 30
        color: "#101925"

        Column {
            anchors.fill: parent
            anchors.margins: 25
            spacing: 12

            Text {
                text: "GPS STATUS"
                color: "#8EA1BB"
                font.pixelSize: 18
                font.bold: true
            }

            Text {
                text: "● CONNECTED"
                color: "#00E676"
                font.pixelSize: 25
                font.bold: true
            }

            Rectangle {
                width: 265
                height: 2
                color: "#26384D"
            }

            Rectangle {
                width: 265
                height: 45
                radius: 14
                color: "#0B1422"

                Text {
                    anchors.centerIn: parent
                    text: "SATELLITES        12"
                    color: "#FFFFFF"
                    font.pixelSize: 16
                }
            }

            Rectangle {
                width: 265
                height: 45
                radius: 14
                color: "#0B1422"

                Text {
                    anchors.centerIn: parent
                    text: "ACCURACY        1.5 m"
                    color: "#FFFFFF"
                    font.pixelSize: 16
                }
            }

            Rectangle {
                width: 265
                height: 45
                radius: 14
                color: "#0B1422"

                Text {
                    anchors.centerIn: parent
                    text: "HEADING          NE"
                    color: "#00E676"
                    font.pixelSize: 16
                }
            }
        }
    }

    Rectangle {
        width: 850
        height: 60
        anchors.horizontalCenter: parent.horizontalCenter
        y: 440
        radius: 25
        color: "#101925"

        Row {
            anchors.centerIn: parent
            spacing: 100

            Column {
                Text {
                    text: "DISTANCE"
                    color: "#7187A5"
                    font.pixelSize: 12
                }

                Text {
                    text: "125 m"
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
                    text: "3.5 km/h"
                    color: "#FFFFFF"
                    font.bold: true
                }
            }

            Column {
                Text {
                    text: "SIGNAL"
                    color: "#7187A5"
                    font.pixelSize: 12
                }

                Text {
                    text: "95 %"
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
        navigator: gps.navigator
    }
}
