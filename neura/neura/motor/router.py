"""
Motor API Router - REST endpoints for local automation.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from neura.motor.executor import get_motor_executor
from neura.motor.types import MotorAction, MotorResult, MotorStatus
from neura.policy.engine import get_policy_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/execute", response_model=MotorResult)
async def execute_action(action: MotorAction) -> dict:
    """
    Execute a motor action.

    Validates action with policy before executing.
    Critical actions return a trace_id for confirmation.

    Args:
        action: Motor action to execute

    Returns:
        MotorResult with status and trace_id

    Raises:
        HTTPException: 403 if blocked by policy, 500 if execution fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/motor/execute \
          -H "Content-Type: application/json" \
          -d '{
            "app": "Notes",
            "action": "type_text",
            "text": "Hello from Neura"
          }'
        ```
    """
    try:
        # 1. Validate with policy engine
        policy = get_policy_engine()
        policy_result = await policy.validate(action)

        if not policy_result.success:
            logger.error(f"Policy validation failed: {policy_result.error}")
            raise HTTPException(status_code=500, detail=f"Policy error: {policy_result.error}")

        decision = policy_result.data

        if not decision.allowed:
            logger.warning(f"Action blocked by policy: {decision.reason}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Action blocked by policy",
                    "reason": decision.reason,
                    "violations": decision.violations,
                },
            )

        # 2. Execute action
        executor = get_motor_executor()
        exec_result = await executor.execute(action, user_approved=False)

        if not exec_result.success:
            logger.error(f"Execution failed: {exec_result.error}")
            raise HTTPException(status_code=500, detail=exec_result.error)

        result = exec_result.data

        # 3. If critical and not approved, return requires_confirmation
        if result.status == MotorStatus.BLOCKED and action.critical:
            return MotorResult(
                status=MotorStatus.BLOCKED,
                reason="Requires user confirmation",
                duration_ms=result.duration_ms,
                trace_id=result.trace_id,
                action=action,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm/{trace_id}", response_model=MotorResult)
async def confirm_action(trace_id: str) -> dict:
    """
    Confirm and execute a critical action.

    Args:
        trace_id: Trace ID of pending action

    Returns:
        MotorResult after execution

    Raises:
        HTTPException: 404 if no pending action, 409 if conflict

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/motor/confirm/abc-123
        ```
    """
    try:
        executor = get_motor_executor()
        result = await executor.confirm(trace_id)

        if not result.success:
            raise HTTPException(
                status_code=404, detail=f"No pending action with trace_id: {trace_id}"
            )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confirmation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """
    Get motor executor status.

    Returns:
        Status information including pending confirmations
    """
    executor = get_motor_executor()

    return {
        "status": "operational",
        "dry_run": executor.dry_run,
        "pending_confirmations": len(executor.pending_confirmations),
        "failsafe_enabled": True,
    }
