#!/usr/bin/python3
############################################################
#  
# This is the main application file for the D*Lite App. 
# It implements the D*Lite algorithm with an interactive
# grid including obstacles, a planner and execution
# modules for screen simulation and Lego EV3 control. 
#
# File: d_star_lite_main.py
# Author: Detlef Heinze 
# Version: 1.0     Date: 22.07.2020      
###########################################################

from d_star_lite_view import *


# Create a start main application window
def main(page: ft.Page):
    print('\nStarting D*Lite Application 2.0')
    print('page size:', page.width, page.height)
    DStarLiteView(page)


if __name__ == '__main__':
    ft.app(port=8550, host='0.0.0.0', target=main)
