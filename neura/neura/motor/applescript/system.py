"""
System-level AppleScript templates.

System control and information for macOS.
"""


class SystemScripts:
    """AppleScript templates for system-level operations."""

    @staticmethod
    def get_volume() -> str:
        """
        Get current system volume.

        Returns:
            str: AppleScript code
        """
        return """
get volume settings
set volLevel to output volume of result
return "🔊 Volume: " & volLevel & "%"
"""

    @staticmethod
    def set_volume(level: int) -> str:
        """
        Set system volume (0-100).

        Args:
            level: Volume level (0-100)

        Returns:
            str: AppleScript code
        """
        # Clamp level between 0-100
        level = max(0, min(100, level))

        return f"""
set volume output volume {level}
return "🔊 Volume set to {level}%"
"""

    @staticmethod
    def mute() -> str:
        """
        Mute system audio.

        Returns:
            str: AppleScript code
        """
        return """
set volume output muted true
return "🔇 Audio muted"
"""

    @staticmethod
    def unmute() -> str:
        """
        Unmute system audio.

        Returns:
            str: AppleScript code
        """
        return """
set volume output muted false
return "🔊 Audio unmuted"
"""

    @staticmethod
    def get_battery() -> str:
        """
        Get battery status.

        Returns:
            str: AppleScript code
        """
        return """
try
    set batteryInfo to do shell script "pmset -g batt"

    -- Extract percentage
    set batteryLevel to do shell script "pmset -g batt | grep -Eo '[0-9]+%' | head -1"

    -- Check if charging
    if batteryInfo contains "AC Power" then
        set powerStatus to "⚡ Charging"
    else if batteryInfo contains "charged" then
        set powerStatus to "✅ Fully Charged"
    else
        set powerStatus to "🔋 On Battery"
    end if

    return "🔋 Battery: " & batteryLevel & " (" & powerStatus & ")"
on error
    return "❌ Battery info not available (desktop Mac?)"
end try
"""

    @staticmethod
    def take_screenshot(filepath: str = "~/Desktop/screenshot.png") -> str:
        """
        Take a screenshot.

        Args:
            filepath: Save location (default: ~/Desktop/screenshot.png)

        Returns:
            str: AppleScript code
        """
        filepath_escaped = filepath.replace('"', '\\"')

        return f"""
do shell script "screencapture {filepath_escaped}"
return "📸 Screenshot saved to {filepath_escaped}"
"""

    @staticmethod
    def take_screenshot_selection() -> str:
        """
        Take screenshot of selected area.

        Returns:
            str: AppleScript code
        """
        return """
do shell script "screencapture -i ~/Desktop/screenshot_selection.png"
return "📸 Screenshot saved to ~/Desktop/screenshot_selection.png"
"""

    @staticmethod
    def get_date_time() -> str:
        """
        Get current date and time.

        Returns:
            str: AppleScript code
        """
        return """
set now to current date
return "📅 " & (now as string)
"""

    @staticmethod
    def get_system_info() -> str:
        """
        Get system information.

        Returns:
            str: AppleScript code
        """
        return """
set output to "💻 SYSTEM INFO:\\n\\n"

-- macOS version
set osVersion to do shell script "sw_vers -productVersion"
set output to output & "macOS: " & osVersion & "\\n"

-- Computer name
set compName to do shell script "scutil --get ComputerName"
set output to output & "Computer: " & compName & "\\n"

-- Uptime
set uptime to do shell script "uptime | awk '{print $3,$4}' | sed 's/,//'"
set output to output & "Uptime: " & uptime & "\\n"

-- Memory
try
    set memInfo to do shell script "top -l 1 | grep PhysMem | awk '{print $2}'"
    set output to output & "Memory Used: " & memInfo & "\\n"
end try

return output
"""

    @staticmethod
    def lock_screen() -> str:
        """
        Lock the screen.

        Returns:
            str: AppleScript code
        """
        return """
tell application "System Events"
    keystroke "q" using {control down, command down}
end tell
return "🔒 Screen locked"
"""

    @staticmethod
    def sleep_computer() -> str:
        """
        Put computer to sleep.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Finder"
    sleep
end tell
return "😴 Computer going to sleep"
"""

    @staticmethod
    def get_wifi_status() -> str:
        """
        Get WiFi connection status.

        Returns:
            str: AppleScript code
        """
        return """
try
    set wifiStatus to do shell script "networksetup -getairportnetwork en0"

    if wifiStatus contains "You are not associated" then
        return "📶 WiFi: Not connected"
    else
        set networkName to do shell script "networksetup -getairportnetwork en0 | cut -d ':' -f 2"
        return "📶 WiFi: Connected to" & networkName
    end if
on error
    return "❌ WiFi info not available"
end try
"""

    @staticmethod
    def set_brightness(level: int) -> str:
        """
        Set screen brightness (0-100).

        Args:
            level: Brightness level (0-100)

        Returns:
            str: AppleScript code
        """
        # Convert 0-100 to 0.0-1.0
        level_float = max(0, min(100, level)) / 100.0

        return f"""
tell application "System Events"
    tell appearance preferences
        set brightness to {level_float}
    end tell
end tell
return "💡 Brightness set to {level}%"
"""

    @staticmethod
    def get_clipboard() -> str:
        """
        Get clipboard content.

        Returns:
            str: AppleScript code
        """
        return """
set clipboardContent to the clipboard as text
return "📋 Clipboard: " & clipboardContent
"""

    @staticmethod
    def set_clipboard(text: str) -> str:
        """
        Set clipboard content.

        Args:
            text: Text to copy to clipboard

        Returns:
            str: AppleScript code
        """
        text_escaped = text.replace('"', '\\"')

        return f"""
set the clipboard to "{text_escaped}"
return "📋 Copied to clipboard: {text_escaped}"
"""

    @staticmethod
    def quit_application(app_name: str) -> str:
        """
        Quit an application.

        Args:
            app_name: Application name (e.g., "Safari", "Mail")

        Returns:
            str: AppleScript code
        """
        app_escaped = app_name.replace('"', '\\"')

        return f"""
tell application "{app_escaped}"
    quit
end tell
return "✅ Quit {app_escaped}"
"""

    @staticmethod
    def restart_computer() -> str:
        """
        Restart computer (requires confirmation).

        Returns:
            str: AppleScript code
        """
        return """
tell application "System Events"
    restart
end tell
return "🔄 Computer restarting..."
"""

    @staticmethod
    def show_notification(title: str, message: str, sound: bool = True) -> str:
        """
        Show macOS notification.

        Args:
            title: Notification title
            message: Notification message
            sound: Play sound (default: True)

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')
        message_escaped = message.replace('"', '\\"')

        sound_param = 'sound name "default"' if sound else ""

        return f"""
display notification "{message_escaped}" with title "{title_escaped}" {sound_param}
return "🔔 Notification shown: {title_escaped}"
"""

    @staticmethod
    def speak_text(text: str, voice: str = "Samantha") -> str:
        """
        Make macOS speak text.

        Args:
            text: Text to speak
            voice: Voice name (default: Samantha)

        Returns:
            str: AppleScript code
        """
        text_escaped = text.replace('"', '\\"')
        voice_escaped = voice.replace('"', '\\"')

        return f"""
say "{text_escaped}" using "{voice_escaped}"
return "🔊 Spoken: {text_escaped}"
"""

    @staticmethod
    def open_url_in_default_browser(url: str) -> str:
        """
        Open URL in default browser.

        Args:
            url: URL to open

        Returns:
            str: AppleScript code
        """
        url_escaped = url.replace('"', '\\"')

        return f"""
open location "{url_escaped}"
return "✅ Opened: {url_escaped}"
"""
