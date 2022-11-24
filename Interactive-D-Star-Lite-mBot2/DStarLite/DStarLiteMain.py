#!/usr/bin/python3
############################################################
#  
# This is the main application file for the D*Lite App. 
# It implements the D*Lite algorithm with an interactive
# grid including obstacles, a planner and execution
# modules for screen simulation and Lego EV3 control. 
#
# File: DStarLiteMain.py
# Author: Detlef Heinze 
# Version: 1.0     Date: 22.07.2020      
###########################################################

from DStarLiteView import *


# Create a start main application window
def main():
    print("\nStarting D*Lite Application 1.0")
    root = Tk()
    DStarLiteView(root)
    root.mainloop()


if __name__ == '__main__':
    main()
