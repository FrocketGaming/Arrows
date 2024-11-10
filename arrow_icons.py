from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from PyQt6.QtCore import Qt

def create_arrow_icon(color=Qt.GlobalColor.black, dissolving=False):
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    pen = QPen(color)
    pen.setWidth(2)
    painter.setPen(pen)
    
    # Draw arrow shaft
    painter.drawLine(5, 16, 27, 16)
    
    # Draw arrow head
    painter.drawLine(27, 16, 20, 10)
    painter.drawLine(27, 16, 20, 22)
    
    if dissolving:
        # Add fade effect indication
        painter.setOpacity(0.5)
        painter.drawLine(5, 20, 20, 20)
        painter.setOpacity(0.2)
        painter.drawLine(5, 24, 15, 24)
    
    painter.end()
    return QIcon(pixmap)
