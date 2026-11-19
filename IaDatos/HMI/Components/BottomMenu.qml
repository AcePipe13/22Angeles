
import QtQuick

Rectangle {
    width: 940
    height: 75

    radius: 25
    color: "#101925"

    property int selected: 0
    property var navigator

    Row {
        anchors.centerIn: parent
        spacing: 55

        Repeater {
            id: menuRepeater

            model: [
                { name: "HOME", symbol: "⌂", page: "Home" },
                { name: "CAMERA", symbol: "◉", page: "Camera" },
                { name: "JOYSTICK", symbol: "⊕", page: "Joystick" },
                { name: "GPS", symbol: "◎", page: "GPS" },
                { name: "VOICE AI", symbol: "✦", page: "VoiceAI" },
                { name: "SYSTEM", symbol: "⚙", page: "System" }
            ]

            delegate: Item {
                id: menuItem

                width: 70
                height: 70

                Rectangle {
                    anchors.centerIn: parent
                    width: 68
                    height: 62
                    radius: 18

                    color: selected === index
                           ? "#172B40"
                           : "transparent"

                    Behavior on color {
                        ColorAnimation {
                            duration: 250
                        }
                    }
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 5

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: modelData.symbol

                        width: selected === index ? 34 : 28
                        height: selected === index ? 34 : 28

                        color: selected === index
                               ? "#00E676"
                               : "#A8B8CC"

                        font.pixelSize: selected === index ? 30 : 25

                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter

                        opacity: selected === index ? 1.0 : 0.65
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: modelData.name

                        color: selected === index
                               ? "#00E676"
                               : "#7187A5"

                        font.pixelSize: 11
                        font.bold: selected === index
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor

                    onClicked: {
                        console.log("CLICK MENU:", modelData.page)
                        console.log("NAVIGATOR RECIBIDO:", navigator)

                        selected = index

                        if (navigator) {
                            navigator(modelData.page, index)
                        } else {
                            console.warn(
                                "No se ha asignado la función navigator"
                            )
                        }
                    }
                }
            }
        }
    }
}
