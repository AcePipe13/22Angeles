#include <Arduino.h>

#define LED_PIN 2
#define INPUT_PIN 15

bool estadoLED = false;
bool estadoEntradaAnterior = false;

void setup() {


  Serial.begin(115200);


  pinMode(
    LED_PIN,
    OUTPUT
  );


  pinMode(
    INPUT_PIN,
    INPUT_PULLDOWN
  );


  digitalWrite(
    LED_PIN,
    LOW
  );


  Serial.println(
    "ESP32_LISTA"
  );

}



// =======================
// LOOP PRINCIPAL
// =======================


void loop() {



  //----------------------
  // RECIBIR COMANDOS
  //----------------------


  if(Serial.available()){


    String comando =
    Serial.readStringUntil('\n');


    comando.trim();



    if(comando=="LED_ON"){


      estadoLED=true;


      digitalWrite(
        LED_PIN,
        HIGH
      );


      Serial.println(
        "LED_ACTIVO"
      );


    }



    if(comando=="LED_OFF"){


      estadoLED=false;


      digitalWrite(
        LED_PIN,
        LOW
      );


      Serial.println(
        "LED_APAGADO"
      );


    }



  }




  //----------------------
  // LEER ENTRADA DIGITAL
  //----------------------


  bool entrada =
  digitalRead(INPUT_PIN);



  if(
     entrada != estadoEntradaAnterior
    ){



      if(entrada){


        Serial.println(
          "ENTRADA_ACTIVA"
        );


      }
      else{


        Serial.println(
          "ENTRADA_DESACTIVA"
        );


      }



      estadoEntradaAnterior =
      entrada;


  }



  delay(50);


}