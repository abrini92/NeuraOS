"""
Notes.app AppleScript templates.

Note-taking automation for macOS Notes.
"""


class NotesScripts:
    """AppleScript templates for Notes.app operations."""

    @staticmethod
    def create_note(title: str, body: str) -> str:
        """
        Create a new note.

        Args:
            title: Note title
            body: Note content

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')
        body_escaped = body.replace('"', '\\"').replace("\\n", "<br>")

        return f"""
tell application "Notes"
    set newNote to make new note with properties {{name:"{title_escaped}", body:"{body_escaped}"}}
    return "✅ Note created: {title_escaped}"
end tell
"""

    @staticmethod
    def list_notes(limit: int = 10) -> str:
        """
        List recent notes.

        Args:
            limit: Number of notes to list (default: 10)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Notes"
    set notesList to notes
    set noteCount to count of notesList

    if noteCount is 0 then
        return "📝 No notes found"
    end if

    set output to "📝 NOTES (" & noteCount & " total):\\n\\n"

    set maxIndex to {limit}
    if noteCount < maxIndex then
        set maxIndex to noteCount
    end if

    repeat with i from 1 to maxIndex
        set n to item i of notesList
        set output to output & i & ". " & (name of n) & "\\n"

        try
            set modDate to modification date of n
            set output to output & "   Modified: " & (modDate as string) & "\\n"
        end try

        set output to output & "\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def read_note(index: int) -> str:
        """
        Read a note's content by index.

        Args:
            index: Note index (1-based)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Notes"
    set n to note {index}
    set output to "📝 NOTE:\\n"
    set output to output & "═══════════════════════════\\n\\n"
    set output to output & "Title: " & (name of n) & "\\n\\n"
    set output to output & (body of n) & "\\n"
    set output to output & "═══════════════════════════\\n"
    return output
end tell
"""

    @staticmethod
    def search_notes(query: str) -> str:
        """
        Search notes by keyword.

        Args:
            query: Search query

        Returns:
            str: AppleScript code
        """
        query_escaped = query.replace('"', '\\"')

        return f"""
tell application "Notes"
    set searchResults to (notes whose name contains "{query_escaped}" or body contains "{query_escaped}")
    set resultCount to count of searchResults

    if resultCount is 0 then
        return "🔍 No notes found matching: {query_escaped}"
    end if

    set output to "🔍 Found " & resultCount & " note(s) matching '{query_escaped}':\\n\\n"

    repeat with n in searchResults
        set output to output & "• " & (name of n) & "\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def delete_note(title: str) -> str:
        """
        Delete a note by title.

        Args:
            title: Note title to delete

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')

        return f"""
tell application "Notes"
    set matchingNotes to (notes whose name is "{title_escaped}")
    set noteCount to count of matchingNotes

    if noteCount is 0 then
        return "❌ No note found with title: {title_escaped}"
    end if

    repeat with n in matchingNotes
        delete n
    end repeat

    return "🗑️ Deleted " & noteCount & " note(s): {title_escaped}"
end tell
"""

    @staticmethod
    def append_to_note(index: int, text: str) -> str:
        """
        Append text to an existing note.

        Args:
            index: Note index (1-based)
            text: Text to append

        Returns:
            str: AppleScript code
        """
        text_escaped = text.replace('"', '\\"').replace("\\n", "<br>")

        return f"""
tell application "Notes"
    set n to note {index}
    set currentBody to body of n
    set body of n to currentBody & "<br><br>" & "{text_escaped}"
    return "✅ Text appended to: " & (name of n)
end tell
"""

    @staticmethod
    def create_checklist_note(title: str, items: list) -> str:
        """
        Create a note with checklist items.

        Args:
            title: Note title
            items: List of checklist items

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')

        # Build checklist HTML
        checklist_html = ""
        for item in items:
            item_escaped = item.replace('"', '\\"')
            checklist_html += f"☐ {item_escaped}<br>"

        return f"""
tell application "Notes"
    set newNote to make new note with properties {{name:"{title_escaped}", body:"{checklist_html}"}}
    return "✅ Checklist created: {title_escaped}"
end tell
"""

    @staticmethod
    def get_note_by_title(title: str) -> str:
        """
        Get note content by exact title match.

        Args:
            title: Exact note title

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')

        return f"""
tell application "Notes"
    set matchingNotes to (notes whose name is "{title_escaped}")

    if (count of matchingNotes) is 0 then
        return "❌ No note found with title: {title_escaped}"
    end if

    set n to item 1 of matchingNotes
    return "📝 " & (name of n) & ":\\n\\n" & (body of n)
end tell
"""

    @staticmethod
    def list_folders() -> str:
        """
        List all note folders.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Notes"
    set folderList to folders
    set output to "📁 NOTE FOLDERS:\\n\\n"

    repeat with f in folderList
        set folderName to name of f
        set noteCount to count of notes of f
        set output to output & "• " & folderName & " (" & noteCount & " notes)\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def create_note_in_folder(folder_name: str, title: str, body: str) -> str:
        """
        Create note in specific folder.

        Args:
            folder_name: Target folder name
            title: Note title
            body: Note content

        Returns:
            str: AppleScript code
        """
        folder_escaped = folder_name.replace('"', '\\"')
        title_escaped = title.replace('"', '\\"')
        body_escaped = body.replace('"', '\\"').replace("\\n", "<br>")

        return f"""
tell application "Notes"
    set targetFolder to folder "{folder_escaped}"
    make new note at targetFolder with properties {{name:"{title_escaped}", body:"{body_escaped}"}}
    return "✅ Note created in {folder_escaped}: {title_escaped}"
end tell
"""
