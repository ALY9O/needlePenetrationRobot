import crtk
import numpy as np
from sensor_msgs.msg import JointState
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from needlePenetrationRobot.gui import RobotGUI  # Update this import

class needle_penetration_robot:
    def __init__(self, ral):
        self.ral = ral
        
        self.crtk_utils = crtk.utils(self, ral)
        self.crtk_utils.add_operating_state()
        self.crtk_utils.add_measured_js()

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

    app = QApplication(sys.argv)
    gui = RobotGUI(NPR)
    gui.show()

    # Use a QTimer to periodically call parse_js and update the GUI
    timer = QTimer()
    timer.timeout.connect(lambda: [NPR.parse_js(), gui.update_labels()])
    timer.start(5)  # Update every 5 ms

    # Ensure the robot is disabled when the application exits
    app.aboutToQuit.connect(NPR.disable)

    sys.exit(app.exec_())