import cyberpi
import event
import mbot2
import mbuild
import time
from mqtt import MQTTClient

mqtt_host = "broker.hivemq.com"
mqtt_port = 1883

# Fill in as you like
client_id = "clientId-rwth-ssrdp-mbot2"

# Example Path
topic_sub = "rwth-ssrdp/route-planning/command"
topic_pub_result = "rwth-ssrdp/route-planning/result"
topic_pub_obstacle = "rwth-ssrdp/route-planning/obstacle"
topic_pub_heartbeat = "rwth-ssrdp/route-planning/heartbeat"
command = None


# Connect to the MQTT server
def on_mqtt_connect():
    cyberpi.display.show_label('Connecting to MQTT', 16, "center", index=0)
    mqtt_client.connect(clean_session=True)
    time.sleep(3)
    cyberpi.display.show_label('Connected to MQTT', 16, "center", index=0)


# publish a message
def on_publish(topic, payload, retain=False, qos=1):
    mqtt_client.publish(topic, payload, retain, qos)


# message processing function
def on_message_come(topic, msg):
    global command
    print(topic + " :" + str(msg))
    command = msg
    cyberpi.display.show_label(msg, 16, "center", index=0)


# subscribe message
def on_subscribe():
    mqtt_client.set_callback(on_message_come)
    mqtt_client.subscribe(topic_sub, qos=1)


mqtt_client = MQTTClient(client_id, mqtt_host, port=mqtt_port, keepalive=600, ssl=False)


def process_command():
    global command
    if command is None:
        return
    else:
        if command == b'Drive':
            print('Forward')
            cyberpi.display.show_label('Forward', 16, "center", index=0)
            mbot2.straight(20)
        elif command == b'Reverse':
            print('Backward')
            cyberpi.display.show_label('Backward', 16, "center", index=0)
            mbot2.straight(-20)
        elif command == b'TurnR90':
            mbot2.turn(90)
        elif command == b'TurnL90':
            mbot2.turn(-90)
        elif command == b'Turn180':
            mbot2.turn(180)
        elif command == b'CheckDistance':
            distance = mbuild.ultrasonic2.get(1)
            on_publish(topic_pub_obstacle, str(distance), retain=False, qos=1)
        elif command == b'Stop':
            mbot2.EM_stop("ALL")
        command = None


@event.start
def on_start():
    count = 0
    mqtt_connected = False

    while True:
        if cyberpi.wifi.is_connected():
            cyberpi.led.show('green black black black green')
            if not mqtt_connected:
                on_mqtt_connect()
                mqtt_connected = True
                on_subscribe()
                time.sleep(2)
            else:
                count = count + 1
                on_publish(topic_pub_heartbeat, str(count), retain=False, qos=1)
                cyberpi.display.show_label(count, 16, "bottom_mid", index=1)
                time.sleep(5)
        else:
            cyberpi.led.show('red black black black red')
            cyberpi.display.show_label('Connecting to WiFi', 16, "center", index=0)
            cyberpi.wifi.connect('SSID', 'password')
            time.sleep(2)


@event.is_press('b')
def is_btn_press():
    distance = mbuild.ultrasonic2.get(1)
    cyberpi.display.show_label('Obstacle ' + str(distance), 16, "top_mid", index=2)
    on_publish(topic_pub_obstacle, str(distance), retain=False, qos=1)


@event.greater_than(0.5, "timer")
def on_compare_than():
    distance = mbuild.ultrasonic2.get(1)
    if distance < 10:
        mbuild.ultrasonic2.play("thinking", 1)
    else:
        mbuild.ultrasonic2.play("happy", 1)
    on_publish(topic_pub_obstacle, str(distance), retain=False, qos=1)
    process_command()
    cyberpi.timer.reset()
