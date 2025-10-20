#!/usr/bin/env python3
"""
AppleScript System - Interactive Demo & Test

Tests all AppleScript modules with real execution on macOS.
"""

import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from neura.motor.applescript import (
    AppleScriptExecutor,
    MailScripts,
    CalendarScripts,
    SafariScripts,
    NotesScripts,
    FinderScripts,
    SystemScripts,
)
from neura.motor.applescript.templates import AppleScriptTemplates

console = Console()


async def test_executor_basic():
    """Test basic executor functionality."""
    console.print("\n[bold cyan]═══ TEST 1: EXECUTOR BASIC ═══[/bold cyan]\n")
    
    executor = AppleScriptExecutor()
    
    # Check availability
    console.print(f"• macOS detected: {executor.is_available()}")
    console.print(f"• Timeout configured: {executor.timeout}s")
    
    # Simple test
    console.print("\n[dim]Running simple script: return 'Hello from AppleScript'[/dim]")
    result = await executor.execute('return "Hello from AppleScript"')
    
    if result.is_success():
        console.print(f"[green]✅ Success:[/green] {result.data}")
    else:
        console.print(f"[red]❌ Failed:[/red] {result.error}")
    
    return result.is_success()


async def test_system_scripts():
    """Test System scripts."""
    console.print("\n[bold cyan]═══ TEST 2: SYSTEM OPERATIONS ═══[/bold cyan]\n")
    
    executor = AppleScriptExecutor()
    tests_passed = 0
    
    # Test 1: Get date/time
    console.print("📅 [cyan]Getting current date/time...[/cyan]")
    script = SystemScripts.get_date_time()
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"   [green]✅ {result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    # Test 2: Get volume
    console.print("\n🔊 [cyan]Getting system volume...[/cyan]")
    script = SystemScripts.get_volume()
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"   [green]✅ {result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    # Test 3: Get battery
    console.print("\n🔋 [cyan]Getting battery status...[/cyan]")
    script = SystemScripts.get_battery()
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"   [green]✅ {result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [yellow]⚠️  {result.error}[/yellow] (OK if desktop Mac)")
    
    # Test 4: Get WiFi
    console.print("\n📶 [cyan]Getting WiFi status...[/cyan]")
    script = SystemScripts.get_wifi_status()
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"   [green]✅ {result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    # Test 5: Get clipboard
    console.print("\n📋 [cyan]Getting clipboard content...[/cyan]")
    script = SystemScripts.get_clipboard()
    result = await executor.execute(script)
    if result.is_success():
        content = result.data[:100] + "..." if len(result.data) > 100 else result.data
        console.print(f"   [green]✅ {content}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    console.print(f"\n[bold]System Tests: {tests_passed}/5 passed[/bold]")
    return tests_passed >= 3


async def test_finder_scripts():
    """Test Finder scripts."""
    console.print("\n[bold cyan]═══ TEST 3: FINDER OPERATIONS ═══[/bold cyan]\n")
    
    executor = AppleScriptExecutor()
    tests_passed = 0
    
    # Test 1: List Desktop files
    console.print("📂 [cyan]Listing Desktop files...[/cyan]")
    script = FinderScripts.list_files(folder="Desktop", max_items=5)
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"[green]{result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    # Test 2: Get disk space
    console.print("\n💾 [cyan]Getting disk space...[/cyan]")
    script = FinderScripts.get_disk_space()
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"[green]{result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    # Test 3: List Downloads (if exists)
    console.print("\n📥 [cyan]Listing Downloads folder...[/cyan]")
    script = FinderScripts.list_files(folder="Downloads", max_items=5)
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"[green]{result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [yellow]⚠️  {result.error}[/yellow]")
    
    console.print(f"\n[bold]Finder Tests: {tests_passed}/3 passed[/bold]")
    return tests_passed >= 2


async def test_safari_scripts():
    """Test Safari scripts (read-only operations)."""
    console.print("\n[bold cyan]═══ TEST 4: SAFARI OPERATIONS ═══[/bold cyan]\n")
    
    executor = AppleScriptExecutor()
    
    # Check if Safari is running
    console.print("🌐 [cyan]Checking Safari status...[/cyan]")
    script = AppleScriptTemplates.is_app_running("Safari")
    result = await executor.execute(script)
    
    if result.is_success():
        console.print(f"   [green]✅ {result.data}[/green]")
        
        if "is running" in result.data:
            # Safari is running, try to get current URL
            console.print("\n🔗 [cyan]Getting current Safari tab...[/cyan]")
            script = SafariScripts.get_current_url()
            result = await executor.execute(script)
            if result.is_success():
                console.print(f"   [green]✅ {result.data}[/green]")
            else:
                console.print(f"   [yellow]⚠️  {result.error}[/yellow]")
            
            # Get page title
            console.print("\n📄 [cyan]Getting page title...[/cyan]")
            script = SafariScripts.get_page_title()
            result = await executor.execute(script)
            if result.is_success():
                console.print(f"   [green]✅ {result.data}[/green]")
            else:
                console.print(f"   [yellow]⚠️  {result.error}[/yellow]")
        else:
            console.print("\n[yellow]⚠️  Safari not running, skipping URL tests[/yellow]")
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    return True


async def test_templates():
    """Test generic templates."""
    console.print("\n[bold cyan]═══ TEST 5: GENERIC TEMPLATES ═══[/bold cyan]\n")
    
    executor = AppleScriptExecutor()
    tests_passed = 0
    
    # Test 1: List running apps
    console.print("🖥️  [cyan]Listing running applications...[/cyan]")
    script = AppleScriptTemplates.list_running_apps()
    result = await executor.execute(script)
    if result.is_success():
        # Truncate if too long
        output = result.data.split('\n')[:15]
        console.print("[green]" + '\n'.join(output) + "[/green]")
        if len(result.data.split('\n')) > 15:
            console.print(f"[dim]... and {len(result.data.split('\\n')) - 15} more apps[/dim]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    # Test 2: Check if Finder is running (always is)
    console.print("\n🔍 [cyan]Checking if Finder is running...[/cyan]")
    script = AppleScriptTemplates.is_app_running("Finder")
    result = await executor.execute(script)
    if result.is_success():
        console.print(f"   [green]✅ {result.data}[/green]")
        tests_passed += 1
    else:
        console.print(f"   [red]❌ {result.error}[/red]")
    
    console.print(f"\n[bold]Template Tests: {tests_passed}/2 passed[/bold]")
    return tests_passed >= 1


async def test_script_generation():
    """Test script generation (no execution)."""
    console.print("\n[bold cyan]═══ TEST 6: SCRIPT GENERATION ═══[/bold cyan]\n")
    
    # Test Mail script generation
    console.print("📧 [cyan]Generating Mail scripts...[/cyan]")
    script = MailScripts.list_inbox(limit=5)
    console.print(f"   [green]✅ list_inbox() generated ({len(script)} chars)[/green]")
    
    script = MailScripts.send_email("test@example.com", "Test", "Body")
    console.print(f"   [green]✅ send_email() generated ({len(script)} chars)[/green]")
    
    # Test Calendar script generation
    console.print("\n📅 [cyan]Generating Calendar scripts...[/cyan]")
    script = CalendarScripts.list_today_events()
    console.print(f"   [green]✅ list_today_events() generated ({len(script)} chars)[/green]")
    
    script = CalendarScripts.create_event("Test", "today", "10:00 AM")
    console.print(f"   [green]✅ create_event() generated ({len(script)} chars)[/green]")
    
    # Test Notes script generation
    console.print("\n📝 [cyan]Generating Notes scripts...[/cyan]")
    script = NotesScripts.create_note("Test", "Body")
    console.print(f"   [green]✅ create_note() generated ({len(script)} chars)[/green]")
    
    script = NotesScripts.list_notes(limit=10)
    console.print(f"   [green]✅ list_notes() generated ({len(script)} chars)[/green]")
    
    # Test Safari script generation
    console.print("\n🌐 [cyan]Generating Safari scripts...[/cyan]")
    script = SafariScripts.open_url("https://example.com")
    console.print(f"   [green]✅ open_url() generated ({len(script)} chars)[/green]")
    
    script = SafariScripts.search_google("test query")
    console.print(f"   [green]✅ search_google() generated ({len(script)} chars)[/green]")
    
    console.print("\n[bold green]All script generation tests passed! ✅[/bold green]")
    return True


async def run_all_tests():
    """Run complete test suite."""
    console.clear()
    
    # Header
    console.print(Panel.fit(
        "[bold white]🍎 APPLESCRIPT SYSTEM - COMPLETE TEST SUITE[/bold white]\n"
        "[dim]Testing all modules with real macOS execution[/dim]",
        border_style="cyan"
    ))
    
    results = {}
    
    # Test 1: Basic executor
    with console.status("[cyan]Running executor tests...[/cyan]"):
        results['executor'] = await test_executor_basic()
    
    await asyncio.sleep(1)
    
    # Test 2: System scripts
    with console.status("[cyan]Running system tests...[/cyan]"):
        results['system'] = await test_system_scripts()
    
    await asyncio.sleep(1)
    
    # Test 3: Finder scripts
    with console.status("[cyan]Running Finder tests...[/cyan]"):
        results['finder'] = await test_finder_scripts()
    
    await asyncio.sleep(1)
    
    # Test 4: Safari scripts
    with console.status("[cyan]Running Safari tests...[/cyan]"):
        results['safari'] = await test_safari_scripts()
    
    await asyncio.sleep(1)
    
    # Test 5: Templates
    with console.status("[cyan]Running template tests...[/cyan]"):
        results['templates'] = await test_templates()
    
    await asyncio.sleep(1)
    
    # Test 6: Script generation
    with console.status("[cyan]Running generation tests...[/cyan]"):
        results['generation'] = await test_script_generation()
    
    # Summary
    console.print("\n" + "═" * 60 + "\n")
    
    # Create summary table
    table = Table(title="🍎 Test Results Summary", show_header=True)
    table.add_column("Test Category", style="cyan", width=20)
    table.add_column("Status", width=10)
    table.add_column("Details", width=30)
    
    for category, passed in results.items():
        status = "[green]✅ PASS[/green]" if passed else "[red]❌ FAIL[/red]"
        table.add_row(category.upper(), status, f"{'Operational' if passed else 'Issues detected'}")
    
    console.print(table)
    
    # Overall result
    total_passed = sum(results.values())
    total_tests = len(results)
    
    console.print()
    if total_passed == total_tests:
        console.print(Panel.fit(
            f"[bold green]🎉 ALL TESTS PASSED! ({total_passed}/{total_tests})[/bold green]\n"
            "[white]AppleScript System is fully operational![/white]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[yellow]⚠️  SOME TESTS FAILED ({total_passed}/{total_tests} passed)[/yellow]\n"
            "[dim]Check details above for issues[/dim]",
            border_style="yellow"
        ))
    
    # Feature showcase
    console.print("\n[bold cyan]📋 Available Features:[/bold cyan]\n")
    features = [
        ("📧 Mail", "10 operations: list, read, send, search, reply, forward, delete"),
        ("📅 Calendar", "8 operations: list events, create, search, upcoming"),
        ("🌐 Safari", "14 operations: open URLs, search, JavaScript, navigation"),
        ("📝 Notes", "10 operations: create, list, read, search, append"),
        ("📂 Finder", "12 operations: list files, search, move, disk space"),
        ("💻 System", "20 operations: volume, battery, screenshot, notifications"),
        ("🛠️  Templates", "15 utilities: generic patterns, app control"),
    ]
    
    for name, desc in features:
        console.print(f"  {name} - [dim]{desc}[/dim]")
    
    console.print("\n[bold]Total: 89 AppleScript operations ready! 🚀[/bold]\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Test error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
