"""
Generic AppleScript templates and utilities.

Reusable script patterns and helpers.
"""


class AppleScriptTemplates:
    """Generic AppleScript templates."""

    @staticmethod
    def tell_app(app_name: str, commands: str) -> str:
        """
        Basic tell application template.

        Args:
            app_name: Application name
            commands: Commands to execute

        Returns:
            str: Complete AppleScript
        """
        return f"""
tell application "{app_name}"
    {commands}
end tell
"""

    @staticmethod
    def activate_app(app_name: str) -> str:
        """
        Activate (bring to front) an application.

        Args:
            app_name: Application name

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "{app_name}"
    activate
end tell
return "✅ Activated {app_name}"
"""

    @staticmethod
    def is_app_running(app_name: str) -> str:
        """
        Check if application is running.

        Args:
            app_name: Application name

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "System Events"
    set isRunning to (name of processes) contains "{app_name}"
end tell

if isRunning then
    return "✅ {app_name} is running"
else
    return "❌ {app_name} is not running"
end if
"""

    @staticmethod
    def launch_app(app_name: str) -> str:
        """
        Launch an application.

        Args:
            app_name: Application name

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "{app_name}"
    launch
    activate
end tell
return "✅ Launched {app_name}"
"""

    @staticmethod
    def get_app_windows(app_name: str) -> str:
        """
        List all windows of an application.

        Args:
            app_name: Application name

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "{app_name}"
    set windowList to name of every window
    set windowCount to count of windowList

    if windowCount is 0 then
        return "{app_name} has no open windows"
    end if

    set output to "{app_name} windows (" & windowCount & "):\\n"
    repeat with w in windowList
        set output to output & "• " & w & "\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def close_app_window(app_name: str, window_name: str) -> str:
        """
        Close specific window of an application.

        Args:
            app_name: Application name
            window_name: Window name or index

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "{app_name}"
    close window "{window_name}"
    return "✅ Closed window: {window_name}"
end tell
"""

    @staticmethod
    def execute_shell_command(command: str) -> str:
        """
        Execute shell command from AppleScript.

        Args:
            command: Shell command

        Returns:
            str: AppleScript code
        """
        command_escaped = command.replace('"', '\\"')

        return f"""
set shellOutput to do shell script "{command_escaped}"
return shellOutput
"""

    @staticmethod
    def display_dialog(message: str, title: str = "Neura", buttons: list = None) -> str:
        """
        Display dialog box.

        Args:
            message: Dialog message
            title: Dialog title (default: "Neura")
            buttons: Button labels (default: ["OK"])

        Returns:
            str: AppleScript code
        """
        message_escaped = message.replace('"', '\\"')
        title_escaped = title.replace('"', '\\"')

        if buttons:
            buttons_str = ", ".join([f'\\"{b}\\"' for b in buttons])
            buttons_param = f"buttons {{{buttons_str}}}"
        else:
            buttons_param = ""

        return f"""
display dialog "{message_escaped}" with title "{title_escaped}" {buttons_param}
return "Dialog shown"
"""

    @staticmethod
    def choose_from_list(prompt: str, items: list, title: str = "Neura") -> str:
        """
        Show selection dialog.

        Args:
            prompt: Selection prompt
            items: List of items to choose from
            title: Dialog title

        Returns:
            str: AppleScript code
        """
        prompt_escaped = prompt.replace('"', '\\"')
        title_escaped = title.replace('"', '\\"')
        items_str = ", ".join([f'\\"{item}\\"' for item in items])

        return f"""
set itemList to {{{items_str}}}
set chosenItem to choose from list itemList with prompt "{prompt_escaped}" with title "{title_escaped}"

if chosenItem is false then
    return "Cancelled"
else
    return "Selected: " & (item 1 of chosenItem)
end if
"""

    @staticmethod
    def get_app_property(app_name: str, property_name: str) -> str:
        """
        Get application property.

        Args:
            app_name: Application name
            property_name: Property to get (e.g., "version", "name")

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "{app_name}"
    set propValue to {property_name}
    return "{app_name} {property_name}: " & propValue
end tell
"""

    @staticmethod
    def list_running_apps() -> str:
        """
        List all running applications.

        Returns:
            str: AppleScript code
        """
        return """
tell application "System Events"
    set processList to name of every process whose background only is false
    set output to "🖥️ RUNNING APPLICATIONS:\\n\\n"

    repeat with proc in processList
        set output to output & "• " & proc & "\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def keystroke(keys: str, modifiers: list = None) -> str:
        """
        Simulate keystroke.

        Args:
            keys: Keys to press
            modifiers: Modifier keys (command, control, option, shift)

        Returns:
            str: AppleScript code
        """
        keys_escaped = keys.replace('"', '\\"')

        if modifiers:
            modifiers_str = ", ".join([f"{mod} down" for mod in modifiers])
            using_clause = f"using {{{modifiers_str}}}"
        else:
            using_clause = ""

        return f"""
tell application "System Events"
    keystroke "{keys_escaped}" {using_clause}
end tell
return "⌨️ Keystroke executed"
"""

    @staticmethod
    def delay_seconds(seconds: int) -> str:
        """
        Add delay/pause.

        Args:
            seconds: Seconds to delay

        Returns:
            str: AppleScript code
        """
        return f"""
delay {seconds}
return "⏸️ Delayed {seconds} second(s)"
"""
