#include <BH1750Lib.h>
#include "MQTT.h"

//function for recieving messages, defined below
void callback(char* topic, byte* payload, unsigned int length);

//configure the MQTT server settings
byte server[] = { 192,168,0,187 };
MQTT client(server, 1883, callback);

//variable to store reset request info from RPi
bool reset_requested = false;
//variable to store messages from RPi
String message = "no_message";

//define pins and variables to store sensor data
uint16_t luxvalue;
BH1750Lib lightSensor;

// function to recieve and decipher messages from RPi
void callback(char* topic, byte* payload, unsigned int length) {
    char p[length + 1];
    memcpy(p, payload, length);
    p[length] = NULL;
    //store the message from the user
    if(String(p) == "off")
        message = "off";
    else if(String(p) == "start")
        message = "start";
}


void setup() {
    lightSensor.begin(BH1750LIB_MODE_CONTINUOUSHIGHRES);

    // connect to the server
    client.connect("sparkclient");

    // publish/subscribe
    if (client.isConnected()) {
        client.publish("data","Connection established");
        client.subscribe("data/reset");
    }
}

void loop() {
    //First check if a reset was requested from the user
    if(message == "off")
    {
        //wait for the user to request a restart
        while(message == "off")
        {
            reset_requested = true;
            delay(100);
            Particle.publish("No reset has been requested");
            client.loop();
            if(message == "start")
            {
                Particle.publish("reset requested");
                reset_requested = false;
                message == "restarted";
            }
        }
        //If we get to here, a reset has been requested
        reset_requested = false;
    }
    //Used for debugging 
    Particle.publish("message cont", message);
    
    //since no reset has been request, function normally
    if(!reset_requested)
    {
        //get values to pass to RPi
        luxvalue = lightSensor.lightLevel();
        Particle.publish("bh1750info", String(luxvalue));
        //sends lux to RPi every two seconds if the MQTT client is connected
        if (client.isConnected())
        {
            client.publish("data/lux",String(luxvalue));
            delay(2000);
            client.loop();
        }
    }
}



