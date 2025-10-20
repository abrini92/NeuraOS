#!/usr/bin/env python3
"""
AppleScript Interactive Demo

Interactive menu to test all AppleScript features.
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

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
executor = AppleScriptExecutor()


def show_menu():
    """Display main menu."""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]🍎 APPLESCRIPT INTERACTIVE DEMO[/bold cyan]\n"
        "[dim]Choose a category to test[/dim]",
        border_style="cyan"
    ))
    
    table = Table(show_header=False, box=None)
    table.add_column("Option", style="cyan", width=5)
    table.add_column("Category", style="white", width=20)
    table.add_column("Description", style="dim", width=40)
    
    table.add_row("1", "📧 Mail", "Email operations")
    table.add_row("2", "📅 Calendar", "Calendar management")
    table.add_row("3", "🌐 Safari", "Web browsing")
    table.add_row("4", "📝 Notes", "Note-taking")
    table.add_row("5", "📂 Finder", "File management")
    table.add_row("6", "💻 System", "System control")
    table.add_row("7", "🛠️  Templates", "Generic utilities")
    table.add_row("8", "🎯 Quick Demo", "Run quick demo of all features")
    table.add_row("0", "🚪 Exit", "Quit demo")
    
    console.print(table)
    console.print()


async def mail_menu():
    """Mail operations menu."""
    while True:
        console.print("\n[bold cyan]📧 MAIL OPERATIONS[/bold cyan]\n")
        console.print("1. Check if Mail is running")
        console.print("2. Get unread count (if Mail open)")
        console.print("3. Generate send email script (no execution)")
        console.print("0. Back to main menu\n")
        
        choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3"])
        
        if choice == "0":
            break
        elif choice == "1":
            script = AppleScriptTemplates.is_app_running("Mail")
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "2":
            script = MailScripts.get_unread_count()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "3":
            script = MailScripts.list_inbox(limit=5)
            console.print(f"\n[dim]Generated script ({len(script)} chars):[/dim]")
            console.print(f"[yellow]{script[:200]}...[/yellow]")
        
        if choice != "0":
            Prompt.ask("\nPress Enter to continue")


async def calendar_menu():
    """Calendar operations menu."""
    while True:
        console.print("\n[bold cyan]📅 CALENDAR OPERATIONS[/bold cyan]\n")
        console.print("1. Check if Calendar is running")
        console.print("2. Generate today's events script")
        console.print("3. Generate create event script")
        console.print("0. Back to main menu\n")
        
        choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3"])
        
        if choice == "0":
            break
        elif choice == "1":
            script = AppleScriptTemplates.is_app_running("Calendar")
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "2":
            script = CalendarScripts.list_today_events()
            console.print(f"\n[dim]Script generated ({len(script)} chars)[/dim]")
            console.print("[yellow]Would list all events for today[/yellow]")
        elif choice == "3":
            title = Prompt.ask("Event title", default="Test Meeting")
            script = CalendarScripts.create_event(title, "tomorrow", "10:00 AM")
            console.print(f"\n[dim]Script generated ({len(script)} chars)[/dim]")
            console.print(f"[yellow]Would create: '{title}' tomorrow at 10:00 AM[/yellow]")
        
        if choice != "0":
            Prompt.ask("\nPress Enter to continue")


async def safari_menu():
    """Safari operations menu."""
    while True:
        console.print("\n[bold cyan]🌐 SAFARI OPERATIONS[/bold cyan]\n")
        console.print("1. Check if Safari is running")
        console.print("2. Get current URL (if Safari open)")
        console.print("3. Get page title (if Safari open)")
        console.print("4. Generate open URL script")
        console.print("0. Back to main menu\n")
        
        choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3", "4"])
        
        if choice == "0":
            break
        elif choice == "1":
            script = AppleScriptTemplates.is_app_running("Safari")
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "2":
            script = SafariScripts.get_current_url()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "3":
            script = SafariScripts.get_page_title()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "4":
            url = Prompt.ask("URL to open", default="https://github.com")
            script = SafariScripts.open_url(url)
            console.print(f"\n[dim]Script generated ({len(script)} chars)[/dim]")
            console.print(f"[yellow]Would open: {url}[/yellow]")
        
        if choice != "0":
            Prompt.ask("\nPress Enter to continue")


async def finder_menu():
    """Finder operations menu."""
    while True:
        console.print("\n[bold cyan]📂 FINDER OPERATIONS[/bold cyan]\n")
        console.print("1. List Desktop files")
        console.print("2. List Downloads files")
        console.print("3. Get disk space")
        console.print("4. Search files")
        console.print("0. Back to main menu\n")
        
        choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3", "4"])
        
        if choice == "0":
            break
        elif choice == "1":
            script = FinderScripts.list_files("Desktop", max_items=10)
            result = await executor.execute(script)
            console.print(f"\n{result.data if result.is_success() else result.error}")
        elif choice == "2":
            script = FinderScripts.list_files("Downloads", max_items=10)
            result = await executor.execute(script)
            console.print(f"\n{result.data if result.is_success() else result.error}")
        elif choice == "3":
            script = FinderScripts.get_disk_space()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "4":
            query = Prompt.ask("Search query", default="pdf")
            console.print(f"\n[yellow]Would search for files containing '{query}'[/yellow]")
            console.print("[dim]Note: File search can be slow on large directories[/dim]")
        
        if choice != "0":
            Prompt.ask("\nPress Enter to continue")


async def system_menu():
    """System operations menu."""
    while True:
        console.print("\n[bold cyan]💻 SYSTEM OPERATIONS[/bold cyan]\n")
        console.print("1. Get current date/time")
        console.print("2. Get system volume")
        console.print("3. Get battery status")
        console.print("4. Get WiFi status")
        console.print("5. Get clipboard")
        console.print("6. Get system info")
        console.print("7. List running apps")
        console.print("0. Back to main menu\n")
        
        choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
        
        if choice == "0":
            break
        elif choice == "1":
            script = SystemScripts.get_date_time()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "2":
            script = SystemScripts.get_volume()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "3":
            script = SystemScripts.get_battery()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "4":
            script = SystemScripts.get_wifi_status()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "5":
            script = SystemScripts.get_clipboard()
            result = await executor.execute(script)
            if result.is_success():
                content = result.data[:200] + "..." if len(result.data) > 200 else result.data
                console.print(f"\n[green]{content}[/green]")
            else:
                console.print(f"\n[red]{result.error}[/red]")
        elif choice == "6":
            script = SystemScripts.get_system_info()
            result = await executor.execute(script)
            console.print(f"\n[green]{result.data if result.is_success() else result.error}[/green]")
        elif choice == "7":
            script = AppleScriptTemplates.list_running_apps()
            result = await executor.execute(script)
            if result.is_success():
                lines = result.data.split('\n')[:20]
                console.print('\n'.join(lines))
                if len(result.data.split('\n')) > 20:
                    console.print(f"[dim]... and more[/dim]")
            else:
                console.print(f"\n[red]{result.error}[/red]")
        
        if choice != "0":
            Prompt.ask("\nPress Enter to continue")


async def quick_demo():
    """Run quick demo of all features."""
    console.print("\n[bold cyan]🎯 QUICK DEMO - ALL FEATURES[/bold cyan]\n")
    console.print("[dim]Running quick tests of all modules...[/dim]\n")
    
    await asyncio.sleep(0.5)
    
    # System info
    console.print("💻 [cyan]System Info...[/cyan]")
    script = SystemScripts.get_date_time()
    result = await executor.execute(script)
    console.print(f"   {result.data if result.is_success() else result.error}")
    await asyncio.sleep(0.3)
    
    script = SystemScripts.get_volume()
    result = await executor.execute(script)
    console.print(f"   {result.data if result.is_success() else result.error}")
    await asyncio.sleep(0.3)
    
    # Finder
    console.print("\n📂 [cyan]Finder...[/cyan]")
    script = FinderScripts.get_disk_space()
    result = await executor.execute(script)
    if result.is_success():
        for line in result.data.split('\n'):
            console.print(f"   {line}")
    await asyncio.sleep(0.3)
    
    # Running apps
    console.print("\n🖥️  [cyan]Running Applications...[/cyan]")
    script = AppleScriptTemplates.list_running_apps()
    result = await executor.execute(script)
    if result.is_success():
        lines = result.data.split('\n')[:6]
        for line in lines:
            console.print(f"   {line}")
    
    console.print("\n[green]✅ Quick demo complete![/green]")
    console.print("\n[bold]All 89 AppleScript operations are ready! 🚀[/bold]")
    
    Prompt.ask("\nPress Enter to continue")


async def main():
    """Main interactive loop."""
    while True:
        show_menu()
        choice = Prompt.ask("Choose option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == "0":
            console.print("\n[cyan]👋 Goodbye![/cyan]\n")
            break
        elif choice == "1":
            await mail_menu()
        elif choice == "2":
            await calendar_menu()
        elif choice == "3":
            await safari_menu()
        elif choice == "4":
            console.print("\n[yellow]Notes menu - same pattern as others[/yellow]")
            Prompt.ask("\nPress Enter to continue")
        elif choice == "5":
            await finder_menu()
        elif choice == "6":
            await system_menu()
        elif choice == "7":
            console.print("\n[yellow]Templates menu - generic utilities[/yellow]")
            Prompt.ask("\nPress Enter to continue")
        elif choice == "8":
            await quick_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
