"""
Neura Background Service - Main daemon.

Runs 24/7 in background with menu bar icon.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

try:
    import rumps
except ImportError:
    rumps = None

from neura.daemon.hotkey import HotkeyListener
from neura.daemon.wakeword import WakeWordDetector
from neura.ui.floating import FloatingMic
from neura.ui.notifications import notify

logger = logging.getLogger(__name__)


class NeuraService:
    """
    Neura background service.
    
    Features:
    - Menu bar app (macOS)
    - Global hotkey listener
    - Wake word detection
    - Floating mic UI
    - Auto-start on boot
    """

    def __init__(self):
        """Initialize Neura service."""
        self.running = False
        self.hotkey_listener = None
        self.wakeword_detector = None
        self.floating_mic = None
        
        # Setup logging
        log_dir = Path.home() / ".neura" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "daemon.log"),
                logging.StreamHandler()
            ]
        )
        
        logger.info("Neura Service initialized")

    async def start(self):
        """Start the background service."""
        logger.info("Starting Neura background service...")
        self.running = True
        
        try:
            # Start hotkey listener
            self.hotkey_listener = HotkeyListener(
                on_trigger=self._on_hotkey_triggered
            )
            self.hotkey_listener.start()
            logger.info("Hotkey listener started")
            
            # Start wake word detector
            self.wakeword_detector = WakeWordDetector(
                on_wake=self._on_wake_word
            )
            await self.wakeword_detector.start()
            logger.info("Wake word detector started")
            
            # Notify user
            notify(
                title="Neura Started",
                message="Background service is running. Say 'Neura' or press Cmd+Space+Space",
                sound=True
            )
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Service error: {e}")
            raise

    async def stop(self):
        """Stop the background service."""
        logger.info("Stopping Neura background service...")
        self.running = False
        
        # Stop components
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        if self.wakeword_detector:
            await self.wakeword_detector.stop()
        
        if self.floating_mic:
            self.floating_mic.hide()
        
        notify(
            title="Neura Stopped",
            message="Background service stopped",
            sound=False
        )
        
        logger.info("Service stopped")

    def _on_hotkey_triggered(self):
        """Handle hotkey trigger."""
        logger.info("Hotkey triggered")
        self._show_floating_mic()

    def _on_wake_word(self):
        """Handle wake word detection."""
        logger.info("Wake word detected")
        self._show_floating_mic()

    def _show_floating_mic(self):
        """Show floating microphone UI."""
        if not self.floating_mic:
            self.floating_mic = FloatingMic(
                on_close=self._on_mic_closed
            )
        
        self.floating_mic.show()
        self.floating_mic.start_listening()

    def _on_mic_closed(self):
        """Handle floating mic closed."""
        logger.info("Floating mic closed")


class NeuraMenuBarApp(rumps.App if rumps else object):
    """
    Neura menu bar application (macOS only).
    
    Provides:
    - Menu bar icon
    - Quick actions
    - Status display
    """

    def __init__(self, service: NeuraService):
        """Initialize menu bar app."""
        if not rumps:
            logger.warning("rumps not available, menu bar disabled")
            return
            
        super().__init__(
            "Neura",
            icon="🧠",
            quit_button=None
        )
        
        self.service = service
        self.menu = [
            rumps.MenuItem("Status: Running", callback=None),
            rumps.separator,
            rumps.MenuItem("Activate (Cmd+Space+Space)", callback=self.activate),
            rumps.MenuItem("Settings", callback=self.settings),
            rumps.separator,
            rumps.MenuItem("Quit Neura", callback=self.quit_app)
        ]

    @rumps.clicked("Activate (Cmd+Space+Space)")
    def activate(self, _):
        """Activate Neura manually."""
        self.service._show_floating_mic()

    @rumps.clicked("Settings")
    def settings(self, _):
        """Open settings."""
        notify(
            title="Settings",
            message="Settings UI coming soon",
            sound=False
        )

    @rumps.clicked("Quit Neura")
    def quit_app(self, _):
        """Quit the application."""
        asyncio.create_task(self.service.stop())
        rumps.quit_application()


def start_daemon():
    """
    Start Neura as background daemon.
    
    Usage:
        poetry run neura daemon
    """
    # Create service
    service = NeuraService()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(service.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start menu bar app (macOS) or run service directly
    if rumps and sys.platform == "darwin":
        app = NeuraMenuBarApp(service)
        
        # Start service in background
        async def run_service():
            await service.start()
        
        # Run both
        import threading
        service_thread = threading.Thread(
            target=lambda: asyncio.run(run_service()),
            daemon=True
        )
        service_thread.start()
        
        # Run menu bar app (blocks)
        app.run()
    else:
        # Run service directly
        asyncio.run(service.start())


if __name__ == "__main__":
    start_daemon()
