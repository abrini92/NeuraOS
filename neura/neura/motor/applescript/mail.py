"""
Mail.app AppleScript templates.

Complete email automation for macOS Mail.
"""


class MailScripts:
    """AppleScript templates for Mail.app operations."""

    @staticmethod
    def list_inbox(limit: int = 10) -> str:
        """
        List recent inbox emails.

        Args:
            limit: Number of emails to list (default: 10)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Mail"
    set msgs to messages of inbox
    set msgCount to count of msgs
    if msgCount is 0 then
        return "Inbox is empty"
    end if

    set output to "📬 Inbox (" & msgCount & " total):\\n\\n"
    set maxIndex to {limit}
    if msgCount < maxIndex then
        set maxIndex to msgCount
    end if

    repeat with i from 1 to maxIndex
        set msg to item i of msgs
        set isRead to read status of msg
        set readMark to "📧"
        if isRead then
            set readMark to "✅"
        end if

        set output to output & readMark & " " & i & ". "
        set output to output & "From: " & sender of msg & "\\n"
        set output to output & "   Subject: " & subject of msg & "\\n"
        set output to output & "   Date: " & date received of msg & "\\n\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def read_email(index: int) -> str:
        """
        Read full email content by index.

        Args:
            index: Email index (1-based)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Mail"
    set msg to message {index} of inbox

    set output to "📧 EMAIL DETAILS\\n"
    set output to output & "═══════════════════════════\\n\\n"
    set output to output & "From: " & sender of msg & "\\n"
    set output to output & "To: " & address of to recipient 1 of msg & "\\n"
    set output to output & "Subject: " & subject of msg & "\\n"
    set output to output & "Date: " & date received of msg & "\\n\\n"
    set output to output & "───────────────────────────\\n"
    set output to output & content of msg & "\\n"
    set output to output & "═══════════════════════════\\n"

    return output
end tell
"""

    @staticmethod
    def search_emails(query: str, limit: int = 10) -> str:
        """
        Search emails by keyword.

        Args:
            query: Search query
            limit: Max results (default: 10)

        Returns:
            str: AppleScript code
        """
        # Escape quotes in query
        query_escaped = query.replace('"', '\\"')

        return f"""
tell application "Mail"
    set searchResults to (messages of inbox whose subject contains "{query_escaped}" or sender contains "{query_escaped}")
    set resultCount to count of searchResults

    if resultCount is 0 then
        return "No emails found matching '{query_escaped}'"
    end if

    set output to "🔍 Search results for '{query_escaped}' (" & resultCount & " found):\\n\\n"

    set maxIndex to {limit}
    if resultCount < maxIndex then
        set maxIndex to resultCount
    end if

    repeat with i from 1 to maxIndex
        set msg to item i of searchResults
        set output to output & i & ". "
        set output to output & "From: " & sender of msg & "\\n"
        set output to output & "   Subject: " & subject of msg & "\\n\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def send_email(to: str, subject: str, body: str) -> str:
        """
        Send a new email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            str: AppleScript code
        """
        # Escape special characters
        to_escaped = to.replace('"', '\\"')
        subject_escaped = subject.replace('"', '\\"')
        body_escaped = body.replace('"', '\\"').replace("\\n", "\\n")

        return f"""
tell application "Mail"
    set newMessage to make new outgoing message with properties {{subject:"{subject_escaped}", content:"{body_escaped}"}}
    tell newMessage
        make new to recipient at end of to recipients with properties {{address:"{to_escaped}"}}
        send
    end tell
    return "✅ Email sent to {to_escaped}"
end tell
"""

    @staticmethod
    def reply_to_email(index: int, body: str) -> str:
        """
        Reply to an email.

        Args:
            index: Email index (1-based)
            body: Reply content

        Returns:
            str: AppleScript code
        """
        body_escaped = body.replace('"', '\\"').replace("\\n", "\\n")

        return f"""
tell application "Mail"
    set originalMsg to message {index} of inbox
    set replyMsg to reply originalMsg with opening window
    set content of replyMsg to "{body_escaped}"
    send replyMsg
    return "✅ Reply sent to " & sender of originalMsg
end tell
"""

    @staticmethod
    def mark_as_read(index: int) -> str:
        """
        Mark email as read.

        Args:
            index: Email index (1-based)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Mail"
    set msg to message {index} of inbox
    set read status of msg to true
    return "✅ Email marked as read"
end tell
"""

    @staticmethod
    def delete_email(index: int) -> str:
        """
        Delete an email (move to trash).

        Args:
            index: Email index (1-based)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Mail"
    set msg to message {index} of inbox
    set mailSubject to subject of msg
    delete msg
    return "🗑️ Email deleted: " & mailSubject
end tell
"""

    @staticmethod
    def get_unread_count() -> str:
        """
        Get count of unread emails.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Mail"
    set unreadMsgs to (messages of inbox whose read status is false)
    set unreadCount to count of unreadMsgs
    return "📬 Unread emails: " & unreadCount
end tell
"""

    @staticmethod
    def forward_email(index: int, to: str) -> str:
        """
        Forward an email.

        Args:
            index: Email index (1-based)
            to: Forward recipient

        Returns:
            str: AppleScript code
        """
        to_escaped = to.replace('"', '\\"')

        return f"""
tell application "Mail"
    set originalMsg to message {index} of inbox
    set forwardMsg to forward originalMsg with opening window
    tell forwardMsg
        make new to recipient at end of to recipients with properties {{address:"{to_escaped}"}}
        send
    end tell
    return "✅ Email forwarded to {to_escaped}"
end tell
"""
