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

    def __init__(self, my_view, my_planner):
        print('\nCreating ScreenExecutor')
        self.view = my_view
        self.planner = my_planner
        self.robotIconsIDs = {}  # Dictionary for canvas icon ids
        self.actualOrientation = ""  # North, East, South, West,
        # NorthWest, NorthEast, SouthWest or SouthEast
        self.stepDelay = 0.4  # second(s) delay between execution steps

        self.create_robot_icons()  # Icons used during execution of plan

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
                    self.view.master.update()
                    self.delay()
                    if next_vertex.isObstacle or self.robot_reports_obstacle():
                        # New obstacle occupies next_vertex on path!!! Replanning!!!
                        # New obstacles besides the path are not considered
                        # because the robot does not see them.
                        print('\nNew obstacle at', next_vertex.x, next_vertex.y)
                        if self.robot_reports_obstacle() and not next_vertex.isObstacle:
                            next_vertex.isObstacle = True
                            self.planner.obstacles.add(next_vertex)
                            self.view.update_color(next_vertex, 'brown')
                        print('Replanning!')
                        self.planner.clear_old_path(step)
                        abort = not self.planner.replanning(next_vertex)
                        self.planner.show_and_remember_path()
                        replanned = True
                        print('Replanning done\n')
                    else:
                        if result:
                            result, reply = self.move_robot(self.planner.startNode, next_vertex, self.actualOrientation)
                        self.view.master.update()
                        self.delay()
                        step += 1
            self.view.canvas_grid.itemconfig(self.robotIconsIDs[self.actualOrientation], state='hidden')
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
    # Return new orientation
    def calc_orientation(self, actual_vertex, next_vertex):
        new_orientation = self.actualOrientation
        if actual_vertex.x == next_vertex.x:
            if actual_vertex.y - 1 == next_vertex.y:
                new_orientation = "South"
            else:
                new_orientation = "North"
        elif actual_vertex.y == next_vertex.y:
            if actual_vertex.x - 1 == next_vertex.x:
                new_orientation = "West"
            else:
                new_orientation = 'East'
        elif actual_vertex.x + 1 == next_vertex.x:
            if actual_vertex.y + 1 == next_vertex.y:
                new_orientation = "NorthEast"
            else:
                new_orientation = "SouthEast"
        elif actual_vertex.x - 1 == next_vertex.x:
            if actual_vertex.y - 1 == next_vertex.y:
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
            result, reply = self.move_robot(self.planner.startNode, self.planner.startNode, new_orientation)
            self.actualOrientation = new_orientation
        return result, reply

    # Calculate the rectangle on screen at the given vertex
    def vertex_to_rect(self, vertex):
        tag = str(vertex.x) + '-' + str(vertex.y)
        rect_handle = self.view.canvas_grid.find_withtag(tag)
        return self.view.canvas_grid.coords(rect_handle)

    # Put robot icon at start of path with initial orientation then
    # orient robot to next vertex.
    # Return True if action was successfully.
    # Return also a string describing the situation.
    def put_robot_at_init_pos(self):
        self.create_robot_icons()
        self.planner.startNode = self.planner.actualPath[0]
        self.actualOrientation = self.view.cbRoboOrientation.get()
        result, reply = self.move_robot(self.planner.vertexGrid[0][0], self.planner.startNode, self.actualOrientation,
                                        command_robot=False)
        self.view.master.update()
        self.delay()
        self.put_real_robot_at_init_pos()
        next_orientation = self.calc_orientation(self.planner.startNode, self.planner.actualPath[1])
        if next_orientation != self.actualOrientation:
            # Orient robot to first vertex of path
            result, reply = self.move_robot(self.planner.startNode, self.planner.startNode, next_orientation)
        else:
            # Is there an unplanned obstacle on the first vertex?
            result, reply = self.obstacle_start_check()
        self.view.master.update()
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
        pass

    # Move robot to aVertex with an orientation
    # Move all polygons to aVertex, only that with given orientation
    # shall be visible. Then command real robot, if any.
    def move_robot(self, from_vertex, to_vertex, orientation, command_robot=True):
        print('\nMove robot to', to_vertex.x, to_vertex.y, orientation)
        result = True
        reply = ''
        rect_from_vertex = self.vertex_to_rect(from_vertex)
        rect_to_vertex = self.vertex_to_rect(to_vertex)
        delta_x = rect_to_vertex[0] - rect_from_vertex[0]
        delta_y = rect_to_vertex[1] - rect_from_vertex[1]
        for key in self.robotIconsIDs:
            self.view.canvas_grid.move(self.robotIconsIDs[key], delta_x, delta_y)  # Moves a delta
        self.view.canvas_grid.itemconfig(self.robotIconsIDs[self.actualOrientation], state='hidden')
        self.view.canvas_grid.itemconfig(self.robotIconsIDs[orientation], state='normal')
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

    # Graphical elements #####################################################################
    # Create robot icons for simulation of moves from start to goal.
    # Initial position of all icons is 0,0 of actual vertexGrid
    def create_robot_icons(self):
        polygon_north = self.view.canvas_grid.create_polygon(10, 0, 20, 35, 0, 35, fill='blue', state='hidden')
        self.robotIconsIDs['North'] = polygon_north
        polygon_south = self.view.canvas_grid.create_polygon(0, 0, 20, 0, 10, 35, fill='blue', state='hidden')
        self.robotIconsIDs['South'] = polygon_south
        polygon_east = self.view.canvas_grid.create_polygon(0, 0, 0, 20, 35, 10, fill='blue', state='hidden')
        self.robotIconsIDs['East'] = polygon_east
        polygon_west = self.view.canvas_grid.create_polygon(0, 10, 35, 0, 35, 20, fill='blue', state='hidden')
        self.robotIconsIDs['West'] = polygon_west

        polygon_north_east = self.view.canvas_grid.create_polygon(30, 0, 0, 24, 18, 33, fill='blue', state='hidden')
        self.robotIconsIDs['NorthEast'] = polygon_north_east
        polygon_north_west = self.view.canvas_grid.create_polygon(0, 0, 30, 24, 14, 33, fill='blue', state='hidden')
        self.robotIconsIDs['NorthWest'] = polygon_north_west
        polygon_south_west = self.view.canvas_grid.create_polygon(0, 30, 18, 0, 30, 16, fill='blue', state='hidden')
        self.robotIconsIDs['SouthWest'] = polygon_south_west
        polygon_south_east = self.view.canvas_grid.create_polygon(30, 30, 12, 0, 0, 16, fill='blue', state='hidden')
        self.robotIconsIDs['SouthEast'] = polygon_south_east

        # Move all polygon to vertex in lower left corner of vertexGrid
        # From that location we can move all polygons to the actual position
        rect = self.vertex_to_rect(self.planner.vertexGrid[0][0])
        x_offset = (rect[0] + rect[2]) // 2
        y_offset = (rect[1] + rect[3]) // 2
        for key in self.robotIconsIDs:
            if key == "West" or key == "East":
                pos_x = x_offset - 17
                pos_y = y_offset - 10
            else:
                pos_x = x_offset - 10
                pos_y = y_offset - 17
            self.view.canvas_grid.move(self.robotIconsIDs[key], pos_x, pos_y)
