#!/usr/bin/python3
############################################################
# Class CloudExecutor
# The class CloudExecutor executes a path-plan by commanding
# a robot with mqtt. A robot is shown on screen
# and drives from vertex to vertex of the path.
# The robot can move forward and change direction to
# north, east, south and west.
#
# This class inherits from ScreenExecutor.
#
# File: cloud_executor.py
# Author: Wei Yang
# Version: 1.0    Date: 25.11.2022
###########################################################

import time
from screen_executor import ScreenExecutor
from mqtt_service import MQTTService


class CloudExecutor(ScreenExecutor):

    def __init__(self, my_view, my_planner):
        self.direction_dict = None
        print('\nCreating Cloud Executor')
        # Call base class initialisation
        ScreenExecutor.__init__(self, my_view, my_planner)

        self.detectRealObstacle = False  # True, if a new obstacle appeared
        # during plan execution
        self.lastCommand = ''  # last command send to the robot
        self.init_command_dict()

        self.robot = MQTTService()

    # Initialize the dictionaries for the robot commands depending
    # on the current orientation North, East, South or West
    def init_command_dict(self):
        north_dict = {'East': 'TurnR90', 'South': 'Turn180', 'West': 'TurnL90', 'North': 'Drive'}
        east_dict = {'North': 'TurnL90', 'South': 'TurnR90', 'West': 'Turn180', 'East': 'Drive'}
        south_dict = {'North': 'Turn180', 'East': 'TurnL90', 'West': 'TurnR90', 'South': 'Drive'}
        west_dict = {'North': 'TurnR90', 'East': 'Turn180', 'South': 'TurnL90', 'West': 'Drive'}

        self.direction_dict = {'North': north_dict,
                               'East': east_dict,
                               'South': south_dict,
                               'West': west_dict}

        # Overwritten method of superclass.

    def execution_allowed(self):
        # Check business rules regarding the plan execution.
        # The EV3 robot control can only move robots to direct
        # neighbors: Vertices in direction north, east,
        # south and west.
        return self.planner.directNeighbors

    # Overwritten method of superclass.
    # Establish a connection to the robot.
    # Return False with error message if connection
    # cannot be  established
    def connect_real_robot(self):
        return True, ''
        # try:
            # print('Connecting EV3 robot')
            # self.ev3 = tmtcCom.TMTCpi2EV3(self.serialPort, self.mailboxName)
            # print('Bluetooth device is present: ' + self.serialPort)
            # ack, result = self.ev3.sendTC('Heartbeat', False)
            # print(ack, result)
            # if not ack:
            #    print('Heartbeat was not acknowledged. Start program on EV3!')
            #    return False, 'Heartbeat was not acknowledged. Start program on EV3!'
            # else:
            #    print("Heartbeat acknowledged")
            #    return True, "Heartbeat acknowledged"
        # except:
        #    print('\nConnection error during EV3 communication')
        #    print('No device: ', self.serialPort)
        #    return False, 'Robot connection error: No device: ' + self.serialPort

    # Overwritten method of superclass.
    # Ask user if robot is put at initial vertex
    # with initial orientation.
    def put_real_robot_at_init_pos(self):
        self.view.show('Click OK if robot is located at vertex ' + str(self.planner.startNode.x) +
                       '-' + str(self.planner.startNode.y) + ' with orientation ' +
                       self.actualOrientation + '?')

    # Overwritten method of superclass
    # Return if a real robot reports an obstacle ahead in driving direction
    # in the telemetry.
    def robot_reports_obstacle(self):
        # Return True if the last tele-command has been reported an obstacle
        # on the next vertex in view direction. If robot is driving then
        # stop it.
        if self.robot.detectRealObstacle and self.lastCommand == 'Drive':
            self.action_at_end()  # Stop robot: do not crash
        return self.robot.detectRealObstacle

    # Overwritten method of superclass
    # Command robot with the next move action. This can be a turn or a
    # forward drive.
    # Return True, if command was executed without error
    # Return additionally the telemetry from the robot
    def command_robot(self, orientation):
        command = self.direction_dict[self.actualOrientation][orientation]
        self.robot.send(command)
        print('Commanding EV3:', command)
        # Send a tele-command, await telemetry and wait for max. 12 seconds
        # ack, reply = self.ev3.0.0
        # sendTC(command, True, 12)
        # self.lastCommand = command
        # If telemetry contains a ! at end then an obstacle is ahead.
        # self.detectRealObstacle = reply[len(reply) - 1] == '!'
        # return ack, reply
        return True, ''

    # Overwritten method of superclass
    # Check for obstacle at start location before robot starts to drive
    # Is there an unplanned obstacle on the next vertex
    # Return True, if command was executed without error
    # Return additionally the telemetry from the robot
    def obstacle_start_check(self):
        print('Commanding EV3: CheckDistance')
        # ack, reply = self.ev3.sendTC('CheckDistance', True, 12)
        # print(ack, reply)
        self.lastCommand = 'CheckDistance'
        # If telemetry contains a ! at end then an obstacle is ahead.
        # self.detectRealObstacle = reply[len(reply) - 1] == '!'
        # return ack, reply
        return self.robot.detectRealObstacle, ''

        # Overwritten method of superclass

    # Robot drives to the goal and must be stopped when
    # it is totally on the goal vertex or a new obstacle appeared.
    # Return True, if command was executed without error
    # Return additionally the telemetry from the robot
    def action_at_end(self):
        print('Commanding EV3: Stop')
        # ack, reply = self.ev3.sendTC('Stop', True, 12)
        self.lastCommand = 'Stop'
        # return ack, reply
        return True, ''

        # Overwritten method of superclass

    # No delay needed here
    def delay(self):
        time.sleep(self.stepDelay)
