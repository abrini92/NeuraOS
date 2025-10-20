#!/usr/bin/env python3
"""
Neura CLI - Version fonctionnelle sans Typer.

Utilise argparse pour éviter les bugs Typer/Click.
"""

import argparse
import asyncio
import sys

import httpx
from rich.console import Console
from rich.table import Table

console = Console()
API_BASE = "http://localhost:8000"


async def status_command() -> None:
    """Show status of all Neura modules."""
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


async def ask_command(prompt: str) -> None:
    """Ask a question to the LLM."""
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


async def remember_command(content: str) -> None:
    """Store information in memory."""
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


async def recall_command(query: str) -> None:
    """Search memories."""
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


async def why_command(
    actor=None,
    action=None,
    result=None,
    since=None,
    limit=20,
    stats=False,
    export_path=None,
    search=None,
) -> None:
    """Query the WHY Journal with filters."""
    from neura.core.why_journal import get_why_journal

    journal = get_why_journal()

    # Stats mode
    if stats:
        stats_data = journal.stats()
        total = stats_data["total_entries"]
        successes = stats_data["successes"]
        failures = stats_data["failures"]
        success_rate = (successes / total * 100) if total > 0 else 0.0

        console.print("\n[bold]WHY Journal Statistics[/bold]\n")
        console.print(f"Total entries: [cyan]{total}[/cyan]")
        console.print(f"Successes: [green]{successes}[/green]")
        console.print(f"Failures: [red]{failures}[/red]")
        console.print(f"Success rate: [yellow]{success_rate:.1f}%[/yellow]\n")

        console.print("[bold]By Actor:[/bold]")
        for actor_name, count in sorted(
            stats_data["actors"].items(), key=lambda x: x[1], reverse=True
        ):
            console.print(f"  {actor_name}: {count}")

        console.print("\n[bold]By Action:[/bold]")
        for action_name, count in sorted(
            stats_data["actions"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            console.print(f"  {action_name}: {count}")

        return

    # Export mode
    if export_path:
        format_type = "csv" if export_path.endswith(".csv") else "json"
        success = journal.export(export_path, format=format_type)
        if success:
            console.print(f"[green]✓ Exported to {export_path}[/green]")
        else:
            console.print("[red]✗ Export failed[/red]")
        return

    # Query with filters
    entries = journal.query(actor=actor, action=action, result=result, since=since, limit=limit)

    # Search filter (client-side)
    if search:
        search_lower = search.lower()
        entries = [
            e
            for e in entries
            if (
                search_lower in e.actor.lower()
                or search_lower in e.action.lower()
                or search_lower in e.input_summary.lower()
            )
        ]

    if not entries:
        console.print("[yellow]No entries found[/yellow]")
        return

    # Build filter description
    filters = []
    if actor:
        filters.append(f"actor={actor}")
    if action:
        filters.append(f"action={action}")
    if result:
        filters.append(f"result={result}")
    if since:
        filters.append(f"since={since}")
    if search:
        filters.append(f"search={search}")

    filter_str = f" ({', '.join(filters)})" if filters else ""

    table = Table(title=f"WHY Journal ({len(entries)} entries{filter_str})", show_header=True)
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


async def motor_run_command(
    app: str,
    action: str,
    text: str | None = None,
    x: int | None = None,
    y: int | None = None,
    critical: bool = False,
    dry_run: bool = False,
) -> None:
    """Execute a motor action."""
    import os

    from neura.motor.executor import MotorExecutor
    from neura.motor.types import ActionType, MotorAction, OSType
    from neura.policy.engine import get_policy_engine

    try:
        # Create action
        action_obj = MotorAction(
            app=app,
            action=ActionType(action),
            text=text,
            x=x,
            y=y,
            critical=critical,
            os=OSType.MAC if os.uname().sysname == "Darwin" else OSType.LINUX,
        )

        # Validate with policy
        console.print("[dim]🔍 Checking policy...[/dim]")
        policy = get_policy_engine()
        decision = await policy.validate(action_obj)

        if not decision.data.allowed:
            console.print(f"[red]❌ Blocked by policy:[/red] {decision.data.reason}")
            if decision.data.violations:
                for violation in decision.data.violations:
                    console.print(f"  [yellow]• {violation}[/yellow]")
            sys.exit(1)

        console.print("[green]✓ Policy check passed[/green]")

        # Execute
        executor = MotorExecutor(dry_run=dry_run)
        result = await executor.execute(action_obj)

        if result.data.status == "SUCCESS":
            console.print(f"[green]✓ Success:[/green] {result.data.reason}")
            console.print(f"[dim]Duration: {result.data.duration_ms:.1f}ms[/dim]")
        elif result.data.status == "BLOCKED":
            console.print(f"[yellow]⚠ Blocked:[/yellow] {result.data.reason}")
            console.print(f"[dim]Trace ID: {result.data.trace_id}[/dim]")
        else:
            console.print(f"[red]❌ Failed:[/red] {result.data.reason}")
            sys.exit(1)

    except ValueError as e:
        console.print(f"[red]❌ Validation error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


async def policy_validate_command(app: str, action: str, text: str | None = None) -> None:
    """Validate an action against policy."""
    import os

    from neura.motor.types import ActionType, MotorAction, OSType
    from neura.policy.engine import get_policy_engine

    try:
        # Create action
        action_obj = MotorAction(
            app=app,
            action=ActionType(action),
            text=text or "",
            os=OSType.MAC if os.uname().sysname == "Darwin" else OSType.LINUX,
        )

        # Validate
        engine = get_policy_engine()
        result = await engine.validate(action_obj)

        decision = result.data

        if decision.allowed:
            console.print("[green]✓ ALLOWED[/green]")
            console.print(f"  Reason: {decision.reason}")
        else:
            console.print("[red]✗ DENIED[/red]")
            console.print(f"  Reason: {decision.reason}")
            if decision.violations:
                console.print("\n  [yellow]Violations:[/yellow]")
                for violation in decision.violations:
                    console.print(f"    • {violation}")

        console.print(f"\n[dim]Policy: {decision.policy_id}[/dim]")

    except ValueError as e:
        console.print(f"[red]❌ Validation error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


async def flow_command(
    save_history: bool = True, context_size: int = 2048, voice_mode: bool = False
) -> None:
    """Launch interactive Flow shell."""
    from neura.flow.repl import start_repl

    try:
        await start_repl(
            save_history=save_history, context_size=context_size, voice_mode=voice_mode
        )
    except Exception as e:
        console.print(f"[red]❌ Flow error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def voice_command(args) -> None:
    """Handle voice subcommands."""
    import tempfile

    from neura.voice.recorder import AudioRecorder
    from neura.voice.stt import WhisperSTT
    from neura.voice.tts import SystemTTS

    try:
        if args.voice_command == "speak":
            # Text-to-speech
            text = " ".join(args.text)
            tts = SystemTTS()

            if not tts.is_available():
                console.print("[yellow]⚠ TTS not available on this system[/yellow]")
                sys.exit(1)

            console.print(f"[cyan]🔊 Speaking:[/cyan] {text}")
            result = await tts.synthesize(text)

            if result.is_failure():
                console.print(f"[red]❌ TTS error:[/red] {result.error}")
                sys.exit(1)

            console.print("[green]✓ Speech completed[/green]")

        elif args.voice_command == "listen":
            # Record and transcribe
            recorder = AudioRecorder()
            stt = WhisperSTT()

            console.print(f"[cyan]🎤 Recording for {args.duration}s...[/cyan]")
            result = recorder.record(duration=args.duration)

            if result.is_failure():
                console.print(f"[red]❌ Recording error:[/red] {result.error}")
                sys.exit(1)

            audio = result.data
            console.print("[green]✓ Recording complete[/green]")

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                save_result = recorder.save_wav(audio, tmp.name)
                if save_result.is_failure():
                    console.print(f"[red]❌ Save error:[/red] {save_result.error}")
                    sys.exit(1)

                # Transcribe
                if stt.is_available():
                    console.print("[cyan]📝 Transcribing...[/cyan]")
                    trans_result = await stt.transcribe(tmp.name)

                    if trans_result.is_success():
                        console.print(f"[green]You said:[/green] {trans_result.data.text}")
                    else:
                        console.print(f"[red]❌ Transcription error:[/red] {trans_result.error}")
                else:
                    console.print("[yellow]⚠ Whisper not installed[/yellow]")
                    console.print("[dim]Install with: pip install openai-whisper[/dim]")

                # Cleanup
                import os

                os.unlink(tmp.name)

        elif args.voice_command == "transcribe":
            # Transcribe existing file
            stt = WhisperSTT()

            if not stt.is_available():
                console.print("[yellow]⚠ Whisper not installed[/yellow]")
                console.print("[dim]Install with: pip install openai-whisper[/dim]")
                sys.exit(1)

            console.print(f"[cyan]📝 Transcribing:[/cyan] {args.file}")
            result = await stt.transcribe(args.file)

            if result.is_failure():
                console.print(f"[red]❌ Error:[/red] {result.error}")
                sys.exit(1)

            console.print(f"[green]Transcription:[/green]\n{result.data.text}")

        else:
            console.print("[red]❌ Unknown voice command[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Voice error:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="neura",
        description="Neura - Local-first Cognitive Operating System",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status command
    subparsers.add_parser("status", help="Show status of all Neura modules")

    # ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question to the LLM")
    ask_parser.add_argument("prompt", help="Question to ask")

    # remember command
    remember_parser = subparsers.add_parser("remember", help="Store information in memory")
    remember_parser.add_argument("content", help="Content to remember")

    # recall command
    recall_parser = subparsers.add_parser("recall", help="Search memories")
    recall_parser.add_argument("query", help="Search query")

    # why command
    why_parser = subparsers.add_parser("why", help="Query the WHY Journal")
    why_parser.add_argument("--actor", help="Filter by actor")
    why_parser.add_argument("--action", help="Filter by action")
    why_parser.add_argument("--result", help="Filter by result")
    why_parser.add_argument("--since", help="Filter by time (e.g., '2h', 'today')")
    why_parser.add_argument("--limit", type=int, default=20, help="Max entries")
    why_parser.add_argument("--stats", action="store_true", help="Show statistics")
    why_parser.add_argument("--export", dest="export_path", help="Export to file (json/csv)")
    why_parser.add_argument("--search", help="Search keyword")

    # motor command
    motor_parser = subparsers.add_parser("motor", help="Motor automation")
    motor_parser.add_argument("--app", help="Target application")
    motor_parser.add_argument(
        "--action", required=True, choices=["type_text", "click", "open_app"], help="Action type"
    )
    motor_parser.add_argument("--text", help="Text to type")
    motor_parser.add_argument("--x", type=int, help="X coordinate")
    motor_parser.add_argument("--y", type=int, help="Y coordinate")
    motor_parser.add_argument(
        "--critical", action="store_true", help="Mark as critical (requires confirmation)"
    )
    motor_parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (don't actually execute)"
    )

    # policy command
    policy_parser = subparsers.add_parser("policy", help="Policy validation")
    policy_parser.add_argument("--app", required=True, help="Target application")
    policy_parser.add_argument(
        "--action", required=True, choices=["type_text", "click", "open_app"], help="Action type"
    )
    policy_parser.add_argument("--text", help="Text to type/check")

    # flow command
    flow_parser = subparsers.add_parser("flow", help="Interactive Flow shell")
    flow_parser.add_argument("--no-history", action="store_true", help="Disable command history")
    flow_parser.add_argument("--context-size", type=int, default=2048, help="Context window size")
    flow_parser.add_argument("--voice", action="store_true", help="Enable voice mode (Jarvis)")

    # hello command (onboarding)
    subparsers.add_parser("hello", help="🌟 First-time magical onboarding")

    # jarvis command (shortcut for flow --voice)
    subparsers.add_parser("jarvis", help="Start Jarvis voice mode")

    # voice command
    voice_parser = subparsers.add_parser("voice", help="Voice operations")
    voice_subs = voice_parser.add_subparsers(dest="voice_command", help="Voice subcommands")

    # voice speak
    speak_parser = voice_subs.add_parser("speak", help="Text-to-speech")
    speak_parser.add_argument("text", nargs="+", help="Text to speak")

    # voice listen
    listen_parser = voice_subs.add_parser("listen", help="Record and transcribe audio")
    listen_parser.add_argument(
        "--duration", type=float, default=5.0, help="Recording duration (seconds)"
    )

    # voice transcribe
    transcribe_parser = voice_subs.add_parser("transcribe", help="Transcribe audio file")
    transcribe_parser.add_argument("file", help="Audio file path")

    # daemon command
    subparsers.add_parser("daemon", help="Start background daemon (menu bar + hotkey + wake word)")

    # autostart command
    autostart_parser = subparsers.add_parser("autostart", help="Setup auto-start on boot")
    autostart_parser.add_argument(
        "--enable", action="store_true", help="Enable auto-start"
    )
    autostart_parser.add_argument(
        "--disable", dest="enable", action="store_false", help="Disable auto-start"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "status":
        asyncio.run(status_command())
    elif args.command == "ask":
        asyncio.run(ask_command(args.prompt))
    elif args.command == "remember":
        asyncio.run(remember_command(args.content))
    elif args.command == "recall":
        asyncio.run(recall_command(args.query))
    elif args.command == "why":
        asyncio.run(
            why_command(
                actor=args.actor,
                action=args.action,
                result=args.result,
                since=args.since,
                limit=args.limit,
                stats=args.stats,
                export_path=args.export_path,
                search=args.search,
            )
        )
    elif args.command == "motor":
        asyncio.run(
            motor_run_command(
                app=args.app,
                action=args.action,
                text=args.text,
                x=args.x,
                y=args.y,
                critical=args.critical,
                dry_run=args.dry_run,
            )
        )
    elif args.command == "policy":
        asyncio.run(policy_validate_command(app=args.app, action=args.action, text=args.text))
    elif args.command == "flow":
        asyncio.run(
            flow_command(
                save_history=not args.no_history,
                context_size=args.context_size,
                voice_mode=args.voice,
            )
        )
    elif args.command == "hello":
        # Onboarding wizard
        from neura.setup.wizard import run_onboarding
        asyncio.run(run_onboarding())
    elif args.command == "jarvis":
        # Jarvis mode = Flow with voice enabled
        asyncio.run(flow_command(save_history=True, context_size=2048, voice_mode=True))
    elif args.command == "voice":
        asyncio.run(voice_command(args))
    elif args.command == "daemon":
        # Start background daemon
        from neura.daemon.service import start_daemon
        start_daemon()
    elif args.command == "autostart":
        # Setup auto-start
        from neura.setup.autostart import setup_autostart, check_autostart_status
        if hasattr(args, 'enable'):
            setup_autostart(enable=args.enable)
        else:
            enabled = check_autostart_status()
            console.print(f"Auto-start: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
