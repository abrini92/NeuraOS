"""
Finder.app AppleScript templates.

File management automation for macOS Finder.
"""


class FinderScripts:
    """AppleScript templates for Finder.app operations."""

    @staticmethod
    def list_files(folder: str = "Desktop", max_items: int = 20) -> str:
        """
        List files in a folder.

        Args:
            folder: Folder name (Desktop, Documents, Downloads, etc.)
            max_items: Maximum items to list (default: 20)

        Returns:
            str: AppleScript code
        """
        folder_escaped = folder.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set theFolder to folder "{folder_escaped}" of home
        set fileList to items of theFolder
        set itemCount to count of fileList

        if itemCount is 0 then
            return "📂 {folder_escaped} is empty"
        end if

        set output to "📂 {folder_escaped.upper()} (" & itemCount & " items):\\n\\n"

        set maxIndex to {max_items}
        if itemCount < maxIndex then
            set maxIndex to itemCount
        end if

        repeat with i from 1 to maxIndex
            set theItem to item i of fileList
            set itemName to name of theItem
            set itemKind to kind of theItem

            if class of theItem is folder then
                set output to output & "📁 " & itemName & " (folder)\\n"
            else
                set output to output & "📄 " & itemName & " (" & itemKind & ")\\n"
            end if
        end repeat

        if itemCount > maxIndex then
            set output to output & "\\n... and " & (itemCount - maxIndex) & " more items"
        end if

        return output
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def open_file(filename: str, folder: str = "Desktop") -> str:
        """
        Open a file.

        Args:
            filename: File name
            folder: Folder containing the file

        Returns:
            str: AppleScript code
        """
        filename_escaped = filename.replace('"', '\\"')
        folder_escaped = folder.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set theFile to file "{filename_escaped}" of folder "{folder_escaped}" of home
        open theFile
        return "✅ Opened: {filename_escaped}"
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def search_files(query: str, location: str = "home") -> str:
        """
        Search for files by name.

        Args:
            query: Search query
            location: Search location (home, Desktop, Documents, etc.)

        Returns:
            str: AppleScript code
        """
        query_escaped = query.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        if "{location}" is "home" then
            set searchLocation to home
        else
            set searchLocation to folder "{location}" of home
        end if

        set searchResults to (every file of entire contents of searchLocation whose name contains "{query_escaped}")
        set resultCount to count of searchResults

        if resultCount is 0 then
            return "🔍 No files found matching: {query_escaped}"
        end if

        set output to "🔍 Found " & resultCount & " file(s) matching '{query_escaped}':\\n\\n"

        set maxResults to 15
        if resultCount < maxResults then
            set maxResults to resultCount
        end if

        repeat with i from 1 to maxResults
            set theFile to item i of searchResults
            set output to output & "• " & (name of theFile) & "\\n"
            set output to output & "  Location: " & (POSIX path of (theFile as alias)) & "\\n\\n"
        end repeat

        if resultCount > maxResults then
            set output to output & "... and " & (resultCount - maxResults) & " more results"
        end if

        return output
    on error errMsg
        return "❌ Search error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def get_file_info(filename: str) -> str:
        """
        Get detailed file information.

        Args:
            filename: File name or path

        Returns:
            str: AppleScript code
        """
        filename_escaped = filename.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set theFile to file "{filename_escaped}" of home

        set output to "📄 FILE INFO:\\n"
        set output to output & "═══════════════════════════\\n\\n"
        set output to output & "Name: " & (name of theFile) & "\\n"
        set output to output & "Kind: " & (kind of theFile) & "\\n"
        set output to output & "Size: " & (size of theFile) & " bytes\\n"
        set output to output & "Created: " & (creation date of theFile as string) & "\\n"
        set output to output & "Modified: " & (modification date of theFile as string) & "\\n"
        set output to output & "Location: " & (POSIX path of (theFile as alias)) & "\\n"

        return output
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def move_file(filename: str, from_folder: str, to_folder: str) -> str:
        """
        Move file between folders.

        Args:
            filename: File to move
            from_folder: Source folder
            to_folder: Destination folder

        Returns:
            str: AppleScript code
        """
        filename_escaped = filename.replace('"', '\\"')
        from_escaped = from_folder.replace('"', '\\"')
        to_escaped = to_folder.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set theFile to file "{filename_escaped}" of folder "{from_escaped}" of home
        set destFolder to folder "{to_escaped}" of home
        move theFile to destFolder
        return "✅ Moved {filename_escaped} from {from_escaped} to {to_escaped}"
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def create_folder(folder_name: str, location: str = "Desktop") -> str:
        """
        Create a new folder.

        Args:
            folder_name: Name for new folder
            location: Parent folder location

        Returns:
            str: AppleScript code
        """
        folder_escaped = folder_name.replace('"', '\\"')
        location_escaped = location.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set parentFolder to folder "{location_escaped}" of home
        make new folder at parentFolder with properties {{name:"{folder_escaped}"}}
        return "✅ Folder created: {folder_escaped} in {location_escaped}"
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def delete_file(filename: str, folder: str = "Desktop") -> str:
        """
        Delete a file (move to trash).

        Args:
            filename: File to delete
            folder: Folder containing the file

        Returns:
            str: AppleScript code
        """
        filename_escaped = filename.replace('"', '\\"')
        folder_escaped = folder.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set theFile to file "{filename_escaped}" of folder "{folder_escaped}" of home
        move theFile to trash
        return "🗑️ Moved to trash: {filename_escaped}"
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def empty_trash() -> str:
        """
        Empty the trash.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Finder"
    try
        set itemCount to count of items of trash
        if itemCount is 0 then
            return "🗑️ Trash is already empty"
        end if

        empty trash
        return "🗑️ Trash emptied (" & itemCount & " items deleted)"
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""

    @staticmethod
    def get_disk_space() -> str:
        """
        Get available disk space.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Finder"
    set diskInfo to disk "Macintosh HD"
    set totalSpace to capacity of diskInfo
    set freeSpace to free space of diskInfo
    set usedSpace to totalSpace - freeSpace

    set totalGB to (totalSpace / 1.0E+9) as integer
    set freeGB to (freeSpace / 1.0E+9) as integer
    set usedGB to (usedSpace / 1.0E+9) as integer
    set usedPercent to ((usedSpace / totalSpace) * 100) as integer

    set output to "💾 DISK SPACE:\\n\\n"
    set output to output & "Total: " & totalGB & " GB\\n"
    set output to output & "Used: " & usedGB & " GB (" & usedPercent & "%)\\n"
    set output to output & "Free: " & freeGB & " GB\\n"

    return output
end tell
"""

    @staticmethod
    def open_folder(folder_name: str) -> str:
        """
        Open a folder in Finder.

        Args:
            folder_name: Folder to open (Desktop, Documents, etc.)

        Returns:
            str: AppleScript code
        """
        folder_escaped = folder_name.replace('"', '\\"')

        return f"""
tell application "Finder"
    try
        set theFolder to folder "{folder_escaped}" of home
        open theFolder
        activate
        return "✅ Opened folder: {folder_escaped}"
    on error errMsg
        return "❌ Error: " & errMsg
    end try
end tell
"""
