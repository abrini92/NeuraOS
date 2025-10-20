"""
Neura CLI - Version simplifiée et fonctionnelle.
"""

import asyncio

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Neura - Local-first Cognitive Operating System")
console = Console()

API_BASE = "http://localhost:8000"


@app.command()
def status() -> None:
    """Show status of all Neura modules."""

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


@app.command()
def ask(prompt: str) -> None:
    """Ask a question to the LLM."""

    async def _ask():
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                console.print(f"[dim]🔍 Asking: {prompt}[/dim]")

                response = await client.post(
                    f"{API_BASE}/api/cortex/generate",
                    json={"prompt": prompt, "model": "mistral"},
                )

                if response.status_code == 200:
                    data = response.json()
                    console.print("\n[bold cyan]🧠 Neura:[/bold cyan]")
                    console.print(data["text"])
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_ask())


@app.command()
def remember(content: str) -> None:
    """Store information in memory."""

    async def _remember():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE}/api/memory/store",
                    json={"content": content},
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
def recall(query: str) -> None:
    """Search memories."""

    async def _recall():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE}/api/memory/recall",
                    json={"query": query, "k": 5},
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


@app.command()
def lock() -> None:
    """Lock the vault."""

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
    """Unlock the vault."""
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
    """Emergency panic mode."""

    async def _panic():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE}/api/vault/panic")

                if response.status_code == 200:
                    console.print("[red bold]🚨 PANIC MODE ACTIVATED[/red bold]")
                else:
                    console.print(f"[red]Error: {response.text}[/red]")

        except httpx.ConnectError:
            console.print("[red]Error: Cannot connect to Neura API[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(_panic())


@app.command()
def why() -> None:
    """Query the WHY Journal."""
    from neura.core.why_journal import get_why_journal

    journal = get_why_journal()
    entries = journal.query(limit=20)

    if not entries:
        console.print("[yellow]No entries found[/yellow]")
        return

    table = Table(title=f"WHY Journal ({len(entries)} entries)", show_header=True)
    table.add_column("Time", style="dim")
    table.add_column("Actor", style="cyan")
    table.add_column("Action", style="blue")
    table.add_column("Result", style="green")

    for entry in entries:
        result_style = "green" if entry.result == "SUCCESS" else "red"
        table.add_row(
            entry.timestamp.strftime("%H:%M:%S"),
            entry.actor,
            entry.action,
            f"[{result_style}]{entry.result}[/{result_style}]",
        )

    console.print(table)


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
