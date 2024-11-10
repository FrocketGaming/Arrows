import sys
import time
import math
import keyboard
import win32gui
import win32con
import win32api
import win32con
import numpy as np
from win32con import MB_ICONINFORMATION
from threading import Thread
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Arrow:
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    creation_time: float
    
    @property
    def age(self) -> float:
        return time.time() - self.creation_time

class ScreenDrawer:
    def __init__(self):
        self.drawing_mode = False
        self.drawing_start: Optional[Tuple[int, int]] = None
        self.arrows: list[Arrow] = []
        self.fade_duration = 4.0  # seconds
        
    def toggle_drawing_mode(self):
        self.drawing_mode = not self.drawing_mode
        if not self.drawing_mode:
            self.drawing_start = None
        # Show popup notification
        status = "ENABLED" if self.drawing_mode else "DISABLED"
        win32api.MessageBox(0, f"Drawing mode {status}", "Screen Arrow", MB_ICONINFORMATION)
    
    def handle_mouse_click(self):
        if self.drawing_mode:
            x, y = win32gui.GetCursorPos()
            self.drawing_start = (x, y)
    
    def handle_mouse_release(self):
        if self.drawing_mode and self.drawing_start:
            end_x, end_y = win32gui.GetCursorPos()
            arrow = Arrow(
                self.drawing_start[0],
                self.drawing_start[1],
                end_x,
                end_y,
                time.time()
            )
            self.arrows.append(arrow)
            self.drawing_start = None
    
    def draw_arrow(self, hdc, arrow: Arrow, alpha: float = 1.0):
        # Calculate arrow properties
        dx = arrow.end_x - arrow.start_x
        dy = arrow.end_y - arrow.start_y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:
            return
            
        # Normalize direction
        dx, dy = dx/length, dy/length
        
        # Arrow head properties
        head_length = min(20, length/3)
        head_width = head_length * 0.8
        
        # Calculate arrow head points
        arrow_end = np.array([arrow.end_x, arrow.end_y])
        direction = np.array([dx, dy])
        normal = np.array([-dy, dx])
        
        point1 = arrow_end - direction * head_length + normal * head_width/2
        point2 = arrow_end - direction * head_length - normal * head_width/2
        
        # Create pen with alpha
        alpha_val = int(255 * alpha)
        pen = win32gui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(255, 0, 0))
        old_pen = win32gui.SelectObject(hdc, pen)
        
        # Draw arrow shaft
        win32gui.MoveToEx(hdc, arrow.start_x, arrow.start_y)
        win32gui.LineTo(hdc, arrow.end_x, arrow.end_y)
        
        # Draw arrow head
        win32gui.MoveToEx(hdc, int(point1[0]), int(point1[1]))
        win32gui.LineTo(hdc, arrow.end_x, arrow.end_y)
        win32gui.LineTo(hdc, int(point2[0]), int(point2[1]))
        
        win32gui.SelectObject(hdc, old_pen)
        win32gui.DeleteObject(pen)
    
    def draw_loop(self):
        while True:
            # Create a fullscreen transparent window
            hwnd = win32gui.CreateWindowEx(
                win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST | win32con.WS_EX_LAYERED,
                'STATIC',
                None,
                win32con.WS_POPUP | win32con.WS_VISIBLE,
                0, 0,
                win32api.GetSystemMetrics(0),
                win32api.GetSystemMetrics(1),
                None, None, None, None
            )
            
            # Make the window transparent
            win32gui.SetLayeredWindowAttributes(
                hwnd, 0, 0, win32con.LWA_ALPHA
            )
            
            hdc = win32gui.GetDC(hwnd)
            
            # Remove expired arrows
            current_time = time.time()
            self.arrows = [arrow for arrow in self.arrows 
                          if arrow.age < self.fade_duration]
            
            # Draw all active arrows
            for arrow in self.arrows:
                alpha = max(0, 1 - (arrow.age / self.fade_duration))
                self.draw_arrow(hdc, arrow, alpha)
            
            # Draw current arrow if in drawing mode
            if self.drawing_mode and self.drawing_start:
                current_x, current_y = win32gui.GetCursorPos()
                temp_arrow = Arrow(
                    self.drawing_start[0],
                    self.drawing_start[1],
                    current_x,
                    current_y,
                    time.time()
                )
                self.draw_arrow(hdc, temp_arrow)
            
            win32gui.ReleaseDC(hwnd, hdc)
            win32gui.DestroyWindow(hwnd)
            
            time.sleep(1/60)  # ~60 FPS

def main():
    drawer = ScreenDrawer()
    
    # Start drawing loop in separate thread
    draw_thread = Thread(target=drawer.draw_loop, daemon=True)
    draw_thread.start()
    
    # Register global hotkey
    keyboard.add_hotkey('ctrl+alt+f', drawer.toggle_drawing_mode)
    
    # Register mouse handlers
    def check_mouse():
        state_left = win32api.GetKeyState(0x01)  # Left mouse button
        while True:
            new_state_left = win32api.GetKeyState(0x01)
            if new_state_left != state_left:  # Button state changed
                state_left = new_state_left
                if new_state_left < 0:  # Button pressed
                    drawer.handle_mouse_click()
                else:  # Button released
                    drawer.handle_mouse_release()
            time.sleep(0.001)  # Small sleep to prevent high CPU usage

    # Start mouse monitoring in separate thread
    mouse_thread = Thread(target=check_mouse, daemon=True)
    mouse_thread.start()
    
    # Keep the main thread running
    keyboard.wait('esc')

if __name__ == "__main__":
    main()
