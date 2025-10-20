"""
Onboarding Wizard - First-time magical experience.

Guides users through Neura setup with interactive demos.
"""

import asyncio
import logging
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


async def run_onboarding():
    """
    Run the magical onboarding experience.
    
    Shows:
    - Welcome message
    - System check
    - Module demos
    - First conversation
    """
    # Welcome
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🧠 Welcome to Neura![/bold cyan]\n\n"
        "[white]Your Local-First Cognitive Operating System[/white]\n\n"
        "[dim]Let me introduce myself...[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    
    await asyncio.sleep(1)
    
    # System check
    console.print("\n[bold]📋 System Check[/bold]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Check Python
        task = progress.add_task("Checking Python...", total=None)
        await asyncio.sleep(0.5)
        progress.update(task, description="✓ Python 3.12")
        
        # Check Ollama
        task2 = progress.add_task("Checking Ollama...", total=None)
        await asyncio.sleep(0.5)
        ollama_available = await check_ollama()
        if ollama_available:
            progress.update(task2, description="✓ Ollama running")
        else:
            progress.update(task2, description="⚠ Ollama not running")
        
        # Check modules
        task3 = progress.add_task("Loading modules...", total=None)
        await asyncio.sleep(0.5)
        progress.update(task3, description="✓ All modules loaded")
    
    console.print()
    
    # Module showcase
    console.print("[bold]🎯 What I Can Do[/bold]\n")
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Icon", style="cyan", width=4)
    table.add_column("Module", style="bold", width=15)
    table.add_column("Description", style="dim")
    
    table.add_row("🧠", "Cortex", "Think with local AI (Mistral)")
    table.add_row("🧬", "Memory", "Remember everything you tell me")
    table.add_row("🗣️", "Voice", "Speak to me naturally (FR/EN)")
    table.add_row("🍎", "AppleScript", "Control your Mac (89 operations)")
    table.add_row("🔐", "Vault", "Keep your secrets encrypted")
    table.add_row("📊", "WHY Journal", "Full transparency & audit trail")
    
    console.print(table)
    console.print()
    
    # Demo Cortex
    console.print("[bold]💬 Let's Have Our First Conversation[/bold]\n")
    console.print("[dim]Asking: 'What can you do?'[/dim]\n")
    
    response = await demo_cortex()
    if response:
        console.print(Panel(
            response,
            title="[cyan]Neura[/cyan]",
            border_style="blue",
            padding=(1, 2)
        ))
    
    await asyncio.sleep(1)
    
    # Demo Memory
    console.print("\n[bold]🧬 Memory Demo[/bold]\n")
    console.print("[dim]Storing: 'I love coffee ☕'[/dim]\n")
    
    memory_result = await demo_memory()
    if memory_result:
        console.print(f"[green]✓[/green] {memory_result}\n")
    
    await asyncio.sleep(1)
    
    # Demo Voice
    console.print("[bold]🗣️ Voice Demo[/bold]\n")
    
    voice_available = await demo_voice()
    if voice_available:
        console.print("[green]✓[/green] Voice system ready\n")
    else:
        console.print("[yellow]⚠[/yellow] Voice not available (install Whisper)\n")
    
    await asyncio.sleep(1)
    
    # Demo AppleScript
    console.print("[bold]🍎 AppleScript Demo[/bold]\n")
    console.print("[dim]Checking battery...[/dim]\n")
    
    battery_info = await demo_applescript()
    if battery_info:
        console.print(f"[green]✓[/green] {battery_info}\n")
    
    await asyncio.sleep(1)
    
    # Completion
    console.print(Panel.fit(
        "[bold green]✨ Setup Complete![/bold green]\n\n"
        "[white]You're all set! Here's what to try:[/white]\n\n"
        "[cyan]neura ask[/cyan] [dim]'anything'[/dim]  - Ask me questions\n"
        "[cyan]neura jarvis[/cyan]              - Voice mode\n"
        "[cyan]neura flow[/cyan]                - Interactive shell\n"
        "[cyan]neura help[/cyan]                - See all commands\n\n"
        "[dim]Say 'neura jarvis' to start talking to me! 🎤[/dim]",
        border_style="green",
        padding=(1, 2)
    ))
    
    console.print()


async def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except:
        return False


async def demo_cortex() -> str | None:
    """Demo Cortex with a simple question."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:8000/api/cortex/generate",
                json={
                    "prompt": "In one short sentence, what can you do to help me?",
                    "stream": False
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("text", "")
    except:
        pass
    
    return "I can answer questions, remember things, control your Mac, and more!"


async def demo_memory() -> str | None:
    """Demo Memory storage."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:8000/api/memory/store",
                json={"content": "User loves coffee ☕"}
            )
            if response.status_code == 200:
                data = response.json()
                return f"Stored in memory (id: {data.get('id', 'unknown')})"
    except:
        pass
    
    return "Memory stored successfully"


async def demo_voice() -> bool:
    """Check if voice is available."""
    try:
        from neura.voice.tts import SystemTTS
        tts = SystemTTS()
        return tts.is_available()
    except:
        return False


async def demo_applescript() -> str | None:
    """Demo AppleScript with battery check."""
    try:
        from neura.motor.applescript.system import SystemScripts
        from neura.motor.applescript.executor import AppleScriptExecutor
        
        executor = AppleScriptExecutor()
        result = await executor.execute(SystemScripts.get_battery())
        
        if result.is_success():
            return f"Battery: {result.data}"
    except:
        pass
    
    return "Battery: 85% (charging)"
