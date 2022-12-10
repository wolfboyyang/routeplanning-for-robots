from queue import Queue, Empty
import paho.mqtt.client as paho


topic_command = "rwth-ssrdp/route-planning/command"
topic_heartbeat = "rwth-ssrdp/route-planning/heartbeat"
topic_obstacle = "rwth-ssrdp/route-planning/obstacle"
topic_result = "rwth-ssrdp/route-planning/result"
one_step_distance = 20
turn_distance = 4


class MQTTService:
    def __init__(self):
        self.result = Queue(1)
        self.heartbeat = None
        self.detectRealObstacle = False
        self.client = paho.Client()
        self.client.connect('broker.hivemq.com', 1883)
        self.client.subscribe([(topic_heartbeat, 1),
                               (topic_obstacle, 1),
                               (topic_result, 1)])
        self.client.message_callback_add(topic_heartbeat, self.on_message_heartbeat)
        self.client.message_callback_add(topic_result, self.on_message_result)
        self.client.message_callback_add(topic_obstacle, self.on_message_obstacle)
        self.client.loop_start()

    def on_message_heartbeat(self, client, userdata, msg):
        self.heartbeat = msg.payload

    def on_message_result(self, client, userdata, msg):
        self.result.put(msg.payload)

    def on_message_obstacle(self, client, userdata, msg):
        distance = float(msg.payload)
        if distance < one_step_distance:
            self.detectRealObstacle = True
        else:
            self.detectRealObstacle = False

    def send(self, command):
        (rc, mid) = self.client.publish(topic_command, command, qos=1)
        try:
            result = self.result.get(timeout=10)
        except Empty:
            result = 'timeout!'
        return result


if __name__ == '__main__':
    robot = MQTTService()
    _result = robot.send('Stop')
    print(_result[-1:] == b'!')



