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
import flet as ft
from math import pi
from d_star_lite_planner import *


# Possible states of the application
class AppState(enum.Enum):
    inDesign = 0
    inPlanning = 1
    planPresent = 2
    inExecution = 3
    afterExecution = 4


class CellType(enum.Enum):
    Empty = 0
    Start = 1
    Goal = 2
    Obstacle = 3


class Orientation(enum.Enum):
    North = 0
    NorthEast = pi/4
    East = pi/2
    SouthEast = 3*pi/4
    South = pi
    SouthWest = 5*pi/4
    West = 3*pi/2
    NorthWest = 7*pi/4


class DStarLiteView:

    # Initialize a new DStarLiteView
    def __init__(self, page: ft.Page):
        self.stepY = None
        self.stepX = None
        self.planner = None
        self.page = page
        page.title = 'Interactive D* Lite 2.0'
        self.appState = AppState.inDesign

        # Default planning grid size
        self.gridHeight = 4
        self.gridWidth = 5

        self.grid_width = ft.Ref[ft.Dropdown]()
        self.grid_height = ft.Ref[ft.Dropdown]()
        self.design_tab = ft.Ref[ft.Tab]()

        self.page.on_resize = self.page_resize

        self.canvas_width = self.page.width - 20
        self.canvas_height = self.page.height - 190
        self.grid_cell_width = self.canvas_width / self.gridWidth
        self.grid_cell_height = self.canvas_height / self.gridHeight

        def update_grid_width(e):
            self.gridWidth = int(e.control.value)
            self.grid_cell_width = self.canvas_width / self.gridWidth

        def update_grad_height(e):
            self.gridHeight = int(e.control.value)
            self.grid_cell_height = self.canvas_height / self.gridHeight

        def update_robot_start_orientation(e):
            self.robotStartOrientation = e.control.value

        self.planningMode = 'Fast'
        self.directNeighbors = True
        self.h0Check = False
        self.planning_mode = ft.Ref[ft.Dropdown]()
        self.h0_check = ft.Ref[ft.Checkbox]()
        self.direct_neighbors = ft.Ref[ft.Checkbox]()
        self.planning_hint = ft.Ref[ft.Text]()
        self.planning_tab = ft.Ref[ft.Tab]()

        self.executionMode = 'Screen Simulation'
        self.robotStartOrientation = 'North'
        self.execution_mode = ft.Ref[ft.Dropdown]()
        self.execution_tab = ft.Ref[ft.Tab]()

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=100,
            tabs=[
                # tab control: Design Tab
                ft.Tab(
                    'Design',
                    ft.Column([
                        # tab control: Design Tab, row=0
                        ft.ResponsiveRow(
                            [
                                ft.Dropdown(
                                    ref=self.grid_width,
                                    label='Grid width',
                                    hint_text='length from east to west',
                                    options=[ft.dropdown.Option(x) for x in range(4, 12)],
                                    value=str(self.gridWidth),
                                    alignment=ft.alignment.center,
                                    autofocus=True,
                                    col={'xs': 3, 'sm': 2},
                                    on_change=update_grid_width
                                ),
                                ft.Dropdown(
                                    ref=self.grid_height,
                                    label='Grid height',
                                    hint_text='length from north to south',
                                    options=[ft.dropdown.Option(x) for x in range(4, 12)],
                                    value=str(self.gridHeight),
                                    alignment=ft.alignment.center,
                                    autofocus=True,
                                    col={'xs': 3, 'sm': 2},
                                    on_change=update_grad_height,
                                ),
                                ft.FilledButton(
                                    'Recreate grid',
                                    col={'xs': 6, 'sm': 4},
                                    on_click=self.btn_recreate_clicked,
                                ),
                            ],
                            height=75,
                        ),
                        # tab control: designTab, row=1
                        ft.Row([
                            ft.Text('Design hint:'),
                            ft.Text(
                                'Click empty(Green) cell to set/clear obstacle(Red). '
                                'Drag Start(Purple)/Goal(Black)/Obstacle(red).',
                            ),
                        ]),
                    ]),
                    ref=self.design_tab,
                ),
                # tab control: Planning Tab
                ft.Tab(
                    'Planing',
                    ft.Column([
                        ft.ResponsiveRow([
                            ft.Text(
                                'Planning mode:',
                                col={'xs': 4, 'sm': 2.5, 'md': 2},
                            ),
                            ft.Dropdown(
                                ref=self.planning_mode,
                                hint_text='Planing mode',
                                options=[ft.dropdown.Option(x) for x in ['Fast', 'Slow step', 'Manual step']],
                                value=self.planningMode,
                                autofocus=True,
                                col={'xs': 4, 'sm': 2.5, 'md': 2},
                            ),
                            ft.Checkbox(
                                ref=self.h0_check,
                                label='h=0',
                                value=self.h0Check,
                                col={'xs': 2, 'sm': 1.3, 'md': 1},
                            ),
                            ft.Checkbox(
                                ref=self.direct_neighbors,
                                label='Only direct neighbors(4)',
                                value=self.directNeighbors,
                                col={'xs': 7, 'sm': 3.7, 'md': 3.5},
                            ),
                            ft.FilledButton(
                                'Start planning',
                                col={'xs': 5, 'sm': 3, 'md': 2.5},
                                on_click=self.btn_plan_clicked,
                            )
                        ]),
                        ft.Row([
                            ft.Text('Planning hint:'),
                            ft.Text(
                                '-',
                                ref=self.planning_hint,
                            ),
                        ]),
                    ]),
                    ref=self.planning_tab,
                ),
                # tab control: Execution Tab
                ft.Tab(
                    'Execution',
                    ft.Column([
                        ft.ResponsiveRow([
                            ft.Text(
                                'Execution mode:',
                                col={'xs': 3.5, 'sm': 3, 'md': 2},
                            ),
                            ft.Dropdown(
                                ref=self.execution_mode,
                                hint_text='Simulation or real control',
                                options=[ft.dropdown.Option(x) for x in ['Screen Simulation', 'Cloud Control']],
                                value=self.executionMode,
                                autofocus=True,
                                col={'xs': 5.5, 'sm': 5, 'md': 3},
                            ),
                            ft.Text(
                                'Robot start orientation:',
                                col={'xs': 5, 'sm': 4.5, 'md': 3},
                            ),
                            ft.Dropdown(
                                hint_text='Absolution orientation',
                                options=[ft.dropdown.Option(x) for x in ['North', 'East', 'South', 'West']],
                                value=self.robotStartOrientation,
                                autofocus=True,
                                col={'xs': 2.8, 'sm': 2.5, 'md': 2},
                                on_change=update_robot_start_orientation,
                            ),
                            ft.FilledButton(
                                'Execute plan',
                                col={'xs': 4, 'sm': 3, 'md': 2},
                                on_click=self.btn_exec_clicked,
                            )
                        ]),
                        ft.Row([
                            ft.Text('Execution hint:'),
                            ft.Text(
                                'Click to add obstacles during plan execution',
                            )
                        ]),
                    ]),
                    ref=self.execution_tab,
                ),
            ],
            height=170,
        )

        # Row = 2 the grid
        self.grid = self.create_grid()
        self.robot = self.create_robot()
        self.canvas_stack = ft.Ref[ft.Stack]()

        self.canvas = ft.Container(
            content=ft.Stack(
                [
                    self.grid,
                    self.robot,
                ],
                ref=self.canvas_stack,
            ),
            margin=0,
            padding=0,
            alignment=ft.alignment.bottom_center,
            bgcolor=ft.colors.WHITE,
            height=self.canvas_height,
        )

        def close_dlg(_):
            self.dialog.open = False
            self.page.update()

        self.dialog_icon = ft.Ref[ft.Icon]()
        self.dialog_title = ft.Ref[ft.Text]()
        self.dialog_text = ft.Ref[ft.Text]()
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(
                        name=ft.icons.MESSAGE,
                        ref=self.dialog_icon,
                        color=ft.colors.WHITE,
                    ),
                    ft.Text('Hint', ref=self.dialog_title),
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            content=ft.Text(
                'Press OK to continue.',
                ref=self.dialog_text,
                text_align=ft.TextAlign.CENTER
            ),
            actions=[
                ft.FilledButton('ok', on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        page.dialog = self.dialog

        page.add(ft.Column(spacing=0, controls=[tabs, self.canvas]))

        self.set_default_start_goal()

    class CellContent(ft.UserControl):
        def __init__(self, width, height, cell):
            super().__init__()
            self.cell = cell
            self.cell_type = CellType.Empty
            self.icon = ft.Icon('')
            self.icon.visible = False
            self.g = ft.Text('g:inf', size=8)
            self.rsh = ft.Text('rsh:inf', size=8)
            self.content = ft.Container(
                content=ft.Column(
                    [
                        self.icon,
                        self.g,
                        self.rsh,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                width=width,
                height=height,
                bgcolor=ft.colors.GREEN,
                border=ft.border.all(0.5, color=ft.colors.WHITE)
            )

        def build(self):
            return self.content

        def update_rsh(self, value):
            self.rsh.value = f'rsh:{value}'
            self.update()

        def update_g(self, value):
            self.g.value = f'g:{value}'
            self.update()

        def update_color(self, color):
            self.content.bgcolor = color
            self.update()

        def update_size(self, width, height):
            self.content.width = width
            self.content.height = height
            self.update()

        def change_type(self, cell_type):
            match cell_type:
                case CellType.Empty:
                    self.content.bgcolor = ft.colors.GREEN
                    self.icon.name = ''
                case CellType.Start:
                    self.content.bgcolor = ft.colors.PURPLE
                    self.icon.name = ft.icons.START
                case CellType.Goal:
                    self.content.bgcolor = ft.colors.BLACK
                    self.icon.name = ft.icons.FLAG
                case CellType.Obstacle:
                    self.content.bgcolor = ft.colors.RED
                    self.icon.name = ft.icons.BLOCK
            self.icon.visible = cell_type != CellType.Empty
            self.rsh.visible = cell_type != CellType.Obstacle
            self.g.visible = cell_type != CellType.Obstacle
            self.cell_type = cell_type

    class Cell(ft.UserControl):

        def __init__(self, x, y, width, height, view):
            super().__init__()
            self.x = x
            self.y = y
            self.view = view
            self.cell_type = CellType.Empty
            self.content = DStarLiteView.CellContent(width, height, self)
            self.container = ft.Container(on_click=self.on_click)
            self.draggable = ft.Draggable(group="grid")
            self.drag_target = ft.DragTarget(group="grid",
                                             on_accept=self.drag_accept,
                                             on_will_accept=self.drag_will_accept,
                                             on_leave=self.drag_leave, )

        def build(self):
            self.container.content = self.drag_target
            self.drag_target.content = self.content
            return self.container

        def update_rsh(self):
            value = round(self.view.planner.vertexGrid[self.x][self.y].rsh, 2)
            self.content.update_rsh(value)

        def update_g(self):
            value = round(self.view.planner.vertexGrid[self.x][self.y].g, 2)
            self.content.update_g(value)

        def update_color(self, color):
            self.content.update_color(color)

        def update_size(self, width, height):
            self.content.update_size(width, height)

        def change_type(self, cell_type):
            match cell_type:
                case CellType.Empty:
                    self.container.content = self.drag_target
                    self.drag_target.content = self.content
                    node = self.view.planner.vertexGrid[self.x][self.y]
                    if node.isObstacle:
                        node.isObstacle = False
                        self.view.planner.obstacles.remove(node)
                case CellType.Start:
                    self.container.content = self.draggable
                    self.draggable.content = self.content
                    self.view.planner.set_start_coordinates(self.x, self.y)
                case CellType.Goal:
                    self.container.content = self.draggable
                    self.draggable.content = self.content
                    self.view.planner.set_goal_coordinates(self.x, self.y)
                case CellType.Obstacle:
                    self.container.content = self.draggable
                    self.draggable.content = self.content
                    node = self.view.planner.vertexGrid[self.x][self.y]
                    if not node.isObstacle:
                        node.isObstacle = True
                        self.view.planner.obstacles.add(node)
            self.content.change_type(cell_type)
            self.update_rsh()
            self.cell_type = cell_type
            self.update()

        def on_click(self, _):
            if self.view.appState == AppState.inPlanning:
                self.view.show('Hint', 'Action not possible in this state of planning. Recreate grid.')
                return
            match self.cell_type:
                case CellType.Empty:
                    self.change_type(CellType.Obstacle)
                case CellType.Obstacle:
                    if self.view.appState == AppState.inDesign:
                        # Obstacles can only be removed in Design
                        self.change_type(CellType.Empty)

        def drag_accept(self, e):
            if self.view.appState != AppState.inDesign:
                self.view.show('Hint', 'Action not possible in this state of planning. Recreate grid.')
                return

            target_content = self.content
            # get draggable (source) control by its ID
            src_content = self.page.get_control(e.src_id).content
            cell_type = src_content.cell_type

            src_content.cell.change_type(CellType.Empty)
            target_content.cell.change_type(cell_type)
            src_content.content.border = ft.border.all(0.5, color=ft.colors.WHITE)
            target_content.content.border = ft.border.all(0.5, color=ft.colors.WHITE)

            src_content.update()
            target_content.update()

        def drag_will_accept(self, _):
            print(self.view.appState)
            target_content = self.content.content
            target_content.border = ft.border.all(
                2, ft.colors.BLACK45 if self.view.appState == AppState.inDesign else ft.colors.RED)
            target_content.update()

        def drag_leave(self, _):
            target_content = self.content.content
            target_content.border = ft.border.all(0.5, color=ft.colors.WHITE)
            target_content.update()

    # Eventhandler ####################################################################

    # Button 'Recreate' has been clicked. 
    def btn_recreate_clicked(self, _):
        # Recreate the planning grid including all variables
        self.show_planning_hint('-')
        self.show_robot(False)
        self.grid = self.create_grid()
        self.canvas_stack.current.controls[0] = self.grid
        self.canvas_stack.current.update()
        self.set_default_start_goal()
        self.h0_check.current.disabled = False
        self.direct_neighbors.current.disabled = False
        self.appState = AppState.inDesign
        self.page.update()

    # Button 'Start Planning' has been clicked. Execute planning
    def btn_plan_clicked(self, _):
        if self.appState != AppState.inDesign:
            self.show('Hint', 'Plan already created')
            return
        self.design_tab.current.content.disabled = True
        self.execution_tab.current.content.disabled = True
        # Check business rules
        if self.planner.are_start_and_goal_set():
            self.planner.hIsZero = self.h0_check.current.value
            self.planner.directNeighbors = self.direct_neighbors.current.value
            self.show_planning_hint('Planning in progress.......')
            self.appState = AppState.inPlanning
            print('planning mode:', self.planning_mode.current.value)
            self.planner.main_planning(self.planning_mode.current.value)
            if self.planner.planReady:
                self.appState = AppState.planPresent
                self.h0_check.current.disabled = True
                self.direct_neighbors.current.disabled = True
                self.show_planning_hint(f'Planning successful within {self.planner.plan_steps} steps')
                self.show('Hint', 'Plan is ready')
            else:
                self.appState = AppState.inDesign
                self.show_planning_hint('Planning unsuccessful !!!')
                self.show('Hint', 'No plan exists')
                self.show('Hint', 'Recreating grid')

        else:
            self.show('Hint', 'Start- and/or Goal vertex is not defined')
            self.appState = AppState.inDesign
        self.design_tab.current.content.disabled = False
        self.execution_tab.current.content.disabled = False

    # Button 'Execute' has been clicked
    def btn_exec_clicked(self, _):
        # Check business rules
        if not self.planner.planReady:
            self.show('Hint', 'No plan present. Goto design and planning tab.')
        else:
            self.appState = AppState.inExecution
            self.design_tab.current.content.disabled = True
            self.planning_tab.current.content.disabled = True
            result = self.planner.execute_plan(self.execution_mode.current.value)
            if result[0]:
                self.show('Hint', 'Plan has been executed!')
                self.appState = AppState.afterExecution
            else:
                self.show('Hint', result[1])
                self.appState = AppState.planPresent
            self.show_planning_hint('-')
            self.design_tab.current.content.disabled = False
            self.planning_tab.current.content.disabled = False

    def show(self, title, message, warning=False):
        self.dialog_title = title
        self.dialog_icon.current.color = ft.colors.YELLOW if warning else ft.colors.WHITE
        self.dialog_text.current.value = message
        self.dialog.open = True
        self.page.update()

    def show_planning_hint(self, message):
        self.planning_hint.current.value = message
        self.planning_hint.current.update()

    # Functions ############################################################

    # Create a new planner and draw the grid
    def create_grid(self):
        # Create a planner and initialize it
        print('Creating planner')
        self.planner = DStarLitePlanner(self,
                                        grid_width=self.gridWidth,
                                        grid_height=self.gridHeight,
                                        h_is_zero=self.h0_check.current.value,
                                        direct_neighbors=self.direct_neighbors.current.value)
        grid = ft.Row([
            ft.Column([
                DStarLiteView.Cell(i, j, self.grid_cell_width, self.grid_cell_height, self)
                for j in range(self.gridHeight)
            ], spacing=0
            ) for i in range(self.gridWidth)
        ], spacing=0)
        return grid

    def create_robot(self):
        print('Creating robot')
        x = 100 / self.gridWidth
        y = 100 / self.gridHeight
        print(x, y)
        robot = ft.Icon(
            ft.icons.AIRPLANEMODE_ON,
            size=1,
            scale=50,
            color=ft.colors.ORANGE,
            offset=ft.transform.Offset(self.grid_cell_width / 2, self.grid_cell_height / 2),
            animate_offset=ft.animation.Animation(400),
            rotate=ft.transform.Rotate(0, alignment=ft.alignment.center),
            animate_rotation=ft.animation.Animation(400, ft.AnimationCurve.LINEAR),
            visible=False,
        )
        return robot

    def set_default_start_goal(self):
        self.grid.controls[0].controls[0].change_type(CellType.Start)
        self.grid.controls[-1].controls[-1].change_type(CellType.Goal)

    # Update rsh-value on screen
    def update_rsh(self, x, y):
        self.grid.controls[x].controls[y].update_rsh()

    # Update g-value on screen
    def update_g(self, x, y):
        self.grid.controls[x].controls[y].update_g()

        # Update-color of vertex on screen if it is not the start- or goal-node

    def update_color(self, vertex, color):
        self.grid.controls[vertex.x].controls[vertex.y].update_color(color)

    def update(self):
        self.page.update()

    def move(self, x, y, orientation):
        print('move robot:', x, y, orientation, Orientation[orientation])
        offset_x = (x + 0.5) * self.grid_cell_width
        offset_y = (y + 0.5) * self.grid_cell_height
        angle = Orientation[orientation].value
        self.robot.offset = ft.transform.Offset(offset_x, offset_y)
        self.robot.rotate = ft.transform.Rotate(angle)
        self.robot.update()

    def show_robot(self, visible):
        self.robot.visible = visible
        self.canvas_stack.current.update()

    def page_resize(self, _):
        self.canvas_width = self.page.width - 20
        self.canvas_height = self.page.height - 190
        self.grid_cell_width = self.canvas_width / self.gridWidth
        self.grid_cell_height = self.canvas_height / self.gridHeight

        for rows in self.grid.controls:
            for cell in rows.controls:
                cell.update_size(self.grid_cell_width, self.grid_cell_height)

        self.canvas.height = self.canvas_height
        self.canvas.update()

    # Print function for test purpose
    def dump_vertices(self):
        [[self.planner.vertexGrid[x][y].print() for x in range(self.gridWidth)] for y in range(self.gridHeight)]
