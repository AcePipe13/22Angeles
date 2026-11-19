import QtQuick


Rectangle {


    width:260
    height:155

    radius:22

    color:"#101925"



    Column{


        anchors.fill:parent

        anchors.margins:16

        spacing:10




        Text{


            text:"BATTERY SYSTEM"

            color:"#8EA1BB"

            font.pixelSize:16

            font.bold:true


        }





        Row{


            spacing:15




            Item{


                width:120

                height:55




                Rectangle{


                    width:105

                    height:45


                    radius:8


                    anchors.verticalCenter:parent.verticalCenter


                    color:"#17283A"


                    border.color:"#334B66"

                    border.width:2





                    Rectangle{


                        width:85

                        height:30


                        anchors.left:parent.left

                        anchors.leftMargin:8


                        anchors.verticalCenter:parent.verticalCenter


                        radius:5


                        color:"#00E676"


                    }






                    Repeater{


                        model:4



                        Rectangle{


                            width:2

                            height:28


                            x:30+(index*18)

                            y:8


                            color:"#063B29"



                        }


                    }



                }





                Rectangle{


                    width:6

                    height:18


                    x:108

                    y:18


                    radius:2


                    color:"#8EA1BB"



                }



            }





            Column{


                anchors.verticalCenter:parent.verticalCenter



                Text{


                    text:"85%"

                    color:"#00E676"


                    font.pixelSize:34

                    font.bold:true


                }



            }



        }







        Rectangle{


            width:210

            height:7


            radius:4


            color:"#26384D"




            Rectangle{


                width:178


                height:7


                radius:4


                color:"#00E676"



            }



        }







        Row{


            width:220


            spacing:18


            anchors.horizontalCenter:parent.horizontalCenter




            Text{


                text:"⚡ 24.6V"


                color:"#FFFFFF"


                font.pixelSize:12


            }





            Text{


                text:"〽 3.2A"


                color:"#8EA1BB"


                font.pixelSize:12


            }





            Text{


                text:"🌡 32°C"


                color:"#8EA1BB"


                font.pixelSize:12


            }



        }




    }



}