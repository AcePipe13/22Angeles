import QtQuick


Rectangle {


    width:260
    height:140


    radius:22


    color:"#101925"




    Column{


        anchors.fill:parent

        anchors.margins:18


        spacing:8





        // TITULO


        Row{


            spacing:8



            Text{


                text:"SYSTEM STATUS"


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






        // ESTADO


        Row{


            spacing:10



            Rectangle{


                width:12

                height:12


                radius:6


                anchors.verticalCenter:parent.verticalCenter


                color:"#00E676"


            }



            Text{


                text:"READY"


                color:"#FFFFFF"


                font.pixelSize:34


                font.bold:true



            }



        }






        // INFORMACION


        Rectangle{


            width:220

            height:1


            color:"#26384D"



        }





        Row{


            spacing:15



            Text{


                text:"ESP32"

                color:"#00E676"

                font.pixelSize:13


                font.bold:true


            }




            Text{


                text:"ONLINE"

                color:"#8EA1BB"

                font.pixelSize:13


            }


        }




    }


}