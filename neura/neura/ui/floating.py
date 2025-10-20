"""
Floating microphone UI.

Beautiful, transparent window that appears when Neura is activated.
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable

logger = logging.getLogger(__name__)


class FloatingMic:
    """
    Floating microphone window.
    
    Features:
    - Transparent background
    - Always on top
    - Breathing animation
    - Transcription display
    - Draggable
    """

    def __init__(self, on_close: Callable[[], None] = None):
        """
        Initialize floating mic.
        
        Args:
            on_close: Callback when window is closed
        """
        self.on_close = on_close
        self.window = None
        self.is_listening = False
        self.transcription_text = ""
        
        logger.info("Floating mic initialized")

    def show(self):
        """Show the floating mic window."""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            return
        
        # Create window
        self.window = tk.Tk()
        self.window.title("Neura")
        
        # Window properties
        self.window.attributes('-alpha', 0.95)  # Slightly transparent
        self.window.attributes('-topmost', True)  # Always on top
        self.window.overrideredirect(True)  # No window decorations
        
        # Size and position
        width = 400
        height = 200
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Style
        style = ttk.Style()
        style.theme_use('default')
        
        # Main frame
        main_frame = tk.Frame(
            self.window,
            bg='#1a1a1a',
            highlightthickness=2,
            highlightbackground='#00ff88'
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🧠 Neura",
            font=('Helvetica', 24, 'bold'),
            fg='#00ff88',
            bg='#1a1a1a'
        )
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(
            main_frame,
            text="Listening...",
            font=('Helvetica', 14),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        self.status_label.pack(pady=5)
        
        # Microphone icon (animated)
        self.mic_label = tk.Label(
            main_frame,
            text="🎤",
            font=('Helvetica', 48),
            fg='#00ff88',
            bg='#1a1a1a'
        )
        self.mic_label.pack(pady=10)
        
        # Transcription
        self.transcription_label = tk.Label(
            main_frame,
            text="",
            font=('Helvetica', 12),
            fg='#cccccc',
            bg='#1a1a1a',
            wraplength=350
        )
        self.transcription_label.pack(pady=5)
        
        # Close button
        close_btn = tk.Button(
            main_frame,
            text="✕",
            command=self.hide,
            font=('Helvetica', 16, 'bold'),
            fg='#ffffff',
            bg='#333333',
            activebackground='#555555',
            bd=0,
            padx=10,
            pady=5
        )
        close_btn.place(x=width-50, y=10)
        
        # Make draggable
        self._make_draggable(main_frame)
        
        # Bind Escape key to close
        self.window.bind('<Escape>', lambda e: self.hide())
        
        logger.info("Floating mic window created")

    def hide(self):
        """Hide the floating mic window."""
        if self.window:
            self.window.withdraw()
            self.is_listening = False
            
            if self.on_close:
                self.on_close()
        
        logger.info("Floating mic hidden")

    def start_listening(self):
        """Start listening for voice input."""
        self.is_listening = True
        self.update_status("Listening...")
        self._start_breathing_animation()
        
        # TODO: Start actual voice recording
        logger.info("Started listening")

    def stop_listening(self):
        """Stop listening for voice input."""
        self.is_listening = False
        self.update_status("Processing...")
        logger.info("Stopped listening")

    def update_status(self, status: str):
        """Update status text."""
        if self.window and self.status_label:
            self.status_label.config(text=status)

    def update_transcription(self, text: str):
        """Update transcription text."""
        self.transcription_text = text
        if self.window and self.transcription_label:
            self.transcription_label.config(text=text)

    def _make_draggable(self, widget):
        """Make widget draggable."""
        widget.bind('<Button-1>', self._start_drag)
        widget.bind('<B1-Motion>', self._on_drag)

    def _start_drag(self, event):
        """Start dragging."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        """Handle dragging."""
        x = self.window.winfo_x() + (event.x - self._drag_start_x)
        y = self.window.winfo_y() + (event.y - self._drag_start_y)
        self.window.geometry(f"+{x}+{y}")

    def _start_breathing_animation(self):
        """Start breathing animation for mic icon."""
        if not self.is_listening or not self.window:
            return
        
        # Pulse animation
        def pulse(scale=1.0, growing=True):
            if not self.is_listening or not self.window:
                return
            
            # Update size
            size = int(48 * scale)
            self.mic_label.config(font=('Helvetica', size))
            
            # Next frame
            if growing:
                next_scale = scale + 0.05
                if next_scale >= 1.2:
                    growing = False
            else:
                next_scale = scale - 0.05
                if next_scale <= 1.0:
                    growing = True
            
            # Schedule next frame
            self.window.after(50, lambda: pulse(next_scale, growing))
        
        pulse()

    def run(self):
        """Run the window (blocking)."""
        if self.window:
            self.window.mainloop()


# Test function
def test_floating_mic():
    """Test the floating mic UI."""
    mic = FloatingMic()
    mic.show()
    mic.start_listening()
    mic.update_transcription("Testing... 1, 2, 3")
    mic.run()


if __name__ == "__main__":
    test_floating_mic()
