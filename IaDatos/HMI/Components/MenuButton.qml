import QtQuick


Item{


    property string icon
    property string name
    property bool selected:false


    width:80
    height:70



    Rectangle{


        anchors.centerIn: parent

        width:70
        height:65

        radius:18


        color:selected
               ? "#18304A"
               : "transparent"



    }



    Image{


        id:iconImage


        source:icon


        width:28
        height:28


        anchors.horizontalCenter:parent.horizontalCenter


        anchors.top:parent.top


        anchors.topMargin:8


        fillMode:Image.PreserveAspectFit


        opacity:selected ? 1 : 0.75


    }




    Text{


        anchors.horizontalCenter:parent.horizontalCenter

        anchors.bottom:parent.bottom

        anchors.bottomMargin:8


        text:name


        color:selected
              ? "#00E676"
              :"#7187A5"



        font.pixelSize:11


        font.bold:selected



    }



}