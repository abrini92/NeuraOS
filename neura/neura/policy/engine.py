"""
Policy Engine - OPA-based rule evaluation.

Uses subprocess to call `opa eval` for policy decisions.
Falls back to simple Python rules if OPA not available.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from neura.core.types import Result
from neura.motor.types import MotorAction
from neura.policy.types import PolicyDecision

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    OPA-based policy engine.

    Evaluates actions against Rego policies.
    Falls back to builtin rules if OPA unavailable.
    """

    def __init__(self, rules_dir: Path | None = None) -> None:
        """
        Initialize policy engine.

        Args:
            rules_dir: Directory containing .rego files
        """
        self.rules_dir = rules_dir or Path(__file__).parent / "rules"
        self.opa_available = self._check_opa_available()

        if not self.opa_available:
            logger.warning("OPA not available, using fallback rules")

    def _check_opa_available(self) -> bool:
        """Check if OPA CLI is available."""
        try:
            result = subprocess.run(["opa", "version"], capture_output=True, timeout=2)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def validate(self, action: MotorAction) -> Result[PolicyDecision]:
        """
        Validate motor action against policies.

        Args:
            action: Motor action to validate

        Returns:
            Result containing PolicyDecision
        """
        # Prepare input for OPA
        input_data = {
            "app": action.app,
            "action": action.action.value,
            "text": self._scrub_text(action.text),
            "critical": action.critical,
            "user_approved": False,  # Will be set by confirmation flow
            "os": action.os.value if action.os else "unknown",
        }

        if self.opa_available:
            return await self._evaluate_opa(input_data)
        else:
            return await self._evaluate_fallback(input_data)

    def _scrub_text(self, text: str | None) -> str:
        """Scrub sensitive text for logging."""
        if not text:
            return ""

        if len(text) > 200:
            return text[:197] + "***redacted***"

        return text

    async def _evaluate_opa(self, input_data: dict[str, Any]) -> Result[PolicyDecision]:
        """
        Evaluate using OPA CLI.

        Args:
            input_data: Normalized input

        Returns:
            Result containing PolicyDecision
        """
        try:
            # Find motor_safe_actions.rego
            rego_file = self.rules_dir / "motor_safe_actions.rego"

            if not rego_file.exists():
                return await self._evaluate_fallback(input_data)

            # Call opa eval
            result = subprocess.run(
                ["opa", "eval", "-d", str(rego_file), "-i", "-", "data.neura.motor"],
                input=json.dumps({"input": input_data}).encode(),
                capture_output=True,
                timeout=5,
            )

            if result.returncode != 0:
                logger.error(f"OPA eval failed: {result.stderr.decode()}")
                return await self._evaluate_fallback(input_data)

            # Parse output
            output = json.loads(result.stdout)
            opa_result = output.get("result", [{}])[0].get("expressions", [{}])[0].get("value", {})

            decision = PolicyDecision(
                allowed=opa_result.get("allow", False, retry_after=None),
                reason=opa_result.get("reason", "No reason provided"),
                policy_id="motor_safe_actions",
                violations=opa_result.get("violations", []),
                inputs=input_data,
            )

            return Result.success(decision)

        except subprocess.TimeoutExpired:
            logger.error("OPA eval timeout")
            return Result.failure("Policy evaluation timeout")
        except Exception as e:
            logger.error(f"OPA eval error: {e}")
            return await self._evaluate_fallback(input_data)

    async def _evaluate_fallback(self, input_data: dict[str, Any]) -> Result[PolicyDecision]:
        """
        Fallback evaluation using Python rules.

        Implements same logic as Rego policies.
        """
        allowed_apps_mac = ["Terminal", "Notes", "TextEdit", "VSCode", "Calculator"]
        allowed_apps_linux = ["gedit", "kate", "code", "xterm", "gnome-terminal"]
        allowed_actions = ["type_text", "click", "open_app"]

        violations = []

        # Check action type
        if input_data["action"] not in allowed_actions:
            violations.append(f"Action '{input_data['action']}' not allowed")

        # Check execute_command is blocked
        if input_data["action"] == "execute_command":
            violations.append("execute_command is blocked by default")

        # Check app whitelist
        app = input_data.get("app")
        os_type = input_data.get("os", "unknown")

        if app:
            allowed_apps = allowed_apps_mac if os_type == "mac" else allowed_apps_linux
            if app not in allowed_apps:
                violations.append(f"App '{app}' not in whitelist")

        # Check text for blocked patterns
        text = input_data.get("text", "")
        blocked_patterns = ["rm -rf", "curl | bash", "sudo ", "DROP TABLE"]
        for pattern in blocked_patterns:
            if pattern in text:
                violations.append(f"Text contains blocked pattern: {pattern}")

        # Check user approval for critical actions
        if input_data.get("critical") and not input_data.get("user_approved"):
            violations.append("Critical action requires user approval")

        # Decision
        allowed = len(violations) == 0
        reason = "Allowed" if allowed else "; ".join(violations)

        decision = PolicyDecision(
            allowed=allowed,
            reason=reason,
            policy_id="fallback_rules",
            violations=violations,
            inputs=input_data,
            retry_after=None
        )

        return Result.success(decision)


# Singleton
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Get or create PolicyEngine singleton."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
