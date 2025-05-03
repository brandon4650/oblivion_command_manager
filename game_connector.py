import pyautogui
import psutil
import time
import os
import sys

# Global variable to track last game status
_last_game_status = None

def is_frozen():
    """Check if the application is running as a PyInstaller frozen executable"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def find_oblivion_process():
    """
    Find the Oblivion Remastered process.
    Returns the process object if found, None otherwise.
    Enhanced for reliability in compiled applications.
    """
    # Specific process names to search for
    target_processes = [
        'OblivionRemastered',
        'The Elder Scrolls IV: Oblivion Remastered'

    ]
    
    # Name of our own application to exclude
    our_app_name = "oblivion console manager"
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            # Get process name (case-sensitive for more accuracy)
            proc_name = proc.info['name'] if proc.info['name'] else ""
            
            # Skip our own application
            if our_app_name.lower() in proc_name.lower():
                continue
            
            # Exact match for specified process names
            for target in target_processes:
                if target in proc_name:
                    if is_frozen():
                        print(f"[Frozen] Found Oblivion process: {proc_name}")
                    return proc
            
            # Check window title if available (for processes with game window)
            try:
                window_titles = [w.title for w in pyautogui.getAllWindows() if w.title]
                for title in window_titles:
                    if "Oblivion Remastered" in title and proc.pid == pyautogui.getWindowsWithTitle(title)[0]._hWnd:
                        if is_frozen():
                            print(f"[Frozen] Found Oblivion window: {title}")
                        return proc
            except:
                pass
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return None

def is_game_running(verbose=False):
    """
    Check if Oblivion Remastered is running.
    Returns True if the game is running, False otherwise.
    Only prints status messages when verbose=True or when status changes.
    Enhanced for better reliability in compiled environments.
    """
    global _last_game_status
    
    # Look for Oblivion process directly
    proc = find_oblivion_process()
    game_running = proc is not None
    
    # Only print if status changed or verbose mode
    if game_running != _last_game_status or verbose:
        if game_running:
            try:
                proc_info = f"{proc.info['name']} (PID: {proc.info['pid']})"
                print(f"Oblivion found: {proc_info}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print("Oblivion found but process details unavailable")
        else:
            print("Oblivion not detected.")
    
    # Update last status
    _last_game_status = game_running
    
    return game_running
def switch_to_game():
    """
    Switch focus to the Oblivion game window.
    """
    print("Switching focus to Oblivion...")
    
    # Save current mouse position
    current_mouse_pos = pyautogui.position()
    
    # Method 1: Alt+Tab to switch to the last active window (should be the game)
    print("Pressing Alt+Tab to focus on game window...")
    pyautogui.keyDown('alt')
    pyautogui.press('tab')
    pyautogui.keyUp('alt')
    
    # Give the game time to come into focus
    time.sleep(1.0)
    
    # Restore mouse position
    pyautogui.moveTo(current_mouse_pos)
    
    # Additional delay to ensure the game has focus
    time.sleep(0.5)

def send_command_to_game(command):
    """
    Send a command to Oblivion Remastered's console using PyAutoGUI.
    Returns True if the command was sent successfully, False otherwise.
    """
    if not command or not command.strip():
        print("Empty command - nothing to send")
        return False
    
    # Check if game is running (but always continue if it's detected as not running)
    if not is_game_running():
        print("WARNING: Oblivion not detected, but proceeding with command anyway...")
    
    try:
        print(f"Preparing to send command: {command}")
        
        # Store current mouse position to restore later
        original_mouse_pos = pyautogui.position()
        
        # Switch focus to the game window
        switch_to_game()
        
        # Open console with tilde key
        print("Opening console...")
        pyautogui.press('`')  # This is the tilde key
        time.sleep(0.7)  # Longer wait for console to open
        
        # Type the command
        print(f"Typing command: {command}")
        pyautogui.write(command)
        time.sleep(0.4)
        
        # Press Enter to execute
        print("Executing command...")
        pyautogui.press('enter')
        time.sleep(0.4)
        
        # Close console with another tilde
        print("Closing console...")
        pyautogui.press('`')
        time.sleep(0.3)
        
        # Restore original mouse position
        pyautogui.moveTo(original_mouse_pos)
        
        print(f"Command executed successfully: {command}")
        return True
        
    except Exception as e:
        print(f"Error sending command to game: {e}")
        return False

# For testing
if __name__ == "__main__":
    # Print runtime environment info
    print(f"Running as frozen executable: {is_frozen()}")
    
    # Show all running processes for debugging
    print("==== ALL RUNNING PROCESSES ====")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            print(f"{proc.info['pid']}: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    print("==============================")
    
    # Test if the game is running
    if is_game_running(verbose=True):
        print("Oblivion is running. Testing with a simple command...")
        # Test with a simple, harmless command
        success = send_command_to_game("player.getpos")
        print(f"Command sent: {'Success' if success else 'Failed'}")
    else:
        print("Oblivion is not detected, but will try anyway...")
        # Test anyway
        success = send_command_to_game("player.getpos")
        print(f"Command sent: {'Success' if success else 'Failed'}")