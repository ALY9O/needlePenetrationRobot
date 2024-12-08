#!/usr/bin/python3

import crtk
import numpy as np
from sensor_msgs.msg import JointState
import sys
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QCoreApplication
from gui import RobotGUI

class needle_penetration_robot:
    
    was_homed = False

    def __init__(self, ral):
        self.ral = ral
        
        self.crtk_utils = crtk.utils(self, ral)
        self.crtk_utils.add_operating_state()
        self.crtk_utils.add_measured_js()
        self.crtk_utils.add_servo_jp()
        self.crtk_utils.add_setpoint_js()
        self.crtk_utils.add_servo_jr()

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.v_x = 0.0
        self.v_y = 0.0
        self.v_z = 0.0
    
    def parse_js(self):
        [position, velocity, effort, time] = self.measured_js()
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.v_x = velocity[0]
        self.v_y = velocity[1]
        self.v_z = velocity[2]

    def do_home(self):
        self.enable()
        self.home()
        self.was_homed = True
        print("Robot homing...")

    def enable(self):
        self.ral.enable()
        print("Robot enabled")

    def disable(self):
        self.ral.disable()
        print("Robot disabled")

    def is_enabled(self):
        print(f"Robot is enabled: {self.ral.is_enabled()}")
        return self.ral.is_enabled()
    
    def move_to_setpoint(self, x, y, z):
        if (self.is_moving()):
            print("Robot is busy")
            return
        else:
            if (abs(self.x) > 0.05 or abs(self.y) > 0.05 or self.z > 0.2 or self.z < 0):
                print("Invalid setpoint")
            else:
                setpoint = np.array([x, y, z])
                self.servo_jp(setpoint)
                print(f"Moving to {x}, {y}, {z}")

    def move_jog(self, axis, offset):
        if (self.is_moving()):
            print("Robot is busy")
            return
        else:
            if (abs(self.x + offset) > 0.05 or abs(self.y + offset) > 0.05 or self.z + offset > 0.2 or self.z + offset < 0):
                print(f"Invalid jog")
            else:
                if (axis == 'x'):
                    setpoint = np.array([self.x + offset, self.y, self.z])
                elif (axis == 'y'):
                    setpoint = np.array([self.x, self.y + offset, self.z])
                elif (axis == 'z'):
                    setpoint = np.array([self.x, self.y, self.z + offset])
                else:
                    print("Invalid axis")
                print(f"Moving to {setpoint}")
                self.servo_jp(setpoint)  

    def is_moving(self):
        if (abs(self.v_x) > 0.01 or abs(self.v_y) > 0.01 or abs(self.v_z) > 0.01):
            return True
        else:
            return False

def main(args=None):
    ral = crtk.ral('NPR', '/control')
    NPR = needle_penetration_robot(ral)
    ral.check_connections()
    print("Connections Verified")
    ral.spin()

    app = QApplication(sys.argv)
    gui = RobotGUI(NPR)
    gui.show()

    print("Setup complete")

    # Use a QTimer to periodically call parse_js and update the GUI
    timer = QTimer()
    timer.timeout.connect(lambda: [NPR.parse_js(), gui.update_labels()])
    timer.start(1)  # Update every 5 ms
    
    # Ensure the robot is disabled when the application exits
    app.aboutToQuit.connect(NPR.disable)
    app.aboutToQuit.connect(ral.shutdown)

    def signal_handler(sig, frame):
        print('Ctrl+C pressed, shutting down...')
        NPR.disable()
        ral.shutdown()
        timer.stop()
        QCoreApplication.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()