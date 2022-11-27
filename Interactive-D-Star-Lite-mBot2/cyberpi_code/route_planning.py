# region import
import time
import cyberpi

# use try import to have lint with IDE like pycharm or vscode on host
try:
    import event
except ImportError:
    from cyberpi import event
try:
    import mbot2
except ImportError:
    from cyberpi import mbot2
try:
    import mbuild
except ImportError:
    from makeblock import mbuild
try:
    from mqtt import MQTTClient
except ImportError:
    from umqtt.simple import MQTTClient
# endregion

mqtt_host = "broker.hivemq.com"
mqtt_port = 1883

# Fill in as you like
client_id = "clientId-rwth-ssrdp-mbot2"

# MQTT Topic
topic_command = "rwth-ssrdp/route-planning/command"
topic_heartbeat = "rwth-ssrdp/route-planning/heartbeat"
topic_obstacle = "rwth-ssrdp/route-planning/obstacle"
topic_result = "rwth-ssrdp/route-planning/result"

mqtt_client = MQTTClient(client_id, mqtt_host, port=mqtt_port, keepalive=600, ssl=False)

one_step_distance = 20
turn_distance = 4


# Connect to the MQTT server
def on_mqtt_connect():
    display('Connecting to MQTT')
    mqtt_client.connect(clean_session=True)
    time.sleep(3)
    display('Connected to MQTT')


# publish a message
def report(result):
    mqtt_client.publish(topic_result, result, retain=False, qos=1)


def report_heartbeat(count):
    mqtt_client.publish(topic_heartbeat, str(count), retain=False, qos=1)


def report_obstacle(distance):
    mqtt_client.publish(topic_obstacle, str(distance), retain=False, qos=1)


# message processing function
def on_command_come(_, msg):
    # print(topic + " :" + str(msg))
    display(msg)
    process_command(msg)


# subscribe message
def subscribe_topic_command():
    mqtt_client.set_callback(on_command_come)
    mqtt_client.subscribe(topic_command, qos=1)


def check_distance():
    distance = mbuild.ultrasonic2.get(1)
    report_obstacle(distance)
    return distance >= one_step_distance


def check_turn():
    distance = mbuild.ultrasonic2.get(1)
    return distance >= turn_distance


def process_command(command):
    if command is None or len(command) == 0:
        return

    if command == b'CheckDistance':
        if check_distance():
            report('ok')
        else:
            report('fail!')
    elif command == b'Drive':
        if check_distance():
            mbot2.straight(one_step_distance)
            time.sleep(0.8)
            check_distance()
            report('ok')
        else:
            report('fail!')
    elif command == b'Reverse':
        mbot2.straight(-one_step_distance)
        time.sleep(0.8)
        check_distance()
        report('ok')
    elif command == b'Stop':
        mbot2.EM_stop("ALL")
        report('ok')
    elif command == b'Turn180':
        mbot2.turn(180)
        time.sleep(0.5)
        check_distance()
        report('ok')
    elif command == b'TurnL90':
        mbot2.turn(-90)
        time.sleep(0.3)
        check_distance()
        report('ok')
    elif command == b'TurnR90':
        mbot2.turn(90)
        time.sleep(0.3)
        check_distance()
        report('ok')


def display(label, align="center", index=0):
    cyberpi.display.show_label(label, 16, align, index)


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
                subscribe_topic_command()
                time.sleep(2)
            else:
                count = count + 1
                report_heartbeat(count)
                display(count, align="bottom_mid", index=1)
                time.sleep(5)
        else:
            cyberpi.led.show('red black black black red')
            display('Connecting to WiFi')
            cyberpi.wifi.connect('SSID', 'password')
            time.sleep(2)


@event.is_press('b')
def is_btn_press():
    distance = mbuild.ultrasonic2.get(1)
    cyberpi.display.show_label('Obstacle ' + str(distance), 16, "top_mid", index=2)
    report_obstacle(distance)
