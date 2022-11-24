#!/usr/bin/python3
############################################################
# Class Vertex
# The class Vertex represents a single vertex in the
# path-planning algorithm D*Lite. A vertex is a field
# in the matrix of the area where the robot drives.
#
# File: vertex.py
# Author: Detlef Heinze 
# Version: 1.0    Date: 22.07.2020       
###########################################################

import math


class Vertex(object):

    def __init__(self, x=0, y=0):
        self.x = x  # x-coordinate in the vertexGrid (not canvas)
        self.y = y  # y-coordinate in the vertexGrid (not canvas)
        self.g = float('inf')  # Estimated cost to goal
        self.rsh = float('inf')  # Sum of costs to goal so far
        # if g !=rsh then vertex is inconsistent
        self.isGoal = False
        self.isObstacle = False
        self.key = 0

        # If vertex is a goal then set rsh value to 0 otherwise to infinite

    def set_is_goal(self, is_goal):
        self.isGoal = is_goal
        if is_goal:
            self.rsh = 0
        else:
            self.rsh = float('inf')

    # If vertex is an obstacle set rsh to infinite
    def set_is_obstacle(self, is_obstacle):
        self.isObstacle = is_obstacle
        if is_obstacle:
            self.rsh = float('inf')

            # CalculateKey function of the D*Lite algorithm

    # Return the calculated key for sorting.
    def calculate_key(self, start_node, k, is_zero, direct_neighbors):
        if self.g < self.rsh:
            min1 = self.g
        else:
            min1 = self.rsh
        self.key = (min1 + self.h(start_node, is_zero, direct_neighbors) + k, min1)
        return self.key

    # Calculate the heuristic-value of the vertex
    def h(self, start_node, is_zero=True, direct_neighbors=False):
        if is_zero:
            # Do not use a heuristic. Then more planning steps are needed
            return 0
        elif direct_neighbors:
            # max. 4 neighbors, use exact distance without considering obstacles
            return abs(self.x - start_node.x) + abs(self.y - start_node.y)
        else:
            # max. eight neighbors: use euclidean distance
            return math.sqrt(math.pow(self.x - start_node.x, 2) + math.pow(self.y - start_node.y, 2))

    # Define a "<"  operator for comparison of two vertices
    def __lt__(self, another_vertex):
        return self.key < another_vertex.key

    def print(self):
        print('x:', self.x, 'y:', self.y, 'g:', self.g,
              'rsh:', self.rsh, 'IsGoal:', self.isGoal,
              'IsObstacle:', self.isObstacle)


if __name__ == "__main__":
    s = Vertex()
    s.print()
    s.set_is_goal(True)
    s.print()
    s2 = Vertex()
    print(s < s2)
