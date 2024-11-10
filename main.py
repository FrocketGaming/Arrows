import sys
import time
import math
import keyboard
import win32gui
import win32con
import win32api
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from threading import Thread, Event

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
        self.current_window = None
        self.exit_event = Event()
        
    def toggle_drawing_mode(self):
        self.drawing_mode = not self.drawing_mode
        if not self.drawing_mode:
            self.drawing_start = None
            if self.current_window:
                win32gui.ShowWindow(self.current_window, win32con.SW_HIDE)
        else:
            if self.current_window:
                win32gui.ShowWindow(self.current_window, win32con.SW_SHOW)
                win32gui.SetWindowPos(
                    self.current_window,
                    win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )
    
    def handle_mouse_click(self):
        if self.drawing_mode:
            x, y = win32gui.GetCursorPos()
            self.drawing_start = (x, y)
            win32gui.InvalidateRect(self.current_window, None, True)
    
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
            win32gui.InvalidateRect(self.current_window, None, True)
    
    def draw_arrow(self, hdc, arrow: Arrow, alpha: float = 1.0):
        dx = arrow.end_x - arrow.start_x
        dy = arrow.end_y - arrow.start_y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:
            return
            
        dx, dy = dx/length, dy/length
        head_length = min(20, length/3)
        head_width = head_length * 0.8
        
        arrow_end = np.array([arrow.end_x, arrow.end_y])
        direction = np.array([dx, dy])
        normal = np.array([-dy, dx])
        
        point1 = arrow_end - direction * head_length + normal * head_width/2
        point2 = arrow_end - direction * head_length - normal * head_width/2
        
        alpha_val = int(255 * alpha)
        pen = win32gui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(255, 0, 0))
        old_pen = win32gui.SelectObject(hdc, pen)
        
        win32gui.MoveToEx(hdc, arrow.start_x, arrow.start_y)
        win32gui.LineTo(hdc, arrow.end_x, arrow.end_y)
        
        win32gui.MoveToEx(hdc, int(point1[0]), int(point1[1]))
        win32gui.LineTo(hdc, arrow.end_x, arrow.end_y)
        win32gui.LineTo(hdc, int(point2[0]), int(point2[1]))
        
        win32gui.SelectObject(hdc, old_pen)
        win32gui.DeleteObject(pen)
    
    def create_window(self):
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.lpszClassName = 'ScreenArrowClass'
        wc.hbrBackground = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        
        try:
            win32gui.RegisterClass(wc)
        except win32gui.error:
            pass

        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        
        style = win32con.WS_POPUP | win32con.WS_VISIBLE
        ex_style = (win32con.WS_EX_TOPMOST | win32con.WS_EX_LAYERED | 
                   win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOOLWINDOW)
        
        self.current_window = win32gui.CreateWindowEx(
            ex_style,
            wc.lpszClassName,
            'Screen Arrow',
            style,
            0, 0, screen_width, screen_height,
            None, None, None, None
        )
        
        win32gui.SetLayeredWindowAttributes(
            self.current_window, 
            win32api.RGB(255, 255, 255),
            0,  # Start fully transparent
            win32con.LWA_ALPHA
        )
        
        return self.current_window

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_DESTROY:
            self.exit_event.set()
            win32gui.PostQuitMessage(0)
            return 0
            
        elif msg == win32con.WM_PAINT:
            ps = win32gui.PAINTSTRUCT()
            hdc = win32gui.BeginPaint(hwnd, ps)
            
            rect = win32gui.GetClientRect(hwnd)
            win32gui.FillRect(hdc, rect, win32gui.GetStockObject(win32con.HOLLOW_BRUSH))
            
            current_time = time.time()
            self.arrows = [arrow for arrow in self.arrows if arrow.age < self.fade_duration]
            
            for arrow in self.arrows:
                alpha = max(0, 1 - (arrow.age / self.fade_duration))
                self.draw_arrow(hdc, arrow, alpha)
            
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
                
            win32gui.EndPaint(hwnd, ps)
            return 0
            
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run(self):
        hwnd = self.create_window()
        if not hwnd:
            print("Failed to create window")
            return

        msg = win32gui.MSG()
        while not self.exit_event.is_set():
            if win32gui.PeekMessage(msg, 0, 0, 0, win32con.PM_REMOVE):
                win32gui.TranslateMessage(msg)
                win32gui.DispatchMessage(msg)
                
                if msg.message == win32con.WM_QUIT:
                    break
            
            # Redraw only when needed
            if self.drawing_mode or self.arrows:
                win32gui.InvalidateRect(hwnd, None, True)
            
            time.sleep(0.016)  # ~60 FPS

def main():
    drawer = ScreenDrawer()
    
    # Start the main window thread
    window_thread = Thread(target=drawer.run, daemon=True)
    window_thread.start()
    
    # Register hotkey
    keyboard.add_hotkey('ctrl+alt+f', drawer.toggle_drawing_mode)
    
    # Mouse monitoring function
    def monitor_mouse():
        state_left = win32api.GetKeyState(0x01)
        while not drawer.exit_event.is_set():
            new_state_left = win32api.GetKeyState(0x01)
            if new_state_left != state_left:
                state_left = new_state_left
                if new_state_left < 0:
                    drawer.handle_mouse_click()
                else:
                    drawer.handle_mouse_release()
            time.sleep(0.001)

    # Start mouse monitoring
    mouse_thread = Thread(target=monitor_mouse, daemon=True)
    mouse_thread.start()
    
    try:
        keyboard.wait('esc')
    except KeyboardInterrupt:
        pass
    finally:
        drawer.exit_event.set()
        if drawer.current_window:
            win32gui.PostMessage(drawer.current_window, win32con.WM_CLOSE, 0, 0)
        window_thread.join(timeout=1.0)

if __name__ == "__main__":
    main()
