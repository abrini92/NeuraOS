import asyncio
from neura.motor.types import MotorAction, ActionType, OSType
from neura.policy.engine import get_policy_engine

async def main():
    engine = get_policy_engine()
    
    # Test safe action
    action = MotorAction(
        app="Notes",
        action=ActionType.TYPE_TEXT,
        text="Hello World",
        os=OSType.MAC
    )
    result = await engine.validate(action)
    print(f"✓ Safe action: allowed={result.data.allowed}")
    print(f"  Reason: {result.data.reason}")
    
    # Test unsafe app
    try:
        action2 = MotorAction(
            app="BadApp",
            action=ActionType.OPEN_APP,
            os=OSType.MAC
        )
        result2 = await engine.validate(action2)
        print(f"\n✗ Unsafe app: allowed={result2.data.allowed}")
        print(f"  Reason: {result2.data.reason}")
        print(f"  Violations: {result2.data.violations}")
    except Exception as e:
        print(f"\n✗ Error with unsafe app: {e}")
    
    # Test blocked pattern in text
    try:
        action3 = MotorAction(
            app="Terminal",
            action=ActionType.TYPE_TEXT,
            text="rm -rf /",
            os=OSType.MAC
        )
        print("\n✗ Should have blocked dangerous text!")
    except ValueError as e:
        print(f"\n✓ Blocked dangerous text: {e}")

asyncio.run(main())
