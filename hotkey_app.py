import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
import keyboard
import win32gui
import win32con

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hotkey App")
        self.setGeometry(100, 100, 400, 200)
        
        # Register global hotkey
        keyboard.add_hotkey('ctrl+alt+f', self.bring_to_front)
        
    def bring_to_front(self):
        # Show window if minimized
        self.showNormal()
        # Bring window to front
        self.activateWindow()
        self.raise_()
        # Force focus using Win32 API
        hwnd = self.winId().__int__()
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
