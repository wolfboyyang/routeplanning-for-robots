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

ssid = "SSID"
password = "password"

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

network_available = False
battery = 0
heartbeat_count = 0


# Connect to the MQTT server
def on_mqtt_connect():
    display('Connecting to MQTT')
    result = mqtt_client.connect(clean_session=True)
    if result:
        display('Connected to MQTT')


# publish a message
def report(result):
    mqtt_client.publish(topic_result, result, retain=False, qos=1)


def report_heartbeat(count):
    mqtt_client.publish(topic_heartbeat, str(count), retain=False, qos=1)
    display_at_bottom(count)


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


def display(label):
    cyberpi.display.show_label(label, 16, "center", index=0)


def display_at_bottom(label):
    cyberpi.display.show_label(label, 16, "bottom_mid", index=1)


def display_at_top(label):
    cyberpi.display.show_label(label, 16, "top_mid", index=2)


def display_at_top_right(label):
    cyberpi.display.show_label(label, 16, "top_right", index=3)


def display_battery():
    global battery
    current_battery = cyberpi.get_battery()
    if current_battery != battery:
        battery = current_battery
        display_at_top_right(battery)


def check_network():
    global network_available
    global heartbeat_count
    if cyberpi.wifi.is_connected():
        if not network_available:
            cyberpi.led.show('green black black black green')
            on_mqtt_connect()
            subscribe_topic_command()
            network_available = True
            display('WiFi connected')
        heartbeat_count += 1
    else:
        if network_available:
            cyberpi.led.show('red black black black red')
            display('Connecting to WiFi')
            cyberpi.wifi.connect(ssid, password)
            network_available = False


@event.start
def on_start():
    display_battery()
    cyberpi.led.show('red black black black red')
    check_network()


@event.is_press('a')
def is_btn_a_press():
    cyberpi.restart()


@event.is_press('b')
def is_btn_b_press():
    distance = mbuild.ultrasonic2.get(1)
    display_at_top('Obstacle ' + str(distance))
    report_obstacle(distance)


@event.greater_than(5, "timer")
def check_health():
    global heartbeat_count
    display_battery()
    check_network()
    if network_available:
        report_heartbeat(heartbeat_count)
    heartbeat_count += 1
    cyberpi.timer.reset()
