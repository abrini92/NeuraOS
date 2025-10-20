"""
Safari.app AppleScript templates.

Web browsing automation for macOS Safari.
"""


class SafariScripts:
    """AppleScript templates for Safari.app operations."""

    @staticmethod
    def open_url(url: str, new_tab: bool = False) -> str:
        """
        Open a URL in Safari.

        Args:
            url: URL to open
            new_tab: Open in new tab (default: False, uses current tab)

        Returns:
            str: AppleScript code
        """
        url_escaped = url.replace('"', '\\"')

        if new_tab:
            return f"""
tell application "Safari"
    activate
    tell window 1
        set current tab to (make new tab with properties {{URL:"{url_escaped}"}})
    end tell
    return "✅ Opened in new tab: {url_escaped}"
end tell
"""
        else:
            return f"""
tell application "Safari"
    activate
    set URL of front document to "{url_escaped}"
    return "✅ Opened: {url_escaped}"
end tell
"""

    @staticmethod
    def get_current_url() -> str:
        """
        Get current tab's URL.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    return "🔗 Current URL: " & (URL of current tab of window 1)
end tell
"""

    @staticmethod
    def get_page_title() -> str:
        """
        Get current page title.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    return "📄 Page title: " & (name of current tab of window 1)
end tell
"""

    @staticmethod
    def search_google(query: str) -> str:
        """
        Search on Google.

        Args:
            query: Search query

        Returns:
            str: AppleScript code
        """
        # URL encode spaces
        query_encoded = query.replace(" ", "+").replace('"', "%22")

        return f"""
tell application "Safari"
    activate
    set URL of front document to "https://www.google.com/search?q={query_encoded}"
    return "🔍 Searching Google for: {query}"
end tell
"""

    @staticmethod
    def execute_javascript(js_code: str) -> str:
        """
        Execute JavaScript in current page.

        Args:
            js_code: JavaScript code to execute

        Returns:
            str: AppleScript code
        """
        # Escape quotes in JavaScript
        js_escaped = js_code.replace('"', '\\"').replace("\\n", " ")

        return f"""
tell application "Safari"
    set jsResult to do JavaScript "{js_escaped}" in current tab of window 1
    return "✅ JavaScript executed. Result: " & jsResult
end tell
"""

    @staticmethod
    def get_page_text() -> str:
        """
        Get all text from current page.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    set pageText to do JavaScript "document.body.innerText" in current tab of window 1
    return "📝 Page text:\\n" & pageText
end tell
"""

    @staticmethod
    def close_current_tab() -> str:
        """
        Close current tab.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    set tabName to name of current tab of window 1
    close current tab of window 1
    return "✅ Closed tab: " & tabName
end tell
"""

    @staticmethod
    def list_open_tabs() -> str:
        """
        List all open tabs.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    set output to "📑 OPEN TABS:\\n\\n"
    set tabList to tabs of window 1
    set tabCount to count of tabList

    repeat with i from 1 to tabCount
        set theTab to item i of tabList
        set output to output & i & ". " & (name of theTab) & "\\n"
        set output to output & "   " & (URL of theTab) & "\\n\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def go_back() -> str:
        """
        Navigate back in history.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    do JavaScript "window.history.back()" in current tab of window 1
    return "◀️ Navigated back"
end tell
"""

    @staticmethod
    def go_forward() -> str:
        """
        Navigate forward in history.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    do JavaScript "window.history.forward()" in current tab of window 1
    return "▶️ Navigated forward"
end tell
"""

    @staticmethod
    def reload_page() -> str:
        """
        Reload current page.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Safari"
    do JavaScript "window.location.reload()" in current tab of window 1
    return "🔄 Page reloaded"
end tell
"""

    @staticmethod
    def search_wikipedia(query: str) -> str:
        """
        Search Wikipedia.

        Args:
            query: Search term

        Returns:
            str: AppleScript code
        """
        query_encoded = query.replace(" ", "_").replace('"', "%22")

        return f"""
tell application "Safari"
    activate
    set URL of front document to "https://en.wikipedia.org/wiki/{query_encoded}"
    return "📚 Opened Wikipedia: {query}"
end tell
"""

    @staticmethod
    def open_youtube_search(query: str) -> str:
        """
        Search YouTube.

        Args:
            query: Search query

        Returns:
            str: AppleScript code
        """
        query_encoded = query.replace(" ", "+")

        return f"""
tell application "Safari"
    activate
    set URL of front document to "https://www.youtube.com/results?search_query={query_encoded}"
    return "🎥 Searching YouTube for: {query}"
end tell
"""

    @staticmethod
    def bookmark_current_page(title: str | None = None) -> str:
        """
        Bookmark current page.

        Args:
            title: Optional custom title

        Returns:
            str: AppleScript code
        """
        if title:
            title_escaped = title.replace('"', '\\"')
            return f"""
tell application "Safari"
    set currentURL to URL of current tab of window 1
    add reading list item currentURL with title "{title_escaped}"
    return "⭐ Bookmarked: {title_escaped}"
end tell
"""
        else:
            return """
tell application "Safari"
    set currentURL to URL of current tab of window 1
    set currentTitle to name of current tab of window 1
    add reading list item currentURL with title currentTitle
    return "⭐ Bookmarked: " & currentTitle
end tell
"""
