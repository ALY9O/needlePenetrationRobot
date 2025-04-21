#!/usr/bin/python3

import crtk
import numpy as np
from sensor_msgs.msg import JointState
import sys
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QCoreApplication
from gui import RobotGUI

np.set_printoptions(precision=4)

class needle_penetration_robot:
    
    was_homed = False
    # Track homing status for each axis
    axis_homed = {
        'x': False,
        'y': False,
        'z': False,
        'd': False  # D axis (former x2)
    }

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
        self.d = 0.0  # Renamed from x2 to d for clarity
        self.v_x = 0.0
        self.v_y = 0.0
        self.v_z = 0.0
        self.v_d = 0.0  # Renamed from v_x2 to v_d for clarity
    
    def parse_js(self):
        [position, velocity, effort, time] = self.measured_js()
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.d = position[3]  # Renamed from x2 to d
        self.v_x = velocity[0]
        self.v_y = velocity[1]
        self.v_z = velocity[2]
        self.v_d = velocity[3]  # Renamed from v_x2 to v_d

    def do_auto_home(self):
        """Use limit switches to home X, Y, Z axes (not D)"""
        self.enable()
        # Store current D axis position since it won't be affected by homing
        current_d_position = self.d
        
        # Call the home function which will only home X, Y, Z axes
        # since D axis has no limit switches
        self.home()
        print("Robot auto-homing X, Y, Z axes...")
        
        # After homing, axes should be at their reference positions
        self.axis_homed['x'] = True
        self.axis_homed['y'] = True
        self.axis_homed['z'] = True
        
        # Set D axis to its previous position
        setpoint = np.array([self.x, self.y, self.z, current_d_position])
        self.servo_jp(setpoint)
        print(f"Auto-homing complete. Axes X, Y, Z at home position")
        print(f"D axis position maintained at {current_d_position:.4f}")
        
        self.was_homed = True
        
    def manual_home_axis(self, axis, reference_position=0.0):
        """
        Manually set the current position of an axis as its homed position
        
        Args:
            axis: String identifier of the axis ('x', 'y', 'z', or 'd')
            reference_position: Position value to assign to the current physical position
        """
        if not self.is_enabled():
            print(f"Error: Robot must be enabled to home {axis} axis")
            return False
            
        if axis not in ['x', 'y', 'z', 'd']:
            print(f"Error: Invalid axis '{axis}'")
            return False
        
        # Create a setpoint that maintains current position for other axes
        # but sets the specified axis to the reference position
        new_position = np.array([self.x, self.y, self.z, self.d])
        
        if axis == 'x':
            new_position[0] = reference_position
        elif axis == 'y':
            new_position[1] = reference_position
        elif axis == 'z':
            new_position[2] = reference_position
        elif axis == 'd':
            new_position[3] = reference_position
        
        # Apply the new position
        self.servo_jp(new_position)
        
        # Mark the axis as homed
        self.axis_homed[axis] = True
        print(f"{axis.upper()} axis manually homed: Current position set to {reference_position:.4f}")
        
        # Check if all axes are now homed
        if all(self.axis_homed.values()):
            self.was_homed = True
            print("All axes are now homed!")
        
        return True

    def enable(self):
        self.ral.enable()
        print("Robot enabled")

    def disable(self):
        self.ral.disable()
        print("Robot disabled")

    def is_enabled(self):
        return self.ral.is_enabled()
    
    def move_to_setpoint(self, x, y, z, d):
        """
        Move robot to a specified setpoint
        
        Args:
            x, y, z: Position values for X, Y, Z axes (range: -0.05 to 0.05)
            d: Position value for D axis (range: 0.0 to 0.2)
        """
        print("move_to_setpoint called")
        if (x > 0.05 or x < -0.05 or 
            y > 0.05 or y < -0.05 or 
            z > 0.05 or z < -0.05 or 
            d < -0.2 or d > 0.0):  # D axis has -0.2 to 0.0 limits
            print(f"Invalid setpoint: x={x}, y={y}, z={z}, d={d}")
            print("Values must be within limits: X/Y/Z: [-0.05, 0.05], D: [-0.2, 0.0]")
            return False
        else:
            setpoint = np.array([x, y, z, d])
            self.servo_jp(setpoint)
            print(f"Moving to x={x:.4f}, y={y:.4f}, z={z:.4f}, d={d:.4f}")
            return True

    def move_jog(self, axis, offset):
        """
        Jog a specific axis by the given offset
        
        Args:
            axis: String identifier of the axis ('x', 'y', 'z', or 'd')
            offset: Amount to jog the axis by (will be added to current position)
        """
        if axis == 'd':  # Handle D axis jog (formerly x2)
            # D axis has range -0.2 to 0.0
            if self.d + offset < -0.2 or self.d + offset > 0.0:
                print(f"Invalid jog for D axis: {self.d + offset:.4f}. Range is [-0.2, 0.0]")
                return False
            else:
                setpoint = np.array([self.x, self.y, self.z, self.d + offset])
                self.servo_jp(setpoint)
                return True
        elif axis == 'x':
            if abs(self.x + offset) > 0.05:
                print(f"Invalid jog for X axis: {self.x + offset:.4f}. Range is [-0.05, 0.05]")
                return False
            else:
                setpoint = np.array([self.x + offset, self.y, self.z, self.d])
                self.servo_jp(setpoint)
                return True
        elif axis == 'y':
            if abs(self.y + offset) > 0.05:
                print(f"Invalid jog for Y axis: {self.y + offset:.4f}. Range is [-0.05, 0.05]")
                return False
            else:
                setpoint = np.array([self.x, self.y + offset, self.z, self.d])
                self.servo_jp(setpoint)
                return True
        elif axis == 'z':
            if abs(self.z + offset) > 0.05:
                print(f"Invalid jog for Z axis: {self.z + offset:.4f}. Range is [-0.05, 0.05]")
                return False
            else:
                setpoint = np.array([self.x, self.y, self.z + offset, self.d])
                self.servo_jp(setpoint)
                return True
        else:
            print(f"Invalid axis: {axis}")
            return False

    def is_busy(self):
        """Check if any axis is currently moving"""
        if (abs(self.v_x) > 0.01 or 
            abs(self.v_y) > 0.01 or 
            abs(self.v_z) > 0.01 or 
            abs(self.v_d) > 0.01):
            return True
        else:
            return False
            
    def reset_home_status(self):
        """Reset homing status for all axes"""
        self.axis_homed = {
            'x': False,
            'y': False,
            'z': False,
            'd': False
        }
        self.was_homed = False
        print("All axes marked as not homed")
        return True

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
    def cleanup():
        NPR.disable()
        ral.shutdown()
    
    app.aboutToQuit.connect(cleanup)

    def signal_handler(sig, frame):
        print('Ctrl+C pressed, shutting down...')
        cleanup()
        app.quit()  # Properly quit the QApplication
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()