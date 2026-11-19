
import QtQuick
import QtQuick.Controls
import "Screens"

ApplicationWindow {
    visible: true
    width: 1024
    height: 600
    color: "#070B12"

    property int currentMenu: 0

    Loader {
        id: screenLoader
        anchors.fill: parent
        source: "Screens/Home.qml"

        onLoaded: {
            screenLoader.item.navigator = changeScreen
            screenLoader.item.currentMenu = currentMenu
        }
    }

    function changeScreen(screen, index) {
        console.log("CAMBIANDO A:", screen)

        currentMenu = index

        screenLoader.setSource(
            "Screens/" + screen + ".qml",
            {
                "navigator": changeScreen,
                "currentMenu": currentMenu
            }
        )
    }
}
