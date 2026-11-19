import QtQuick


Item {

    width:330
    height:330


    property real speed:3.5
    property real maxSpeed:8



    Canvas {


        anchors.fill:parent



        onPaint:{


            var ctx=getContext("2d")


            ctx.clearRect(
                0,
                0,
                width,
                height
            )



            var cx=width/2
            var cy=height/2



            // radios

            var outer=130
            var progress=112
            var inner=82




            // sombra exterior


            ctx.beginPath()

            ctx.arc(
                cx,
                cy,
                outer+5,
                0,
                Math.PI*2
            )

            ctx.fillStyle="#050A12"

            ctx.fill()




            // fondo del gauge


            ctx.beginPath()

            ctx.arc(
                cx,
                cy,
                outer,
                0,
                Math.PI*2
            )


            ctx.fillStyle="#101925"

            ctx.fill()



            // borde externo


            ctx.beginPath()

            ctx.arc(
                cx,
                cy,
                outer,
                0,
                Math.PI*2
            )


            ctx.lineWidth=3

            ctx.strokeStyle="#26384D"

            ctx.stroke()




            // escala


            for(
                var i=0;
                i<=24;
                i++
            ){


                var angle=
                (-Math.PI*0.75)
                +
                (i/24)
                *
                (Math.PI*1.5)



                var r1=112

                var r2=
                i%4===0 ? 98:105



                ctx.beginPath()


                ctx.moveTo(

                    cx+Math.cos(angle)*r1,
                    cy+Math.sin(angle)*r1

                )


                ctx.lineTo(

                    cx+Math.cos(angle)*r2,
                    cy+Math.sin(angle)*r2

                )



                ctx.lineWidth=
                i%4===0 ? 3:1



                ctx.strokeStyle=
                "#7187A5"


                ctx.stroke()



            }




            // barra verde progreso


            var start=
            -Math.PI*0.75



            var end=
            start+
            (Math.PI*1.5)
            *
            (speed/maxSpeed)



            ctx.beginPath()


            ctx.arc(

                cx,
                cy,
                progress,

                start,
                end

            )


            ctx.lineWidth=10

            ctx.lineCap="round"


            ctx.strokeStyle="#00E676"


            ctx.stroke()




            // aro interior


            ctx.beginPath()


            ctx.arc(

                cx,
                cy,
                inner,

                0,
                Math.PI*2

            )


            ctx.lineWidth=2

            ctx.strokeStyle="#1B3048"

            ctx.stroke()



        }


    }




    Column{


        anchors.centerIn:parent


        spacing:8




        Text{


            anchors.horizontalCenter:parent.horizontalCenter


            text:speed.toFixed(1)


            color:"#FFFFFF"


            font.pixelSize:88

            font.bold:true



        }




        Text{


            anchors.horizontalCenter:parent.horizontalCenter


            text:"km/h"


            color:"#94A3B8"


            font.pixelSize:26



        }



    }


}