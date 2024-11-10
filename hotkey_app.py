import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QKeySequence, QShortcut, QPainter, QPen
import keyboard
import win32gui
import win32con
import win32process
import win32api

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.arrows = []
        self.start_point = None
        self.current_end = None
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.current_end = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.start_point is not None:
            self.current_end = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_point:
            self.arrows.append((self.start_point, event.pos()))
            self.start_point = None
            self.current_end = None
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.red, 4))
        
        # Draw completed arrows
        for start, end in self.arrows:
            self.draw_arrow(painter, start, end)
            
        # Draw current arrow
        if self.start_point and self.current_end:
            self.draw_arrow(painter, self.start_point, self.current_end)
            
    def draw_arrow(self, painter, start, end):
        painter.drawLine(start, end)
        
        # Calculate arrow head
        arrow_size = 10
        angle = 30  # degrees
        
        # Calculate direction vector
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            return
            
        # Normalize direction vector
        dx = dx / length
        dy = dy / length
        
        # Calculate arrow head points
        import math
        angle_rad = math.radians(angle)
        x1 = end.x() - arrow_size * (dx * math.cos(angle_rad) + dy * math.sin(angle_rad))
        y1 = end.y() - arrow_size * (dy * math.cos(angle_rad) - dx * math.sin(angle_rad))
        x2 = end.x() - arrow_size * (dx * math.cos(angle_rad) - dy * math.sin(angle_rad))
        y2 = end.y() - arrow_size * (dy * math.cos(angle_rad) + dx * math.sin(angle_rad))
        
        # Draw arrow head
        painter.drawLine(end, QPoint(int(x1), int(y1)))
        painter.drawLine(end, QPoint(int(x2), int(y2)))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arrow Drawing App")
        self.setGeometry(100, 100, 800, 600)
        
        # Set window flags for transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Set stylesheet for border
        self.setStyleSheet("""
            QMainWindow {
                border: 1px solid #808080;
                background-color: rgba(255, 255, 255, 30);
            }
        """)
        
        # Create and set the drawing widget as central widget
        self.drawing_widget = DrawingWidget()
        self.setCentralWidget(self.drawing_widget)
        
        # Register global hotkey
        keyboard.add_hotkey('ctrl+alt+f', self.bring_to_front)
        
    def bring_to_front(self):
        try:
            # Show window if minimized
            self.showNormal()
            # Bring window to front
            self.activateWindow()
            self.raise_()
            
            # Force focus using Win32 API
            hwnd = self.winId().__int__()
            # Get current foreground window
            current_hwnd = win32gui.GetForegroundWindow()
            # Get current thread
            current_thread = win32process.GetWindowThreadProcessId(current_hwnd)[0]
            # Get app's thread
            app_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
            
            # Attach threads if necessary
            if current_thread != app_thread:
                win32api.AttachThreadInput(current_thread, app_thread, True)
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
                finally:
                    win32api.AttachThreadInput(current_thread, app_thread, False)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.BringWindowToTop(hwnd)
        except Exception as e:
            print(f"Error bringing window to front: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
