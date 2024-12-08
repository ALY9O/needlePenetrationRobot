#!/usr/bin/python3

import crtk
import numpy as np
from sensor_msgs.msg import JointState
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import time


class needle_penetration_robot:
    def __init__(self, ral):
        self.ral = ral
        
        self.crtk_utils = crtk.utils(self, ral)
        self.crtk_utils.add_operating_state()
        self.crtk_utils.add_measured_js()
        self.crtk_utils.add_servo_jp()
        self.crtk_utils.add_setpoint_js()

        self.ral = ral
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.v_x = 0.0
        self.v_y = 0.0
        self.v_z = 0.0
        #self.e_x = 0.0
        #self.e_y = 0.0
        #self.e_z = 0.0

    def parse_js(self):
        [position, velocity, effort, time] = self.measured_js()
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.v_x = velocity[0]
        self.v_y = velocity[1]
        self.v_z = velocity[2]
        #self.e_x = effort[0]
        #self.e_y = effort[1]
        #self.e_z = effort[2]

    def do_home(self):
        self.enable()        
        self.home()

    def enable(self):
        self.ral.enable()

    def disable(self):
        self.ral.disable()

    def is_enabled(self):
        return self.ral.is_enabled()

    

def main(args=None):
    ral = crtk.ral('NPR', '/control')
    NPR = needle_penetration_robot(ral)
    ral.check_connections()
    ral.spin()
    print("connection verified")

    NPR.enable()
    print("enabled")

    start = NPR.measured_jp()
    print("start JS:")
    print(start)

    origin = start
    origin[0] *= 0
    origin[1] *= 0
    origin[2] *= 0
    print(f"Moving to {origin}")
    NPR.servo_jp(origin)
    print(f"Moved to {origin}")

    time.sleep(5)

    goal = np.array([0.010, 0.010, 0.010])
    print(f"Moving to {goal}")
    NPR.servo_jp(goal)
    print(f"Moved to {goal}")


    ral.shutdown()
    #NPR.move_to_setpoint(goal)
    # Example usage of move_to_setpoint

if __name__ == '__main__':
    main()
