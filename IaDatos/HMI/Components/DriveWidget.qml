import QtQuick


Rectangle {


    width:260
    height:140


    radius:22


    color:"#101925"




    Column{


        anchors.fill:parent

        anchors.margins:16


        spacing:8





        Row{


            spacing:8



            Text{


                text:"DRIVE SYSTEM"


                color:"#8EA1BB"


                font.pixelSize:16


                font.bold:true


            }



            Item{

                width:55

                height:1

            }



            Rectangle{


                width:10

                height:10


                radius:5


                color:"#00E676"



            }


        }






        // SISTEMA DE RUEDAS


        Row{


            anchors.horizontalCenter:parent.horizontalCenter


            spacing:25





            // RUEDA IZQUIERDA


            Column{


                spacing:4



                Rectangle{


                    width:38

                    height:38


                    radius:19


                    color:"#17283A"


                    border.color:"#00E676"

                    border.width:3



                    Text{


                        anchors.centerIn:parent


                        text:"L"


                        color:"#FFFFFF"


                        font.bold:true


                        font.pixelSize:15



                    }



                }




                Text{


                    text:"LEFT"


                    color:"#FFFFFF"


                    font.pixelSize:12


                    font.bold:true


                    anchors.horizontalCenter:parent.horizontalCenter


                }




                Text{


                    text:"ACTIVE"

                    color:"#00E676"

                    font.pixelSize:11


                    anchors.horizontalCenter:parent.horizontalCenter



                }


            }





            // EJE CENTRAL


            Rectangle{


                width:25

                height:4


                color:"#26384D"


                anchors.verticalCenter:parent.verticalCenter



            }







            // RUEDA DERECHA


            Column{


                spacing:4



                Rectangle{


                    width:38

                    height:38


                    radius:19


                    color:"#17283A"


                    border.color:"#00E676"

                    border.width:3




                    Text{


                        anchors.centerIn:parent


                        text:"R"


                        color:"#FFFFFF"


                        font.bold:true


                        font.pixelSize:15



                    }


                }




                Text{


                    text:"RIGHT"


                    color:"#FFFFFF"


                    font.pixelSize:12


                    font.bold:true


                    anchors.horizontalCenter:parent.horizontalCenter


                }





                Text{


                    text:"ACTIVE"


                    color:"#00E676"


                    font.pixelSize:11


                    anchors.horizontalCenter:parent.horizontalCenter



                }



            }



        }





    }


}