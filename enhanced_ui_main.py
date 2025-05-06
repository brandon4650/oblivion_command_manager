
from PyQt6.QtWidgets import (QMainWindow, QTreeWidget, QTreeWidgetItem, 
                           QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QSplitter, QTextEdit, QStackedWidget,
                           QSizePolicy, QFrame, QMenu, QMessageBox, QTabWidget,
                           QComboBox, QGroupBox, QGraphicsOpacityEffect, QSpinBox, QApplication,
                           QListWidget, QListWidgetItem, QScrollArea)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize, QRect, QEvent
from PyQt6.QtGui import (QIcon, QFont, QPixmap, QPainter, QColor, QPen, QPolygon, QBrush, 
                        QTextCursor, QTextCharFormat)
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
    
    # Replace your current setup_ui_contents method with this updated version
    def setup_ui_contents(self):
        """Set up the UI contents with an enhanced tabbed layout"""
        # Header area with logo and game status
        header_layout = QHBoxLayout()
        
        # Game status indicator (left)
        status_container = QFrame()
        status_container.setFrameShape(QFrame.Shape.StyledPanel)
        status_container.setStyleSheet("background-color: #252526; border-radius: 5px; padding: 5px;")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Game Status: Not Detected")
        status_layout.addWidget(self.status_label)
        header_layout.addWidget(status_container)
        
        # Oblivion logo (center)
        logo_label = QLabel()
        logo_path = os.path.join("icons", "oblivion.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(180, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            logo_label.setText("Oblivion Console Manager")
            logo_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #C0C0C0;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(logo_label, 1)
        
        # Action buttons (right)
        actions_layout = QHBoxLayout()
        
        # Max skills button
        max_skills_btn = QPushButton("⚡ Max Skills")
        max_skills_btn.setStyleSheet("""
            QPushButton {
                background-color: #8E44AD;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9B59B6;
            }
        """)
        max_skills_btn.clicked.connect(self.max_all_skills_attributes)
        actions_layout.addWidget(max_skills_btn)
            
        # Discord button
        self.discord_button = QPushButton("💬 Discord")
        self.discord_button.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)
        self.discord_button.clicked.connect(self.open_discord)
        actions_layout.addWidget(self.discord_button)
        
        # Donate button (simplified)
        donate_btn = QPushButton("❤️ Donate")
        donate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.donate_button = DonateButton()
        actions_layout.addWidget(self.donate_button)
        
        header_layout.addLayout(actions_layout)
        self.main_layout.addLayout(header_layout)
        
        # Search bar (full width)
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search commands and items...")
        self.search_box.setMinimumHeight(30)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #333337;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #E6E6E6;
                padding: 5px 10px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 1px solid #007ACC;
            }
        """)
        self.search_box.textChanged.connect(self.filter_commands)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(search_layout)
        self.main_layout.addSpacing(10)
        
        # Main tab widget - new addition
        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)  # Modern tab appearance
        
        # Create the three main tabs
        commands_tab = self.create_commands_tab()
        items_tab = self.create_items_tab()
        history_tab = self.create_history_tab()
        
        # Add the tabs to the main tab widget
        self.main_tabs.addTab(commands_tab, "Commands")
        self.main_tabs.addTab(items_tab, "Items")
        self.main_tabs.addTab(history_tab, "History")
        
        self.main_layout.addWidget(self.main_tabs)
        
        # Status bar
        status_bar = QHBoxLayout()
        
        version_label = QLabel("v1.0.2")
        version_label.setStyleSheet("color: #808080; font-size: 9pt;")
        status_bar.addWidget(version_label)
        
        status_bar.addStretch()
        
        help_label = QLabel("Right-click items for more options | Select a command to see details")
        help_label.setStyleSheet("color: #808080; font-size: 9pt;")
        status_bar.addWidget(help_label)
        
        self.main_layout.addLayout(status_bar)
        
        # Initial setup
        self.check_game_status()

    def create_commands_tab(self):
        """Create the commands tab with category buttons and command list/details"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # Category buttons
        category_frame = QFrame()
        category_frame.setStyleSheet("background-color: #252526; border-radius: 5px;")
        category_layout = QHBoxLayout(category_frame)
        
        # Get categories (excluding item categories) for command buttons
        command_categories = ["Favorites", "Useful Cheats", "Toggle", "Targeted", "Quest"]
        
        self.category_buttons = {}
        
        for category in command_categories:
            cat_info = self.data_loader.get_category_info(category)
            button = QPushButton(f"{cat_info['icon']} {category}")
            button.setProperty("category", category)
            button.setCheckable(True)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42;
                    color: #E6E6E6;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:checked {
                    background-color: #0E639C;
                    color: white;
                }
            """)
            button.clicked.connect(lambda checked, cat=category: self.on_command_category_clicked(cat))
            category_layout.addWidget(button)
            self.category_buttons[category] = button
        
        category_layout.addStretch()
        tab_layout.addWidget(category_frame)
        
        # Split view for commands
        commands_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Command list
        list_panel = QFrame()
        list_panel.setFrameShape(QFrame.Shape.StyledPanel)
        list_panel.setStyleSheet("background-color: #252526; border-radius: 5px;")
        list_layout = QVBoxLayout(list_panel)
        
        self.command_list_title = QLabel("Commands")
        self.command_list_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #00B050;")
        list_layout.addWidget(self.command_list_title)
        
        self.command_list = QListWidget()
        self.command_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                border: 1px solid #3F3F46;
                alternate-background-color: #2A2A2B;
                selection-background-color: #0E639C;
            }
            QListWidget::item {
                padding: 4px;
                min-height: 25px;
            }
        """)
        self.command_list.setAlternatingRowColors(True)
        self.command_list.itemClicked.connect(self.on_command_selected)
        list_layout.addWidget(self.command_list)
        
        commands_splitter.addWidget(list_panel)
        
        # Right panel: Command details - Create it here instead of using self.command_details
        command_details_panel = QFrame()
        command_details_panel.setFrameShape(QFrame.Shape.StyledPanel)
        command_details_panel.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        details_layout = QVBoxLayout(command_details_panel)
        
        # Create the command details widgets
        details_title = QLabel("Command Details")
        details_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #00B050;")
        details_layout.addWidget(details_title)
        
        # Command info frame
        cmd_info_frame = QFrame()
        cmd_info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        cmd_info_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        cmd_info_layout = QVBoxLayout(cmd_info_frame)
        
        self.command_title = QLabel("Select a command")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.command_title.setFont(font)
        self.command_title.setStyleSheet("color: #E6E6E6;")
        cmd_info_layout.addWidget(self.command_title)
        
        self.command_description = QLabel("")
        self.command_description.setWordWrap(True)
        self.command_description.setStyleSheet("padding: 5px 0;")
        cmd_info_layout.addWidget(self.command_description)
        
        self.command_syntax = QLabel("")
        self.command_syntax.setStyleSheet("color: #CEA139; padding: 5px 0;")
        cmd_info_layout.addWidget(self.command_syntax)
        
        details_layout.addWidget(cmd_info_frame)
        
        # Command builder
        self.builder_widget = CommandBuilderWidget()
        details_layout.addWidget(self.builder_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("Execute Command")
        self.execute_button.setMinimumHeight(35)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
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
        self.favorite_button.setMinimumHeight(35)
        self.favorite_button.setStyleSheet("""
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
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
        
        details_layout.addLayout(button_layout)
        
        commands_splitter.addWidget(command_details_panel)
        
        # Store reference to the command details panel
        self.command_details = command_details_panel
        
        # Set default sizes (1:2 ratio)
        commands_splitter.setSizes([300, 600])
        
        tab_layout.addWidget(commands_splitter)
        
        # Select Favorites by default
        if "Favorites" in self.category_buttons:
            self.category_buttons["Favorites"].setChecked(True)
            self.on_command_category_clicked("Favorites")
        
        return tab_widget
        
    def create_items_tab(self):
        """Create the items tab with two rows of category buttons"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container for category buttons
        category_frame = QFrame()
        category_frame.setFrameShape(QFrame.Shape.StyledPanel)
        category_frame.setStyleSheet("background-color: #252526; border-radius: 5px; padding: 10px;")
        category_layout = QVBoxLayout(category_frame)
        
        # First row of categories (8 buttons)
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(5)
        item_categories_row1 = [
            "Weapons", "Armor", "Spells", "Potions", 
            "Books", "Clothing", "Miscellaneous", "NPCs"
        ]
        
        self.item_category_buttons = {}
        
        for category in item_categories_row1:
            cat_info = self.data_loader.get_category_info(category)
            button = QPushButton(f"{cat_info['icon']} {category}")
            button.setProperty("category", category)
            button.setCheckable(True)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42;
                    color: #E6E6E6;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:checked {
                    background-color: #0E639C;
                    color: white;
                }
            """)
            button.clicked.connect(lambda checked, cat=category: self.on_item_category_clicked(cat))
            row1_layout.addWidget(button)
            self.item_category_buttons[category] = button
        
        category_layout.addLayout(row1_layout)
        
        # Second row of categories (remaining buttons)
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(5)
        item_categories_row2 = [
            "Locations", "Keys", "Horses", "Soul Gems", 
            "Sigil Stones", "Alchemy Equipment", "Alchemy Ingredients", "Arrows"
        ]
        
        for category in item_categories_row2:
            cat_info = self.data_loader.get_category_info(category)
            button = QPushButton(f"{cat_info['icon']} {category}")
            button.setProperty("category", category)
            button.setCheckable(True)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42;
                    color: #E6E6E6;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:checked {
                    background-color: #0E639C;
                    color: white;
                }
            """)
            button.clicked.connect(lambda checked, cat=category: self.on_item_category_clicked(cat))
            row2_layout.addWidget(button)
            self.item_category_buttons[category] = button
        
        category_layout.addLayout(row2_layout)
        tab_layout.addWidget(category_frame)
        
        # Item content area
        # We can reuse the existing item_tabs but display only the active tab
        self.item_content = QStackedWidget()
        tab_layout.addWidget(self.item_content)
        
        # Create selector widgets for each category
        for category in item_categories_row1 + item_categories_row2:
            selector = EnhancedItemSelector(self.data_loader, category)
            selector.commandSelected.connect(self.item_command_selected)
            self.item_content.addWidget(selector)
        
        # Select the first category by default
        if item_categories_row1:
            self.item_category_buttons[item_categories_row1[0]].setChecked(True)
            self.on_item_category_clicked(item_categories_row1[0])
        
        return tab_widget
    
    def create_history_tab(self):
        """Create the history tab with command execution history"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # Reuse your existing history frame, with enhancements
        history_frame = QFrame()
        history_frame.setFrameShape(QFrame.Shape.StyledPanel)
        history_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        history_layout = QVBoxLayout(history_frame)
        
        # Header with title and clear button
        header_layout = QHBoxLayout()
        
        history_title = QLabel("Command History")
        history_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #00B050;")
        header_layout.addWidget(history_title)
        
        header_layout.addStretch()
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #504F52;
            }
        """)
        clear_history_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(clear_history_btn)
        
        history_layout.addLayout(header_layout)
        
        # History text area
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3F3F46;
                border-radius: 3px;
                color: #E6E6E6;
                padding: 5px;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        history_layout.addWidget(self.history_text)
        
        # Button for re-executing selected command
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("Copy Selected")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #504F52;
            }
        """)
        copy_btn.clicked.connect(self.copy_selected_history)
        button_layout.addWidget(copy_btn)
        
        execute_selected_btn = QPushButton("Execute Selected")
        execute_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
        """)
        execute_selected_btn.clicked.connect(self.execute_selected_history)
        button_layout.addWidget(execute_selected_btn)
        
        history_layout.addLayout(button_layout)
        
        tab_layout.addWidget(history_frame)
        
        return tab_widget
    
    def on_command_category_clicked(self, category):
        """Handle command category selection"""
        # Update button states
        for cat, button in self.category_buttons.items():
            button.setChecked(cat == category)
        
        # Update title
        cat_info = self.data_loader.get_category_info(category)
        self.command_list_title.setText(f"{cat_info['icon']} {category}")
        
        # Clear the list
        self.command_list.clear()
        
        # Fill with commands from the selected category
        if category == "Favorites":
            # Get favorites from settings
            favorites_data = self.settings.value("favorites", [])
            for fav_data in favorites_data:
                item = QListWidgetItem(fav_data["name"])
                item.setData(Qt.ItemDataRole.UserRole, fav_data)
                self.command_list.addItem(item)
        else:
            # Get commands for the category
            commands = self.data_loader.get_category_commands(category)
            for cmd_name, cmd_data in sorted(commands, key=lambda x: x[0]):
                item = QListWidgetItem(cmd_name)
                item.setData(Qt.ItemDataRole.UserRole, {
                    "type": "command",
                    "name": cmd_name,
                    "data": cmd_data
                })
                self.command_list.addItem(item)

    def on_command_selected(self, item):
        """Handle command selection from the list"""
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return
        
        if item_data["type"] == "command":
            self.command_selected(item_data)
        elif item_data["type"] == "item":
            self.item_selected(item_data)
    
    def on_item_category_clicked(self, category):
        """Handle item category button click"""
        # Update button states
        for cat, button in self.item_category_buttons.items():
            button.setChecked(cat == category)
        
        # Find the index of the category in our stacked widget
        all_categories = [
            "Weapons", "Armor", "Spells", "Potions", 
            "Books", "Clothing", "Miscellaneous", "NPCs",
            "Locations", "Keys", "Horses", "Soul Gems", 
            "Sigil Stones", "Alchemy Equipment", "Alchemy Ingredients", "Arrows"
        ]
        
        if category in all_categories:
            index = all_categories.index(category)
            self.item_content.setCurrentIndex(index)
    
    def copy_selected_history(self):
        """Copy selected text from history"""
        cursor = self.history_text.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            QApplication.clipboard().setText(selected_text)
    
    def execute_selected_history(self):
        """Execute the selected command from history"""
        cursor = self.history_text.textCursor()
        if not cursor.hasSelection():
            # If no selection, get the current line
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        
        selected_text = cursor.selectedText()
        
        # Extract command (remove '>' prefix if present)
        if selected_text.startswith('> '):
            selected_text = selected_text[2:]
        
        if not selected_text:
            return
        
        # Execute the command
        if not is_game_running():
            QMessageBox.warning(self, "Game Not Running", 
                               "The game is not running. Command cannot be executed.")
            return
        
        success = send_command_to_game(selected_text)
        
        if success:
            self.history_text.append(f"> {selected_text} (re-run)")
            
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
        """Display command details"""
        cmd_name = item_data["name"]
        cmd_data = item_data["data"]
        
        self.command_title.setText(f"{cmd_name}")
        self.command_description.setText(cmd_data["description"])
        self.command_syntax.setText(f"<b>Syntax:</b> {cmd_data['syntax']}")
        
        # Update builder with command parameters
        self.builder_widget.set_command(cmd_name, cmd_data)
    
    def item_selected(self, item_data):
        """Display item details"""
        item_key = item_data["name"]
        item_data = item_data["data"]
        
        self.command_title.setText(f"{item_data['name']}")
        self.command_description.setText(f"ID: {item_data['id']}")
        self.command_syntax.setText(f"<b>Command:</b> {item_data['command']}")
        
        # Set the builder to manual mode with the command
        self.builder_widget.manual_checkbox.setChecked(True)
        self.builder_widget.manual_edit.setText(item_data["command"])
            
    def filter_commands(self):
        """Filter both commands and items based on search text"""
        search_text = self.search_box.text().lower()
        
        # Get current tab
        current_tab = self.main_tabs.currentIndex()
        
        if current_tab == 0:  # Commands tab
            # Filter command list
            for i in range(self.command_list.count()):
                item = self.command_list.item(i)
                item_data = item.data(Qt.ItemDataRole.UserRole)
                
                if not item_data:
                    continue
                    
                if search_text:
                    if item_data["type"] == "command":
                        # Search in command name and description
                        name = item_data["name"].lower()
                        desc = item_data["data"]["description"].lower()
                        
                        item.setHidden(search_text not in name and search_text not in desc)
                    elif item_data["type"] == "item":
                        # Search in item name and ID
                        name = item_data["data"]["name"].lower()
                        item_id = item_data["data"]["id"].lower()
                        
                        item.setHidden(search_text not in name and search_text not in item_id)
                else:
                    item.setHidden(False)
        elif current_tab == 1:  # Items tab
            # Get current item category widget
            current_selector = self.item_content.currentWidget()
            if isinstance(current_selector, EnhancedItemSelector):
                # Use the selector's filter method
                current_selector.search_box.setText(search_text)
        elif current_tab == 2:  # History tab
            # For history tab, just highlight matching text if any
            if search_text:
                # Using QTextDocument's find functionality
                cursor = self.history_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.history_text.setTextCursor(cursor)
                
                # Set text format for highlighting (yellow background)
                format = QTextCharFormat()
                format.setBackground(QColor(Qt.GlobalColor.yellow))
                
                # Clear previous highlighting
                cursor = self.history_text.textCursor()
                cursor.select(QTextCursor.SelectionType.Document)
                cursor.setCharFormat(QTextCharFormat())
                
                # Search and highlight
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.history_text.setTextCursor(cursor)
                
                # Find all occurrences
                found = self.history_text.find(search_text)
                while found:
                    # Apply highlight format
                    cursor = self.history_text.textCursor()
                    cursor.mergeCharFormat(format)
                    
                    # Find next
                    found = self.history_text.find(search_text)
            else:
                # Clear highlighting
                cursor = self.history_text.textCursor()
                cursor.select(QTextCursor.SelectionType.Document)
                cursor.setCharFormat(QTextCharFormat())
                cursor.clearSelection()
                self.history_text.setTextCursor(cursor)
                
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
        """Create tabs for each item category"""
        # Categories to include
        item_categories = [
            "Useful Cheats", "Weapons", "Armor", "Spells", "Potions", "Books", 
            "Clothing", "Miscellaneous", "NPCs", "Locations", 
            "Keys", "Horses", "Soul Gems", "Sigil Stones", 
            "Alchemy Equipment", "Alchemy Ingredients", "Arrows"
        ]
        
        # Create a tab for each category
        for category in item_categories:
            if category == "Useful Cheats":
                # Create a container widget for useful cheats
                container = QWidget()
                container_layout = QVBoxLayout()
                
                # Add the existing useful cheats selector
                selector = EnhancedItemSelector(self.data_loader, category)
                selector.commandSelected.connect(self.item_command_selected)
                container_layout.addWidget(selector)
                
                # Add our attribute/skill commands section
                attr_skill_widget = self.create_attribute_skill_commands()
                container_layout.addWidget(attr_skill_widget)
                
                container.setLayout(container_layout)
                
                # Get category info for icon
                cat_info = self.data_loader.get_category_info(category)
                self.item_tabs.addTab(container, f"{cat_info['icon']} {category}")
            else:
                # Regular category tabs
                selector = EnhancedItemSelector(self.data_loader, category)
                selector.commandSelected.connect(self.item_command_selected)
                
                # Get category info for icon
                cat_info = self.data_loader.get_category_info(category)
                self.item_tabs.addTab(selector, f"{cat_info['icon']} {category}")
    
    def show_item_browser(self, category):
        """Show the item browser for a specific category"""
        # Switch to the items tab
        self.main_tabs.setCurrentIndex(1)
        
        # Find and select the category
        if category in self.item_category_buttons:
            self.item_category_buttons[category].setChecked(True)
            self.on_item_category_clicked(category)
        
        # Also update the search box to clear any existing filters
        self.search_box.clear()
        
        # Find the appropriate index for this category
        all_categories = [
            "Weapons", "Armor", "Spells", "Potions", 
            "Books", "Clothing", "Miscellaneous", "NPCs",
            "Locations", "Keys", "Horses", "Soul Gems", 
            "Sigil Stones", "Alchemy Equipment", "Alchemy Ingredients", "Arrows"
        ]
        
        if category in all_categories:
            index = all_categories.index(category)
            self.item_content.setCurrentIndex(index)
        
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