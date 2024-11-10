from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class KeyboardManager(QObject):
    drawing_mode_toggled = pyqtSignal()  # Signal emitted when hotkey is activated

    def __init__(self):
        super().__init__()
        self._hotkey_config = '<ctrl>+<alt>+<shift>+d'
        self.setup_hotkey_listener()

    def setup_hotkey_listener(self):
        """Set up the key listener with the parsed hotkey."""
        self.hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(self._hotkey_config),
            self.activate
        )
        self.listener = keyboard.Listener(
            on_press=self.for_canonical(self.hotkey.press),
            on_release=self.for_canonical(self.hotkey.release)
        )
        self.listener.start()

    def activate(self):
        """Handle the activation of the hotkey."""
        self.drawing_mode_toggled.emit()

    def for_canonical(self, f):
        """Wrapper for canonical key handling."""
        return lambda k: f(self.listener.canonical(k))
