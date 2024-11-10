import sys
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QToolBar, QPushButton, QColorDialog,
                            QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        self.base_flags = (Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowStaysOnTopHint | 
                          Qt.WindowType.Tool)
        self.drawing_flags = self.base_flags
        self.inactive_flags = self.base_flags | Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(self.inactive_flags)
        
        # Set initial attributes
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.drawing_mode = False
        
        # Create transparent widget
        self.transparent_widget = TransparentWidget(self)
        self.setCentralWidget(self.transparent_widget)
        
        # Set window to full screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Initialize arrows list
        self.arrows = []
        
        # Create floating toolbar window
        self.toolbar = FloatingToolbar(self)
        
        # Initialize current color
        self.current_color = QColor(255, 0, 0)  # Default red
        
        # Start without focus
        self.clearFocus()
        
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            
    def clear_arrows(self):
        self.arrows.clear()
        self.transparent_widget.update()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.arrows.clear()
            self.transparent_widget.update()
            
    def toggle_drawing_mode(self):
        self.drawing_mode = not self.drawing_mode
        
        if self.drawing_mode:
            # Enable drawing mode
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setWindowFlags(self.drawing_flags)
            self.show()
            self.toolbar.show()
            
            # Force window to top and activate
            self.raise_()
            self.activateWindow()
            QApplication.setActiveWindow(self)
            self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            
            # Ensure toolbar is visible and on top
            self.toolbar.raise_()
            self.toolbar.activateWindow()
        else:
            # Disable drawing mode
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setWindowFlags(self.inactive_flags)
            self.toolbar.hide()
            self.show()
            self.clearFocus()
            
        self.transparent_widget.update()
            
    def focusOutEvent(self, event):
        """Keep focus when in drawing mode"""
        super().focusOutEvent(event)
        if self.drawing_mode:
            self.activateWindow()
            self.raise_()
            self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        
class FloatingToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Create toolbar with minimal size
        self.toolbar = QToolBar()
        self.toolbar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background: rgba(50, 50, 50, 230);
                border-radius: 5px;
                padding: 2px;
            }
            QPushButton {
                background: rgba(70, 70, 70, 230);
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                margin: 2px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(90, 90, 90, 230);
                border-color: #666;
            }
        """)
        
        # Add buttons
        color_button = QPushButton("Color")
        color_button.clicked.connect(parent.choose_color)
        self.toolbar.addWidget(color_button)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(parent.clear_arrows)
        self.toolbar.addWidget(clear_button)
        
        # Add toolbar to layout
        layout.addWidget(self.toolbar)
        self.setLayout(layout)
        
        # Set size and position
        self.adjustSize()
        self.move(10, 10)
        
        # Ensure minimal size
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

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
    
    # Create shortcut using Qt
    from PyQt6.QtGui import QShortcut, QKeySequence
    shortcut = QShortcut(QKeySequence('Ctrl+Alt+Shift+D'), window)
    shortcut.activated.connect(window.toggle_drawing_mode)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
