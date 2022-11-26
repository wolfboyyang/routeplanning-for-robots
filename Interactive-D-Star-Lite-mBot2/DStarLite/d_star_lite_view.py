#!/usr/bin/python3
############################################################
# Class DStarLiteView
# The class DStarLiteView implements an interactive view
# for the vertexGrid of the D*Lite algorithm. It implements
# the interactive design of the terrain with start-, goal-node
# and obstacles and the path-planning and path execution.
#
# File: d_star_lite_view.py
# Author: Detlef Heinze 
# Version: 1.1    Date: 22.07.2020       
###########################################################

import enum
from tkinter import *
from tkinter import messagebox
from tkinter import ttk

from d_star_lite_planner import *


# Possible states of the application
class AppState(enum.Enum):
    inDesign = 0
    inPlanning = 1
    planPresent = 2
    inExecution = 3
    afterExecution = 4


class DStarLiteView(object):

    # Initialize a new DStarLiteView
    def __init__(self, master):
        self.stepY = None
        self.stepX = None
        self.canvas_grid = None
        self.planner = None
        self.master = master
        self.master.geometry('700x600')
        self.master.resizable(0, 0)
        master.title("Interactive D* Lite 1.0")
        self.appState = AppState.inDesign

        # Default planning grid size
        self.gridHeight = 4
        self.gridWidth = 5

        # tab control: designTab, row=0
        self.tab_control = ttk.Notebook(master)
        self.designTab = ttk.Frame(self.tab_control)
        self.planTab = ttk.Frame(self.tab_control)
        self.execTab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.designTab, text='Design')
        self.tab_control.add(self.planTab, text='Planning')
        self.tab_control.add(self.execTab, text='Execution')

        self.lblGridWith = Label(self.designTab, text="Grid width:")
        self.lblGridWith.grid(column=0, row=0, pady=5, sticky=W)
        self.gridWidthVal = IntVar()
        self.gridWidthVal.set(self.gridWidth)
        self.spinGridWidth = Spinbox(self.designTab, from_=4, to=11, width=5, state='readonly',
                                     textvariable=self.gridWidthVal)
        self.spinGridWidth.grid(column=1, row=0, pady=5, sticky=W)
        self.lblGridHeight = Label(self.designTab, text="Grid height:")
        self.lblGridHeight.grid(column=2, row=0, pady=5, sticky=W)
        self.gridHeightVal = IntVar()
        self.gridHeightVal.set(self.gridHeight)
        self.spinGridHeight = Spinbox(self.designTab, from_=4, to=11, width=5, state='readonly',
                                      textvariable=self.gridHeightVal)
        self.spinGridHeight.grid(column=3, row=0, pady=5, sticky=W)
        self.btnRecreate = Button(self.designTab, text="Recreate grid", command=self.btn_recreate_clicked)
        self.btnRecreate.grid(column=4, row=0, pady=5, padx=5, sticky=W)
        self.tab_control.grid(column=0, row=0)

        # tab control: designTab, row=1
        self.lblClickMode = Label(self.designTab, text="Click mode:")
        self.lblClickMode.grid(column=0, row=1, pady=5, sticky=W)
        self.clickModeVal = IntVar()
        self.clickModeVal.set(1)
        self.rad1 = Radiobutton(self.designTab, text='Start', value=1, variable=self.clickModeVal)
        self.rad2 = Radiobutton(self.designTab, text='Goal', value=2, variable=self.clickModeVal)
        self.rad3 = Radiobutton(self.designTab, text='Obstacle', value=3, variable=self.clickModeVal)
        self.rad1.grid(column=1, row=1)
        self.rad2.grid(column=2, row=1)
        self.rad3.grid(column=3, row=1)

        # tab control: planningTab
        self.lblMode = Label(self.planTab, text="Planning mode:")
        self.lblMode.grid(column=0, row=0, sticky=W)
        self.cbPlanningMode = ttk.Combobox(self.planTab, state="readonly", values=('Fast', 'Slow step', 'Manual step'),
                                           width=12)
        self.cbPlanningMode.current(0)
        self.cbPlanningMode.grid(column=1, row=0, pady=5, padx=0, sticky=W)
        self.h0_check = BooleanVar()
        self.h0_check.set(FALSE)  # set check state
        self.h0Check = Checkbutton(self.planTab, text='h = 0', state=NORMAL, variable=self.h0_check)
        self.h0Check.grid(column=2, row=0, padx=10)
        self.directNeighbors = BooleanVar()
        self.directNeighbors.set(True)  # False= 8 neighbors, True= 4 neighbors
        self.neighbors = Checkbutton(self.planTab, text='Only direct neighbors(4)', variable=self.directNeighbors)
        self.neighbors.grid(column=3, row=0, padx=10)
        self.btnPlan = Button(self.planTab, text="Start planning", command=self.btn_plan_clicked)
        self.btnPlan.grid(column=4, row=0, pady=5, padx=20, sticky=W)

        self.lblPlanHint = Label(self.planTab, text="Planning hint:")
        self.lblPlanHint.grid(column=0, row=1, pady=5, sticky=W)
        self.planHint = StringVar()
        self.planHint.set('-')
        self.lblPlanHintText = Label(self.planTab, text="", textvariable=self.planHint)
        self.lblPlanHintText.grid(column=1, row=1, pady=5, columnspan=2, sticky=W)

        # tab control: execTab
        self.lblExecMode = Label(self.execTab, text="Execution mode:")
        self.lblExecMode.grid(column=0, row=0, sticky=W)
        self.cbExecMode = ttk.Combobox(self.execTab, state="readonly", values=('Screen Simulation', 'Cloud Control'),
                                       width=18)
        self.cbExecMode.current(0)
        self.cbExecMode.grid(column=1, row=0, pady=5, padx=0, sticky=W)
        self.lblRoboOrientation = Label(self.execTab, text="Robot start orientation:")
        self.lblRoboOrientation.grid(column=2, row=0, padx=8, sticky=W)
        self.cbRoboOrientation = ttk.Combobox(self.execTab, state="readonly", values=('North', 'East', 'South', 'West'),
                                              width=8)
        self.cbRoboOrientation.current(0)
        self.cbRoboOrientation.grid(column=3, row=0, pady=5, padx=0, sticky=W)
        self.btnExec = Button(self.execTab, text="Execute plan", command=self.btn_exec_clicked)
        self.btnExec.grid(column=4, row=0, pady=5, padx=20, sticky=W)
        self.lblExecHint = Label(self.execTab, text="Execution hint:")
        self.lblExecHint.grid(column=0, row=1, pady=5, sticky=W)
        self.execHint = StringVar()
        self.execHint.set('-')
        self.lblExecHintText = Label(self.execTab, text="", textvariable=self.execHint)
        self.lblExecHintText.grid(column=1, row=1, pady=5, columnspan=2, sticky=W)

        # Row = 2 the grid
        self.create_grid()

    # Eventhandler ####################################################################

    # Button "Recreate" has been clicked. 
    def btn_recreate_clicked(self):
        # Recreate the planning grid including all variables
        self.planHint.set('-')
        self.master.update()
        self.create_grid()
        self.h0Check.config(state="normal")
        self.neighbors.config(state="normal")
        self.appState = AppState.inDesign

    # Button "Start Planning" has been clicked. Execute planning
    def btn_plan_clicked(self):
        if self.appState != AppState.inDesign:
            messagebox.showinfo('Hint', 'Plan already created')
            return
        self.tab_control.tab(0, state="disabled")
        self.tab_control.tab(2, state="disabled")
        # Check business rules
        if self.planner.are_start_and_goal_set():
            self.planner.hIsZero = self.h0_check.get()
            self.planner.directNeighbors = self.directNeighbors.get()
            self.planHint.set('Planning in progress.......')
            self.appState = AppState.inPlanning
            self.master.update()
            self.planner.main_planning(self.cbPlanningMode.get())
            if self.planner.planReady:
                self.appState = AppState.planPresent
                self.h0Check.config(state="disabled")
                self.neighbors.config(state="disabled")
                self.planHint.set('Planning successful within ' + str(self.planner.plan_steps) + ' steps')
                messagebox.showinfo('Hint', 'Plan is ready')
            else:
                self.appState = AppState.inDesign
                self.planHint.set('Planning unsuccessful !!!')
                messagebox.showinfo('Hint', 'No plan exists')
                messagebox.showinfo('Hint', 'Recreating grid')
                self.btn_recreate_clicked()

        else:
            messagebox.showinfo('Hint', 'Start- and/or Goalvertex is not definied')
            self.appState = AppState.inDesign
        self.tab_control.tab(0, state="normal")
        self.tab_control.tab(2, state="normal")

    # Button "Execute" has been clicked
    def btn_exec_clicked(self):
        # Check business rules
        if not self.planner.planReady:
            messagebox.showinfo('Hint', 'No plan present. Goto design and planning tab.')
        else:
            self.appState = AppState.inExecution
            self.tab_control.tab(0, state="disabled")
            self.tab_control.tab(1, state="disabled")
            self.clickModeVal.set(3)  # Obstacle Mode
            self.execHint.set('Click to add obstacles during plan execution')
            result = self.planner.execute_plan(self.cbExecMode.get())
            if result[0]:
                messagebox.showinfo('Hint', 'Plan has been executed!')
                self.appState = AppState.afterExecution
            else:
                messagebox.showinfo('Hint', result[1])
                self.appState = AppState.planPresent
            self.planHint.set('-')
            self.tab_control.tab(0, state="normal")
            self.tab_control.tab(1, state="normal")

    # Calculate the x and y coordinate of vertexGrid which the user has clicked.
    # If a g- or rsh- value was clicks find the rectangle below it.
    # Return 4 values: True, if click was within a rectangle,
    #                  the x anf y coord of the rectangle in vertexGrid
    #                  and the rectangle clicked
    def get_click_in_rectangle(self, current):
        if self.canvas_grid.gettags(current)[0] == 'rect':
            return True, self.canvas_grid.gettags(current)[1], \
                self.canvas_grid.gettags(current)[2], \
                current
        if self.canvas_grid.gettags(current)[0] == 'gtext':
            below = self.canvas_grid.find_below(current)
            if self.canvas_grid.gettags(below)[0] == 'rect':
                return True, self.canvas_grid.gettags(below)[1], \
                    self.canvas_grid.gettags(below)[2], \
                    below
        if self.canvas_grid.gettags(current)[0] == 'rshtext':
            below = self.canvas_grid.find_below(current)
            below1 = self.canvas_grid.find_below(below)
            if self.canvas_grid.gettags(below1)[0] == 'rect':
                return True, self.canvas_grid.gettags(below1)[1], \
                    self.canvas_grid.gettags(below1)[2], \
                    below1
        else:  # no rectangle clicked
            return False, 0, 0, current

    # Handle the click-event in the canvas if appState is inDesing or inExecution
    def canvas_clicked(self, event):
        print("clicked at", event.x, event.y)
        if (self.appState == AppState.inDesign or self.appState == AppState.inExecution) and \
                self.canvas_grid.find_withtag(CURRENT):
            print(self.canvas_grid.gettags(CURRENT))
            print(self.get_click_in_rectangle(CURRENT))
            result = self.get_click_in_rectangle(CURRENT)
            if result[0]:  # Click within a rectangle of the grid
                x = result[1]  # x coordinate in grid
                y = result[2]  # y coordinate in grid
                click_mode = self.clickModeVal.get()
                if not self.is_node_occupied(x, y, click_mode):
                    if click_mode == 1:
                        # Set start node
                        if self.planner.get_start_coordinates()[0] != float('inf'):
                            tag = str(self.planner.get_start_coordinates()[0]) + '-' + str(
                                self.planner.get_start_coordinates()[1])
                            handle = self.canvas_grid.find_withtag(tag)
                            self.canvas_grid.itemconfig(handle, fill="white")
                        self.canvas_grid.itemconfig(result[3], fill="green")
                        self.planner.set_start_coordinates(x, y)
                    elif click_mode == 2:
                        # Set goal node
                        old_goal = self.planner.get_goal_coordinates()[0] != float('inf')
                        if old_goal:
                            old_goal_coord = self.planner.get_goal_coordinates()
                            tag = str(old_goal_coord[0]) + '-' + str(old_goal_coord[1])
                            handle = self.canvas_grid.find_withtag(tag)
                            self.canvas_grid.itemconfig(handle, fill="white")
                        self.canvas_grid.itemconfig(result[3], fill="red")
                        self.planner.set_goal_coordinates(x, y)
                        self.update_rsh(x, y)
                        if old_goal:
                            self.update_rsh(old_goal_coord[0], old_goal_coord[1])
                    elif click_mode == 3:
                        # Set or reset obstacle node
                        node = self.planner.vertexGrid[int(x)][int(y)]
                        if not node.isObstacle:
                            node.isObstacle = True
                            self.canvas_grid.itemconfig(result[3], fill="brown")
                            self.planner.obstacles.add(node)
                        elif not self.appState == AppState.inExecution:
                            # Obstacles can only be removed in Design
                            node.isObstacle = False
                            self.canvas_grid.itemconfig(result[3], fill="white")
                            self.planner.obstacles.remove(node)
                        self.update_rsh(x, y)
        else:
            self.show('Action not possible in this state of planning. Recreate grid.')

    @staticmethod
    def show(message):
        messagebox.showinfo('Hint', message)

    # Functions ############################################################

    # Create a new planner and draw the grid
    def create_grid(self):
        # Create a planner and initialize it
        print('Creating planner')
        self.planner = DStarLitePlanner(self,
                                        grid_width=self.gridWidthVal.get(),
                                        grid_height=self.gridHeightVal.get(),
                                        h_is_zero=self.h0_check.get(),
                                        direct_neighbors=self.directNeighbors.get())
        horizon_shift = 30
        self.canvas_grid = Canvas(self.master, height=800, width=600 + horizon_shift)
        self.canvas_grid.bind("<Button-1>", self.canvas_clicked)
        self.canvas_grid.grid(column=0, row=2, pady=10, padx=10, columnspan=6, sticky=W)
        self.draw_planning_grid(horizon_shift)

    # Draw the actual status of the planning grid
    def draw_planning_grid(self, horizon_shift):
        # Draw planning grid
        self.canvas_grid.create_rectangle(0, 0, 680, 430, outline="white", fill="white")
        self.stepX = 600 // self.gridWidthVal.get()
        self.stepY = 400 // self.gridHeightVal.get()
        row_count = self.gridHeightVal.get() - 1
        column_count = 0
        # Add rectangles with g and rsh values
        for i in range(0, 600 - self.stepX + 1, self.stepX):
            for j in range(0, 400 - self.stepY + 1, self.stepY):
                self.canvas_grid.create_rectangle(i + horizon_shift, j + 2, i + horizon_shift + self.stepX,
                                                  j + self.stepY + 2, fill="white",
                                                  tags=('rect', column_count, row_count, str(column_count)
                                                        + '-' + str(row_count)))
                self.canvas_grid.create_text(i + horizon_shift + self.stepX // 2, j + 2 + self.stepY // 3,
                                             text='g:' + str(self.planner.vertexGrid[column_count][row_count].g),
                                             tags=('gtext', 'g-' + str(column_count) + '-' + str(row_count)))
                self.canvas_grid.create_text(i + horizon_shift + self.stepX // 2 - 5, j + 2 + self.stepY // 3 + 15,
                                             text='rsh:' + str(self.planner.vertexGrid[column_count][row_count].rsh),
                                             tags=('rshtext', 'rsh-' + str(column_count) + '-' + str(row_count)))
                row_count -= 1
            column_count += 1
            row_count = self.gridHeightVal.get() - 1
        # Add row and column numbers
        row_count = self.gridHeightVal.get() - 1
        for i in range(0, 400 - self.stepY + 1, self.stepY):
            self.canvas_grid.create_text(15, i + self.stepY / 2, text=str(row_count))
            row_count -= 1
        column_count = 0
        for i in range(0, 600, self.stepX):
            self.canvas_grid.create_text(i + horizon_shift + self.stepX / 2, 400 + 15, text=str(column_count))
            column_count += 1

    # Update rsh-value on screen
    def update_rsh(self, x, y):
        tag = 'rsh-' + str(x) + '-' + str(y)
        # print('rsh-tag:' + tag)
        handle = self.canvas_grid.find_withtag(tag)
        value = round(self.planner.vertexGrid[int(x)][int(y)].rsh, 2)
        self.canvas_grid.itemconfig(handle, text='rsh:' + str(value))
        # print(value)

    # Update g-value on screen
    def update_g(self, x, y):
        tag = 'g-' + str(x) + '-' + str(y)
        # print('g:' + tag)
        handle = self.canvas_grid.find_withtag(tag)
        value = round(self.planner.vertexGrid[int(x)][int(y)].g, 2)
        self.canvas_grid.itemconfig(handle, text='g:' + str(value))

    # Update-color of vertex on screen if it is not the start- or goal-node
    def update_color(self, vertex, color):
        tag = str(vertex.x) + '-' + str(vertex.y)
        handle = self.canvas_grid.find_withtag(tag)
        self.canvas_grid.itemconfig(handle, fill=color)

    # Check if the clicked rectangle is occupied by other or the same
    # type of node regarding the clickMode
    def is_node_occupied(self, x, y, click_mode):
        start = self.planner.get_start_coordinates()
        if [int(x), int(y)] != start:
            goal = self.planner.get_goal_coordinates()
            if [int(x), int(y)] != goal:
                ob = self.planner.vertexGrid[int(x)][int(y)].isObstacle
                if ob and click_mode <= 2:
                    messagebox.showwarning('Vertex occupied', 'The vertex is occupied by an obstacle')
                    return True
                else:
                    return False
            else:
                messagebox.showwarning('Vertex occupied', 'The vertex is occupied by a goal')
                return True
        else:
            messagebox.showwarning('Vertex occupied', 'The vertex is occupied by a start node')
            return True

    # Print function for test purpose
    def dump_vertices(self):
        [[self.planner.vertexGrid[x][y].print() for x in range(self.gridWidth)] for y in range(self.gridHeight)]
