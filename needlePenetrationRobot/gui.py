import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QHBoxLayout, QLineEdit
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor

class RobotGUI(QWidget):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Robot Control Panel')

        layout = QVBoxLayout()

        self.position_label = QLabel('Position: x=0.0000, y=0.0000, z=0.0000')
        self.velocity_label = QLabel('Velocity: vx=0.0000, vy=0.0000, vz=0.0000')
        self.status_label = QLabel('Status: Disabled')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('background-color: red; color: white;')

        layout.addWidget(self.position_label)
        layout.addWidget(self.velocity_label)
        layout.addWidget(self.status_label)

        grid = QGridLayout()

        self.x_up_button = QPushButton('↑')
        self.x_down_button = QPushButton('↓')
        self.y_up_button = QPushButton('↑')
        self.y_down_button = QPushButton('↓')
        self.z_up_button = QPushButton('↑')
        self.z_down_button = QPushButton('↓')

        self.x_label = QLabel('X')
        self.x_label.setAlignment(Qt.AlignCenter)
        self.y_label = QLabel('Y')
        self.y_label.setAlignment(Qt.AlignCenter)
        self.z_label = QLabel('Z')
        self.z_label.setAlignment(Qt.AlignCenter)

        grid.addWidget(self.x_up_button, 0, 0)
        grid.addWidget(self.x_label, 1, 0)
        grid.addWidget(self.x_down_button, 2, 0)

        grid.addWidget(self.y_up_button, 0, 1)
        grid.addWidget(self.y_label, 1, 1)
        grid.addWidget(self.y_down_button, 2, 1)

        grid.addWidget(self.z_up_button, 0, 2)
        grid.addWidget(self.z_label, 1, 2)
        grid.addWidget(self.z_down_button, 2, 2)

        layout.addLayout(grid)

        self.home_button = QPushButton('Home')
        self.enable_button = QPushButton('Enable')
        self.enable_button.setCheckable(True)
        self.enable_button.setStyleSheet('background-color: red; color: white;')

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.enable_button)

        layout.addLayout(button_layout)

        # Add input boxes and button for position setpoints
        setpoint_layout = QGridLayout()

        self.x_setpoint_input = QLineEdit()
        self.y_setpoint_input = QLineEdit()
        self.z_setpoint_input = QLineEdit()

        self.x_setpoint_input.setPlaceholderText('X Setpoint')
        self.y_setpoint_input.setPlaceholderText('Y Setpoint')
        self.z_setpoint_input.setPlaceholderText('Z Setpoint')

        self.setpoint_button = QPushButton('Set Position')

        setpoint_layout.addWidget(QLabel('X:'), 0, 0)
        setpoint_layout.addWidget(self.x_setpoint_input, 0, 1)
        setpoint_layout.addWidget(QLabel('Y:'), 1, 0)
        setpoint_layout.addWidget(self.y_setpoint_input, 1, 1)
        setpoint_layout.addWidget(QLabel('Z:'), 2, 0)
        setpoint_layout.addWidget(self.z_setpoint_input, 2, 1)
        setpoint_layout.addWidget(self.setpoint_button, 3, 0, 1, 2)

        layout.addLayout(setpoint_layout)

        self.setLayout(layout)

        self.initial_jog_timer = QTimer(self)
        self.initial_jog_timer.setSingleShot(True)
        self.initial_jog_timer.timeout.connect(self.start_continuous_jog)

        self.continuous_jog_timer = QTimer(self)
        self.continuous_jog_timer.timeout.connect(self.perform_jog)

        self.x_up_button.pressed.connect(lambda: self.start_jog('x', 1))
        self.x_down_button.pressed.connect(lambda: self.start_jog('x', -1))
        self.y_up_button.pressed.connect(lambda: self.start_jog('y', 1))
        self.y_down_button.pressed.connect(lambda: self.start_jog('y', -1))
        self.z_up_button.pressed.connect(lambda: self.start_jog('z', 1))
        self.z_down_button.pressed.connect(lambda: self.start_jog('z', -1))

        self.x_up_button.released.connect(self.stop_jog)
        self.x_down_button.released.connect(self.stop_jog)
        self.y_up_button.released.connect(self.stop_jog)
        self.y_down_button.released.connect(self.stop_jog)
        self.z_up_button.released.connect(self.stop_jog)
        self.z_down_button.released.connect(self.stop_jog)

        self.home_button.clicked.connect(self.home_robot)
        self.enable_button.clicked.connect(self.toggle_enable)
        self.setpoint_button.clicked.connect(self.set_position)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_labels)
        self.update_timer.start(1000)  # Update every second

    def start_jog(self, axis, direction):
        self.jog_axis = axis
        self.jog_direction = direction
        self.perform_jog()  # Perform an immediate jog
        self.initial_jog_timer.start(500)  # Start the initial delay timer (500 ms)

    def start_continuous_jog(self):
        self.continuous_jog_timer.start(100)  # Start the continuous jog timer (100 ms)

    def stop_jog(self):
        self.initial_jog_timer.stop()
        self.continuous_jog_timer.stop()

    def perform_jog(self):
        print(f'Jogging {self.jog_axis} axis {"up" if self.jog_direction > 0 else "down"}')

    def home_robot(self):
        self.robot.do_home()
        print('Homing robot')

    def toggle_enable(self):
        if self.enable_button.isChecked():
            self.robot.enable()
            self.enable_button.setText('Enabled')
            self.enable_button.setStyleSheet('background-color: green; color: white;')
            self.status_label.setText('Status: Enabled')
            self.status_label.setStyleSheet('background-color: green; color: white;')
            print('Robot enabled')
        else:
            self.robot.disable()
            self.enable_button.setText('Disabled')
            self.enable_button.setStyleSheet('background-color: red; color: white;')
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('background-color: red; color: white;')
            print('Robot disabled')

    def set_position(self):
        try:
            x = float(self.x_setpoint_input.text())
            y = float(self.y_setpoint_input.text())
            z = float(self.z_setpoint_input.text())
            self.robot.set_position(x, y, z)
            print(f'Setting position to x={x}, y={y}, z={z}')
        except ValueError:
            print('Invalid input for position setpoints')

    def update_labels(self):
        self.position_label.setText(f'Position: x={self.robot.x:.4f}, y={self.robot.y:.4f}, z={self.robot.z:.4f}')
        self.velocity_label.setText(f'Velocity: vx={self.robot.v_x:.4f}, vy={self.robot.v_y:.4f}, vz={self.robot.v_z:.4f}')
        self.update_status()

    def update_status(self):
        if self.robot.is_enabled():
            self.status_label.setText('Status: Enabled')
            self.status_label.setStyleSheet('background-color: green; color: white;')
        else:
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('background-color: red; color: white;')

def main(args=None):
    app = QApplication(sys.argv)
    ral = crtk.ral('NPR', '/control')
    robot = NPR(ral)
    gui = RobotGUI(robot)
    gui.show()

    # Use a QTimer to periodically call parse_js and update the GUI
    timer = QTimer()
    timer.timeout.connect(lambda: [robot.parse_js(), gui.update_labels()])
    timer.start(5)  # Update every 5 ms

    sys.exit(app.exec_())
'''
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QHBoxLayout, QLineEdit
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor

class RobotGUI(QWidget):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Robot Control Panel')

        layout = QVBoxLayout()

        self.position_label = QLabel('Position: x=0.0000, y=0.0000, z=0.0000')
        self.velocity_label = QLabel('Velocity: vx=0.0000, vy=0.0000, vz=0.0000')
        self.status_label = QLabel('Status: Disabled')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('background-color: red; color: white;')

        layout.addWidget(self.position_label)
        layout.addWidget(self.velocity_label)
        layout.addWidget(self.status_label)

        grid = QGridLayout()

        self.x_up_button = QPushButton('↑')
        self.x_down_button = QPushButton('↓')
        self.y_up_button = QPushButton('↑')
        self.y_down_button = QPushButton('↓')
        self.z_up_button = QPushButton('↑')
        self.z_down_button = QPushButton('↓')

        self.x_label = QLabel('X')
        self.x_label.setAlignment(Qt.AlignCenter)
        self.y_label = QLabel('Y')
        self.y_label.setAlignment(Qt.AlignCenter)
        self.z_label = QLabel('Z')
        self.z_label.setAlignment(Qt.AlignCenter)

        grid.addWidget(self.x_up_button, 0, 0)
        grid.addWidget(self.x_label, 1, 0)
        grid.addWidget(self.x_down_button, 2, 0)

        grid.addWidget(self.y_up_button, 0, 1)
        grid.addWidget(self.y_label, 1, 1)
        grid.addWidget(self.y_down_button, 2, 1)

        grid.addWidget(self.z_up_button, 0, 2)
        grid.addWidget(self.z_label, 1, 2)
        grid.addWidget(self.z_down_button, 2, 2)

        layout.addLayout(grid)

        self.home_button = QPushButton('Home')
        self.enable_button = QPushButton('Enable')
        self.enable_button.setCheckable(True)
        self.enable_button.setStyleSheet('background-color: red; color: white;')

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.enable_button)

        layout.addLayout(button_layout)

        # Add input boxes and button for position setpoints
        setpoint_layout = QGridLayout()

        self.x_setpoint_input = QLineEdit()
        self.y_setpoint_input = QLineEdit()
        self.z_setpoint_input = QLineEdit()

        self.x_setpoint_input.setPlaceholderText('X Setpoint')
        self.y_setpoint_input.setPlaceholderText('Y Setpoint')
        self.z_setpoint_input.setPlaceholderText('Z Setpoint')

        self.setpoint_button = QPushButton('Set Position')

        setpoint_layout.addWidget(QLabel('X:'), 0, 0)
        setpoint_layout.addWidget(self.x_setpoint_input, 0, 1)
        setpoint_layout.addWidget(QLabel('Y:'), 1, 0)
        setpoint_layout.addWidget(self.y_setpoint_input, 1, 1)
        setpoint_layout.addWidget(QLabel('Z:'), 2, 0)
        setpoint_layout.addWidget(self.z_setpoint_input, 2, 1)
        setpoint_layout.addWidget(self.setpoint_button, 3, 0, 1, 2)

        layout.addLayout(setpoint_layout)

        self.setLayout(layout)

        self.initial_jog_timer = QTimer(self)
        self.initial_jog_timer.setSingleShot(True)
        self.initial_jog_timer.timeout.connect(self.start_continuous_jog)

        self.continuous_jog_timer = QTimer(self)
        self.continuous_jog_timer.timeout.connect(self.perform_jog)

        self.x_up_button.pressed.connect(lambda: self.start_jog('x', 1))
        self.x_down_button.pressed.connect(lambda: self.start_jog('x', -1))
        self.y_up_button.pressed.connect(lambda: self.start_jog('y', 1))
        self.y_down_button.pressed.connect(lambda: self.start_jog('y', -1))
        self.z_up_button.pressed.connect(lambda: self.start_jog('z', 1))
        self.z_down_button.pressed.connect(lambda: self.start_jog('z', -1))

        self.x_up_button.released.connect(self.stop_jog)
        self.x_down_button.released.connect(self.stop_jog)
        self.y_up_button.released.connect(self.stop_jog)
        self.y_down_button.released.connect(self.stop_jog)
        self.z_up_button.released.connect(self.stop_jog)
        self.z_down_button.released.connect(self.stop_jog)

        self.home_button.clicked.connect(self.home_robot)
        self.enable_button.clicked.connect(self.toggle_enable)
        self.setpoint_button.clicked.connect(self.set_position)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_labels)
        self.update_timer.start(1000)  # Update every second

    def start_jog(self, axis, direction):
        self.jog_axis = axis
        self.jog_direction = direction
        self.perform_jog()  # Perform an immediate jog
        self.initial_jog_timer.start(500)  # Start the initial delay timer (500 ms)

    def start_continuous_jog(self):
        self.continuous_jog_timer.start(100)  # Start the continuous jog timer (100 ms)

    def stop_jog(self):
        self.initial_jog_timer.stop()
        self.continuous_jog_timer.stop()

    def perform_jog(self):
        print(f'Jogging {self.jog_axis} axis {"up" if self.jog_direction > 0 else "down"}')

    def home_robot(self):
        self.robot.do_home()
        print('Homing robot')

    def toggle_enable(self):
        if self.enable_button.isChecked():
            self.robot.enable()
            self.enable_button.setText('Enabled')
            self.enable_button.setStyleSheet('background-color: green; color: white;')
            self.status_label.setText('Status: Enabled')
            self.status_label.setStyleSheet('background-color: green; color: white;')
            print('Robot enabled')
        else:
            self.robot.disable()
            self.enable_button.setText('Disabled')
            self.enable_button.setStyleSheet('background-color: red; color: white;')
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('background-color: red; color: white;')
            print('Robot disabled')

    def set_position(self):
        try:
            x = float(self.x_setpoint_input.text())
            y = float(self.y_setpoint_input.text())
            z = float(self.z_setpoint_input.text())
            self.robot.set_position(x, y, z)
            print(f'Setting position to x={x}, y={y}, z={z}')
        except ValueError:
            print('Invalid input for position setpoints')

    def update_labels(self):
        self.robot.parse_js()
        self.position_label.setText(f'Position: x={self.robot.x:.4f}, y={self.robot.y:.4f}, z={self.robot.z:.4f}')
        self.velocity_label.setText(f'Velocity: vx={self.robot.v_x:.4f}, vy={self.robot.v_y:.4f}, vz={self.robot.v_z:.4f}')
        self.update_status()

    def update_status(self):
        state = self.robot.get_state()
        if state == 'enabled':
            self.status_label.setText('Status: Enabled')
            self.status_label.setStyleSheet('background-color: green; color: white;')
        elif state == 'disabled':
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('background-color: red; color: white;')
        elif state == 'fault':
            self.status_label.setText('Status: Fault')
            self.status_label.setStyleSheet('background-color: darkred; color: white;')
        elif state == 'busy':
            self.status_label.setText('Status: Busy')
            self.status_label.setStyleSheet('background-color: orange; color: white;')
        elif state == 'paused':
            self.status_label.setText('Status: Paused')
            self.status_label.setStyleSheet('background-color: yellow; color: black;')

class DummyRobot:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.v_x = 0.0
        self.v_y = 0.0
        self.v_z = 0.0
        self.state = 'disabled'

    def parse_js(self):
        # Dummy implementation for testing
        self.x += 0.01
        self.y += 0.01
        self.z += 0.01
        self.v_x += 0.001
        self.v_y += 0.001
        self.v_z += 0.001

    def do_home(self):
        print('Homing robot')

    def enable(self):
        self.state = 'enabled'
        print('Enabling robot')

    def disable(self):
        self.state = 'disabled'
        print('Disabling robot')

    def get_state(self):
        return self.state

    def set_position(self, x, y, z):
        print(f'Setting position to x={x}, y={y}, z={z}')

def main(args=None):
    app = QApplication(sys.argv)
    robot = DummyRobot()
    gui = RobotGUI(robot)
    gui.show()
    sys.exit(app.exec_())
    '''