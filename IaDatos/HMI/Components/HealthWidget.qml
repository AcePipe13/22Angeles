import QtQuick


Rectangle {


    width:260
    height:150


    radius:22


    color:"#101925"



    Column{


        anchors.fill:parent

        anchors.margins:18


        spacing:6



        Row{


            width:parent.width


            spacing:8



            Text{


                text:"♥"


                color:"#00E676"


                font.pixelSize:18


            }



            Text{


                text:"HEALTH MONITOR"


                color:"#8EA1BB"


                font.pixelSize:16


                font.bold:true


            }



            Item{


                width:1

                height:1

                anchors.horizontalCenter:parent.horizontalCenter

            }



            Rectangle{


                width:10

                height:10


                radius:5


                color:"#00E676"


            }



        }




        Text{


            text:"78 BPM"


            color:"#FFFFFF"


            font.pixelSize:38


            font.bold:true



        }





        Canvas{


            width:220

            height:25



            onPaint:{


                var ctx=getContext("2d")


                ctx.clearRect(
                    0,
                    0,
                    width,
                    height
                )


                ctx.beginPath()



                ctx.moveTo(0,13)



                ctx.lineTo(35,13)

                ctx.lineTo(45,5)

                ctx.lineTo(55,20)

                ctx.lineTo(70,13)

                ctx.lineTo(100,13)

                ctx.lineTo(115,7)

                ctx.lineTo(125,18)

                ctx.lineTo(140,13)

                ctx.lineTo(220,13)



                ctx.lineWidth=2


                ctx.strokeStyle="#00E676"


                ctx.stroke()



            }



        }




        Rectangle{


            width:95

            height:22


            radius:11


            color:"#063B29"



            Text{


                anchors.centerIn:parent


                text:"● NORMAL"


                color:"#00E676"


                font.pixelSize:12


                font.bold:true


            }


        }



    }


}