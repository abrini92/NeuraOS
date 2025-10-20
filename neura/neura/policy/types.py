"""
Policy types - Models for OPA-based authorization.
"""

from typing import Any

from pydantic import BaseModel, Field


class PolicyDecision(BaseModel):
    """
    Result of policy evaluation.

    Attributes:
        allowed: Whether action is allowed
        reason: Human-readable reason for decision
        policy_id: ID of policy that made decision
        violations: List of policy violations
        retry_after: Seconds to wait before retry (for rate limits)
        inputs: Normalized inputs that were evaluated
    """

    allowed: bool = Field(..., description="Action allowed")
    reason: str = Field("", description="Decision reason")
    policy_id: str = Field(..., description="Policy ID")
    violations: list[str] = Field(default_factory=list, description="Violations")
    retry_after: int | None = Field(None, description="Retry after seconds")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Evaluated inputs")


class PolicyValidateRequest(BaseModel):
    """Request to validate action against policy."""

    policy: str = Field(..., description="Policy name")
    input_data: dict[str, Any] = Field(..., description="Input to evaluate")


class PolicyValidateResponse(BaseModel):
    """Response from policy validation."""

    allowed: bool
    reason: str
    policy_id: str
    violations: list[str] = []
    retry_after: int | None = None
