
from PyQt6.QtWidgets import (QMainWindow, QTreeWidget, QTreeWidgetItem, 
                           QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QSplitter, QTextEdit, QStackedWidget,
                           QSizePolicy, QFrame, QMenu, QMessageBox, QTabWidget,
                           QComboBox, QGroupBox, QGraphicsOpacityEffect, QSpinBox, QApplication)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize, QRect, QEvent
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QPen, QPolygon, QBrush
import pyautogui
import psutil
import os
import webbrowser
from json_loader import OblivionDataLoader
from game_connector import send_command_to_game, is_game_running
from ui_builder import CommandBuilderWidget


class EnhancedItemSelector(QWidget):
    """Enhanced widget for selecting items from all available categories"""
    
    # Signal emitted when a command is selected
    commandSelected = pyqtSignal(str, dict)
    
    def __init__(self, data_loader, category):
        super().__init__()
        self.data_loader = data_loader
        self.category = category
        self.items = data_loader.get_category_items(category)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Title with category icon
        category_info = self.data_loader.get_category_info(self.category)
        title_label = QLabel(f"{category_info['icon']} {self.category}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(category_info["description"])
        desc_label.setWordWrap(True)  # ADD THIS LINE
        desc_label.setMinimumHeight(40)  # ADD THIS LINE
        main_layout.addWidget(desc_label)
            
        # Search filter
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(f"Search {self.category.lower()}...")
        self.search_box.textChanged.connect(self.filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        main_layout.addLayout(search_layout)
        
        # Item selector
        self.item_combo = QComboBox()
        self.item_combo.setMinimumWidth(300)
        self.item_combo.setMinimumHeight(30)  # ADD THIS LINE
        self.populate_items()
        self.item_combo.currentIndexChanged.connect(self.update_preview)
        main_layout.addWidget(self.item_combo)
        
        # Item details group
        details_group = QGroupBox("Item Details")
        details_group.setMinimumHeight(150)  # ADD THIS LINE
        details_layout = QVBoxLayout(details_group)
        
        # Item ID
        id_layout = QHBoxLayout()
        id_label = QLabel("Item ID:")
        self.id_field = QLineEdit()
        self.id_field.setReadOnly(True)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_field)
        details_layout.addLayout(id_layout)
        
        # Command preview
        cmd_label = QLabel("Command:")
        self.cmd_field = QLineEdit()
        self.cmd_field.setReadOnly(True)
        details_layout.addWidget(cmd_label)
        details_layout.addWidget(self.cmd_field)
        
        # Only show quantity field for item categories that support it
        if self.category not in ["NPCs", "Locations", "Spells"]:
            # Quantity
            qty_layout = QHBoxLayout()
            qty_label = QLabel("Quantity:")
            self.qty_spin = QLineEdit("1")
            self.qty_spin.setMaximumWidth(100)
            self.qty_spin.textChanged.connect(self.update_command)
            qty_layout.addWidget(qty_label)
            qty_layout.addWidget(self.qty_spin)
            qty_layout.addStretch()
            details_layout.addLayout(qty_layout)
        else:
            self.qty_spin = None
        
        main_layout.addWidget(details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Copy button
        self.copy_btn = QPushButton("Copy Command")
        self.copy_btn.clicked.connect(self.copy_command)
        self.copy_btn.setEnabled(False)
        button_layout.addWidget(self.copy_btn)
        
        # Add to favorites button
        self.fav_btn = QPushButton("Add to Favorites")
        self.fav_btn.clicked.connect(self.add_to_favorites)
        self.fav_btn.setEnabled(False)
        button_layout.addWidget(self.fav_btn)
        
        # Execute button
        self.execute_btn = QPushButton("Execute Command")
        self.execute_btn.clicked.connect(self.execute_command)
        self.execute_btn.setEnabled(False)
        button_layout.addWidget(self.execute_btn)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        # Initialize with first item if available
        if self.item_combo.count() > 0:
            self.update_preview(0)
        
    def populate_items(self, filtered_items=None):
       """Populate the item dropdown with all or filtered items"""
       self.item_combo.clear()
       
       items_to_show = filtered_items if filtered_items is not None else self.items
       
       # Sort items alphabetically by name
       sorted_items = sorted(items_to_show, key=lambda x: x[1].get("name", ""))
       
       for item_key, item_data in sorted_items:
           self.item_combo.addItem(item_data["name"], item_key)
       
       # Set item height for the combo box
       self.item_combo.setStyleSheet("""
           QComboBox {
               min-height: 25px;
           }
           QComboBox QAbstractItemView {
               min-height: 25px;
           }
       """)  # ADD THIS STYLE
    
    def filter_items(self):
        """Filter items based on search text"""
        search_text = self.search_box.text().lower()
        
        if not search_text:
            self.populate_items()
            return
        
        filtered_items = []
        for item_key, item_data in self.items:
            # Search in name and ID
            if (search_text in item_data["name"].lower() or 
                search_text in item_data["id"].lower()):
                filtered_items.append((item_key, item_data))
        
        self.populate_items(filtered_items)
        
    def update_preview(self, index):
        """Update the item details when an item is selected"""
        if index < 0 or index >= self.item_combo.count():
            self.copy_btn.setEnabled(False)
            self.fav_btn.setEnabled(False)
            self.execute_btn.setEnabled(False)
            return
        
        item_key = self.item_combo.itemData(index)
        if not item_key:
            return
            
        # Find item data
        item_data = None
        for key, data in self.items:
            if key == item_key:
                item_data = data
                break
                
        if not item_data:
            return
            
        # Update fields
        self.id_field.setText(item_data["id"])
        
        # Update command with current quantity if applicable
        self.update_command()
        
        self.copy_btn.setEnabled(True)
        self.fav_btn.setEnabled(True)
        self.execute_btn.setEnabled(True)
        
    def update_command(self):
        """Update the command preview with the current quantity"""
        index = self.item_combo.currentIndex()
        if index < 0:
            return
            
        item_key = self.item_combo.itemData(index)
        if not item_key:
            return
            
        # Find item data
        item_data = None
        for key, data in self.items:
            if key == item_key:
                item_data = data
                break
                
        if not item_data:
            return
            
        # Get base command
        command = item_data["command"]
        
        # Update quantity if applicable
        if self.qty_spin and "additem" in command.lower():
            try:
                quantity = int(self.qty_spin.text())
                if quantity < 1:
                    quantity = 1
            except ValueError:
                quantity = 1
                
            # Replace the last number in the command
            parts = command.split()
            parts[-1] = str(quantity)
            command = " ".join(parts)
        
        self.cmd_field.setText(command)
        
    def copy_command(self):
        """Copy the command to clipboard"""
        command = self.cmd_field.text()
        if command:
            pyautogui.hotkey('ctrl', 'c')
            QMessageBox.information(self, "Command Copied", 
                                    "Command has been copied to clipboard")
            
    def add_to_favorites(self):
        """Emit signal to add the selected command to favorites"""
        index = self.item_combo.currentIndex()
        if index < 0:
            return
            
        item_key = self.item_combo.itemData(index)
        if not item_key:
            return
            
        # Find item data
        item_data = None
        for key, data in self.items:
            if key == item_key:
                item_data = data
                break
                
        if not item_data:
            return
            
        command = self.cmd_field.text()
        
        # Create a command data dictionary
        cmd_data = {
            "description": f"Adds {item_data['name']}",
            "syntax": command,
            "parameters": [],
            "category": self.category,
            "item_key": item_key,
            "is_item": True
        }
        
        self.commandSelected.emit(command, cmd_data)
            
    def execute_command(self):
        """Execute the current command in the game"""
        command = self.cmd_field.text()
        if not command:
            return
            
        # Check if game is running
        if not is_game_running():
            QMessageBox.warning(self, "Game Not Running", 
                               "The game is not running. Command cannot be executed.")
            return
            
        # Send command to game
        success = send_command_to_game(command)
        
        if success:
            QMessageBox.information(self, "Command Executed", 
                                   "Command has been executed in the game.")
        else:
            QMessageBox.warning(self, "Command Failed", 
                               "Failed to execute command in the game.")


class DonateButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 60)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the donate button
        self.button = QPushButton("❤️ Donate")
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.button.setFixedHeight(40)
        self.layout.addWidget(self.button)
        
        # Create scrolling message label
        self.message_label = QLabel("▲ Support")
        self.message_label.setStyleSheet("""
            color: #4CAF50;
            font-weight: bold;
            font-size: 10pt;
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.message_label)
        
        # Long thank you message that will scroll
        self.full_message = "Thanks for your support! Your donations help us create more awesome tools for the Elder Scrolls community. ❤️ "
        
        # Current display position in the text
        self.scroll_position = 0
        
        # Set up scroll timer
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.update_scroll_text)
        self.scroll_timer.start(150)  # Update every 150ms
        
        # Character display width for the scrolling window
        self.display_width = 20
        
        # Connect button to open URL
        self.button.clicked.connect(self.open_donate_url)
        
        # Create a popup message that appears once
        self.popup_displayed = False
        QTimer.singleShot(3000, self.show_popup_message)
    
    def update_scroll_text(self):
        """Update the scrolling text"""
        # Get the text segment to display
        wrapped_text = self.full_message + "    " + self.full_message  # Add space between repeats
        segment_end = self.scroll_position + self.display_width
        
        if segment_end <= len(wrapped_text):
            display_text = wrapped_text[self.scroll_position:segment_end]
        else:
            # Handle wraparound
            overflow = segment_end - len(wrapped_text)
            display_text = wrapped_text[self.scroll_position:] + wrapped_text[:overflow]
        
        # Update label
        self.message_label.setText(display_text)
        
        # Advance position
        self.scroll_position = (self.scroll_position + 1) % len(self.full_message)
    
    def open_donate_url(self):
        """Open the donation URL"""
        import webbrowser
        webbrowser.open("https://cryptocraft.sell.app/product/product-ocm")
        
    def show_popup_message(self):
        """Show a one-time popup message"""
        if not self.popup_displayed:
            self.popup_displayed = True
            
            popup = QLabel(self.parentWidget())
            popup.setText("Please consider supporting this project!")
            popup.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
            """)
            popup.setWordWrap(True)
            popup.setAlignment(Qt.AlignmentFlag.AlignCenter)
            popup.resize(220, 40)
            
            # Position near donate button
            popup_pos = self.mapToParent(QPoint(0, -60))
            popup.move(popup_pos)
            
            # Show with fade-in effect
            self.fade_in_widget(popup)
            
            # Auto-hide after 5 seconds
            QTimer.singleShot(5000, lambda: self.fade_out_widget(popup))
    
    def fade_in_widget(self, widget):
        """Fade in a widget with animation"""
        self.fade_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.fade_effect)
        
        # Create and configure the animation
        self.fade_anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Show the widget and start the animation
        widget.show()
        self.fade_anim.start()
    
    def fade_out_widget(self, widget):
        """Fade out a widget with animation"""
        self.fade_out_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.fade_out_effect)
        
        # Create and configure the animation
        self.fade_out_anim = QPropertyAnimation(self.fade_out_effect, b"opacity")
        self.fade_out_anim.setDuration(500)
        self.fade_out_anim.setStartValue(1)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Connect the animation's finished signal to hide the widget
        self.fade_out_anim.finished.connect(widget.hide)
        self.fade_out_anim.start()

class DonateArrowIndicator(QWidget):
    """A separate widget that shows a small animated arrow pointing to the donate button"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Make widget transparent so only the arrow shows
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Increase the size for better visibility
        self.setFixedSize(80, 50)  # Larger size
        
        # Animation for the arrow
        self.arrow_animation = QPropertyAnimation(self, b"pos")
        self.arrow_animation.setDuration(800)
        self.arrow_animation.setStartValue(QPoint(0, 0))
        self.arrow_animation.setEndValue(QPoint(10, 0))  # Larger movement
        self.arrow_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.arrow_animation.setLoopCount(-1)  # Infinite loop
        
        # Start animation
        self.arrow_animation.start()
    
    def paintEvent(self, event):
        """Draw a simple arrow pointing to the donate button"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up pen and brush for arrow
        pen = QPen(QColor("#4CAF50"))  # Green
        pen.setWidth(2)  # Thicker line
        painter.setPen(pen)
        
        brush = QBrush(QColor("#4CAF50"))
        painter.setBrush(brush)
        
        # Calculate arrow position based on animation
        offset = self.arrow_animation.currentValue().x() if self.arrow_animation.state() == QPropertyAnimation.State.Running else 0
        
        # Draw a larger arrow
        points = [
            QPoint(25 + int(offset), 25),      # Tip
            QPoint(10 + int(offset), 18),      # Top corner
            QPoint(15 + int(offset), 25),      # Top indent
            QPoint(10 + int(offset), 32)       # Bottom corner
        ]
        
        # Create a polygon from the points and draw it
        arrow = QPolygon(points)
        painter.drawPolygon(arrow)
        
        # Draw "Support" text with larger font
        pen = QPen(QColor("#4CAF50"))
        painter.setPen(pen)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)  # Larger font
        painter.setFont(font)
        painter.drawText(QPoint(30, 28), "Support")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oblivion Console Manager")
        self.setMinimumSize(900, 700)
        
        # Load data
        self.data_loader = OblivionDataLoader("data")  # Adjust path as needed
        if not self.data_loader.load_all_json_data():
            QMessageBox.critical(self, "Error", "Failed to load data files.")
            return
        
        # Check if icons exist
        self.check_icons()
        
        # Set up the core UI structure
        self.setup_core_ui()
        
        # Setup main UI contents
        self.setup_ui_contents()
        
        # Load settings
        self.settings = QSettings("OblivionConsoleManager", "Settings")
        self.load_settings()
        
        # Set up game status checker
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_game_status)
        self.status_timer.start(2000)  # Check every 2 seconds
        
    def check_icons(self):
        """Check if required icons exist, create default ones if necessary"""
        icons_dir = "icons"
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
            
        # List of required icons
        required_icons = ["folder.png", "collapsed.png", "expanded.png", "down_arrow.png", "checkmark.png"]
        
        # Check each icon
        for icon in required_icons:
            icon_path = os.path.join(icons_dir, icon)
            if not os.path.exists(icon_path):
                print(f"Icon {icon} not found, using default styling")
                
    def setup_core_ui(self):
        """Set up the core UI structure"""
        # Create main central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # Apply solid background to central widget
        self.central_widget.setAutoFillBackground(True)
        self.central_widget.setStyleSheet("""
            background-color: #1E1E1E;
            color: #E6E6E6;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        """)
        
        # Create our main layout for UI elements
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)  # Increase spacing between elements
        self.main_layout.setContentsMargins(15, 15, 15, 15)  # Add some padding around the edges

    def create_attribute_skill_commands(self):
        """Create special UI section for attributes and skills"""
        # Create main group box
        group = QGroupBox("Character Attributes & Skills")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 1px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Attributes section
        attr_group = QGroupBox("Attributes")
        attr_layout = QVBoxLayout()
        
        # Attributes list
        attributes = ["Strength", "Intelligence", "Willpower", "Agility", 
                     "Speed", "Endurance", "Personality", "Luck"]
        
        # Create attribute dropdown and value input
        attr_row = QHBoxLayout()
        attr_dropdown = QComboBox()
        attr_dropdown.addItems(attributes)
        attr_value = QSpinBox()
        attr_value.setRange(0, 255)
        attr_value.setValue(50)
        
        attr_button = QPushButton("Set Attribute")
        attr_button.clicked.connect(lambda: self.execute_setav_command(
            f"player.setav {attr_dropdown.currentText()} {attr_value.value()}"
        ))
        
        attr_row.addWidget(QLabel("Attribute:"))
        attr_row.addWidget(attr_dropdown)
        attr_row.addWidget(QLabel("Value:"))
        attr_row.addWidget(attr_value)
        attr_row.addWidget(attr_button)
        
        attr_layout.addLayout(attr_row)
        attr_group.setLayout(attr_layout)
        
        # Skills section
        skills_group = QGroupBox("Skills (Major & Minor)")
        skills_layout = QVBoxLayout()
        
        # All skills list (can be major or minor depending on character class)
        all_skills = [
            "Acrobatics", "Alchemy", "Alteration", "Armorer", "Athletics", 
            "Blade", "Block", "Blunt", "Conjuration", "Destruction", 
            "Hand to Hand", "Heavy Armor", "Illusion", "Light Armor", 
            "Marksman", "Mercantile", "Mysticism", "Restoration", 
            "Security", "Sneak", "Speechcraft"
        ]
        
        # Create skill dropdown and value input
        skill_row = QHBoxLayout()
        skill_dropdown = QComboBox()
        skill_dropdown.addItems(sorted(all_skills))  # Sort alphabetically
        skill_value = QSpinBox()
        skill_value.setRange(0, 100)
        skill_value.setValue(50)
        
        skill_button = QPushButton("Set Skill")
        skill_button.clicked.connect(lambda: self.execute_setav_command(
            f"player.setav {skill_dropdown.currentText()} {skill_value.value()}"
        ))
        
        skill_row.addWidget(QLabel("Skill:"))
        skill_row.addWidget(skill_dropdown)
        skill_row.addWidget(QLabel("Value:"))
        skill_row.addWidget(skill_value)
        skill_row.addWidget(skill_button)
        
        skills_layout.addLayout(skill_row)
        
        # Add a note about major/minor skills
        note = QLabel("Note: Skills can be Major or Minor depending on your character's class")
        note.setStyleSheet("color: #888; font-style: italic;")
        skills_layout.addWidget(note)
        
        skills_group.setLayout(skills_layout)
        
        # Add both groups to main layout
        layout.addWidget(attr_group)
        layout.addWidget(skills_group)
        
        # Add divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(divider)
        
        # Add modpca command section for attributes
        modpca_group = QGroupBox("Modify Current Attribute (modpca)")
        modpca_layout = QVBoxLayout()
        
        modpca_row = QHBoxLayout()
        modpca_dropdown = QComboBox()
        modpca_dropdown.addItems(attributes)
        modpca_value = QSpinBox()
        modpca_value.setRange(-100, 100)
        modpca_value.setValue(10)
        
        modpca_button = QPushButton("Modify Attribute")
        modpca_button.clicked.connect(lambda: self.execute_setav_command(
            f'modpca "{modpca_dropdown.currentText()}" {modpca_value.value()}'
        ))
        
        modpca_row.addWidget(QLabel("Attribute:"))
        modpca_row.addWidget(modpca_dropdown)
        modpca_row.addWidget(QLabel("Amount (+/-):"))
        modpca_row.addWidget(modpca_value)
        modpca_row.addWidget(modpca_button)
        
        modpca_layout.addLayout(modpca_row)
        modpca_group.setLayout(modpca_layout)
        
        layout.addWidget(modpca_group)
        group.setLayout(layout)
        
        return group
    
    def execute_setav_command(self, command):
        """Execute the setav command with proper formatting"""
        if is_game_running():
            send_command_to_game(command)
            self.history_text.append(f"> {command}")  # Add to history
        else:
            QMessageBox.warning(self, "Game Not Running", 
                              "Oblivion Remastered must be running to execute commands.")
    
    def setup_ui_contents(self):
        """Set up the actual UI contents in the central widget with improved layout"""
        # Header area with logo and game status
        header_container = QFrame()
        header_container.setFrameShape(QFrame.Shape.StyledPanel)
        header_container.setFrameShadow(QFrame.Shadow.Raised)
        header_container.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)
        
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        # Game status indicator (left)
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("Game Status: Not Detected")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        status_layout.addWidget(self.status_label)
        
        header_layout.addWidget(status_frame)
    
        # Add Discord button (left-middle)
        self.discord_button = QPushButton("💬 Join Discord")
        self.discord_button.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11pt;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
            QPushButton:pressed {
                background-color: #3C45A5;
            }
        """)
        self.discord_button.clicked.connect(self.open_discord)
        header_layout.addWidget(self.discord_button)
        
        # Oblivion logo (center)
        logo_label = QLabel()
        logo_path = os.path.join("icons", "oblivion.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale the image to a larger size for better quality
            pixmap = pixmap.scaled(300, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Set a minimum height for the label to give the logo more space
            logo_label.setMinimumHeight(150)
        else:
            logo_label.setText("Oblivion Console Manager")
            logo_label.setStyleSheet("font-size: 22pt; font-weight: bold; color: #C0C0C0;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(logo_label, 1)  # Give the logo more space
        
        # Donate button (right)
        donate_container = QWidget()
        donate_layout = QVBoxLayout(donate_container)
        donate_layout.setContentsMargins(0, 0, 0, 0)
        
        self.donate_button = DonateButton()
        donate_layout.addWidget(self.donate_button, 0, Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(donate_container)
        
        # Add the header to the main layout
        self.main_layout.addWidget(header_container)
        
        # Search container
        search_container = QFrame()
        search_container.setFrameShape(QFrame.Shape.StyledPanel)
        search_container.setFrameShadow(QFrame.Shadow.Raised)
        search_container.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search commands and items...")
        self.search_box.setMinimumHeight(40)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #E6E6E6;
                padding: 5px 15px;
                font-size: 12pt;
            }
            QLineEdit:focus {
                border: 1px solid #007ACC;
            }
        """)
        self.search_box.textChanged.connect(self.filter_commands)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        
        self.main_layout.addWidget(search_container)
        
        # Create a horizontal layout for the main content
        main_content_container = QFrame()
        main_content_container.setFrameShape(QFrame.Shape.StyledPanel)
        main_content_container.setFrameShadow(QFrame.Shadow.Raised)
        main_content_container.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        main_content_layout = QHBoxLayout(main_content_container)
        main_content_layout.setContentsMargins(10, 10, 10, 10)
        main_content_layout.setSpacing(15)
        
        # Left side: Categories and History (vertical layout)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # Categories tree
        tree_container = QFrame()
        tree_container.setFrameShape(QFrame.Shape.StyledPanel)
        tree_container.setFrameShadow(QFrame.Shadow.Raised)
        tree_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(10, 10, 10, 10)
        
        tree_title = QLabel("Categories")
        tree_title.setStyleSheet("font-weight: bold; font-size: 14pt; padding: 5px; color: #00B050;")
        tree_layout.addWidget(tree_title)
        
        self.command_tree = QTreeWidget()
        self.command_tree.setHeaderLabels(["Commands and Items"])
        self.command_tree.setAnimated(True)
        self.command_tree.setExpandsOnDoubleClick(True)
        self.command_tree.setAlternatingRowColors(True)
        self.command_tree.setIndentation(15)
        self.command_tree.setFrameShape(QFrame.Shape.StyledPanel)
        self.command_tree.setFrameShadow(QFrame.Shadow.Sunken)
        self.command_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                border: 1px solid #3F3F46;
                alternate-background-color: #2A2A2B;
                selection-background-color: #0E639C;
                selection-color: white;
                border-radius: 5px;
            }
            QTreeWidget::item {
                padding: 6px;
                min-height: 30px;
            }
            QTreeWidget::item:hover {
                background-color: #3E3E40;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(icons/collapsed.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(icons/expanded.png);
            }
        """)
        
        tree_layout.addWidget(self.command_tree)
        left_layout.addWidget(tree_container, 3) # Tree gets 3 parts of the space
        
        # Command History (below categories)
        history_container = QFrame()
        history_container.setFrameShape(QFrame.Shape.StyledPanel)
        history_container.setFrameShadow(QFrame.Shadow.Raised)
        history_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        # History header with title and clear button
        history_header = QHBoxLayout()
        
        history_label = QLabel("Command History")
        history_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #00B050;")
        history_header.addWidget(history_label)
        
        history_header.addStretch()
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #504F52;
            }
            QPushButton:pressed {
                background-color: #2D2D30;
            }
        """)
        clear_history_btn.clicked.connect(self.clear_history)
        history_header.addWidget(clear_history_btn)
        
        history_layout.addLayout(history_header)
        
        # History text area
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                color: #E6E6E6;
                padding: 10px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11pt;
            }
        """)
        history_layout.addWidget(self.history_text)
        
        left_layout.addWidget(history_container, 2) # History gets 2 parts of the space
        
        # Add the left panel to the main content layout
        main_content_layout.addWidget(left_panel, 3) # Left panel gets 3 parts of width
        
        # Right side: Command details and stacked widget
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # Stacked widget for different detail panels
        self.details_stack = QStackedWidget()
        
        # Command details widget
        self.command_details = QWidget()
        self.command_details.setAutoFillBackground(True)
        self.details_layout = QVBoxLayout(self.command_details)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.setSpacing(15)
        
        # Create a default view for the details panel
        default_detail_container = QFrame()
        default_detail_container.setFrameShape(QFrame.Shape.StyledPanel)
        default_detail_container.setFrameShadow(QFrame.Shadow.Raised)
        default_detail_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 20px;
            }
        """)
        default_detail_layout = QVBoxLayout(default_detail_container)
        
        default_title = QLabel("Command Details")
        default_title.setStyleSheet("font-weight: bold; font-size: 14pt; color: #00B050;")
        default_detail_layout.addWidget(default_title)
        
        self.command_title = QLabel("Select a command")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.command_title.setFont(font)
        self.command_title.setStyleSheet("color: #E6E6E6; margin-top: 10px;")
        default_detail_layout.addWidget(self.command_title)
        
        self.command_description = QLabel("")
        self.command_description.setWordWrap(True)
        self.command_description.setStyleSheet("padding: 10px 0; font-size: 11pt;")
        default_detail_layout.addWidget(self.command_description)
        
        self.command_syntax = QLabel("")
        self.command_syntax.setStyleSheet("""
            color: #CEA139; 
            padding: 10px; 
            background-color: #1E1E1E; 
            border-radius: 5px;
            font-family: Consolas, Monaco, monospace;
            margin: 10px 0;
        """)
        default_detail_layout.addWidget(self.command_syntax)
        
        # Add default panel to details layout
        self.details_layout.addWidget(default_detail_container)
        
        # Command builder area
        builder_container = QFrame()
        builder_container.setFrameShape(QFrame.Shape.StyledPanel)
        builder_container.setFrameShadow(QFrame.Shape.Raised)
        builder_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 20px;
            }
        """)
        builder_layout = QVBoxLayout(builder_container)
        
        builder_title = QLabel("Command Builder")
        builder_title.setStyleSheet("font-weight: bold; font-size: 14pt; color: #00B050;")
        builder_layout.addWidget(builder_title)
        
        self.builder_widget = CommandBuilderWidget()
        self.builder_widget.setStyleSheet("""
            QLineEdit, QSpinBox, QComboBox {
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #E6E6E6;
                padding: 5px 10px;
                min-height: 30px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #007ACC;
            }
            QLabel {
                font-size: 11pt;
            }
        """)
        builder_layout.addWidget(self.builder_widget)
        
        self.details_layout.addWidget(builder_container)
        
        # Button area
        button_container = QFrame()
        button_container.setFrameShape(QFrame.Shape.NoFrame)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(15)
        
        self.execute_button = QPushButton("Execute Command")
        self.execute_button.setMinimumHeight(45)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #0A4C7C;
            }
        """)
        self.execute_button.clicked.connect(self.execute_command)
        button_layout.addWidget(self.execute_button)
        
        self.favorite_button = QPushButton("Add to Favorites")
        self.favorite_button.setMinimumHeight(45)
        self.favorite_button.setStyleSheet("""
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #504F52;
            }
            QPushButton:pressed {
                background-color: #2D2D30;
            }
        """)
        self.favorite_button.clicked.connect(self.add_to_favorites)
        button_layout.addWidget(self.favorite_button)
        
        self.details_layout.addWidget(button_container)
        
        # Add command details to stacked widget
        self.details_stack.addWidget(self.command_details)  # Index 0
        
        # Item selector tab container will be added in create_item_selector_tabs()
        # This method will add the tab container to index 1 of the details_stack
        
        right_layout.addWidget(self.details_stack)
        main_content_layout.addWidget(right_panel, 7) # Right panel gets 7 parts of width
        
        # Add the main content container to the layout
        self.main_layout.addWidget(main_content_container, 1) # Give it all remaining space
        
        # Status bar with additional info
        footer_container = QFrame()
        footer_container.setFrameShape(QFrame.Shape.StyledPanel)
        footer_container.setFrameShadow(QFrame.Shape.Raised)
        footer_container.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        
        footer_layout = QHBoxLayout(footer_container)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        version_label = QLabel("v1.0.2")
        version_label.setStyleSheet("color: #808080; font-size: 10pt;")
        footer_layout.addWidget(version_label)
        
        footer_layout.addStretch()
        
        help_label = QLabel("Right-click items for more options | Select a command to see details")
        help_label.setStyleSheet("color: #808080; font-size: 10pt;")
        footer_layout.addWidget(help_label)
        
        self.main_layout.addWidget(footer_container)
        
        # Continue with the rest of your existing code...
        self.setup_context_menu()
        self.populate_command_tree()
        self.command_tree.itemClicked.connect(self.item_clicked)
        self.create_item_selector_tabs()
        
        # Expand all categories by default
        for i in range(self.command_tree.topLevelItemCount()):
            self.command_tree.topLevelItem(i).setExpanded(True)
        
        self.check_game_status()
        
    def setup_context_menu(self):
        """Set up context menu for the command tree"""
        # Enable context menu
        self.command_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.command_tree.customContextMenuRequested.connect(self.show_context_menu)

    def clear_history(self):
        """Clear the command history"""
        # Ask for confirmation
        reply = QMessageBox.question(self, "Clear History", 
                                    "Are you sure you want to clear the command history?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        # Clear the history text
        self.history_text.clear()
        
        # Optionally, you could also save the empty history to settings
        # self.settings.setValue("command_history", [])
        
        QMessageBox.information(self, "History Cleared", 
                              "Command history has been cleared.")
        
    def show_context_menu(self, position):
        """Show context menu for the command tree"""
        # Get the item under the cursor
        item = self.command_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # Check if it's a command or category
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            # It might be a category (top level item)
            if item.parent() is None:
                # For the Favorites category, add a "Clear Favorites" option
                if "Favorites" in item.text(0):
                    clear_action = menu.addAction("Clear All Favorites")
                    clear_action.triggered.connect(self.clear_favorites)
                    menu.exec(self.command_tree.mapToGlobal(position))
            return
            
        parent_item = item.parent()
        
        if parent_item and "Favorites" in parent_item.text(0):
            # Item is in favorites, offer to remove
            remove_action = menu.addAction("Remove from Favorites")
            remove_action.triggered.connect(lambda: self.remove_from_favorites(item))
        else:
            # Item is not in favorites, offer to add
            add_action = menu.addAction("Add to Favorites")
            add_action.triggered.connect(lambda: self.add_to_favorites_from_menu(item))
        
        # Add execute option for commands
        execute_action = menu.addAction("Execute Command")
        execute_action.triggered.connect(lambda: self.execute_command_from_menu(item))
        
        # Show the menu
        menu.exec(self.command_tree.mapToGlobal(position))

    def max_all_skills_attributes(self):
        """Max all attributes to 255 and all skills to 100"""
        # Check if game is running first
        if not is_game_running():
            QMessageBox.warning(self, "Game Not Running", 
                              "Oblivion must be running to execute commands.")
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(self, "Max All Skills & Attributes", 
                                   "This will set ALL attributes to 255 and ALL skills to 100.\n\n"
                                   "This is a 'god mode' change and may affect game balance.\n\n"
                                   "Do you want to continue?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Prepare command lists
        attributes = ["Strength", "Intelligence", "Willpower", "Agility", 
                     "Speed", "Endurance", "Personality", "Luck"]
        
        skills = [
            "Acrobatics", "Alchemy", "Alteration", "Armorer", "Athletics", 
            "Blade", "Block", "Blunt", "Conjuration", "Destruction", 
            "HandtoHand", "HeavyArmor", "Illusion", "LightArmor", 
            "Marksman", "Mercantile", "Mysticism", "Restoration", 
            "Security", "Sneak", "Speechcraft"
        ]
        
        # Build command list
        commands = []
        # Add attribute commands
        for attribute in attributes:
            commands.append(f'player.setav "{attribute}" 255')
        
        # Add skill commands
        for skill in skills:
            commands.append(f'player.setav "{skill}" 100')
        
        # Show instructions dialog
        QMessageBox.information(self, "Instructions", 
                              "1. Click OK on this message\n"
                              "2. Switch to Oblivion (Alt+Tab)\n"
                              "3. Wait while commands are executed (10-15 seconds)\n"
                              "4. You'll see a completion message when done")
        
        # Get the game window and activate it
        import time
        
        # Find and switch to the Oblivion window
        # This uses the game_connector's approach for sending commands
        try:
            # Find the Oblivion process
            for process in psutil.process_iter(['pid', 'name']):
                # Check for Oblivion process
                if "oblivion" in process.info['name'].lower():
                    # Switch to it using Alt+Tab
                    pyautogui.keyDown('alt')
                    pyautogui.press('tab')
                    pyautogui.keyUp('alt')
                    time.sleep(1)  # Give it time to switch
                    break
                    
            # Wait briefly to ensure the game window is active
            time.sleep(0.5)
            
            # Open console
            pyautogui.press('`')
            time.sleep(0.3)
            
            # Execute all commands
            for command in commands:
                # Type command
                pyautogui.write(command)
                time.sleep(0.1)
                # Press Enter
                pyautogui.press('enter')
                # Record in history
                self.history_text.append(f"> {command}")
                # Small delay between commands
                time.sleep(0.1)
            
            # Close console
            time.sleep(0.3)
            pyautogui.press('`')
            
            # Switch back to the app
            time.sleep(0.5)
            pyautogui.keyDown('alt')
            pyautogui.press('tab')
            pyautogui.keyUp('alt')
            
            # Show completion message
            QMessageBox.information(self, "Operation Complete", 
                                "All attributes set to 255 and all skills set to 100!")
                                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to apply settings: {str(e)}\n\n"
                               "Try using individual commands instead.")
    
    def populate_command_tree(self):
        """Populate command tree with categories and commands"""
        # Add categories
        self.category_items = {}
        
        # Add "Favorites" category first
        favorites = QTreeWidgetItem(self.command_tree)
        favorites.setText(0, "❤️ Favorites")
        
        # Use folder icon if it exists
        if os.path.exists("icons/folder.png"):
            favorites.setIcon(0, QIcon("icons/folder.png"))
        
        self.category_items["Favorites"] = favorites
        
        # Add all other categories (follow the order in data_loader.categories)
        for category_data in self.data_loader.categories:
            category_name = category_data["name"]
            category_icon = category_data["icon"]
            
            # Skip old categories we don't need anymore
            if category_name in ["Character", "Items", "World", "Other"]:
                continue
                
            category_item = QTreeWidgetItem(self.command_tree)
            category_item.setText(0, f"{category_icon} {category_name}")
            
            # Use folder icon if it exists
            if os.path.exists("icons/folder.png"):
                category_item.setIcon(0, QIcon("icons/folder.png"))
            
            self.category_items[category_name] = category_item
        
        # Add commands to categories
        for category_name, category_item in self.category_items.items():
            if category_name == "Favorites":
                continue  # Skip for now, will be populated from settings
                
            # Get commands for this category
            category_commands = self.data_loader.get_category_commands(category_name)
            
            for cmd_name, cmd_data in category_commands:
                command_item = QTreeWidgetItem(category_item)
                command_item.setText(0, cmd_name)
                command_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "command",
                    "name": cmd_name,
                    "data": cmd_data
                })
            
            # For item categories, add an entry to open the item browser
            if category_name in ["Weapons", "Armor", "Spells", "Potions", "Books", 
                                 "Clothing", "Miscellaneous", "NPCs", "Locations", 
                                 "Keys", "Horses", "Soul Gems", "Sigil Stones", 
                                 "Alchemy Equipment", "Alchemy Ingredients", "Arrows"]:
                browse_item = QTreeWidgetItem(category_item)
                browse_item.setText(0, f"Browse All {category_name}")
                browse_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "browser",
                    "category": category_name
                })
                
                # Make it visually distinct
                browse_item.setBackground(0, Qt.GlobalColor.darkBlue)
                browse_item.setForeground(0, Qt.GlobalColor.white)
                
                # Make the text bold
                font = browse_item.font(0)
                font.setBold(True)
                browse_item.setFont(0, font)
        
    def item_clicked(self, item):
        """Handle item click in the command tree"""
        # Check if this is a command, category, or browser
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        if item_data["type"] == "browser":
            # Show the item browser for this category
            category = item_data["category"]
            self.show_item_browser(category)
            return
            
        elif item_data["type"] == "command":
            # Show command details
            self.details_stack.setCurrentIndex(0)
            self.command_selected(item_data)
            return
        
        elif item_data["type"] == "item":
            # Show item details - use command details panel
            self.details_stack.setCurrentIndex(0)
            self.item_selected(item_data)
            return
            
    def command_selected(self, item_data):
        """Display command details with improved layout"""
        cmd_name = item_data["name"]
        cmd_data = item_data["data"]
        
        # Update command information
        self.command_title.setText(f"{cmd_name}")
        self.command_description.setText(cmd_data["description"])
        self.command_syntax.setText(f"<b>Syntax:</b> {cmd_data['syntax']}")
        
        # Update builder with command parameters
        self.builder_widget.set_command(cmd_name, cmd_data)
        
        # Enable buttons
        self.execute_button.setEnabled(True)
        self.favorite_button.setEnabled(True)
    
    def item_selected(self, item_data):
        """Display item details with improved layout"""
        item_key = item_data["name"]
        item_data = item_data["data"]
        
        # Update item information
        self.command_title.setText(f"{item_data['name']}")
        
        # Create a detailed description with item ID
        description = f"""
        <div style="margin-bottom: 10px;">
            <span style="font-weight: bold;">ID:</span> {item_data['id']}
        </div>
        """
        
        # Add any additional item properties if available
        if "weight" in item_data:
            description += f"""
            <div style="margin-bottom: 10px;">
                <span style="font-weight: bold;">Weight:</span> {item_data['weight']}
            </div>
            """
        
        if "value" in item_data:
            description += f"""
            <div style="margin-bottom: 10px;">
                <span style="font-weight: bold;">Value:</span> {item_data['value']}
            </div>
            """
            
        if "damage" in item_data:
            description += f"""
            <div style="margin-bottom: 10px;">
                <span style="font-weight: bold;">Damage:</span> {item_data['damage']}
            </div>
            """
        
        self.command_description.setText(description)
        self.command_syntax.setText(f"<b>Command:</b> {item_data['command']}")
        
        # Set the builder to manual mode with the command
        self.builder_widget.manual_checkbox.setChecked(True)
        self.builder_widget.manual_edit.setText(item_data["command"])
        
        # Enable buttons
        self.execute_button.setEnabled(True)
        self.favorite_button.setEnabled(True)
            
    def filter_commands(self):
        """Filter commands and items based on search text"""
        search_text = self.search_box.text().lower()
        
        # If empty, show all
        if not search_text:
            for category_name, category_item in self.category_items.items():
                category_item.setHidden(False)
                for i in range(category_item.childCount()):
                    category_item.child(i).setHidden(False)
            return
            
        # Hide/show based on search
        for category_name, category_item in self.category_items.items():
            visible_children = 0
            
            for i in range(category_item.childCount()):
                child = category_item.child(i)
                item_data = child.data(0, Qt.ItemDataRole.UserRole)
                
                if not item_data:
                    continue
                    
                # Handle different item types
                if item_data["type"] == "browser":
                    if search_text in category_name.lower():
                        child.setHidden(False)
                        visible_children += 1
                    else:
                        child.setHidden(True)
                        
                elif item_data["type"] == "command":
                    cmd_name = item_data["name"]
                    cmd_data = item_data["data"]
                    
                    # Search in command name and description
                    if (search_text in cmd_name.lower() or 
                        search_text in cmd_data["description"].lower()):
                        child.setHidden(False)
                        visible_children += 1
                    else:
                        child.setHidden(True)
                        
                elif item_data["type"] == "item":
                    item_name = item_data["data"]["name"]
                    item_id = item_data["data"]["id"]
                    
                    # Search in item name and ID
                    if (search_text in item_name.lower() or 
                        search_text in item_id.lower()):
                        child.setHidden(False)
                        visible_children += 1
                    else:
                        child.setHidden(True)
                    
            # Hide category if no visible children
            category_item.setHidden(visible_children == 0)
            
    def execute_command(self):
        """Execute the command from the command builder"""
        # Get command from builder
        command = self.builder_widget.get_command()
        if not command:
            return
            
        # Check if game is running
        if not is_game_running():
            self.status_label.setText("Game Status: Not Running - Can't Execute Command")
            QMessageBox.warning(self, "Game Not Running", 
                               "The game is not running. Command cannot be executed.")
            return
            
        # Send command to game
        success = send_command_to_game(command)
        
        # Update history
        if success:
            self.history_text.append(f"> {command}")
            QMessageBox.information(self, "Command Executed", 
                                  "Command has been executed in the game.")
        else:
            QMessageBox.warning(self, "Command Failed", 
                              "Failed to execute command in the game.")
    
    def execute_command_from_menu(self, item):
        """Execute command from context menu"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        # Get the command
        command = ""
        if item_data["type"] == "command":
            command = item_data["name"]
        elif item_data["type"] == "item":
            command = item_data["data"]["command"]
        else:
            return
            
        # Check if game is running
        if not is_game_running():
            self.status_label.setText("Game Status: Not Running - Can't Execute Command")
            QMessageBox.warning(self, "Game Not Running", 
                              "The game is not running. Command cannot be executed.")
            return
            
        # Send command to game
        success = send_command_to_game(command)
        
        # Update history
        if success:
            self.history_text.append(f"> {command}")
            QMessageBox.information(self, "Command Executed", 
                                  "Command has been executed in the game.")
        else:
            QMessageBox.warning(self, "Command Failed", 
                              "Failed to execute command in the game.")
            
    def add_to_favorites(self):
        """Add the current command to favorites"""
        # Get current command from builder
        cmd_name = self.builder_widget.current_command
        if not cmd_name:
            return
            
        cmd_data = self.builder_widget.current_data
        
        # Check if already in favorites
        favorites = self.category_items["Favorites"]
        for i in range(favorites.childCount()):
            child_data = favorites.child(i).data(0, Qt.ItemDataRole.UserRole)
            if child_data and child_data["type"] == "command" and child_data["name"] == cmd_name:
                # Show message that it's already in favorites
                QMessageBox.information(self, "Already in Favorites", 
                                       f"{cmd_name} is already in your favorites.")
                return  # Already in favorites
                
        # Add to favorites
        fav_item = QTreeWidgetItem(favorites)
        fav_item.setText(0, cmd_name)
        fav_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "command",
            "name": cmd_name,
            "data": cmd_data
        })
        
        # Save favorites to settings
        self.save_settings()
        
        QMessageBox.information(self, "Added to Favorites", 
                              f"{cmd_name} has been added to your favorites.")
        
    def add_to_favorites_from_menu(self, item):
        """Add the selected item to favorites via context menu"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        # Check if already in favorites
        favorites = self.category_items["Favorites"]
        for i in range(favorites.childCount()):
            child_data = favorites.child(i).data(0, Qt.ItemDataRole.UserRole)
            if (child_data and child_data["type"] == item_data["type"] and 
                child_data["name"] == item_data["name"]):
                return  # Already in favorites
                
        # Add to favorites
        fav_item = QTreeWidgetItem(favorites)
        fav_item.setText(0, item.text(0))
        fav_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Save favorites to settings
        self.save_settings()
        
        QMessageBox.information(self, "Added to Favorites", 
                              f"{item.text(0)} has been added to your favorites.")
    
    def remove_from_favorites(self, item):
        """Remove the selected item from favorites"""
        parent_item = item.parent()
        if not parent_item or "Favorites" not in parent_item.text(0):
            return
            
        # Remove from tree
        parent_item.removeChild(item)
        
        # Save updated favorites to settings
        self.save_settings()
        
        QMessageBox.information(self, "Removed from Favorites", 
                              "Item has been removed from your favorites.")
                              
    def clear_favorites(self):
        """Clear all favorites"""
        # Ask for confirmation
        reply = QMessageBox.question(self, "Clear Favorites", 
                                    "Are you sure you want to clear all favorites?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        # Get favorites category
        favorites = self.category_items["Favorites"]
        
        # Remove all children
        while favorites.childCount() > 0:
            favorites.removeChild(favorites.child(0))
        
        # Save updated favorites to settings
        self.save_settings()
        
        QMessageBox.information(self, "Favorites Cleared", 
                              "All favorites have been cleared.")
    
    def create_item_selector_tabs(self):
        """Create tabs for each item category in two rows"""
        # Categories to include in top and bottom rows
        top_row_categories = [
            "Useful Cheats", "Weapons", "Armor", "Spells", 
            "Potions", "Books", "Clothing", "Miscellaneous"
        ]
        
        bottom_row_categories = [
            "NPCs", "Locations", "Keys", "Horses", 
            "Soul Gems", "Sigil Stones", "Alchemy Equipment", "Alchemy Ingredients"
        ]
        
        # Create a container widget for the tab rows
        tab_container = QWidget()
        tab_container_layout = QVBoxLayout(tab_container)
        tab_container_layout.setSpacing(10)
        
        # Create top row tabs
        self.top_tabs = QTabWidget()
        self.top_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.top_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3F3F46;
                background-color: #2D2D30;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #3E3E42;
                color: #E6E6E6;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #0E639C;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #504F52;
            }
        """)
        
        # Create bottom row tabs
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.bottom_tabs.setStyleSheet(self.top_tabs.styleSheet())
        
        # Add tabs to the top row
        for category in top_row_categories:
            if category == "Useful Cheats":
                # Create a container widget for useful cheats
                container = QWidget()
                container_layout = QVBoxLayout(container)
                
                # Add the existing useful cheats selector
                selector = EnhancedItemSelector(self.data_loader, category)
                selector.commandSelected.connect(self.item_command_selected)
                container_layout.addWidget(selector)
                
                # Add our attribute/skill commands section
                attr_skill_widget = self.create_attribute_skill_commands()
                container_layout.addWidget(attr_skill_widget)
                
                # Get category info for icon
                cat_info = self.data_loader.get_category_info(category)
                self.top_tabs.addTab(container, f"{cat_info['icon']} {category}")
            else:
                # Regular category tabs
                selector = EnhancedItemSelector(self.data_loader, category)
                selector.commandSelected.connect(self.item_command_selected)
                
                # Get category info for icon
                cat_info = self.data_loader.get_category_info(category)
                self.top_tabs.addTab(selector, f"{cat_info['icon']} {category}")
        
        # Add tabs to the bottom row
        for category in bottom_row_categories:
            # Regular category tabs
            selector = EnhancedItemSelector(self.data_loader, category)
            selector.commandSelected.connect(self.item_command_selected)
            
            # Get category info for icon
            cat_info = self.data_loader.get_category_info(category)
            self.bottom_tabs.addTab(selector, f"{cat_info['icon']} {category}")
        
        # Add both tab widgets to the container
        tab_container_layout.addWidget(self.top_tabs)
        tab_container_layout.addWidget(self.bottom_tabs)
        
        # Add the container to the details stack
        self.details_stack.addWidget(tab_container)  # Index 1
    
    def show_item_browser(self, category):
        """Show the item browser for a specific category with improved layout"""
        # Update the UI to show we're browsing items
        self.status_label.setText(f"Browsing: {category}")
        
        # Find the tab index for this category
        tab_index = -1
        
        # First check top tabs
        for i in range(self.top_tabs.count()):
            tab_text = self.top_tabs.tabText(i)
            if category in tab_text:
                self.top_tabs.setCurrentIndex(i)
                tab_index = i
                break
        
        # If not found in top tabs, check bottom tabs
        if tab_index == -1:
            for i in range(self.bottom_tabs.count()):
                tab_text = self.bottom_tabs.tabText(i)
                if category in tab_text:
                    self.bottom_tabs.setCurrentIndex(i)
                    # Make sure bottom tabs are visible
                    break
        
        # Switch to the item tabs
        self.details_stack.setCurrentIndex(1)
        
        # Add a back button to return to command details if not already present
        if not hasattr(self, 'back_button'):
            self.back_button = QPushButton("← Back to Commands")
            self.back_button.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #504F52;
                }
                QPushButton:pressed {
                    background-color: #2D2D30;
                }
            """)
            self.back_button.clicked.connect(self.show_command_details)
            
            # Find the tab layouts to add the back button
            top_layout = self.top_tabs.findChild(QVBoxLayout)
            if top_layout:
                top_layout.insertWidget(0, self.back_button)
            else:
                # If we can't find the layout, create a new container
                back_container = QWidget()
                back_layout = QHBoxLayout(back_container)
                back_layout.addWidget(self.back_button)
                back_layout.addStretch()
                
                # Add it directly to the tab container
                tab_container = self.details_stack.widget(1)
                if isinstance(tab_container, QWidget):
                    tab_container_layout = tab_container.layout()
                    if tab_container_layout:
                        tab_container_layout.insertWidget(0, back_container)

    def apply_global_styles(self):
        """Apply consistent styling throughout the application"""
        # Main application styles
        self.setStyleSheet("""
            /* Main UI */
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #E6E6E6;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            
            /* Frames and Cards */
            QFrame {
                background-color: #252526;
                border: 1px solid #3F3F46;
                border-radius: 8px;
            }
            
            /* Text inputs */
            QLineEdit, QTextEdit, QSpinBox {
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #E6E6E6;
                padding: 5px 10px;
                selection-background-color: #264F78;
            }
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border: 1px solid #007ACC;
            }
            
            /* Combo boxes */
            QComboBox {
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #E6E6E6;
                padding: 5px 10px;
                min-height: 30px;
            }
            
            QComboBox:on {
                border-color: #007ACC;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #555555;
                border-left-style: solid;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            
            QComboBox::down-arrow {
                image: url(icons/down_arrow.png);
            }
            
            QComboBox QAbstractItemView {
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 0px;
                selection-background-color: #007ACC;
                outline: 0;
            }
            
            /* Push buttons */
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 30px;
            }
            
            QPushButton:hover {
                background-color: #504F52;
            }
            
            QPushButton:pressed {
                background-color: #2D2D30;
            }
            
            /* Primary buttons */
            QPushButton[role="primary"] {
                background-color: #0E639C;
                color: white;
            }
            
            QPushButton[role="primary"]:hover {
                background-color: #1177BB;
            }
            
            QPushButton[role="primary"]:pressed {
                background-color: #0A4C7C;
            }
            
            /* Tab widgets */
            QTabWidget::pane {
                border: 1px solid #3F3F46;
                border-radius: 5px;
                background-color: #2D2D30;
            }
            
            QTabBar::tab {
                background-color: #3E3E42;
                color: #E6E6E6;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background-color: #0E639C;
                color: white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #504F52;
            }
            
            /* Tree widget */
            QTreeWidget {
                background-color: #252526;
                alternate-background-color: #2A2A2B;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 5px;
            }
            
            QTreeWidget::item {
                padding: 6px;
                min-height: 30px;
            }
            
            QTreeWidget::item:selected {
                background-color: #0E639C;
                color: white;
            }
            
            QTreeWidget::item:hover {
                background-color: #3E3E42;
            }
            
            /* Scroll bars */
            QScrollBar:vertical {
                background-color: #252526;
                width: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3E3E42;
                min-height: 30px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #504F52;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #252526;
                height: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #3E3E42;
                min-width: 30px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #504F52;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Labels */
            QLabel[role="heading"] {
                font-size: 16pt;
                font-weight: bold;
                color: #E6E6E6;
                padding: 5px 0;
            }
            
            QLabel[role="subheading"] {
                font-size: 12pt;
                font-weight: bold;
                color: #00B050;
                padding: 5px 0;
            }
            
            /* Checkboxes */
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007ACC;
                border-color: #007ACC;
                image: url(icons/checkmark.png);
            }
            
            QCheckBox::indicator:hover {
                border-color: #007ACC;
            }
        """)
        
    def item_command_selected(self, command, cmd_data):
        """Handle item commands from the item selector"""
        # Switch to the command details panel
        self.details_stack.setCurrentIndex(0)
        
        # Update the UI with the selected item command
        self.command_title.setText(cmd_data["description"])
        self.command_description.setText(f"Command: {command}")
        self.command_syntax.setText(f"<b>Syntax:</b> {cmd_data['syntax']}")
        
        # Set the builder to manual mode with the command
        self.builder_widget.manual_checkbox.setChecked(True)
        self.builder_widget.manual_edit.setText(command)
        
        # Store the command data for add to favorites
        self.builder_widget.current_command = command
        self.builder_widget.current_data = cmd_data

    def open_discord(self):
        """Open Discord invite link"""
        import webbrowser
        webbrowser.open("https://discord.gg/92NKqFrM")
            
    def check_game_status(self):
        """Check if the game is running and update status label"""
        if is_game_running():
            self.status_label.setText("Game Status: Running ✅")
            self.status_label.setStyleSheet("color: #00B050; font-weight: bold;")  # Green text
        else:
            self.status_label.setText("Game Status: Not Detected ❌")
            self.status_label.setStyleSheet("color: #FF5050; font-weight: bold;")  # Red text
            
    def load_settings(self):
        """Load user settings and favorites"""
        # Load favorites
        favorites_data = self.settings.value("favorites", [])
        favorites_item = self.category_items["Favorites"]
        
        for fav_data in favorites_data:
            # Skip if invalid data
            if not isinstance(fav_data, dict) or "type" not in fav_data:
                continue
                
            # Add to favorites tree
            fav_item = QTreeWidgetItem(favorites_item)
            
            if fav_data["type"] == "command":
                # Command favorite
                cmd_name = fav_data["name"]
                fav_item.setText(0, cmd_name)
                fav_item.setData(0, Qt.ItemDataRole.UserRole, fav_data)
                
            elif fav_data["type"] == "item":
                # Item favorite
                item_name = fav_data["data"]["name"]
                fav_item.setText(0, item_name)
                fav_item.setData(0, Qt.ItemDataRole.UserRole, fav_data)
                
    def save_settings(self):
        """Save user settings and favorites"""
        # Save favorites
        favorites = []
        favorites_item = self.category_items["Favorites"]
        
        for i in range(favorites_item.childCount()):
            item_data = favorites_item.child(i).data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                favorites.append(item_data)
                
        self.settings.setValue("favorites", favorites)
    
    def closeEvent(self, event):
        """Handle close event"""
        # No need to stop a timer that doesn't exist
        # Just save settings before closing
        self.save_settings()
        event.accept()