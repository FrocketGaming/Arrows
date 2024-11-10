import sys
import math
from keyboard_manager import KeyboardManager
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QToolBar,
    QPushButton,
    QColorDialog,
    QVBoxLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QTime, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPolygon, QPixmap
from arrow_icons import create_arrow_icon


class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.base_flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
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
        self.current_arrow_type = "normal"  # or 'dissolving'

        # Set up timer for dissolving arrows
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.update_dissolving_arrows)
        self.fade_timer.start(100)  # Update every 100ms

        # Create floating toolbar window
        self.toolbar = FloatingToolbar(self)
        # Don't show toolbar initially since we start in non-drawing mode

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
        self.arrows = [
            arrow
            for arrow in self.arrows
            if not arrow[4]  # Keep normal arrows
            or (arrow[4] and current_time - arrow[3] < 2000)
        ]  # Keep dissolving arrows within time

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
                self.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
                )
                self.setWindowFlags(self.drawing_flags)
                self.show()
                # Show toolbar and ensure it's collapsed
                self.toolbar.is_expanded = True  # Force it to collapse
                self.toolbar.toggle_toolbar()    # Collapse it
                self.toolbar.show()
                self.raise_()
                self.activateWindow()
                self.toolbar.raise_()

            else:
                # Disable drawing mode
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                self.setWindowFlags(self.inactive_flags)
                # Ensure toolbar is collapsed before hiding
                if self.toolbar.is_expanded:
                    self.toolbar.toggle_toolbar()
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
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create toggle button first
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(40, 20)
        self.toggle_button.clicked.connect(self.toggle_toolbar)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background: rgb(50, 50, 50);
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: rgb(60, 60, 60);
            }
        """)
        self.update_toggle_button_icon(False)
        layout.addWidget(self.toggle_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Create toolbar container above
        self.toolbar_container = QWidget()
        self.toolbar_container.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        layout.insertWidget(0, self.toolbar_container)  # Insert at top
        
        # Create toolbar layout
        toolbar_layout = QVBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(0)
        self.toolbar_container.setStyleSheet("""
            QWidget {
                background: rgb(70, 70, 70);
                border-radius: 5px;
            }
        """)
        # Set initial height to match toggle button
        self.toolbar_container.setFixedHeight(20)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
            QToolBar { 
                background: transparent;
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
        self.normal_arrow_button.clicked.connect(
            lambda: self.handle_arrow_selection("normal")
        )
        self.toolbar.addWidget(self.normal_arrow_button)

        self.dissolving_arrow_button = QPushButton()
        self.dissolving_arrow_button.setIcon(create_arrow_icon(dissolving=True))
        self.dissolving_arrow_button.setToolTip("Dissolving Arrow")
        self.dissolving_arrow_button.setCheckable(True)
        self.dissolving_arrow_button.clicked.connect(
            lambda: self.handle_arrow_selection("dissolving")
        )
        self.toolbar.addWidget(self.dissolving_arrow_button)

        color_button = QPushButton("Color")
        color_button.clicked.connect(parent.choose_color)
        self.toolbar.addWidget(color_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(parent.clear_arrows)
        self.toolbar.addWidget(clear_button)

        # Add toolbar to layout
        self.toolbar.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        toolbar_layout.addWidget(self.toolbar)
        
        # Set fixed width to accommodate all buttons
        self.toolbar.setFixedWidth(200)
        
        # Set up animation
        self.animation = QPropertyAnimation(self.toolbar_container, b"minimumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Initialize state
        self.is_expanded = False
        self.toolbar_container.setMinimumHeight(0)
        self.toolbar_container.setMaximumHeight(0)
        
        # Center the toolbar horizontally
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() // 2 - self.sizeHint().width() // 2, 0)
        
    def update_toggle_button_icon(self, is_expanded):
        # Create a custom arrow icon
        icon_size = self.toggle_button.size()
        pixmap = QPixmap(icon_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw arrow centered in button - arrow points up when collapsed, down when expanded
        center_x = icon_size.width() // 2
        points = QPolygon([
            QPoint(center_x - 10, 14 if is_expanded else 6),  # Reversed logic
            QPoint(center_x, 6 if is_expanded else 14),       # Reversed logic
            QPoint(center_x + 10, 14 if is_expanded else 6)   # Reversed logic
        ])
        
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.setBrush(QColor(200, 200, 200))
        painter.drawPolygon(points)
        painter.end()
        
        self.toggle_button.setIcon(QIcon(pixmap))
        
    def toggle_toolbar(self):
        self.is_expanded = not self.is_expanded
        
        # Calculate heights
        expanded_height = self.toolbar.sizeHint().height()
        collapsed_height = 20  # Same as toggle button height
        current_height = self.toolbar_container.height()
        target_height = expanded_height if self.is_expanded else collapsed_height
        
        # Configure animation
        self.animation.setStartValue(current_height)
        self.animation.setEndValue(target_height)
        
        # Update the container constraints
        self.toolbar_container.setMaximumHeight(expanded_height)
        
        def animation_finished():
            if not self.is_expanded:
                # When collapsed, set height to match toggle button
                self.toolbar_container.setMaximumHeight(collapsed_height)
                self.toolbar_container.setMinimumHeight(collapsed_height)
            else:
                # When expanded, allow the container to fit the content
                self.toolbar_container.setMinimumHeight(target_height)
        
        # Disconnect any previous connections to avoid multiple calls
        try:
            self.animation.finished.disconnect()
        except:
            pass
            
        self.animation.finished.connect(animation_finished)
        self.animation.start()
        
        self.update_toggle_button_icon(self.is_expanded)

    def handle_arrow_selection(self, arrow_type):
        """Handle arrow type selection and button states"""
        if arrow_type == "normal":
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
        self.default_cursor = Qt.CursorShape.ArrowCursor
        self.drawing_cursor = Qt.CursorShape.CrossCursor
        self.setCursor(self.default_cursor)

    def update_cursor(self):
        if self.parent().drawing_mode:
            self.setCursor(self.drawing_cursor)
        else:
            self.setCursor(self.default_cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent().drawing_mode:
            self.update_cursor()
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
                is_dissolving = self.parent().current_arrow_type == "dissolving"
                self.parent().arrows.append(
                    (
                        self.start_point,
                        self.end_point,
                        self.parent().current_color,
                        current_time,
                        is_dissolving,
                    )
                )
                print(
                    f"Arrow added: from ({self.start_point.x()}, {self.start_point.y()}) to ({self.end_point.x()}, {self.end_point.y()})"
                )
                print(f"Total arrows: {len(self.parent().arrows)}")
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add very slight background when in drawing mode
        if self.parent().drawing_mode:
            painter.fillRect(
                self.rect(), QColor(255, 255, 255, 3)
            )  # 1% opacity white background

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

        angle1 = line_angle + math.pi / 180 * (180 - angle)
        angle2 = line_angle + math.pi / 180 * (180 + angle)

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


if __name__ == "__main__":
    main()
