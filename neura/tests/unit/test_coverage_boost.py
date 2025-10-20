"""Quick coverage boost tests."""
import pytest
from neura.core.types import Result, Event
from neura.core.exceptions import NeuraError, CoreError, EventBusError
from neura.motor.types import ActionType, OSType
from neura.vault.types import VaultState
from neura.policy.types import PolicyDecision

def test_result_success():
    r = Result.success("data")
    assert r.is_success()
    assert r.data == "data"

def test_result_failure():
    r = Result.failure("error")
    assert not r.is_success()
    assert r.error == "error"

def test_event_create():
    e = Event.create("test", {"key": "val"}, "source")
    assert e.name == "test"
    assert e.source == "source"

def test_neura_error():
    err = NeuraError("test")
    assert str(err) == "test"

def test_core_error():
    err = CoreError("test")
    assert "test" in str(err)

def test_eventbus_error():
    err = EventBusError("test")
    assert "test" in str(err)

def test_action_type_values():
    assert ActionType.TYPE_TEXT.value == "type_text"
    assert ActionType.CLICK.value == "click"
    assert ActionType.OPEN_APP.value == "open_app"

def test_os_type_values():
    assert OSType.MAC.value == "mac"
    assert OSType.LINUX.value == "linux"

def test_vault_state_values():
    assert VaultState.LOCKED.value == "locked"
    assert VaultState.UNLOCKED.value == "unlocked"
    assert VaultState.PANIC.value == "panic"

def test_policy_decision_creation():
    d = PolicyDecision(
        allowed=True,
        reason="OK",
        policy_id="test",
        violations=[],
        inputs={}
    )
    assert d.allowed is True
