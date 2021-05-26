#Required libraries
import paho.mqtt.client as mqttClient
import time
import RPi.GPIO as GPIO
from gpiozero import Button

##setup board using GPIO pin numbering system 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#variable to monitor request for reset from user
global reset_requested
reset_requested = False

##initialising the board, LED, button and buzzer
LED = 21
BUZZER = 20
RESET_BUTTON = Button(16)
GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(BUZZER, GPIO.OUT, initial=GPIO.LOW)

#variable to store lux
global lux
lux = b'0'
#lux = 200
#lux threshold for waking up user

#calculated based on light level early morning
#58 represents a lux of 10 converted from bytes to int
morning_lux = 58

##loops the alarm until a reset request hasn't been made
def trigger_alarm(reset_requested):
    #Since we've split from the main thread,
    #we need to reinstantiate the client 
    client = mqttClient.Client()
    client.on_connect= on_connect
    client.on_message= on_message
    client.on_publish= on_publish
    client.connect(broker_address, port, 60)
    #sound alarm until user presses reset button
    while(not reset_requested):
        #Sound alarm
        GPIO.output(LED, GPIO.HIGH)
        GPIO.output(BUZZER,GPIO.HIGH)
        #reset pressed, turn off alarm
        if(RESET_BUTTON.is_pressed):
            GPIO.output(LED, GPIO.LOW)
            GPIO.output(BUZZER, GPIO.LOW)
            reset_requested = True
            #publish off signal while we wait for restart
            while(reset_requested):
                client.publish("data/reset", "off")
                time.sleep(0.5)
                #user requested a restart, publish start and reset
                if(RESET_BUTTON.is_pressed):
                    client.publish("data/reset", "start")
                    reset_requested = False
                    #system sleeps for five seconds to ensure
                    #that the lux value from the Argon has been updated
                    #without this, the lux value will sometimes be pulled
                    #from an old message from the MQTT broker, casuing a false
                    #alarm to the raised
                    #also resetting lux to be safe
                    global lux
                    time.sleep(5)
                    lux = 0
                    #return to main function
                    return

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("data/lux")

# The callback for when a PUBLISH message is received from the server.
# Triggers alarm on RPi if the lux value from the Argon is bright enough,
# indicating it is morning
def on_message(client, userdata, msg):
    #get lux then print the value for debugging
    global lux
    lux = b'0'
    print("on_message ", lux)
    #lux = b'0'
    if(msg.topic == "data/lux"):
        lux = msg.payload
    print(lux)
    #convert lux from bytes to int for comparison 
    light = int.from_bytes(lux,byteorder='big')
    ##trigger alarm if its getting bright outside
    if(light >= morning_lux):
        trigger_alarm(reset_requested)
    else:
        return
#function for publishing data to server        
def on_publish(client,userdata,result):
    #uncomment for debugging to ensure publish is being called
    #print("data published")
    pass

broker_address="192.168.0.187"   #Broker address RPi ip address in this case
port = 1883                      #Broker port using default MQTT port
   
client = mqttClient.Client()      
client.on_connect= on_connect                  #attach function to callback
client.on_message= on_message                  #attach function to callback
client.on_publish= on_publish                  #attach function to callback
client.connect(broker_address, port, 60)
#subscribe to lux info from the Argon
client.subscribe("data/lux")
#loop until we get a high lux value
#breaks out of loop when the lux value exceeds morning lux
#see on_message function definition
client.loop_start()
