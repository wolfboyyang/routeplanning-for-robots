import cyberpi
import event
import mbot2
import mbuild
import time
from mqtt import MQTTClient

MQTT_HOST = "broker.hivemq.com"
MQTT_PORT = 1883

# Fill in as you like
client_id = "clientId-wei-mbot2"

# Example Path
TopicSub = "ssrdp/wei/COMMAND"
TopicPub = "ssrdp/wei/signalfromrobot"
TopicPubDebug = "ssrdp/wei/debug"

command = ''


# Connect to the MQTT server
def on_mqtt_connect():
    cyberpi.display.show_label('Connecting to MQTT', 16, "center", index=0)
    mqttClient.connect(clean_session=True)
    time.sleep(3)
    cyberpi.display.show_label('Connected to MQTT', 16, "center", index=0)


# publish a message
def on_publish(topic, payload, retain=False, qos=1):
    mqttClient.publish(topic, payload, retain, qos)


# message processing function
def on_message_come(topic, msg):
    print(topic + " " + ":" + str(msg))
    global command
    if str(topic).find(TopicSub) > 0:
        command = str(msg)[1:]
        print('Received', command)
    cyberpi.display.show_label(msg, 16, "center", index=0)


# subscribe message
def on_subscribe():
    mqttClient.set_callback(on_message_come)
    mqttClient.subscribe(TopicSub, qos=1)


mqttClient = MQTTClient(client_id, MQTT_HOST, port=MQTT_PORT, keepalive=600, ssl=False)


@event.start
def on_start():
    count = 0
    is_connected_mqtt = 0

    while True:
        if cyberpi.wifi.is_connected():
            cyberpi.led.show('green black black black green')
            if is_connected_mqtt == 0:
                on_mqtt_connect()
                is_connected_mqtt = 1
                on_subscribe()
                time.sleep(2)
            else:
                count = count + 1
                on_publish(TopicPub, 'count ' + str(count), retain=False, qos=1)
                cyberpi.display.show_label(count, 16, "bottom_mid", index=1)
                time.sleep(5)
        else:
            cyberpi.led.show('red black black black red')
            cyberpi.display.show_label('Connecting to WiFi', 16, "center", index=0)
            cyberpi.wifi.connect('SSID', 'password')
            time.sleep(2)


@event.is_press('b')
def is_btn_press():
    cyberpi.display.show_label('Press B ' + str(cyberpi.controller.get_count('b')), 16, "top_mid", index=2)
    on_publish(TopicPubDebug, 'Press B ' + str(cyberpi.controller.get_count('b')), retain=False, qos=1)


@event.greater_than(1, "timer")
def on_compare_than():
    global command

    if mbuild.ultrasonic2.get(1) < 10:
        mbuild.ultrasonic2.play("thinking", 1)
    else:
        mbuild.ultrasonic2.play("happy", 1)

    if command != '':
        if command.find('F') > 0:
            print('Forward')
            cyberpi.display.show_label('Forward', 16, "center", index=0)
            mbot2.straight(10)
        elif command.find('B') > 0:
            print('Backward')
            cyberpi.display.show_label('Backward', 16, "center", index=0)
            mbot2.straight(-10)
        elif command.find('R') > 0:
            mbot2.turn(90)
        elif command.find('L') > 0:
            mbot2.turn(-90)
        command = ''
    cyberpi.timer.reset()
