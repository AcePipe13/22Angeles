
import QtQuick
import "../Components"

Rectangle {
    id: home
    property var navigator
    property int currentMenu: 0

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

        Rectangle {
            width: 140
            height: 40
            x: 20
            y: 18
            radius: 20
            color: "#17283A"

            Text {
                anchors.centerIn: parent
                text: "🔋 85%"
                color: "#FFFFFF"
                font.pixelSize: 20
                font.bold: true
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 15
            text: "SMART CHAIR"
            color: "#FFFFFF"
            font.pixelSize: 32
            font.bold: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 50
            text: "INTELLIGENT MOBILITY SYSTEM"
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

    SpeedGauge {
        id: speed
        anchors.centerIn: parent
        y: 290
        speed: 3.5
        maxSpeed: 8
    }

    HealthWidget {
        x: 55
        y: 170
    }

    BatteryWidget {
        x: 55
        y: 345
    }

    SystemWidget {
        x: 710
        y: 170
    }

    DriveWidget {
        x: 710
        y: 360
    }

    Rectangle {
        width: 230
        height: 45
        radius: 20
        anchors.horizontalCenter: parent.horizontalCenter
        y: 445
        color: "#101925"

        Text {
            anchors.centerIn: parent
            text: "ASSISTED MODE"
            color: "#00E676"
            font.bold: true
            font.pixelSize: 16
        }
    }

    BottomMenu {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 515
        selected: currentMenu
        navigator: home.navigator
    }
}
