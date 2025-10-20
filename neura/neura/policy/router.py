"""
Policy API Router - REST endpoints for policy validation.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from neura.motor.types import MotorAction
from neura.policy.engine import get_policy_engine
from neura.policy.types import PolicyValidateResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/validate", response_model=PolicyValidateResponse)
async def validate_policy(action: MotorAction) -> dict:
    """
    Validate an action against policy without executing.

    Useful for pre-flight checks.

    Args:
        action: Motor action to validate

    Returns:
        PolicyValidateResponse with allow/deny decision

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/policy/validate \
          -H "Content-Type: application/json" \
          -d '{
            "app": "Terminal",
            "action": "type_text",
            "text": "ls -la"
          }'
        ```
    """
    try:
        engine = get_policy_engine()
        result = await engine.validate(action)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        decision = result.data

        return PolicyValidateResponse(
            allowed=decision.allowed,
            reason=decision.reason,
            policy_id=decision.policy_id,
            violations=decision.violations,
            retry_after=decision.retry_after,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_policy_status() -> dict[str, Any]:
    """
    Get policy engine status.

    Returns:
        Status information including OPA availability
    """
    engine = get_policy_engine()

    return {
        "status": "operational",
        "opa_available": engine.opa_available,
        "rules_dir": str(engine.rules_dir),
        "mode": "opa" if engine.opa_available else "fallback",
    }
