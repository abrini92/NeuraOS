"""
WHY Journal - Audit trail query and analysis.

Provides utilities to query and analyze the WHY Journal for audit purposes.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WHYEntry(BaseModel):
    """A WHY Journal entry."""

    timestamp: datetime
    actor: str
    action: str
    input_summary: str
    policy_check: str
    user_approved: bool
    result: str
    trace_id: str


class WHYStats(BaseModel):
    """WHY Journal statistics."""

    total_entries: int
    success_count: int
    failure_count: int
    success_rate: float
    by_actor: dict[str, int]
    by_action: dict[str, int]


class WHYJournalQuery:
    """
    Query and analyze WHY Journal entries.

    Example:
        >>> journal = WHYJournalQuery()
        >>> entries = journal.query(action="unlock_vault", result="FAILURE")
        >>> for entry in entries:
        ...     print(f"{entry.timestamp}: {entry.action} - {entry.result}")
    """

    def __init__(self, journal_path: str = "data/why_journal.jsonl") -> None:
        """
        Initialize WHY Journal query.

        Args:
            journal_path: Path to WHY Journal file
        """
        self.journal_path = Path(journal_path)
        logger.info(f"WHYJournalQuery initialized: {journal_path}")

    def query(
        self,
        actor: str | None = None,
        action: str | None = None,
        result: str | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> list[WHYEntry]:
        """
        Query WHY Journal entries.

        Args:
            actor: Filter by actor (e.g., "vault", "memory")
            action: Filter by action (e.g., "unlock_vault", "store_memory")
            result: Filter by result ("SUCCESS" or "FAILURE")
            since: Filter by time (e.g., "1h", "today", "2025-10-18")
            limit: Maximum number of entries to return

        Returns:
            List[WHYEntry]: Matching entries

        Example:
            >>> # Get failed unlock attempts today
            >>> entries = journal.query(
            ...     action="unlock_vault",
            ...     result="FAILURE",
            ...     since="today"
            ... )
        """
        if not self.journal_path.exists():
            logger.warning(f"WHY Journal not found: {self.journal_path}")
            return []

        entries = []
        cutoff_time = self._parse_since(since) if since else None

        try:
            with open(self.journal_path) as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        entry_time = datetime.fromisoformat(data["timestamp"])

                        # Apply filters
                        if cutoff_time and entry_time < cutoff_time:
                            continue

                        if actor and data.get("actor") != actor:
                            continue

                        if action and data.get("action") != action:
                            continue

                        if result and data.get("result") != result:
                            continue

                        # Create entry
                        entry = WHYEntry(
                            timestamp=entry_time,
                            actor=data["actor"],
                            action=data["action"],
                            input_summary=data["input_summary"],
                            policy_check=data.get("policy_check", "N/A"),
                            user_approved=data.get("user_approved", False),
                            result=data["result"],
                            trace_id=data["trace_id"],
                        )
                        entries.append(entry)

                        # Apply limit
                        if limit and len(entries) >= limit:
                            break

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid WHY Journal entry: {e}")
                        continue

            logger.info(f"Found {len(entries)} matching entries")
            return entries

        except Exception as e:
            logger.error(f"Failed to query WHY Journal: {e}")
            return []

    def _parse_since(self, since: str) -> datetime:
        """
        Parse 'since' parameter to datetime.

        Args:
            since: Time specification ("1h", "30m", "today", "2025-10-18")

        Returns:
            datetime: Cutoff time
        """
        now = datetime.utcnow()

        # Relative time (e.g., "1h", "30m")
        if since.endswith("h"):
            hours = int(since[:-1])
            return now - timedelta(hours=hours)
        elif since.endswith("m"):
            minutes = int(since[:-1])
            return now - timedelta(minutes=minutes)
        elif since.endswith("d"):
            days = int(since[:-1])
            return now - timedelta(days=days)

        # Special cases
        if since.lower() == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif since.lower() == "yesterday":
            yesterday = now - timedelta(days=1)
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

        # ISO date (e.g., "2025-10-18")
        try:
            return datetime.fromisoformat(since)
        except ValueError:
            logger.warning(f"Invalid 'since' format: {since}, using 'today'")
            return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def stats(self) -> dict[str, int]:
        """
        Get statistics about WHY Journal.

        Returns:
            Dict[str, int]: Statistics
        """
        entries = self.query()

        stats = {
            "total_entries": len(entries),
            "successes": sum(1 for e in entries if e.result == "SUCCESS"),
            "failures": sum(1 for e in entries if e.result == "FAILURE"),
            "actors": {},
            "actions": {},
        }

        # Count by actor
        actors: dict[str, int] = {}
        for entry in entries:
            actors[entry.actor] = actors.get(entry.actor, 0) + 1
        stats["actors"] = actors

        # Count by action
        actions: dict[str, int] = {}
        for entry in entries:
            actions[entry.action] = actions.get(entry.action, 0) + 1
        stats["actions"] = actions

        return stats

    def get_stats(self) -> WHYStats:
        """
        Get structured statistics about WHY Journal.

        Returns:
            WHYStats: Statistics object
        """
        entries = self.query()
        
        success_count = sum(1 for e in entries if e.result == "SUCCESS")
        failure_count = sum(1 for e in entries if e.result == "FAILURE")
        total = len(entries)
        success_rate = (success_count / total * 100) if total > 0 else 0.0
        
        # Count by actor
        by_actor: dict[str, int] = {}
        for entry in entries:
            by_actor[entry.actor] = by_actor.get(entry.actor, 0) + 1
        
        # Count by action
        by_action: dict[str, int] = {}
        for entry in entries:
            by_action[entry.action] = by_action.get(entry.action, 0) + 1
        
        return WHYStats(
            total_entries=total,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            by_actor=by_actor,
            by_action=by_action,
        )

    def export(self, output_path: str, format: str = "json") -> bool:
        """
        Export WHY Journal entries.

        Args:
            output_path: Output file path
            format: Output format ("json" or "csv")

        Returns:
            bool: Success
        """
        entries = self.query()

        try:
            if format == "json":
                with open(output_path, "w") as f:
                    data = [e.dict() for e in entries]
                    json.dump(data, f, indent=2, default=str)

            elif format == "csv":
                import csv

                with open(output_path, "w", newline="") as f:
                    if not entries:
                        return True

                    fieldnames = entries[0].dict().keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for entry in entries:
                        writer.writerow(entry.dict())

            else:
                logger.error(f"Unsupported format: {format}")
                return False

            logger.info(f"Exported {len(entries)} entries to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export: {e}")
            return False


# Global instance
_why_journal: WHYJournalQuery | None = None


def get_why_journal(journal_path: str = "data/why_journal.jsonl") -> WHYJournalQuery:
    """
    Get the global WHY Journal query instance.

    Args:
        journal_path: Path to journal file

    Returns:
        WHYJournalQuery: Singleton instance
    """
    global _why_journal
    if _why_journal is None:
        _why_journal = WHYJournalQuery(journal_path=journal_path)
    return _why_journal


def log_action(
    actor: str,
    action: str,
    input_summary: str,
    policy_check: str,
    user_approved: bool,
    result: str,
    trace_id: str = "",
) -> None:
    """
    Log an action to the WHY Journal.

    Args:
        actor: Who performed the action (e.g., "motor", "vault")
        action: What action was performed
        input_summary: Summary of input (max 200 chars)
        policy_check: Policy check result ("PASS", "FAIL", "N/A")
        user_approved: Whether user approved the action
        result: Result of action ("SUCCESS", "FAILURE", "PENDING", etc.)
        trace_id: Trace ID for correlation
    """
    import uuid

    if not trace_id:
        trace_id = str(uuid.uuid4())

    # Ensure data directory exists
    journal_path = Path("data/why_journal.jsonl")
    journal_path.parent.mkdir(parents=True, exist_ok=True)

    # Create entry
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "actor": actor,
        "action": action,
        "input_summary": input_summary[:200],  # Limit to 200 chars
        "policy_check": policy_check,
        "user_approved": user_approved,
        "result": result,
        "trace_id": trace_id,
    }

    # Append to journal
    try:
        with open(journal_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.debug(f"WHY: {actor}.{action} -> {result}")
    except Exception as e:
        logger.error(f"Failed to write WHY Journal: {e}")
