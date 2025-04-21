#!/usr/bin/python3

import crtk
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QGridLayout, QHBoxLayout, QLineEdit, QPlainTextEdit, 
                            QTabWidget, QDoubleSpinBox, QGroupBox, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QFont

class OutputStream:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        if text.strip():  
            self.text_widget.appendPlainText(text.rstrip())  

    def flush(self):
        pass

class RobotGUI(QWidget):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.initUI()

    def initUI(self):
        self.setWindowTitle('NPR Control Panel v0.2.0')
        self.setMinimumWidth(600)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create status panel
        status_panel = self.create_status_panel()
        main_layout.addLayout(status_panel)
        
        # Create tab widget for different control panels
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_control_panel(), "Control")
        self.tabs.addTab(self.create_homing_panel(), "Manual Homing")
        main_layout.addWidget(self.tabs)
        
        # Console output
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("font-size: 10px;")
        self.console_output.setMaximumHeight(200)
        console_layout = QVBoxLayout()
        console_layout.addWidget(QLabel("Console Output:"))
        console_layout.addWidget(self.console_output)
        main_layout.addLayout(console_layout)
        
        # Set the stdout to our custom stream
        sys.stdout = OutputStream(self.console_output)
        
        self.setLayout(main_layout)
        
        # Set up timers
        self.setup_timers()
        
        # Initial update
        self.update_labels()

    def create_status_panel(self):
        """Create the status panel with position, velocity and status indicators"""
        # Position and velocity labels
        status_layout = QVBoxLayout()
        
        # Use a larger, fixed-width font for position display
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        font.setBold(True)
        
        # Position labels with better formatting
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        
        self.position_indicators = {}
        for axis in ['x', 'y', 'z', 'd']:
            axis_frame = QFrame()
            axis_frame.setFrameStyle(QFrame.StyledPanel)
            axis_layout = QVBoxLayout(axis_frame)
            axis_layout.setContentsMargins(5, 5, 5, 5)
            
            # Axis label
            axis_name = QLabel(f"{axis.upper()}")
            axis_name.setAlignment(Qt.AlignCenter)
            axis_layout.addWidget(axis_name)
            
            # Position value
            pos_label = QLabel("0.0000")
            pos_label.setFont(font)
            pos_label.setAlignment(Qt.AlignCenter)
            pos_label.setStyleSheet("font-size: 14px;")
            axis_layout.addWidget(pos_label)
            
            self.position_indicators[axis] = pos_label
            position_layout.addWidget(axis_frame)
            
        status_layout.addLayout(position_layout)
        
        # Velocity label (simpler, just one line)
        self.velocity_label = QLabel('Velocity: vx=0.0000, vy=0.0000, vz=0.0000, vd=0.0000')
        status_layout.addWidget(self.velocity_label)
        
        # Status indicators
        status_indicators = QHBoxLayout()
        
        # Robot status (enabled/disabled)
        self.status_label = QLabel('Status: Disabled')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('background-color: red; color: white; padding: 5px;')
        
        # Command status (busy/ready)
        self.busy_label = QLabel('Command: Ready')
        self.busy_label.setAlignment(Qt.AlignCenter)
        self.busy_label.setStyleSheet('background-color: green; color: white; padding: 5px;')
        
        # Home status
        self.home_status_label = QLabel('Homing: Not Homed')
        self.home_status_label.setAlignment(Qt.AlignCenter)
        self.home_status_label.setStyleSheet('background-color: orange; color: white; padding: 5px;')
        
        status_indicators.addWidget(self.status_label)
        status_indicators.addWidget(self.busy_label)
        status_indicators.addWidget(self.home_status_label)
        
        status_layout.addLayout(status_indicators)
        
        # Add individual axis homing indicators
        axis_status_layout = QHBoxLayout()
        self.axis_status_labels = {}
        
        for axis in ['x', 'y', 'z', 'd']:
            label = QLabel(f"{axis.upper()}: Not Homed")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('background-color: #FFA500; color: white; padding: 3px;')
            self.axis_status_labels[axis] = label
            axis_status_layout.addWidget(label)
            
        status_layout.addLayout(axis_status_layout)
        
        return status_layout

    def create_control_panel(self):
        """Create the main control panel with jog controls and setpoint inputs"""
        control_panel = QWidget()
        layout = QVBoxLayout(control_panel)
        
        # Create jog controls
        jog_group = QGroupBox("Jog Controls")
        jog_layout = QGridLayout(jog_group)
        
        self.jog_buttons = {}
        # Create jog buttons for all 4 axes
        for i, axis in enumerate(['x', 'y', 'z', 'd']):
            # Create up button
            up_btn = QPushButton('↑')
            up_btn.setFixedSize(40, 40)
            up_btn.pressed.connect(lambda a=axis: self.start_jog(a, 1))
            up_btn.released.connect(self.stop_jog)
            
            # Create axis label
            axis_label = QLabel(axis.upper())
            axis_label.setAlignment(Qt.AlignCenter)
            
            # Create down button
            down_btn = QPushButton('↓')
            down_btn.setFixedSize(40, 40)
            down_btn.pressed.connect(lambda a=axis: self.start_jog(a, -1))
            down_btn.released.connect(self.stop_jog)
            
            # Add to layout
            jog_layout.addWidget(up_btn, 0, i)
            jog_layout.addWidget(axis_label, 1, i)
            jog_layout.addWidget(down_btn, 2, i)
            
            # Store buttons
            self.jog_buttons[axis] = (up_btn, down_btn)
            
        layout.addWidget(jog_group)
        
        # Create enable/disable and homing buttons
        button_layout = QHBoxLayout()
        
        # Auto-home button
        self.auto_home_button = QPushButton('Auto-Home (X,Y,Z)')
        self.auto_home_button.setToolTip('Automatically home X, Y, Z axes using limit switches')
        button_layout.addWidget(self.auto_home_button)
        
        # Switch to manual homing tab button
        self.manual_home_button = QPushButton('Manual Homing')
        self.manual_home_button.setToolTip('Open manual homing panel to align with reference marks')
        button_layout.addWidget(self.manual_home_button)
        
        # Enable/disable button
        self.enable_button = QPushButton('Enable')
        self.enable_button.setCheckable(True)
        self.enable_button.setStyleSheet('background-color: red; color: white;')
        button_layout.addWidget(self.enable_button)
        
        layout.addLayout(button_layout)
        
        # Create setpoint input layout
        setpoint_group = QGroupBox("Set Position")
        setpoint_layout = QGridLayout(setpoint_group)
        
        self.setpoint_inputs = {}
        
        # Create inputs for all 4 axes
        for i, (axis, limits) in enumerate([('x', '[-0.05, 0.05]'), 
                                           ('y', '[-0.05, 0.05]'), 
                                           ('z', '[-0.05, 0.05]'), 
                                           ('d', '[-0.2, 0.0]')]):
            label = QLabel(f"{axis.upper()}:")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"{axis.upper()} Setpoint {limits}")
            
            setpoint_layout.addWidget(label, i, 0)
            setpoint_layout.addWidget(input_field, i, 1)
            
            self.setpoint_inputs[axis] = input_field
        
        # Add button to apply setpoints
        self.setpoint_button = QPushButton('Set Position')
        setpoint_layout.addWidget(self.setpoint_button, 4, 0, 1, 2)
        
        layout.addWidget(setpoint_group)
        
        # Connect buttons
        self.auto_home_button.clicked.connect(self.auto_home_robot)
        self.manual_home_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.enable_button.clicked.connect(self.toggle_enable)
        self.setpoint_button.clicked.connect(self.set_position)
        
        return control_panel

    def create_homing_panel(self):
        """Create the manual homing panel"""
        homing_panel = QWidget()
        layout = QVBoxLayout(homing_panel)
        
        # Instructions
        instructions = QLabel(
            "Manual Homing Instructions:\n"
            "1. Make sure the robot is enabled\n"
            "2. Use the jog controls to align each axis with its reference mark\n"
            "3. Click 'Set Home Position' for that axis\n"
            "4. Repeat for all axes that need to be manually homed"
        )
        instructions.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(instructions)
        
        # Create individual axis homing sections
        axis_groups = {}
        self.home_position_inputs = {}
        
        for axis, name, limits in [('x', 'X Axis', '[-0.05, 0.05]'), 
                                  ('y', 'Y Axis', '[-0.05, 0.05]'), 
                                  ('z', 'Z Axis', '[-0.05, 0.05]'), 
                                  ('d', 'D Axis', '[0.0, 0.2]')]:
            # Create group
            group = QGroupBox(name)
            group_layout = QVBoxLayout(group)
            
            # Current position
            pos_layout = QHBoxLayout()
            pos_layout.addWidget(QLabel(f"Current Position:"))
            pos_label = QLabel("0.0000")
            pos_label.setStyleSheet("font-weight: bold;")
            pos_layout.addWidget(pos_label)
            pos_layout.addStretch()
            group_layout.addLayout(pos_layout)
            
            # Jog controls
            jog_layout = QHBoxLayout()
            axis_label = QLabel(axis.upper())
            axis_label.setAlignment(Qt.AlignCenter)
            
            # Down jog button
            down_btn = QPushButton('←')
            down_btn.setFixedSize(40, 40)
            down_btn.pressed.connect(lambda a=axis: self.start_jog(a, -1))
            down_btn.released.connect(self.stop_jog)
            
            # Up jog button
            up_btn = QPushButton('→')
            up_btn.setFixedSize(40, 40)
            up_btn.pressed.connect(lambda a=axis: self.start_jog(a, 1))
            up_btn.released.connect(self.stop_jog)
            
            jog_layout.addWidget(QLabel("Jog Controls:"))
            jog_layout.addWidget(down_btn)
            jog_layout.addWidget(axis_label)
            jog_layout.addWidget(up_btn)
            jog_layout.addStretch()
            group_layout.addLayout(jog_layout)
            
            # Home position input
            home_layout = QHBoxLayout()
            home_layout.addWidget(QLabel("Home Position Value:"))
            
            # Use a QDoubleSpinBox for numeric input with limits
            if axis == 'd':
                position_input = QDoubleSpinBox()
                position_input.setRange(-0.2, 0.0)
            else:
                position_input = QDoubleSpinBox()
                position_input.setRange(-0.05, 0.05)
                
            position_input.setDecimals(4)
            position_input.setSingleStep(0.001)
            position_input.setValue(0.0)
            
            home_layout.addWidget(position_input)
            self.home_position_inputs[axis] = position_input
            
            # Set home button
            home_btn = QPushButton(f"Set {axis.upper()} Home Position")
            home_btn.clicked.connect(lambda checked=False, a=axis: self.set_home_position(a))
            
            home_layout.addWidget(home_btn)
            group_layout.addLayout(home_layout)
            
            # Store references
            axis_groups[axis] = {
                'group': group,
                'position_label': pos_label,
                'home_button': home_btn
            }
            
            # Add to layout
            layout.addWidget(group)
        
        # Store reference
        self.axis_groups = axis_groups
        
        # Reset homing status button
        reset_button = QPushButton("Reset All Home Positions")
        reset_button.setStyleSheet("background-color: #ffcccc;")
        reset_button.clicked.connect(self.reset_home_status)
        layout.addWidget(reset_button)
        
        # Return to control panel button
        back_button = QPushButton("Return to Control Panel")
        back_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        layout.addWidget(back_button)
        
        return homing_panel

    def setup_timers(self):
        """Set up all the timers needed for GUI operation"""
        # Timer for jog button press-and-hold behavior
        self.initial_jog_timer = QTimer(self)
        self.initial_jog_timer.setSingleShot(True)
        self.initial_jog_timer.timeout.connect(self.start_continuous_jog)

        self.continuous_jog_timer = QTimer(self)
        self.continuous_jog_timer.timeout.connect(self.perform_jog)

        # Timer for updating labels
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_labels)
        self.update_timer.start(200)  # Update every 200ms

    def start_jog(self, axis, direction):
        """Start jogging an axis"""
        if not self.robot.is_enabled():
            print("Robot must be enabled to jog")
            return
            
        self.jog_axis = axis
        self.jog_direction = direction
        self.perform_jog()  # Perform an immediate jog
        self.initial_jog_timer.start(500)  # Start the initial delay timer (500 ms)

    def start_continuous_jog(self):
        """Start continuous jogging after initial delay"""
        self.continuous_jog_timer.start(100)  # Start the continuous jog timer (100 ms)

    def stop_jog(self):
        """Stop all jogging"""
        self.initial_jog_timer.stop()
        self.continuous_jog_timer.stop()

    def perform_jog(self):
        """Perform a single jog step"""
        self.robot.move_jog(self.jog_axis, 0.001 * self.jog_direction)

    def auto_home_robot(self):
        """Home the robot using limit switches (X, Y, Z only)"""
        if not self.robot.is_enabled():
            print("Robot must be enabled to home")
            return
            
        self.robot.do_auto_home()
        self.update_home_status()

    def toggle_enable(self):
        """Toggle robot enable/disable state"""
        if self.enable_button.isChecked():
            self.robot.enable()
            self.enable_button.setText('Enabled')
            self.enable_button.setStyleSheet('background-color: green; color: white;')
        else:
            self.robot.disable()
            self.enable_button.setText('Disabled')
            self.enable_button.setStyleSheet('background-color: red; color: white;')

    def set_position(self):
        """Set position based on input values"""
        try:
            # Get values from input fields, defaulting to current position if empty
            x = float(self.setpoint_inputs['x'].text()) if self.setpoint_inputs['x'].text() else self.robot.x
            y = float(self.setpoint_inputs['y'].text()) if self.setpoint_inputs['y'].text() else self.robot.y
            z = float(self.setpoint_inputs['z'].text()) if self.setpoint_inputs['z'].text() else self.robot.z
            d = float(self.setpoint_inputs['d'].text()) if self.setpoint_inputs['d'].text() else self.robot.d
            
            self.robot.move_to_setpoint(x, y, z, d)
        except ValueError:
            print("Invalid setpoint value. Please enter valid numbers.")
    
    def set_home_position(self, axis):
        """Set the home position for a specific axis"""
        if not self.robot.is_enabled():
            print(f"Robot must be enabled to set {axis.upper()} home position")
            return
            
        # Get the value from the spin box
        reference_position = self.home_position_inputs[axis].value()
        
        # Call the robot method to set the home position
        success = self.robot.manual_home_axis(axis, reference_position)
        
        if success:
            # Update the homing status display
            self.update_home_status()
    
    def update_labels(self):
        """Update all position, velocity and status labels"""
        # Update position indicators
        self.position_indicators['x'].setText(f"{self.robot.x:.4f}")
        self.position_indicators['y'].setText(f"{self.robot.y:.4f}")
        self.position_indicators['z'].setText(f"{self.robot.z:.4f}")
        self.position_indicators['d'].setText(f"{self.robot.d:.4f}")
        
        # Update velocity label
        self.velocity_label.setText(f'Velocity: vx={self.robot.v_x:.4f}, vy={self.robot.v_y:.4f}, vz={self.robot.v_z:.4f}, vd={self.robot.v_d:.4f}')
        
        # Update status indicators
        self.update_robot_status()
        self.update_busy_status()
        self.update_home_status()
        
        # Update position labels in homing panel
        if hasattr(self, 'axis_groups'):
            for axis in ['x', 'y', 'z', 'd']:
                if axis == 'x':
                    self.axis_groups[axis]['position_label'].setText(f"{self.robot.x:.4f}")
                elif axis == 'y':
                    self.axis_groups[axis]['position_label'].setText(f"{self.robot.y:.4f}")
                elif axis == 'z':
                    self.axis_groups[axis]['position_label'].setText(f"{self.robot.z:.4f}")
                elif axis == 'd':
                    self.axis_groups[axis]['position_label'].setText(f"{self.robot.d:.4f}")
    
    def update_robot_status(self):
        """Update robot enable/disable status"""
        if self.robot.is_enabled():
            self.status_label.setText('Status: Enabled')
            self.status_label.setStyleSheet('background-color: green; color: white; padding: 5px;')
            self.enable_button.setChecked(True)
            self.enable_button.setText('Enabled')
            self.enable_button.setStyleSheet('background-color: green; color: white;')
        else:
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('background-color: red; color: white; padding: 5px;')
            self.enable_button.setChecked(False)
            self.enable_button.setText('Disabled')
            self.enable_button.setStyleSheet('background-color: red; color: white;')
    
    def update_busy_status(self):
        """Update busy/ready status"""
        if self.robot.is_busy():
            self.busy_label.setText('Command: Busy')
            self.busy_label.setStyleSheet('background-color: yellow; color: black; padding: 5px;')
        else:
            self.busy_label.setText('Command: Ready')
            self.busy_label.setStyleSheet('background-color: green; color: white; padding: 5px;')
    
    def update_home_status(self):
        """Update home status indicators"""
        # Overall home status
        if self.robot.was_homed:
            self.home_status_label.setText('Homing: Homed')
            self.home_status_label.setStyleSheet('background-color: green; color: white; padding: 5px;')
        else:
            self.home_status_label.setText('Homing: Not Homed')
            self.home_status_label.setStyleSheet('background-color: orange; color: white; padding: 5px;')
        
        # Individual axis home status
        for axis in ['x', 'y', 'z', 'd']:
            if self.robot.axis_homed[axis]:
                self.axis_status_labels[axis].setText(f"{axis.upper()}: Homed")
                self.axis_status_labels[axis].setStyleSheet('background-color: green; color: white; padding: 3px;')
                
                # Also update in the homing panel if it exists
                if hasattr(self, 'axis_groups'):
                    self.axis_groups[axis]['group'].setStyleSheet('QGroupBox { border: 2px solid green; }')
            else:
                self.axis_status_labels[axis].setText(f"{axis.upper()}: Not Homed")
                self.axis_status_labels[axis].setStyleSheet('background-color: #FFA500; color: white; padding: 3px;')
                
                # Also update in the homing panel
                if hasattr(self, 'axis_groups'):
                    self.axis_groups[axis]['group'].setStyleSheet('')  # Default style
    
    def reset_home_status(self):
        """Reset the homing status for all axes"""
        from PyQt5.QtWidgets import QMessageBox
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            'Reset Home Status',
            'This will reset the home status for all axes.\n\n'
            'The robot will NOT move, but all axes will be marked as "Not Homed".\n\n'
            'Continue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.robot.reset_home_status():
                # Update UI to reflect the change
                self.update_home_status()
                
                # Show confirmation message
                QMessageBox.information(
                    self,
                    "Home Status Reset",
                    "All axes have been marked as Not Homed. You'll need to recalibrate."
                )
                
                print("Home status reset for all axes")
                return True
        
        return False