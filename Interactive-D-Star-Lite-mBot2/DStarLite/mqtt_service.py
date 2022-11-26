import time

import paho.mqtt.client as paho


class MQTTService:
    def __init__(self):
        self.detectRealObstacle = False
        self.client = paho.Client()
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.client.connect('broker.hivemq.com', 1883)
        self.client.subscribe('rwth-ssrdp/route-planning/result', qos=1)
        self.client.message_callback_add('rwth-ssrdp/route-planning/obstacle', self.on_message_obstacle)
        self.client.loop_start()

    @staticmethod
    def on_connect(userdata, flags, rc):
        print('CONNACK received with code %d.' % rc)

    @staticmethod
    def on_publish(client, userdata, mid):
        print("mid: " + str(mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    @staticmethod
    def on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_message_obstacle(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        distance = msg.payload
        if distance < 10:
            self.detectRealObstacle = True
        else:
            self.detectRealObstacle = False

    def send(self, command):
        (rc, mid) = self.client.publish('rwth-ssrdp/route-planning/command', command, qos=1)


