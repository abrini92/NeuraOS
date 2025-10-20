"""
Native notifications for macOS/Linux.

Uses system notification APIs for native look and feel.
"""

import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


def notify(
    title: str,
    message: str,
    sound: bool = False,
    icon: str = None
):
    """
    Show native notification.
    
    Args:
        title: Notification title
        message: Notification message
        sound: Play sound
        icon: Icon path (optional)
    
    Example:
        >>> notify("Neura", "Task completed!", sound=True)
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            _notify_macos(title, message, sound)
        elif system == "Linux":
            _notify_linux(title, message, sound, icon)
        else:
            logger.warning(f"Notifications not supported on {system}")
    
    except Exception as e:
        logger.error(f"Failed to show notification: {e}")


def _notify_macos(title: str, message: str, sound: bool):
    """Show notification on macOS using osascript."""
    script = f'''
    display notification "{message}" with title "{title}"
    '''
    
    if sound:
        script += ' sound name "Glass"'
    
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True
        )
        logger.debug(f"Notification shown: {title}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to show macOS notification: {e}")


def _notify_linux(title: str, message: str, sound: bool, icon: str = None):
    """Show notification on Linux using notify-send."""
    cmd = ["notify-send", title, message]
    
    if icon:
        cmd.extend(["-i", icon])
    
    if sound:
        cmd.extend(["-u", "normal"])
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.debug(f"Notification shown: {title}")
    except FileNotFoundError:
        logger.error("notify-send not found. Install libnotify-bin")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to show Linux notification: {e}")


def notify_success(message: str):
    """Show success notification."""
    notify("✅ Neura Success", message, sound=True)


def notify_error(message: str):
    """Show error notification."""
    notify("❌ Neura Error", message, sound=True)


def notify_info(message: str):
    """Show info notification."""
    notify("ℹ️ Neura", message, sound=False)


# Test function
def test_notifications():
    """Test notifications."""
    notify("Neura Test", "This is a test notification", sound=True)
    notify_success("Task completed successfully!")
    notify_error("Something went wrong")
    notify_info("Just letting you know...")


if __name__ == "__main__":
    test_notifications()
