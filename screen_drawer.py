import sys
import math
import keyboard
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QToolBar, QPushButton, QColorDialog)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        # Set up global hotkey
        keyboard.on_press_key('d', self.handle_hotkey, suppress=True)
        self.base_flags = (
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint |
            Qt.WindowType.MaximizeUsingFullscreenGeometryHint
        )
        self.setWindowFlags(self.base_flags | Qt.WindowType.WindowTransparentForInput)
        self.drawing_mode = False
        
        # Create transparent widget
        self.transparent_widget = TransparentWidget(self)
        self.setCentralWidget(self.transparent_widget)
        
        # Set window to full screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Initialize arrows list
        self.arrows = []
        
        # Create and setup toolbar
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: 2px;
            }
            QPushButton {
                background: rgba(240, 240, 240, 200);
                border: 1px solid gray;
                border-radius: 3px;
                padding: 4px;
                margin: 2px;
            }
            QPushButton:hover {
                background: rgba(220, 220, 220, 200);
            }
        """)
        
        # Add toolbar buttons
        self.color_button = QPushButton("Color")
        self.color_button.clicked.connect(self.choose_color)
        self.toolbar.addWidget(self.color_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_arrows)
        self.toolbar.addWidget(self.clear_button)
        
        # Set initial position
        self.toolbar.move(10, 10)
        self.toolbar.hide()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Initialize current color
        self.current_color = QColor(255, 0, 0)  # Default red
        
        # Start without focus
        self.clearFocus()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.arrows.clear()
            self.transparent_widget.update()
            
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            
    def clear_arrows(self):
        self.arrows.clear()
        self.transparent_widget.update()
        
    def handle_hotkey(self, e):
        if keyboard.is_pressed('ctrl+alt+shift'):
            if not self.drawing_mode:
                self.drawing_mode = True
                self.setWindowFlags(self.base_flags)
                self.show()
                self.activateWindow()
                self.raise_()
                self.setWindowState(Qt.WindowState.WindowActive)
                self.toolbar.show()
            else:
                self.drawing_mode = False
                self.setWindowFlags(self.base_flags | Qt.WindowType.WindowTransparentForInput)
                self.show()
                self.clearFocus()
                self.toolbar.hide()
            self.transparent_widget.update()
        
class TransparentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.start_point = None
        self.end_point = None
        self.drawing = False
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent().drawing_mode:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            print(f"Drawing mode: {self.parent().drawing_mode}")
            print(f"Mouse press at: {self.start_point.x()}, {self.start_point.y()}")
            self.update()  # Force immediate update
            
    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if self.start_point and self.end_point:
                self.parent().arrows.append((self.start_point, self.end_point))
                print(f"Arrow added: from ({self.start_point.x()}, {self.start_point.y()}) to ({self.end_point.x()}, {self.end_point.y()})")
                print(f"Total arrows: {len(self.parent().arrows)}")
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Only show background in drawing mode
        if self.parent().drawing_mode:
            painter.fillRect(self.rect(), QColor(0, 255, 0, 30))  # Green tint when drawing mode
        
        # Set pen for drawing
        pen = QPen(self.parent().current_color)
        pen.setWidth(4)  # Make lines thicker
        painter.setPen(pen)
        
        # Draw all saved arrows
        for start, end in self.parent().arrows:
            self.draw_arrow(painter, start, end)
            
        # Draw current arrow if drawing
        if self.drawing and self.start_point and self.end_point:
            self.draw_arrow(painter, self.start_point, self.end_point)
            
    def draw_arrow(self, painter, start, end):
        painter.drawLine(start, end)
        
        # Calculate arrow head
        angle = 30  # degrees
        arrow_length = 20
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        line_angle = math.atan2(dy, dx)
        
        angle1 = line_angle + math.pi/180 * (180 - angle)
        angle2 = line_angle + math.pi/180 * (180 + angle)
        
        x1 = end.x() + arrow_length * math.cos(angle1)
        y1 = end.y() + arrow_length * math.sin(angle1)
        x2 = end.x() + arrow_length * math.cos(angle2)
        y2 = end.y() + arrow_length * math.sin(angle2)
        
        painter.drawLine(end, QPoint(int(x1), int(y1)))
        painter.drawLine(end, QPoint(int(x2), int(y2)))

def main():
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
