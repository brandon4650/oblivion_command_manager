from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QComboBox, QPushButton, QCheckBox)

class CommandBuilderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_command = ""
        self.current_data = None
        self.parameter_widgets = []
        
        layout = QVBoxLayout(self)
        
        # Command preview
        self.preview_label = QLabel("Command Preview:")
        layout.addWidget(self.preview_label)
        
        self.preview_text = QLineEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Parameters area
        self.params_layout = QVBoxLayout()
        layout.addLayout(self.params_layout)
        
        # Manual edit option
        self.manual_checkbox = QCheckBox("Edit command manually")
        self.manual_checkbox.toggled.connect(self.toggle_manual_edit)
        layout.addWidget(self.manual_checkbox)
        
        self.manual_edit = QLineEdit()
        self.manual_edit.setEnabled(False)
        self.manual_edit.textChanged.connect(self.update_preview)
        layout.addWidget(self.manual_edit)
        
    def set_command(self, cmd_name, cmd_data):
        self.current_command = cmd_name
        self.current_data = cmd_data
        
        # Clear previous parameters
        self.clear_parameters()
        
        # If has parameters, create input fields
        if "parameters" in cmd_data and cmd_data["parameters"]:
            for param in cmd_data["parameters"]:
                param_layout = QHBoxLayout()
                
                # Parameter label
                if isinstance(param, str):
                    # Simple parameter name
                    label = QLabel(f"{param}:")
                    input_widget = QLineEdit()
                else:
                    # Detailed parameter object
                    label = QLabel(f"{param['name']}:")
                    input_widget = QLineEdit()
                    if "description" in param:
                        input_widget.setToolTip(param["description"])
                
                param_layout.addWidget(label)
                param_layout.addWidget(input_widget)
                
                self.params_layout.addLayout(param_layout)
                self.parameter_widgets.append((label, input_widget))
                
                # Connect to update preview
                input_widget.textChanged.connect(self.update_preview)
        
        # Update preview
        self.update_preview()
        
    def clear_parameters(self):
        # Clear all parameter widgets
        for label, widget in self.parameter_widgets:
            label.deleteLater()
            widget.deleteLater()
            
        self.parameter_widgets.clear()
        
        # Clear any layouts in the params area
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively clear nested layouts
                while item.layout().count():
                    nested_item = item.layout().takeAt(0)
                    if nested_item.widget():
                        nested_item.widget().deleteLater()
        
    def update_preview(self):
        if not self.current_command:
            self.preview_text.setText("")
            return
            
        if self.manual_checkbox.isChecked():
            # Use manual edit text
            self.preview_text.setText(self.manual_edit.text())
            return
            
        # Build command from parameters
        command = self.current_command
        
        # Add parameters if any
        if self.parameter_widgets:
            for i, (_, widget) in enumerate(self.parameter_widgets):
                param_value = widget.text().strip()
                if param_value:
                    command += f" {param_value}"
                    
        self.preview_text.setText(command)
        
    def toggle_manual_edit(self, checked):
        self.manual_edit.setEnabled(checked)
        
        if checked:
            # Copy current preview to manual edit
            self.manual_edit.setText(self.preview_text.text())
        else:
            # Update preview from parameters
            self.update_preview()
            
    def get_command(self):
        """Return the full command string"""
        return self.preview_text.text()