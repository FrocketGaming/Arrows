import sys
import math
from keyboard_manager import KeyboardManager
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QToolBar, QPushButton, QColorDialog,
                            QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QPoint, QTimer, QTime
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon
from arrow_icons import create_arrow_icon

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
        
        # Initialize arrows list with tuples: (start, end, color, creation_time, is_dissolving)
        self.arrows = []
        self.current_arrow_type = 'normal'  # or 'dissolving'
        
        # Set up timer for dissolving arrows
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.update_dissolving_arrows)
        self.fade_timer.start(100)  # Update every 100ms
        
        # Create floating toolbar window
        self.toolbar = FloatingToolbar(self)
        
        # Initialize current color
        self.current_color = QColor(255, 0, 0)  # Default red
        
        # Start without focus
        self.clearFocus()
        
    def choose_color(self):
        # Store current drawing mode state
        was_drawing = self.drawing_mode
        if was_drawing:
            # Temporarily disable drawing mode
            self.toggle_drawing_mode()
        
        # Show color dialog
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            
        # Restore drawing mode if it was active
        if was_drawing:
            self.toggle_drawing_mode()
            
    def clear_arrows(self):
        self.arrows.clear()
        self.transparent_widget.update()
        
    def set_arrow_type(self, arrow_type):
        self.current_arrow_type = arrow_type
        
    def update_dissolving_arrows(self):
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        
        # Check if we have any dissolving arrows
        has_dissolving = any(arrow[4] for arrow in self.arrows)
        
        # Filter out arrows that have exceeded their 2-second lifetime
        self.arrows = [arrow for arrow in self.arrows 
                      if not arrow[4] or  # Keep normal arrows
                      (arrow[4] and current_time - arrow[3] < 2000)]  # Keep dissolving arrows within time
        
        # Force update if we have any dissolving arrows
        if has_dissolving:
            self.transparent_widget.update()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.arrows.clear()
            self.transparent_widget.update()
            
    def toggle_drawing_mode(self):
        try:
            print(f"Toggle drawing mode called. Current state: {self.drawing_mode}")
            self.drawing_mode = not self.drawing_mode
            print(f"New drawing mode state: {self.drawing_mode}")
            
            if self.drawing_mode:
                # Enable drawing mode
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                self.setWindowFlags(self.drawing_flags)
                self.show()
                
                # Use timer to sequence the window operations
                def show_and_raise():
                    self.toolbar.show()
                    self.raise_()
                    self.activateWindow()
                    QApplication.setActiveWindow(self)
                    self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                    self.toolbar.raise_()
                    self.toolbar.activateWindow()
                
                # Schedule the window operations
                QTimer.singleShot(100, show_and_raise)
                
            else:
                # Disable drawing mode
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                self.setWindowFlags(self.inactive_flags)
                self.toolbar.hide()
                self.show()
                self.clearFocus()
                
            self.transparent_widget.update()
            
        except Exception as e:
            print(f"Error toggling drawing mode: {e}")
            # Try to recover to a safe state
            self.drawing_mode = False
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setWindowFlags(self.inactive_flags)
            self.toolbar.hide()
            self.show()
            
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background: rgb(50, 50, 50);
                border-radius: 5px;
                padding: 2px;
            }
            QPushButton {
                background: rgb(70, 70, 70);
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                margin: 2px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgb(90, 90, 90);
                border-color: #666;
            }
            QPushButton:checked {
                background: rgb(100, 100, 255);
                border-color: #88f;
            }
        """)
        
        # Add buttons
        self.normal_arrow_button = QPushButton()
        self.normal_arrow_button.setIcon(create_arrow_icon())
        self.normal_arrow_button.setToolTip("Normal Arrow")
        self.normal_arrow_button.setCheckable(True)
        self.normal_arrow_button.setChecked(True)
        self.normal_arrow_button.clicked.connect(lambda: self.handle_arrow_selection('normal'))
        self.toolbar.addWidget(self.normal_arrow_button)
        
        self.dissolving_arrow_button = QPushButton()
        self.dissolving_arrow_button.setIcon(create_arrow_icon(dissolving=True))
        self.dissolving_arrow_button.setToolTip("Dissolving Arrow")
        self.dissolving_arrow_button.setCheckable(True)
        self.dissolving_arrow_button.clicked.connect(lambda: self.handle_arrow_selection('dissolving'))
        self.toolbar.addWidget(self.dissolving_arrow_button)
        
        color_button = QPushButton("Color")
        color_button.clicked.connect(parent.choose_color)
        self.toolbar.addWidget(color_button)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(parent.clear_arrows)
        self.toolbar.addWidget(clear_button)
        
        # Add toolbar to layout and set initial position
        layout.addWidget(self.toolbar)
        self.move(10, 10)
        self.adjustSize()
        
    def handle_arrow_selection(self, arrow_type):
        """Handle arrow type selection and button states"""
        if arrow_type == 'normal':
            self.normal_arrow_button.setChecked(True)
            self.dissolving_arrow_button.setChecked(False)
        else:
            self.normal_arrow_button.setChecked(False)
            self.dissolving_arrow_button.setChecked(True)
        self.parent().set_arrow_type(arrow_type)

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
                # Store arrow with its color, creation time, and type
                current_time = QTime.currentTime().msecsSinceStartOfDay()
                is_dissolving = self.parent().current_arrow_type == 'dissolving'
                self.parent().arrows.append((
                    self.start_point, 
                    self.end_point, 
                    self.parent().current_color,
                    current_time,
                    is_dissolving
                ))
                print(f"Arrow added: from ({self.start_point.x()}, {self.start_point.y()}) to ({self.end_point.x()}, {self.end_point.y()})")
                print(f"Total arrows: {len(self.parent().arrows)}")
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Only show background in drawing mode
        if self.parent().drawing_mode:
            painter.fillRect(self.rect(), QColor(0, 255, 0, 30))  # Semi-transparent green tint when drawing mode
            
        # Set pen for drawing
        pen = QPen(self.parent().current_color)
        pen.setWidth(4)  # Make lines thicker
        painter.setPen(pen)
        
        # Draw all saved arrows with their colors and opacity
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        for start, end, color, creation_time, is_dissolving in self.parent().arrows:
            if is_dissolving:
                age = current_time - creation_time
                if age >= 2000:  # 2 seconds
                    continue
                opacity = 1.0 - (age / 2000.0)
                painter.setOpacity(opacity)
            else:
                painter.setOpacity(1.0)
                
            pen.setColor(color)
            painter.setPen(pen)
            self.draw_arrow(painter, start, end)
            
        # Draw current arrow if drawing (with current color)
        if self.drawing and self.start_point and self.end_point:
            pen.setColor(self.parent().current_color)
            painter.setPen(pen)
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
    
    # Set up keyboard manager
    keyboard_manager = KeyboardManager()
    keyboard_manager.drawing_mode_toggled.connect(window.toggle_drawing_mode)
    
    # Start Qt event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
