import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer
import os
import PyQt6

def check_requirements():
    """Check if required packages are installed"""
    try:
        from PyQt6.QtMultimedia import QMediaPlayer
        from PyQt6.QtMultimediaWidgets import QVideoWidget
        return True
    except ImportError:
        print("Missing required packages for video functionality.")
        print("Install required packages with: pip install PyQt6-Qt6 PyQt6-sip PyQt6-tools PyQt6-QtMultimedia")
        return False

def ensure_data_directory():
    """Make sure the data directory exists and properly prepare it"""
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created data directory. Please place your JSON files there.")
    
    # Check if JSON files exist in the root directory but not in data/
    root_json_files = [f for f in os.listdir('.') if f.endswith('.json') and 
                       not f.startswith('package') and not os.path.exists(os.path.join("data", f))]
    
    if root_json_files:
        print(f"Found {len(root_json_files)} JSON files in root directory. Moving to data/...")
        for json_file in root_json_files:
            try:
                os.rename(json_file, os.path.join("data", json_file))
                print(f"  Moved {json_file} to data/")
            except Exception as e:
                print(f"  Error moving {json_file}: {e}")
        
        print("All JSON files moved to data/ directory.")

def show_splash_screen():
    """Show a splash screen while the application is loading"""
    # Create splash screen
    splash_pix = QPixmap("icons/oblivion.png") if os.path.exists("icons/oblivion.png") else QPixmap(400, 200)
    
    if not os.path.exists("icons/oblivion.png"):
        # Create a simple splash screen if image doesn't exist
        temp_widget = QWidget()
        temp_widget.setStyleSheet("background-color: #1E1E1E;")
        temp_layout = QVBoxLayout(temp_widget)
        temp_label = QLabel("Oblivion Console Manager")
        temp_label.setStyleSheet("color: #E6E6E6; font-size: 20pt; font-weight: bold;")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_layout.addWidget(temp_label)
        temp_widget.resize(400, 200)
        splash_pix = QPixmap(temp_widget.size())
        temp_widget.render(splash_pix)
    
    splash = QSplashScreen(splash_pix)
    
    # Add a progress bar
    layout = QVBoxLayout()
    layout.setContentsMargins(20, splash_pix.height() - 50, 20, 20)
    
    # Add loading text
    loading_label = QLabel("Loading Oblivion Console Manager...")
    loading_label.setStyleSheet("color: white; font-weight: bold;")
    loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(loading_label)
    
    # Create and add progress bar
    progress = QProgressBar()
    progress.setRange(0, 100)
    progress.setValue(0)
    progress.setTextVisible(False)
    progress.setStyleSheet("""
        QProgressBar {
            border: 1px solid white;
            border-radius: 5px;
            background-color: #333333;
            height: 10px;
        }
        QProgressBar::chunk {
            background-color: #00B050;
            border-radius: 5px;
        }
    """)
    layout.addWidget(progress)
    
    # Apply layout to a widget
    container = QWidget(splash)
    container.setLayout(layout)
    container.setFixedWidth(splash_pix.width())
    
    # Show splash screen
    splash.show()
    
    # Simulate loading progress
    for i in range(1, 101):
        progress.setValue(i)
        QApplication.processEvents()
        # Add small delays to show progress
        import time
        time.sleep(0.02)
    
    return splash

def main():
    # Check requirements
    requirements_met = check_requirements()
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Create application
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icons/oblivion.png' if os.path.exists('icons/oblivion.png') else 'icons/folder.png'))
    
    # Show splash screen
    splash = show_splash_screen()
    
    # Load stylesheet
    try:
        with open('styles.qss', 'r') as style_file:
            app.setStyleSheet(style_file.read())
    except FileNotFoundError:
        print("Warning: styles.qss not found. The application will use default styling.")
        
    # Create and show main window
    try:
        # Use the enhanced UI version
        from enhanced_ui_main import MainWindow
        window = MainWindow()
        window.show()
        
        # Close splash screen after main window appears
        splash.finish(window)
        
        # If missing requirements, show warning
        if not requirements_met:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                window,
                "Missing Requirements",
                "Some features may not work correctly.\n\n"
                "Please install required packages with:\n"
                "pip install PyQt6-Qt6 PyQt6-sip PyQt6-tools PyQt6-QtMultimedia"
            )
        
        # Start event loop
        sys.exit(app.exec())
    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Startup Error")
        error_box.setText("Error starting application")
        error_box.setDetailedText(f"Error details: {str(e)}")
        error_box.exec()
        sys.exit(1)

if __name__ == "__main__":
    main()