"""
Global hotkey listener.

Listens for Cmd+Space+Space (double-tap Space while holding Cmd).
"""

import logging
import threading
import time
from typing import Callable

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

logger = logging.getLogger(__name__)


class HotkeyListener:
    """
    Global hotkey listener.
    
    Default: Cmd+Space+Space (double-tap Space while holding Cmd)
    
    Features:
    - Cross-platform (macOS, Linux, Windows)
    - Configurable hotkey
    - Non-blocking
    """

    def __init__(
        self,
        on_trigger: Callable[[], None],
        hotkey: str = "<cmd>+<space>+<space>",
        double_tap_window: float = 0.5
    ):
        """
        Initialize hotkey listener.
        
        Args:
            on_trigger: Callback when hotkey is triggered
            hotkey: Hotkey combination (default: Cmd+Space+Space)
            double_tap_window: Time window for double-tap (seconds)
        """
        if not keyboard:
            raise ImportError("pynput not installed. Run: pip install pynput")
        
        self.on_trigger = on_trigger
        self.double_tap_window = double_tap_window
        
        # State
        self.cmd_pressed = False
        self.last_space_time = 0
        self.listener = None
        self.running = False
        
        logger.info(f"Hotkey listener initialized: {hotkey}")

    def start(self):
        """Start listening for hotkey."""
        if self.running:
            logger.warning("Hotkey listener already running")
            return
        
        self.running = True
        
        # Start keyboard listener
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        
        logger.info("Hotkey listener started")

    def stop(self):
        """Stop listening for hotkey."""
        if not self.running:
            return
        
        self.running = False
        
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        logger.info("Hotkey listener stopped")

    def _on_press(self, key):
        """Handle key press."""
        try:
            # Check for Cmd/Super key
            if key == keyboard.Key.cmd or key == keyboard.Key.cmd_r:
                self.cmd_pressed = True
            
            # Check for Space while Cmd is pressed
            elif key == keyboard.Key.space and self.cmd_pressed:
                current_time = time.time()
                
                # Check if this is a double-tap
                if current_time - self.last_space_time < self.double_tap_window:
                    logger.info("Hotkey triggered: Cmd+Space+Space")
                    self._trigger()
                    self.last_space_time = 0  # Reset
                else:
                    self.last_space_time = current_time
        
        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

    def _on_release(self, key):
        """Handle key release."""
        try:
            # Release Cmd key
            if key == keyboard.Key.cmd or key == keyboard.Key.cmd_r:
                self.cmd_pressed = False
                self.last_space_time = 0  # Reset on Cmd release
        
        except Exception as e:
            logger.error(f"Error in key release handler: {e}")

    def _trigger(self):
        """Trigger the callback."""
        try:
            # Run callback in separate thread to avoid blocking
            thread = threading.Thread(target=self.on_trigger, daemon=True)
            thread.start()
        except Exception as e:
            logger.error(f"Error triggering callback: {e}")


# Alternative: Simple hotkey using keyboard module
class SimpleHotkeyListener:
    """
    Simple hotkey listener using keyboard module.
    
    Fallback if pynput doesn't work.
    """

    def __init__(self, on_trigger: Callable[[], None]):
        """Initialize simple hotkey listener."""
        self.on_trigger = on_trigger
        self.running = False

    def start(self):
        """Start listening."""
        try:
            import keyboard as kb
            
            self.running = True
            
            # Register hotkey
            kb.add_hotkey('cmd+space+space', self.on_trigger)
            
            logger.info("Simple hotkey listener started")
        
        except ImportError:
            logger.error("keyboard module not available")
        except Exception as e:
            logger.error(f"Failed to start simple hotkey listener: {e}")

    def stop(self):
        """Stop listening."""
        try:
            import keyboard as kb
            kb.unhook_all()
            self.running = False
            logger.info("Simple hotkey listener stopped")
        except:
            pass
