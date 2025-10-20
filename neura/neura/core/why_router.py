"""
WHY Journal API Router.

Provides REST endpoints for querying and exporting WHY Journal.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from neura.core.why_journal import get_why_journal

logger = logging.getLogger(__name__)

router = APIRouter()


class WHYEntryResponse(BaseModel):
    """WHY Journal entry response."""

    timestamp: str
    actor: str
    action: str
    input_summary: str
    policy_check: str
    user_approved: bool
    result: str
    trace_id: str


class WHYStatsResponse(BaseModel):
    """WHY Journal statistics response."""

    total_entries: int
    successes: int
    failures: int
    success_rate: float
    actors: dict
    actions: dict


@router.get("/", response_model=list[WHYEntryResponse])
async def list_entries(
    actor: str | None = Query(None, description="Filter by actor"),
    action: str | None = Query(None, description="Filter by action"),
    result: str | None = Query(None, description="Filter by result"),
    since: str | None = Query(None, description="Filter by time (e.g., '2h', 'today')"),
    limit: int | None = Query(100, ge=1, le=1000, description="Max entries to return"),
):
    """
    Query WHY Journal entries with filters.

    Example:
        GET /api/why?actor=motor&result=SUCCESS&limit=10
    """
    try:
        journal = get_why_journal()
        entries = journal.query(actor=actor, action=action, result=result, since=since, limit=limit)

        return [
            WHYEntryResponse(
                timestamp=entry.timestamp.isoformat(),
                actor=entry.actor,
                action=entry.action,
                input_summary=entry.input_summary,
                policy_check=entry.policy_check,
                user_approved=entry.user_approved,
                result=entry.result,
                trace_id=entry.trace_id,
            )
            for entry in entries
        ]

    except Exception as e:
        logger.error(f"Failed to query WHY Journal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=WHYStatsResponse)
async def get_stats() -> dict:
    """
    Get WHY Journal statistics.

    Returns counts by actor, action, and success/failure rates.
    """
    try:
        journal = get_why_journal()
        stats = journal.stats()

        total = stats["total_entries"]
        successes = stats["successes"]
        success_rate = (successes / total * 100) if total > 0 else 0.0

        return WHYStatsResponse(
            total_entries=total,
            successes=successes,
            failures=stats["failures"],
            success_rate=round(success_rate, 2),
            actors=stats["actors"],
            actions=stats["actions"],
        )

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_entries(
    q: str = Query(..., description="Search keyword"), limit: int = Query(100, ge=1, le=1000)
):
    """
    Search WHY Journal entries by keyword.

    Searches in actor, action, and input_summary fields.
    """
    try:
        journal = get_why_journal()
        all_entries = journal.query(limit=limit)

        # Filter entries containing keyword
        keyword_lower = q.lower()
        matching = [
            entry
            for entry in all_entries
            if (
                keyword_lower in entry.actor.lower()
                or keyword_lower in entry.action.lower()
                or keyword_lower in entry.input_summary.lower()
            )
        ]

        return {
            "query": q,
            "total_matches": len(matching),
            "entries": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "actor": entry.actor,
                    "action": entry.action,
                    "input_summary": entry.input_summary,
                    "result": entry.result,
                    "trace_id": entry.trace_id,
                }
                for entry in matching[:limit]
            ],
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_journal(
    format: str = Query("json", regex="^(json|csv)$"),
    actor: str | None = None,
    since: str | None = None,
):
    """
    Export WHY Journal to JSON or CSV.

    Example:
        GET /api/why/export?format=json
        GET /api/why/export?format=csv&actor=motor
    """
    try:
        journal = get_why_journal()
        entries = journal.query(actor=actor, since=since)

        if format == "json":
            import json

            data = [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "actor": entry.actor,
                    "action": entry.action,
                    "input_summary": entry.input_summary,
                    "policy_check": entry.policy_check,
                    "user_approved": entry.user_approved,
                    "result": entry.result,
                    "trace_id": entry.trace_id,
                }
                for entry in entries
            ]
            content = json.dumps(data, indent=2)
            media_type = "application/json"
            filename = "why_journal.json"

        else:  # csv
            import csv
            import io

            output = io.StringIO()
            if entries:
                fieldnames = [
                    "timestamp",
                    "actor",
                    "action",
                    "input_summary",
                    "policy_check",
                    "user_approved",
                    "result",
                    "trace_id",
                ]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for entry in entries:
                    writer.writerow(
                        {
                            "timestamp": entry.timestamp.isoformat(),
                            "actor": entry.actor,
                            "action": entry.action,
                            "input_summary": entry.input_summary,
                            "policy_check": entry.policy_check,
                            "user_approved": entry.user_approved,
                            "result": entry.result,
                            "trace_id": entry.trace_id,
                        }
                    )

            content = output.getvalue()
            media_type = "text/csv"
            filename = "why_journal.csv"

        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
