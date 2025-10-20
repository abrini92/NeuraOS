"""
Auto-start configuration for Neura daemon.

Creates LaunchAgent (macOS) or systemd service (Linux) for auto-start on boot.
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_autostart(enable: bool = True):
    """
    Setup auto-start for Neura daemon.
    
    Args:
        enable: True to enable, False to disable
    
    Returns:
        bool: Success
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            return _setup_launchagent(enable)
        elif system == "Linux":
            return _setup_systemd(enable)
        else:
            logger.error(f"Auto-start not supported on {system}")
            return False
    
    except Exception as e:
        logger.error(f"Failed to setup auto-start: {e}")
        return False


def _setup_launchagent(enable: bool) -> bool:
    """
    Setup macOS LaunchAgent.
    
    Creates ~/Library/LaunchAgents/com.neura.daemon.plist
    """
    # LaunchAgent directory
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    
    plist_path = launch_agents_dir / "com.neura.daemon.plist"
    
    if enable:
        # Get Python executable and script path
        python_exe = sys.executable
        script_path = Path(__file__).parent.parent / "daemon" / "service.py"
        
        # Create plist content
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.neura.daemon</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>-m</string>
        <string>neura.daemon.service</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>{Path.home()}/.neura/logs/daemon.out.log</string>
    
    <key>StandardErrorPath</key>
    <string>{Path.home()}/.neura/logs/daemon.err.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
'''
        
        # Write plist file
        plist_path.write_text(plist_content)
        logger.info(f"Created LaunchAgent: {plist_path}")
        
        # Load the agent
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            check=True,
            capture_output=True
        )
        logger.info("LaunchAgent loaded")
        
        print(f"✅ Auto-start enabled")
        print(f"   Neura will start automatically on login")
        print(f"   Config: {plist_path}")
        
        return True
    
    else:
        # Disable auto-start
        if plist_path.exists():
            # Unload the agent
            subprocess.run(
                ["launchctl", "unload", str(plist_path)],
                capture_output=True
            )
            
            # Remove plist file
            plist_path.unlink()
            logger.info("LaunchAgent removed")
            
            print(f"✅ Auto-start disabled")
        
        return True


def _setup_systemd(enable: bool) -> bool:
    """
    Setup Linux systemd service.
    
    Creates ~/.config/systemd/user/neura-daemon.service
    """
    # Systemd user directory
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    
    service_path = systemd_dir / "neura-daemon.service"
    
    if enable:
        # Get Python executable
        python_exe = sys.executable
        
        # Create service content
        service_content = f'''[Unit]
Description=Neura Background Daemon
After=network.target

[Service]
Type=simple
ExecStart={python_exe} -m neura.daemon.service
Restart=always
RestartSec=10
StandardOutput=append:{Path.home()}/.neura/logs/daemon.out.log
StandardError=append:{Path.home()}/.neura/logs/daemon.err.log

[Install]
WantedBy=default.target
'''
        
        # Write service file
        service_path.write_text(service_content)
        logger.info(f"Created systemd service: {service_path}")
        
        # Reload systemd
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            check=True
        )
        
        # Enable and start service
        subprocess.run(
            ["systemctl", "--user", "enable", "neura-daemon.service"],
            check=True
        )
        subprocess.run(
            ["systemctl", "--user", "start", "neura-daemon.service"],
            check=True
        )
        
        logger.info("Systemd service enabled and started")
        
        print(f"✅ Auto-start enabled")
        print(f"   Neura will start automatically on login")
        print(f"   Config: {service_path}")
        print(f"   Status: systemctl --user status neura-daemon")
        
        return True
    
    else:
        # Disable auto-start
        if service_path.exists():
            # Stop and disable service
            subprocess.run(
                ["systemctl", "--user", "stop", "neura-daemon.service"],
                capture_output=True
            )
            subprocess.run(
                ["systemctl", "--user", "disable", "neura-daemon.service"],
                capture_output=True
            )
            
            # Remove service file
            service_path.unlink()
            
            # Reload systemd
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                capture_output=True
            )
            
            logger.info("Systemd service removed")
            
            print(f"✅ Auto-start disabled")
        
        return True


def check_autostart_status() -> bool:
    """
    Check if auto-start is enabled.
    
    Returns:
        bool: True if enabled
    """
    system = platform.system()
    
    if system == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.neura.daemon.plist"
        return plist_path.exists()
    
    elif system == "Linux":
        service_path = Path.home() / ".config" / "systemd" / "user" / "neura-daemon.service"
        return service_path.exists()
    
    return False


# CLI interface
def main():
    """CLI for auto-start setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Neura auto-start")
    parser.add_argument(
        "action",
        choices=["enable", "disable", "status"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "enable":
        setup_autostart(enable=True)
    elif args.action == "disable":
        setup_autostart(enable=False)
    elif args.action == "status":
        enabled = check_autostart_status()
        if enabled:
            print("✅ Auto-start is ENABLED")
        else:
            print("❌ Auto-start is DISABLED")


if __name__ == "__main__":
    main()
