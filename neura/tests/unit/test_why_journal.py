"""
Tests for WHY Journal query and analysis.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from neura.core.why_journal import WHYEntry, WHYJournalQuery, WHYStats


class TestWHYEntry:
    """Tests for WHYEntry model."""

    def test_why_entry_creation(self):
        """Test creating a WHY entry."""
        entry = WHYEntry(
            timestamp=datetime.now(),
            actor="vault",
            action="unlock_vault",
            input_summary="User unlocked vault",
            policy_check="PASS",
            user_approved=True,
            result="SUCCESS",
            trace_id="test-trace-123",
        )
        assert entry.actor == "vault"
        assert entry.action == "unlock_vault"
        assert entry.result == "SUCCESS"

    def test_why_entry_validation(self):
        """Test WHY entry validation."""
        # Valid entry
        entry = WHYEntry(
            timestamp=datetime.now(),
            actor="memory",
            action="store_memory",
            input_summary="Stored memory",
            policy_check="PASS",
            user_approved=False,
            result="SUCCESS",
            trace_id="trace-456",
        )
        assert entry is not None


class TestWHYJournalQuery:
    """Tests for WHYJournalQuery."""

    @pytest.fixture
    def temp_journal(self):
        """Create a temporary journal file with test data."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            # Write test entries
            now = datetime.now()
            
            # Entry 1: Successful vault unlock
            entry1 = {
                "timestamp": now.isoformat(),
                "actor": "vault",
                "action": "unlock_vault",
                "input_summary": "User unlocked vault",
                "policy_check": "PASS",
                "user_approved": True,
                "result": "SUCCESS",
                "trace_id": "trace-001",
            }
            f.write(json.dumps(entry1) + "\n")
            
            # Entry 2: Failed vault unlock
            entry2 = {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "actor": "vault",
                "action": "unlock_vault",
                "input_summary": "Failed unlock attempt",
                "policy_check": "PASS",
                "user_approved": True,
                "result": "FAILURE",
                "trace_id": "trace-002",
            }
            f.write(json.dumps(entry2) + "\n")
            
            # Entry 3: Memory store
            entry3 = {
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "actor": "memory",
                "action": "store_memory",
                "input_summary": "Stored user memory",
                "policy_check": "PASS",
                "user_approved": False,
                "result": "SUCCESS",
                "trace_id": "trace-003",
            }
            f.write(json.dumps(entry3) + "\n")
            
            # Entry 4: Motor execution
            entry4 = {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "actor": "motor",
                "action": "execute_requested",
                "input_summary": "Executed automation",
                "policy_check": "PASS",
                "user_approved": True,
                "result": "SUCCESS",
                "trace_id": "trace-004",
            }
            f.write(json.dumps(entry4) + "\n")
            
            journal_path = f.name
        
        yield journal_path
        
        # Cleanup
        Path(journal_path).unlink(missing_ok=True)

    def test_journal_init(self, temp_journal):
        """Test journal initialization."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        assert journal.journal_path == Path(temp_journal)

    def test_query_all_entries(self, temp_journal):
        """Test querying all entries."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        entries = journal.query()
        assert len(entries) == 4

    def test_query_by_actor(self, temp_journal):
        """Test filtering by actor."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        # Query vault entries
        vault_entries = journal.query(actor="vault")
        assert len(vault_entries) == 2
        assert all(e.actor == "vault" for e in vault_entries)
        
        # Query memory entries
        memory_entries = journal.query(actor="memory")
        assert len(memory_entries) == 1
        assert memory_entries[0].actor == "memory"

    def test_query_by_action(self, temp_journal):
        """Test filtering by action."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        unlock_entries = journal.query(action="unlock_vault")
        assert len(unlock_entries) == 2
        assert all(e.action == "unlock_vault" for e in unlock_entries)

    def test_query_by_result(self, temp_journal):
        """Test filtering by result."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        # Query successes
        success_entries = journal.query(result="SUCCESS")
        assert len(success_entries) == 3
        assert all(e.result == "SUCCESS" for e in success_entries)
        
        # Query failures
        failure_entries = journal.query(result="FAILURE")
        assert len(failure_entries) == 1
        assert failure_entries[0].result == "FAILURE"

    def test_query_with_limit(self, temp_journal):
        """Test limiting results."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        entries = journal.query(limit=2)
        assert len(entries) == 2

    def test_query_combined_filters(self, temp_journal):
        """Test combining multiple filters."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        # Query vault failures
        entries = journal.query(actor="vault", result="FAILURE")
        assert len(entries) == 1
        assert entries[0].actor == "vault"
        assert entries[0].result == "FAILURE"

    def test_query_since_hours(self, temp_journal):
        """Test filtering by time (hours)."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        # Get entries from last 30 minutes
        entries = journal.query(since="30m")
        assert len(entries) >= 1  # At least the most recent entry

    def test_query_since_today(self, temp_journal):
        """Test filtering by 'today'."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        entries = journal.query(since="today")
        assert len(entries) >= 3  # Entries from today

    def test_query_empty_journal(self):
        """Test querying an empty journal."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            journal_path = f.name
        
        try:
            journal = WHYJournalQuery(journal_path=journal_path)
            entries = journal.query()
            assert len(entries) == 0
        finally:
            Path(journal_path).unlink(missing_ok=True)

    def test_query_nonexistent_journal(self):
        """Test querying a non-existent journal."""
        journal = WHYJournalQuery(journal_path="/tmp/nonexistent_journal.jsonl")
        entries = journal.query()
        assert len(entries) == 0

    def test_get_stats(self, temp_journal):
        """Test getting journal statistics."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        stats = journal.get_stats()
        
        assert stats.total_entries == 4
        assert stats.success_count == 3
        assert stats.failure_count == 1
        assert stats.success_rate == 75.0
        
        # Check actor stats
        assert "vault" in stats.by_actor
        assert stats.by_actor["vault"] == 2
        assert "memory" in stats.by_actor
        assert stats.by_actor["memory"] == 1
        
        # Check action stats
        assert "unlock_vault" in stats.by_action
        assert stats.by_action["unlock_vault"] == 2


class TestWHYStats:
    """Tests for WHYStats model."""

    def test_stats_creation(self):
        """Test creating WHY statistics."""
        stats = WHYStats(
            total_entries=100,
            success_count=80,
            failure_count=20,
            success_rate=80.0,
            by_actor={"vault": 50, "memory": 30, "motor": 20},
            by_action={"unlock_vault": 25, "store_memory": 30, "execute": 20},
        )
        
        assert stats.total_entries == 100
        assert stats.success_rate == 80.0
        assert stats.by_actor["vault"] == 50

    def test_stats_calculation(self):
        """Test statistics calculation."""
        stats = WHYStats(
            total_entries=10,
            success_count=7,
            failure_count=3,
            success_rate=70.0,
            by_actor={},
            by_action={},
        )
        
        assert stats.success_count + stats.failure_count == stats.total_entries
        assert stats.success_rate == (stats.success_count / stats.total_entries) * 100


class TestWHYJournalIntegration:
    """Integration tests for WHY Journal."""

    @pytest.fixture
    def temp_journal(self):
        """Create a temporary journal file with test data."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            # Write test entries
            now = datetime.now()
            
            # Entry 1: Successful vault unlock
            entry1 = {
                "timestamp": now.isoformat(),
                "actor": "vault",
                "action": "unlock_vault",
                "input_summary": "User unlocked vault",
                "policy_check": "PASS",
                "user_approved": True,
                "result": "SUCCESS",
                "trace_id": "trace-001",
            }
            f.write(json.dumps(entry1) + "\n")
            
            # Entry 2: Failed vault unlock
            entry2 = {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "actor": "vault",
                "action": "unlock_vault",
                "input_summary": "Failed unlock attempt",
                "policy_check": "PASS",
                "user_approved": True,
                "result": "FAILURE",
                "trace_id": "trace-002",
            }
            f.write(json.dumps(entry2) + "\n")
            
            # Entry 3: Memory store
            entry3 = {
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "actor": "memory",
                "action": "store_memory",
                "input_summary": "Stored user memory",
                "policy_check": "PASS",
                "user_approved": False,
                "result": "SUCCESS",
                "trace_id": "trace-003",
            }
            f.write(json.dumps(entry3) + "\n")
            
            # Entry 4: Motor execution
            entry4 = {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "actor": "motor",
                "action": "execute_requested",
                "input_summary": "Executed automation",
                "policy_check": "PASS",
                "user_approved": True,
                "result": "SUCCESS",
                "trace_id": "trace-004",
            }
            f.write(json.dumps(entry4) + "\n")
            
            journal_path = f.name
        
        yield journal_path
        
        # Cleanup
        Path(journal_path).unlink(missing_ok=True)

    def test_full_workflow(self, temp_journal):
        """Test complete query workflow."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        # 1. Get all entries
        all_entries = journal.query()
        assert len(all_entries) > 0
        
        # 2. Filter by actor
        vault_entries = journal.query(actor="vault")
        assert len(vault_entries) > 0
        
        # 3. Get statistics
        stats = journal.get_stats()
        assert stats.total_entries == len(all_entries)
        
        # 4. Filter by result
        failures = journal.query(result="FAILURE")
        assert stats.failure_count == len(failures)

    def test_time_based_queries(self, temp_journal):
        """Test various time-based queries."""
        journal = WHYJournalQuery(journal_path=temp_journal)
        
        # Recent entries
        recent = journal.query(since="1h")
        assert len(recent) >= 1
        
        # Today's entries
        today = journal.query(since="today")
        assert len(today) >= 3
        
        # Limited results
        limited = journal.query(limit=2)
        assert len(limited) == 2
