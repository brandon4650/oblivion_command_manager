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
        
        # Special handling for player.setav
        if cmd_name == "player.setav":
            param_layout = QHBoxLayout()
            
            # Create dropdown for attributes/skills
            type_label = QLabel("Type:")
            type_combo = QComboBox()
            type_combo.addItems(["Attribute", "Skill"])
            type_combo.currentTextChanged.connect(self.on_type_changed)
            
            param_layout.addWidget(type_label)
            param_layout.addWidget(type_combo)
            self.params_layout.addLayout(param_layout)
            
            # Create dropdown for specific attribute/skill
            value_layout = QHBoxLayout()
            value_label = QLabel("Select:")
            self.value_combo = QComboBox()
            
            # Start with attributes
            self.populate_attributes()
            
            value_layout.addWidget(value_label)
            value_layout.addWidget(self.value_combo)
            self.params_layout.addLayout(value_layout)
            
            # Create number input
            number_layout = QHBoxLayout()
            number_label = QLabel("Value:")
            self.number_input = QLineEdit()
            self.number_input.setPlaceholderText("Enter value (0-255 for attributes, 0-100 for skills)")
            
            number_layout.addWidget(number_label)
            number_layout.addWidget(self.number_input)
            self.params_layout.addLayout(number_layout)
            
            # Store references
            self.type_combo = type_combo
            
            # Connect changes to update preview
            self.value_combo.currentTextChanged.connect(self.update_preview)
            self.number_input.textChanged.connect(self.update_preview)
            
        else:
            # Regular parameter handling for other commands
            if "parameters" in cmd_data and cmd_data["parameters"]:
                for param in cmd_data["parameters"]:
                    param_layout = QHBoxLayout()
                    
                    if isinstance(param, str):
                        label = QLabel(f"{param}:")
                        input_widget = QLineEdit()
                    else:
                        label = QLabel(f"{param['name']}:")
                        input_widget = QLineEdit()
                        if "description" in param:
                            input_widget.setToolTip(param["description"])
                    
                    param_layout.addWidget(label)
                    param_layout.addWidget(input_widget)
                    
                    self.params_layout.addLayout(param_layout)
                    self.parameter_widgets.append((label, input_widget))
                    
                    input_widget.textChanged.connect(self.update_preview)
        
        self.update_preview()

    def on_type_changed(self, type_text):
        """Handle change in attribute/skill type selection"""
        if type_text == "Attribute":
            self.populate_attributes()
        else:
            self.populate_skills()
        self.update_preview()
    
    def populate_attributes(self):
        """Populate the dropdown with attributes"""
        self.value_combo.clear()
        attributes = ["Strength", "Intelligence", "Willpower", "Agility", 
                     "Speed", "Endurance", "Personality", "Luck"]
        self.value_combo.addItems(attributes)
    
    def populate_skills(self):
        """Populate the dropdown with skills"""
        self.value_combo.clear()
        skills = ["Acrobatics", "Alchemy", "Alteration", "Armorer", "Athletics", 
                  "Blade", "Block", "Blunt", "Conjuration", "Destruction", 
                  "Hand to Hand", "Heavy Armor", "Illusion", "Light Armor", 
                  "Marksman", "Mercantile", "Mysticism", "Restoration", 
                  "Security", "Sneak", "Speechcraft"]
        self.value_combo.addItems(sorted(skills))
            
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
            self.preview_text.setText(self.manual_edit.text())
            return
        
        # Special handling for player.setav
        if self.current_command == "player.setav" and hasattr(self, 'value_combo'):
            selected_value = self.value_combo.currentText()
            number_value = self.number_input.text()
            
            if selected_value and number_value:
                command = f"player.setav {selected_value} {number_value}"
            else:
                command = "player.setav"
            
            self.preview_text.setText(command)
            return
        
        # Regular command building
        command = self.current_command
        
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