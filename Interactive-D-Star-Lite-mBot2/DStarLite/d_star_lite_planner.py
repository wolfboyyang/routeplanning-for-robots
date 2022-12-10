#!/usr/bin/python3
############################################################
# Class DStarLitePlanner
# This class implements the planning algorithm D* Lite 
# (see Sven Koenig, Maxim Likhachev, 2002) on a 
# two-dimensional grid of vertices (Class Vertex) with
# additional support for an interactive view.
#
# File: d_star_lite_planner.py
# Author: Detlef Heinze 
# Version: 1.1    Date: 05.06.2020       
###########################################################

import platform as pf  # Used for check if program runs on
import time

from priority_queue import PriorityQueue
from screen_executor import ScreenExecutor
from vertex import Vertex
from cloud_executor import CloudExecutor


class DStarLitePlanner(object):

    # Create a new initialized DStarLitePlanner with a vertex-grid
    def __init__(self, my_view, grid_width=5, grid_height=4, h_is_zero=True, direct_neighbors=False):
        self.stepDelay = None
        self.plan_steps = None
        self.k = None
        self.view = my_view
        self.width = grid_width
        self.height = grid_height
        self.directNeighbors = direct_neighbors  # false=8, true=4
        self.vertexGrid = [[Vertex(x, y) for y in range(grid_height)] for x in range(grid_width)]
        print(f'Creating vertex grid with height: {grid_height} and width:{grid_width} \n')
        self.startCoordinates = [float('inf'), float('inf')]
        self.goalCoordinates = [float('inf'), float('inf')]
        self.obstacles = set()
        self.startNode = None
        self.goalNode = None
        self.lastNode = None
        self.hIsZero = h_is_zero
        self.priorityQueue = PriorityQueue()  # The priority queue U
        self.planReady = False  # True if a plan (= a path) is present
        self.actualPath = []  # Sequence of vertices from start to goal
        self.executor = None  # Plan executor

    # ### Functions for interactive view ########################################################

    def set_start_coordinates(self, x=0, y=0):
        self.startCoordinates = [int(x), int(y)]
        print('  New start coordinates:', self.startCoordinates)

    def get_start_coordinates(self):
        return self.startCoordinates

    def set_goal_coordinates(self, x=0, y=0):
        if self.goalCoordinates[0] != float('inf'):
            # Old goal-node
            vertex = self.vertexGrid[int(self.goalCoordinates[0])][int(self.goalCoordinates[1])]
            vertex.set_is_goal(False)
        self.goalCoordinates = [x, y]
        self.vertexGrid[self.goalCoordinates[0]][self.goalCoordinates[1]].set_is_goal(True)
        print('  New goal coordinates:', self.goalCoordinates)

    def get_goal_coordinates(self):
        return self.goalCoordinates

    def are_start_and_goal_set(self):
        return (self.get_start_coordinates() != [float('inf'), float('inf')]) and \
            self.get_goal_coordinates() != [float('inf'), float('inf')]

    # Execute the created plan.
    def execute_plan(self, exec_mode_str):
        if exec_mode_str == 'Screen Simulation':
            self.executor = ScreenExecutor(self.view, self)
            result = self.executor.execute_plan()
            return result
        # communicate with robot via MQTT
        elif exec_mode_str == 'Cloud Control':
            self.executor = CloudExecutor(self.view, self)
            result = self.executor.execute_plan()
            return result

    # #### D* Lite Algorithm #############################################################

    # Initialize the planning process. Function implements the 'Initialize' procedure
    # of the D*Lite algorithm.
    def initialize_planning(self):
        print('Initialize planning:')
        self.goalNode = self.vertexGrid[int(self.goalCoordinates[0])][int(self.goalCoordinates[1])]
        self.k = 0.0
        # All vertices have been already initialized with inf-value in vertex.py.
        # Also, the goal node's rsh value is already initialized with 0 in the interactive view
        # Add now the inconsistent goal node into the priority queue.
        key = self.goalNode.calculate_key(self.startNode, self.k, self.hIsZero, self.directNeighbors)
        self.priorityQueue.insert(self.goalNode, key)
        print('Start- and goal-node:')
        self.startNode.print()
        self.goalNode.print()

    # Function implements the ComputeShortestPath function of the D*Lite algorithm
    def compute_shortest_path(self):
        print('\nComputing shortest path')
        self.plan_steps = 0  # counts loops of while-statement
        while (self.priorityQueue.top_key() < self.startNode.calculate_key(self.startNode, self.k, self.hIsZero,
                                                                           self.directNeighbors)) or \
                (self.startNode.rsh != self.startNode.g):
            k_old = self.priorityQueue.top_key()
            u = self.priorityQueue.pop()
            if u not in self.obstacles:
                self.update_vertex_color(u, 'green')
            k = u.calculate_key(self.startNode, self.k, self.hIsZero, self.directNeighbors)
            if k_old < k:
                self.priorityQueue.insert(u, k)
                self.update_vertex_color(u, 'orange')
            elif u.g > u.rsh:
                u.g = u.rsh
                self.view.update_g(u.x, u.y)
                for pred in self.neighbors(u):
                    self.update_vertex(pred)
            else:
                u.g = float('inf')
                self.view.update_g(u.x, u.y)
                pred_plus_u = self.neighbors(u)
                pred_plus_u.append(u)
                for i in pred_plus_u:
                    self.update_vertex(i)
            self.plan_steps += 1
            # Interactive behavior:
            if self.stepDelay > 0:
                time.sleep(self.stepDelay)
                self.view.page.update()
            elif self.stepDelay < 0:
                self.view.show('Press ok for next step')

    # Main planning function of the D* Lite algorithm
    def main_planning(self, planning_mode='Run to result'):
        print('\nStart planning using mode:', planning_mode)
        if planning_mode == 'Slow step':
            self.stepDelay = 2  # 2s delay
        elif planning_mode == 'Manual step':
            self.stepDelay = -1  # User presses button to go forward
        else:
            self.stepDelay = 0  # 0 ms delay
        self.planReady = False
        start_time = time.time()
        # Start the planning algorithm
        self.startNode = self.vertexGrid[int(self.startCoordinates[0])][int(self.startCoordinates[1])]
        self.lastNode = self.startNode
        self.initialize_planning()
        self.compute_shortest_path()
        print('End ComputeShortestPath')
        print('Time to plan:', time.time() - start_time, 's\n')

        # A path exists if g(startNode) != float('inf')
        # Mark the path on screen in light blue
        self.planReady = self.startNode.g != float('inf')
        self.actualPath = []
        self.show_and_remember_path()

    # Utilities for planning #########################################################

    # Calculate the cost of moving to a neighbor vertex
    def neighbor_cost(self, from_vertex, to_vertex):
        if to_vertex.isObstacle or from_vertex.isObstacle:
            return float('inf')  # Do not move in or from an obstacle
        elif ((abs(from_vertex.x - to_vertex.x) == 0) and
              (abs(from_vertex.y - to_vertex.y) == 1)) or\
                ((abs(from_vertex.x - to_vertex.x) == 1) and
                 (abs(from_vertex.y - to_vertex.y) == 0)):
            return 1  # straight move
        elif (abs(from_vertex.x - to_vertex.x) == 1 and
              abs(from_vertex.y - to_vertex.y) == 1):
            return 1.4  # diagonal move
        else:
            raise Exception('NeighborCost: Vertex is not a neighbor')

    # Calculate neighbors of a vertex depending on the
    # maximum count (4 or 8). Return neighbor vertices.
    def neighbors(self, vertex):
        result = []
        if not self.directNeighbors:  # 8 neighbors
            for x in range(vertex.x - 1, vertex.x + 2):
                for y in range(vertex.y - 1, vertex.y + 2):
                    if x in range(self.width) and \
                            y in range(self.height) and \
                            not (x == vertex.x and y == vertex.y):
                        result.append(self.vertexGrid[x][y])
        else:  # 4 neighbors
            if vertex.x - 1 >= 0:
                result.append(self.vertexGrid[vertex.x - 1][vertex.y])
            if vertex.x + 1 < self.width:
                result.append(self.vertexGrid[vertex.x + 1][vertex.y])
            if vertex.y - 1 >= 0:
                result.append(self.vertexGrid[vertex.x][vertex.y - 1])
            if vertex.y + 1 < self.height:
                result.append(self.vertexGrid[vertex.x][vertex.y + 1])
        return result

    # Calculate the neighbor with the smallest sum of g and rsh-value.
    # Used after planning for finding the cheapest path.
    def calc_cheapest_neighbor(self, vertex):
        neighbors = self.neighbors(vertex)
        cheapest = neighbors[0]
        for i in range(1, len(neighbors)):
            if (cheapest.g + cheapest.rsh) > (neighbors[i].g + neighbors[i].rsh):
                cheapest = neighbors[i]
        return cheapest

    # Function implements the UpdateVertex procedure of the D*Lite algorithm
    # Only calls for update on screen are added
    def update_vertex(self, vertex):
        print('Update vertex', vertex.x, vertex.y)
        if vertex != self.goalNode:
            # Calculate new rsh(aVertex)
            all_neighbors = self.neighbors(vertex)
            values = []
            for s in all_neighbors:
                value = self.neighbor_cost(vertex, s) + s.g
                values.append(value)
            sorted_values = sorted(values)
            vertex.rsh = sorted_values[0]
            # Update rsh-value on screen
            self.view.update_rsh(vertex.x, vertex.y)
        if vertex in self.priorityQueue:
            self.priorityQueue.remove(vertex)
            print('Removed', vertex.x, vertex.y)
        if vertex.g != vertex.rsh and not vertex.isObstacle:  # obstacle could not pass
            key = vertex.calculate_key(self.startNode, self.k, self.hIsZero, self.directNeighbors)
            self.priorityQueue.insert(vertex, key)
            print(vertex.x, vertex.y, 'added to priorityQueue')
            self.update_vertex_color(vertex, 'orange')

    # Show the planned path on the view and remember the path
    # for execution.
    def show_and_remember_path(self):
        node = self.lastNode  # from here to goal
        self.actualPath = []
        while (node != self.goalNode) and self.planReady:
            self.actualPath.append(node)
            node = self.calc_cheapest_neighbor(node)
            if node != self.goalNode and not node.isObstacle:
                self.view.update_color(node, 'lightblue')
            self.planReady = node.g != float('inf')
        if self.planReady:
            self.actualPath.append(self.goalNode)

    def clear_old_path(self, start_step):
        # Re-planning occurred. Remove old path#
        i = start_step
        node = self.actualPath[i]
        while node != self.goalNode:
            if node not in self.obstacles:
                self.view.update_color(node, 'green')
            i += 1
            node = self.actualPath[i]

    def update_vertex_color(self, vertex, color):
        if not vertex == self.startNode and not vertex == self.goalNode:
            self.view.update_color(vertex, color)

    # New obstacle on planned path during plan execution has been found. 
    # Re-plan the path to goal
    # Return if a plan exists.
    def replanning(self, a_vertex):
        self.k = self.k + self.lastNode.h(self.startNode, self.hIsZero, self.directNeighbors)
        self.lastNode = self.startNode
        self.update_vertex(a_vertex)
        neighbors = self.neighbors(a_vertex)
        for n in neighbors:
            self.update_vertex(n)
        self.compute_shortest_path()
        self.planReady = self.startNode.g != float('inf')
        return self.planReady
