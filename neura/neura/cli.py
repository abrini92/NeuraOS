"""
Neura CLI - Command-line interface.

Main entry point for all Neura CLI commands.
"""

import asyncio

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="neura",
    help="Neura - Local-first Cognitive Operating System",
    add_completion=False,
)

console = Console()

# Base URL for API
API_BASE = "http://localhost:8000"


# ============================================================================
# Onboarding & Setup
# ============================================================================


@app.command()
def hello() -> None:
    """
    🌟 First-time magical onboarding experience.
    
    Interactive introduction to Neura with live demos.
    
    Example:
        neura hello
    """
    from neura.setup.wizard import run_onboarding
    
    asyncio.run(run_onboarding())


# ============================================================================
# Cortex Commands
# ============================================================================


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Question to ask"),
    model: str = typer.Option("mistral", "--model", help="Model to use"),
    stream: bool = typer.Option(False, "--stream", help="Enable streaming"),
) -> None:
    """
    Ask a question to the LLM with context from memory.

    Example:
        neura ask "Who created Neura?"
        neura ask "Explain local-first architecture" --stream
    """

    async def _ask():
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # First, recall relevant context from memory
                console.print("[dim]🔍 Searching memory...[/dim]")

                try:
                    recall_response = await client.post(
                        f"{API_BASE}/api/memory/recall",
                        json={"query": prompt, "k": 3},
                    )
                    context = []
                    if recall_response.status_code == 200:
                        memories = recall_response.json()
                        if memories:
                            console.print(f"[dim]✓ Found {len(memories)} relevant memories[/dim]")
                            context = [m["entry"]["content"] for m in memories]
                except Exception:
                    pass  # Continue without memory if unavailable

                # Generate response
                console.print("[bold cyan]🧠 Neura:[/bold cyan]")

                response = await client.post(
                    f"{API_BASE}/api/cortex/generate",
                    json={
                        "prompt": prompt,
                        "model": model,
                        "stream": stream,
                        "context": context if context else None,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    console.print(data["text"])
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API. Is it running?[/red]")
            console.print("[dim]Run: poetry run uvicorn neura.core.api:app[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_ask())


# ============================================================================
# Memory Commands
# ============================================================================


@app.command()
def remember(
    content: str = typer.Argument(..., help="Content to remember"),
    note: bool = typer.Option(False, "--note", "-n", help="Store as note"),
) -> None:
    """
    Store information in memory.

    Example:
        neura remember "Neura was created by Abderrahim"
        neura remember "Important deadline: Oct 25" --note
    """

    async def _remember():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE}/api/memory/store",
                    json={
                        "content": content,
                        "memory_type": "note" if note else "observation",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    console.print(f"[green]✓ Stored:[/green] {data['id']}")
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_remember())


@app.command()
def recall(
    query: str = typer.Argument(..., help="Search query"),
    k: int = typer.Option(5, "--k", help="Number of results"),
) -> None:
    """
    Search memories.

    Example:
        neura recall "cognitive OS"
        neura recall "deadline" --k 10
    """

    async def _recall():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE}/api/memory/recall",
                    json={"query": query, "k": k},
                )

                if response.status_code == 200:
                    results = response.json()

                    if not results:
                        console.print("[yellow]No memories found[/yellow]")
                        return

                    console.print(f"\n[bold]Found {len(results)} memories:[/bold]\n")

                    for i, result in enumerate(results, 1):
                        entry = result["entry"]
                        score = result["score"]
                        source = result["source"]

                        console.print(
                            f"[bold cyan]{i}. [{source.upper()}] Score: {score:.3f}[/bold cyan]"
                        )
                        console.print(f"   {entry['content'][:200]}")
                        console.print()
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_recall())


# ============================================================================
# Vault Commands
# ============================================================================


@app.command()
def lock() -> None:
    """
    Lock the vault.

    Example:
        neura lock
    """

    async def _lock():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE}/api/vault/lock")

                if response.status_code == 200:
                    console.print("[green]🔒 Vault locked[/green]")
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_lock())


@app.command()
def unlock() -> None:
    """
    Unlock the vault.

    Example:
        neura unlock
    """
    # Prompt for password interactively
    password = typer.prompt("Enter password", hide_input=True)

    async def _unlock():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE}/api/vault/unlock",
                    json={"password": password},
                )

                if response.status_code == 200:
                    console.print("[green]🔓 Vault unlocked[/green]")
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_unlock())


@app.command()
def panic() -> None:
    """
    Emergency panic mode - immediately lock vault.

    Example:
        neura panic
    """

    async def _panic():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE}/api/vault/panic")

                if response.status_code == 200:
                    console.print("[red bold]🚨 PANIC MODE ACTIVATED[/red bold]")
                    console.print("[yellow]Vault locked. All keys erased from memory.[/yellow]")
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_panic())


# ============================================================================
# Status & Monitoring
# ============================================================================


@app.command()
def status() -> None:
    """
    Show status of all Neura modules.

    Example:
        neura status
    """

    async def _status():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE}/health")

                if response.status_code == 200:
                    data = response.json()

                    table = Table(title="Neura Status", show_header=True)
                    table.add_column("Module", style="cyan")
                    table.add_column("Status", style="green")

                    for module, status in data["modules"].items():
                        emoji = "✅" if "loaded" in status else "❌"
                        table.add_row(f"{emoji} {module.upper()}", status)

                    console.print(table)
                    console.print(f"\n[dim]Version: {data['version']}[/dim]")
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
            console.print("[dim]Run: poetry run uvicorn neura.core.api:app[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_status())


# ============================================================================
# WHY Journal Commands
# ============================================================================


@app.command()
def why(
    action: str | None = typer.Option(None, "--action", help="Filter by action"),
    actor: str | None = typer.Option(None, "--actor", help="Filter by actor"),
    result: str | None = typer.Option(None, "--result", help="Filter by result (SUCCESS/FAILURE)"),
    since: str | None = typer.Option(None, "--since", help="Time filter (e.g., '1h', 'today')"),
    limit: int = typer.Option(20, "--limit", help="Maximum entries to show"),
    export_file: str | None = typer.Option(None, "--export-file", help="Export to file"),
) -> None:
    """
    Query the WHY Journal for audit trail.

    Example:
        neura why --action unlock_vault --result FAILURE
        neura why --since today
        neura why --actor vault --export-file audit.json
    """
    from neura.core.why_journal import get_why_journal

    journal = get_why_journal()

    # Query entries
    entries = journal.query(
        actor=actor,
        action=action,
        result=result,
        since=since,
        limit=limit,
    )

    if not entries:
        console.print("[yellow]No entries found[/yellow]")
        return

    # Display entries
    table = Table(title=f"WHY Journal ({len(entries)} entries)", show_header=True)
    table.add_column("Time", style="dim")
    table.add_column("Actor", style="cyan")
    table.add_column("Action", style="blue")
    table.add_column("Result", style="green")
    table.add_column("Summary", style="white")

    for entry in entries:
        result_style = "green" if entry.result == "SUCCESS" else "red"
        table.add_row(
            entry.timestamp.strftime("%H:%M:%S"),
            entry.actor,
            entry.action,
            f"[{result_style}]{entry.result}[/{result_style}]",
            entry.input_summary[:50] + "..."
            if len(entry.input_summary) > 50
            else entry.input_summary,
        )

    console.print(table)

    # Export if requested
    if export_file:
        journal.export(export_file, format="json")
        console.print(f"\n[green]✓ Exported to {export_file}[/green]")


# ============================================================================
# Main
# ============================================================================


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
