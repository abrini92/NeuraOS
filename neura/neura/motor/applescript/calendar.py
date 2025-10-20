"""
Calendar.app AppleScript templates.

Complete calendar automation for macOS Calendar.
"""


class CalendarScripts:
    """AppleScript templates for Calendar.app operations."""

    @staticmethod
    def list_today_events() -> str:
        """
        List all events for today.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Calendar"
    set today to current date
    set beginning of today to today - (time of today)
    set end of today to beginning of today + (24 * hours)

    set todayEvents to (every event of every calendar whose start date ≥ beginning of today and start date < end of today)
    set eventCount to count of todayEvents

    if eventCount is 0 then
        return "📅 No events scheduled for today"
    end if

    set output to "📅 TODAY'S SCHEDULE (" & eventCount & " events):\\n\\n"

    repeat with evt in todayEvents
        set eventStart to start date of evt
        set eventEnd to end date of evt
        set eventTitle to summary of evt

        set output to output & "• " & eventTitle & "\\n"
        set output to output & "  Time: " & time string of eventStart & " - " & time string of eventEnd & "\\n"

        try
            set eventLocation to location of evt
            if eventLocation is not "" then
                set output to output & "  Location: " & eventLocation & "\\n"
            end if
        end try

        set output to output & "\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def create_event(
        title: str, start_date: str, start_time: str, duration_minutes: int = 60
    ) -> str:
        """
        Create a new calendar event.

        Args:
            title: Event title
            start_date: Date in format "MM/DD/YYYY" or "today", "tomorrow"
            start_time: Time in format "HH:MM" or "HH:MM AM/PM"
            duration_minutes: Event duration (default: 60)

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')

        return f"""
tell application "Calendar"
    set targetCalendar to first calendar whose writable is true

    -- Parse date
    if "{start_date}" is "today" then
        set eventDate to current date
    else if "{start_date}" is "tomorrow" then
        set eventDate to (current date) + (1 * days)
    else
        set eventDate to date "{start_date}"
    end if

    -- Set time
    set time of eventDate to (time of (date "{start_time}"))
    set eventEnd to eventDate + ({duration_minutes} * minutes)

    -- Create event
    set newEvent to make new event at targetCalendar with properties {{summary:"{title_escaped}", start date:eventDate, end date:eventEnd}}

    return "✅ Event created: {title_escaped} on " & (eventDate as string)
end tell
"""

    @staticmethod
    def search_events(query: str) -> str:
        """
        Search calendar events by keyword.

        Args:
            query: Search query

        Returns:
            str: AppleScript code
        """
        query_escaped = query.replace('"', '\\"')

        return f"""
tell application "Calendar"
    set searchResults to (every event of every calendar whose summary contains "{query_escaped}")
    set resultCount to count of searchResults

    if resultCount is 0 then
        return "🔍 No events found matching '{query_escaped}'"
    end if

    set output to "🔍 Found " & resultCount & " event(s) matching '{query_escaped}':\\n\\n"

    repeat with evt in searchResults
        set output to output & "• " & summary of evt & "\\n"
        set output to output & "  When: " & (start date of evt as string) & "\\n\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def list_upcoming_events(days: int = 7) -> str:
        """
        List upcoming events for next N days.

        Args:
            days: Number of days ahead (default: 7)

        Returns:
            str: AppleScript code
        """
        return f"""
tell application "Calendar"
    set startDate to current date
    set beginning of startDate to startDate - (time of startDate)
    set endDate to startDate + ({days} * days)

    set upcomingEvents to (every event of every calendar whose start date ≥ startDate and start date < endDate)
    set eventCount to count of upcomingEvents

    if eventCount is 0 then
        return "📅 No upcoming events in the next {days} days"
    end if

    set output to "📅 UPCOMING EVENTS (next {days} days, " & eventCount & " total):\\n\\n"

    repeat with evt in upcomingEvents
        set output to output & "• " & summary of evt & "\\n"
        set output to output & "  " & (start date of evt as string) & "\\n\\n"
    end repeat

    return output
end tell
"""

    @staticmethod
    def delete_event(title: str) -> str:
        """
        Delete event by title.

        Args:
            title: Event title to delete

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')

        return f"""
tell application "Calendar"
    set matchingEvents to (every event of every calendar whose summary is "{title_escaped}")
    set eventCount to count of matchingEvents

    if eventCount is 0 then
        return "❌ No event found with title: {title_escaped}"
    end if

    repeat with evt in matchingEvents
        delete evt
    end repeat

    return "🗑️ Deleted " & eventCount & " event(s): {title_escaped}"
end tell
"""

    @staticmethod
    def get_next_event() -> str:
        """
        Get the next upcoming event.

        Returns:
            str: AppleScript code
        """
        return """
tell application "Calendar"
    set now to current date
    set futureEvents to (every event of every calendar whose start date > now)

    if (count of futureEvents) is 0 then
        return "📅 No upcoming events"
    end if

    set nextEvent to item 1 of futureEvents
    set earliestStart to start date of nextEvent

    -- Find earliest event
    repeat with evt in futureEvents
        if start date of evt < earliestStart then
            set nextEvent to evt
            set earliestStart to start date of evt
        end if
    end repeat

    set output to "⏰ NEXT EVENT:\\n\\n"
    set output to output & "• " & summary of nextEvent & "\\n"
    set output to output & "  When: " & (start date of nextEvent as string) & "\\n"

    try
        set eventLocation to location of nextEvent
        if eventLocation is not "" then
            set output to output & "  Where: " & eventLocation & "\\n"
        end if
    end try

    return output
end tell
"""

    @staticmethod
    def add_event_with_location(title: str, start_date: str, start_time: str, location: str) -> str:
        """
        Create event with location.

        Args:
            title: Event title
            start_date: Date string
            start_time: Time string
            location: Event location

        Returns:
            str: AppleScript code
        """
        title_escaped = title.replace('"', '\\"')
        location_escaped = location.replace('"', '\\"')

        return f"""
tell application "Calendar"
    set targetCalendar to first calendar whose writable is true

    set eventDate to date "{start_date} {start_time}"
    set eventEnd to eventDate + (1 * hours)

    set newEvent to make new event at targetCalendar with properties {{summary:"{title_escaped}", start date:eventDate, end date:eventEnd, location:"{location_escaped}"}}

    return "✅ Event created with location: {title_escaped} at {location_escaped}"
end tell
"""
