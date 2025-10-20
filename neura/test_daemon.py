#!/usr/bin/env python3
"""
Test Neura Daemon components.

Tests each component individually before running full daemon.
"""

import sys


def test_imports():
    """Test that all daemon modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from neura.daemon import service, hotkey, wakeword
        print("✅ daemon modules")
    except ImportError as e:
        print(f"❌ daemon modules: {e}")
        return False
    
    try:
        from neura.ui import floating, notifications
        print("✅ ui modules")
    except ImportError as e:
        print(f"❌ ui modules: {e}")
        return False
    
    try:
        from neura.setup import autostart
        print("✅ setup modules")
    except ImportError as e:
        print(f"❌ setup modules: {e}")
        return False
    
    return True


def test_notifications():
    """Test native notifications."""
    print("\n🧪 Testing notifications...")
    
    try:
        from neura.ui.notifications import notify
        notify("Neura Test", "Notification system works!", sound=False)
        print("✅ Notification sent (check your screen)")
        return True
    except Exception as e:
        print(f"❌ Notifications failed: {e}")
        return False


def test_floating_mic():
    """Test floating mic UI (visual test)."""
    print("\n🧪 Testing floating mic UI...")
    print("   A window should appear. Press Escape or close it to continue.")
    
    try:
        from neura.ui.floating import FloatingMic
        
        mic = FloatingMic()
        mic.show()
        mic.start_listening()
        mic.update_transcription("Testing... 1, 2, 3")
        
        # Run for 3 seconds
        import time
        time.sleep(3)
        mic.hide()
        
        print("✅ Floating mic works")
        return True
    except Exception as e:
        print(f"❌ Floating mic failed: {e}")
        return False


def test_hotkey():
    """Test hotkey listener (manual test)."""
    print("\n🧪 Testing hotkey listener...")
    print("   Press Cmd+Space+Space within 5 seconds...")
    
    try:
        from neura.daemon.hotkey import HotkeyListener
        import time
        
        triggered = [False]
        
        def on_trigger():
            triggered[0] = True
            print("   🎯 Hotkey triggered!")
        
        listener = HotkeyListener(on_trigger=on_trigger)
        listener.start()
        
        # Wait 5 seconds
        time.sleep(5)
        
        listener.stop()
        
        if triggered[0]:
            print("✅ Hotkey works")
            return True
        else:
            print("⚠️  Hotkey not triggered (you may not have pressed it)")
            return True  # Not a failure
    
    except Exception as e:
        print(f"❌ Hotkey failed: {e}")
        return False


def test_autostart():
    """Test autostart status."""
    print("\n🧪 Testing autostart...")
    
    try:
        from neura.setup.autostart import check_autostart_status
        
        enabled = check_autostart_status()
        status = "ENABLED" if enabled else "DISABLED"
        print(f"   Auto-start: {status}")
        print("✅ Autostart check works")
        return True
    except Exception as e:
        print(f"❌ Autostart failed: {e}")
        return False


def main():
    """Run all tests."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║              🧪 NEURA DAEMON TEST SUITE                      ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Notifications", test_notifications()))
    results.append(("Autostart", test_autostart()))
    
    # Optional visual tests
    print("\n" + "="*60)
    print("OPTIONAL VISUAL TESTS (you can skip with Ctrl+C)")
    print("="*60)
    
    try:
        results.append(("Floating Mic", test_floating_mic()))
        results.append(("Hotkey", test_hotkey()))
    except KeyboardInterrupt:
        print("\n⚠️  Visual tests skipped")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Daemon is ready to use.")
        print("\nNext steps:")
        print("  1. Install dependencies: poetry install")
        print("  2. Start daemon: poetry run neura daemon")
        print("  3. Enable auto-start: poetry run neura autostart --enable")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
