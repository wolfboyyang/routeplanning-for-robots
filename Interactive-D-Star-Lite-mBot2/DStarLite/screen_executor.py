#!/usr/bin/python3
############################################################
# Class ScreenExecutor
# The class ScreenExecutor simulates the execution of the
# path by a robot. The simulated robot is shown on screen 
# and drives from vertex to vertex of the path. Also
# changes in the direction are simulated (N, E, S, W) and
# (SW, SE, NW, NE).
# 
# File: screen_executor.py
# Author: Detlef Heinze 
# Version: 1.1    Date: 22.07.2020       
###########################################################

import time


class ScreenExecutor(object):

    def __init__(self, view, my_planner):
        print('\nCreating ScreenExecutor')
        self.view = view
        self.planner = my_planner
        self.robotIconsIDs = {}  # Dictionary for canvas icon ids
        self.actualOrientation = ""  # North, East, South, West,
        # NorthWest, NorthEast, SouthWest or SouthEast
        self.stepDelay = 0.4  # second(s) delay between execution steps

    # Has to be overwritten in subclasses controlling real robots
    # Check business rules regarding the plan execution.
    # Return True or False
    def execution_allowed(self):
        # This class has no restrictions.
        return True

    # Execute the actual plan. Let the robot drive from startNode to goalNode.
    # Re-plan if an obstacle suddenly appears on the path.
    # Return True if execution was successfully, False otherwise.
    # Return also a string describing the result
    def execute_plan(self):
        if not self.execution_allowed():
            return False, "Plan incompatible with executor. Check direct neighbors setting (Tab: Planning)"
        result = self.connect_real_robot()
        if not result[0]:  # no connection possible
            return result[0], result[1]
        else:
            print('Starting plan execution')
            result, reply = self.put_robot_at_init_pos()
            abort = False
            # Now execute the plan including orientation of the robot
            while self.planner.startNode != self.planner.goalNode \
                    and not abort and result:
                step = 1
                replanned = False
                while step < len(self.planner.actualPath) \
                        and not replanned and result:
                    next_vertex = self.planner.actualPath[step]
                    result, reply = self.orient_robot_to(next_vertex)
                    self.delay()
                    if next_vertex.isObstacle or self.robot_reports_obstacle():
                        # New obstacle occupies next_vertex on path!!! Replanning!!!
                        # New obstacles besides the path are not considered
                        # because the robot does not see them.
                        print('\nNew obstacle at', next_vertex.x, next_vertex.y)
                        if self.robot_reports_obstacle() and not next_vertex.isObstacle:
                            next_vertex.isObstacle = True
                            self.planner.obstacles.add(next_vertex)
                            self.view.update_color(next_vertex, 'red')
                        print('Replanning!')
                        self.planner.clear_old_path(step)
                        abort = not self.planner.replanning(next_vertex)
                        self.planner.show_and_remember_path()
                        self.view.update_color(self.planner.startNode, 'blue100')
                        replanned = True
                        print('Replanning done\n')
                    else:
                        if result:
                            result, reply = self.move_robot(next_vertex, self.actualOrientation)
                        self.delay()
                        step += 1
            # self.view.canvas_grid.itemconfig(self.robotIconsIDs[self.actualOrientation], state='hidden')
            if not abort and result:
                result, reply = self.action_at_end()
                if result:
                    print('Goal reached.')
                    return True, 'Goal reached.'
                else:
                    return False, 'Robot error at goal'
            elif abort:
                print('No path to goal exists')
                result, reply = self.action_at_end()
                return False, 'No path to goal exists'
            elif not result:
                print('Abort with robot connection error')
                return result, 'Abort with robot connection error'

    # Calculate the orientation to the next vertex in the plan
    # which has to be a neighbor.
    # Note: Origin in flutter is topLeft while in Tkinter is bottomLeft
    # Return new orientation
    def calc_orientation(self, actual_vertex, next_vertex):
        new_orientation = self.actualOrientation
        if actual_vertex.x == next_vertex.x:
            if actual_vertex.y + 1 == next_vertex.y:
                new_orientation = "South"
            else:
                new_orientation = "North"
        elif actual_vertex.y == next_vertex.y:
            if actual_vertex.x - 1 == next_vertex.x:
                new_orientation = "West"
            else:
                new_orientation = 'East'
        elif actual_vertex.x + 1 == next_vertex.x:
            if actual_vertex.y - 1 == next_vertex.y:
                new_orientation = "NorthEast"
            else:
                new_orientation = "SouthEast"
        elif actual_vertex.x - 1 == next_vertex.x:
            if actual_vertex.y + 1 == next_vertex.y:
                new_orientation = "SouthWest"
            else:
                new_orientation = "NorthWest"
        print('Orientation: ', new_orientation)
        return new_orientation

    # Orient the robot to the next vertex.
    # Return True if action was successful.
    # Return also a string describing the situation.
    def orient_robot_to(self, next_vertex):
        print('\nOrient robot to next vertex', next_vertex.x, next_vertex.y)
        new_orientation = self.calc_orientation(self.planner.startNode, next_vertex)
        result = True
        reply = ''
        if self.actualOrientation != new_orientation:
            result, reply = self.move_robot(self.planner.startNode, new_orientation)
            self.actualOrientation = new_orientation
        return result, reply

    # Put robot icon at start of path with initial orientation then
    # orient robot to next vertex.
    # Return True if action was successfully.
    # Return also a string describing the situation.
    def put_robot_at_init_pos(self):
        self.planner.startNode = self.planner.actualPath[0]
        self.actualOrientation = self.view.robotStartOrientation
        self.view.show_robot(False)
        print(self.actualOrientation)
        result, reply = self.move_robot(self.planner.startNode, self.actualOrientation,
                                        command_robot=False)
        self.delay()
        self.put_real_robot_at_init_pos()
        next_orientation = self.calc_orientation(self.planner.startNode, self.planner.actualPath[1])
        if next_orientation != self.actualOrientation:
            # Orient robot to first vertex of path
            result, reply = self.move_robot(self.planner.startNode, next_orientation)
        else:
            # Is there an unplanned obstacle on the first vertex?
            result, reply = self.obstacle_start_check()
        self.delay()
        return result, reply

    # Has to be overwritten in subclasses controlling real robots
    # Establish a connection to the robot.
    # Return False with error message if connection
    # cannot be  established.
    # Return also a string describing the situation
    def connect_real_robot(self):
        # The screenExecutor always has a connection
        return True, ''

    # Has to be overwritten in subclasses controlling real
    # robots. Ask user if robot is put at initial vertex
    # with initial orientation. 
    def put_real_robot_at_init_pos(self):
        self.view.show_robot(True)
        self.delay()

    # Move robot to aVertex with an orientation
    # Move all polygons to aVertex, only that with given orientation
    # shall be visible. Then command real robot, if any.
    def move_robot(self, to_vertex, orientation, command_robot=True):
        print('\nMove robot to', to_vertex.x, to_vertex.y, orientation)
        result = True
        reply = ''
        self.view.move(to_vertex.x, to_vertex.y, orientation)  # Moves a delta
        if command_robot:
            # To be overwritten in subclasses for real robots
            result, reply = self.command_robot(orientation)
        self.planner.startNode = to_vertex
        self.actualOrientation = orientation
        return result, reply

    # To be overwritten in subclasses with real robots (no simulation)
    # Command a real robot.
    # Return True if action was successfully.
    # Return also a string describing the situation.
    def command_robot(self, orientation):
        # Do nothing here because this is a screen simulator
        return True, ''

    # To be overwritten in subclasses with real robots (no simulation)
    # Return if a real robot reports an obstacle ahead in driving direction
    # in the telemetry.
    def robot_reports_obstacle(self):
        # No real robot here
        return False

    # To be overwritten in subclasses with real robots (no simulation)
    # Check for obstacle at start location before robot starts to drive
    # Is there an unplanned obstacle on the next vertex
    def obstacle_start_check(self):
        # Do nothing here because this is a screen simulator
        return True, ''

    # To be overwritten in subclasses with real robots (no simulation)
    # Add action when path has been executed or robot has to stop when
    # re-planning must be done because of a new obstacle
    # Return True if action was successfully.
    # Return also a string describing the situation.
    def action_at_end(self):
        # Do nothing here because this is a screen simulator
        return True, ''

    # To be overwritten in subclasses.
    # Add some delay between steps of plan execution for screen simulation 
    def delay(self):
        time.sleep(self.stepDelay)
