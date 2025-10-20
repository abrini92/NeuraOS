"""
Flow REPL - Interactive command-line interface for Neura.

Main REPL loop with prompt-toolkit, command execution, and session management.
"""

import asyncio
import logging
import uuid
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory

from neura.flow.commands import CommandRegistry
from neura.flow.completer import create_completer
from neura.flow.types import FlowCommand, FlowConfig, FlowSession
from neura.flow.ui import get_ui

logger = logging.getLogger(__name__)


class FlowREPL:
    """
    Interactive REPL for Neura Flow.

    Provides a conversational interface with auto-completion,
    history, and multi-turn conversations with Cortex.

    Example:
        >>> repl = FlowREPL()
        >>> await repl.start()
    """

    def __init__(self, config: FlowConfig | None = None, api_base: str = "http://localhost:8000") -> None:
        """
        Initialize Flow REPL.

        Args:
            config: Flow configuration (optional)
            api_base: Base URL for Neura API
        """
        self.config = config or FlowConfig()
        self.api_base = api_base
        self.ui = get_ui()

        # Create session
        self.session = FlowSession(
            session_id=str(uuid.uuid4()), context_window_size=self.config.context_window
        )

        # Command registry
        self.registry = CommandRegistry(api_base=api_base)

        # Setup prompt session
        self.prompt_session: PromptSession | None = None
        self._setup_prompt()

    def _setup_prompt(self) -> None:
        """Setup prompt-toolkit session with history and completion."""
        # Ensure history directory exists
        history_path = Path(self.config.history_file).expanduser()
        history_path.parent.mkdir(parents=True, exist_ok=True)

        # Create prompt session
        if self.config.save_history:
            history = FileHistory(str(history_path))
        else:
            history = None

        if self.config.enable_auto_completion:
            completer = create_completer()
        else:
            completer = None

        self.prompt_session = PromptSession(
            history=history,
            completer=completer,
            auto_suggest=AutoSuggestFromHistory(),
            complete_while_typing=False,
            vi_mode=False,
        )

    async def start(self) -> None:
        """
        Start the Flow REPL.

        Main loop that:
        1. Prints welcome banner
        2. Reads user input
        3. Parses and executes commands
        4. Displays responses
        5. Handles errors gracefully
        """
        # Print welcome banner
        self.ui.print_welcome()

        # Main REPL loop
        running = True

        while running:
            try:
                # Get user input
                user_input = await self._get_input()

                # Skip empty input
                if not user_input or not user_input.strip():
                    continue

                # Parse command
                command = FlowCommand.parse(user_input)

                # Execute command
                response = await self.registry.execute(command, self.session)

                # Check for exit
                if response.content == "__EXIT__":
                    running = False
                    self.ui.print_goodbye()
                    break

                # Display response
                if response.content:
                    if response.is_error():
                        self.ui.print_error(response.content, title="Error")
                    else:
                        self.ui.print_response(
                            response.content, source=response.source, markdown=True
                        )

            except KeyboardInterrupt:
                # Ctrl+C - continue to next prompt
                self.ui.console.print("\n[dim]Use /exit to quit[/dim]\n")
                continue

            except EOFError:
                # Ctrl+D - exit
                running = False
                self.ui.print_goodbye()
                break

            except Exception as e:
                # Unexpected error
                logger.error(f"REPL error: {e}", exc_info=True)
                self.ui.print_error(
                    f"Unexpected error: {str(e)}\nPlease report this bug.", title="Internal Error"
                )

        # Save session if configured
        if self.config.auto_save_conversations:
            await self._save_session()

    async def _get_input(self) -> str:
        """
        Get user input from prompt.

        Returns:
            str: User input
        """
        # Run prompt in executor to avoid blocking
        loop = asyncio.get_event_loop()

        try:
            user_input = await loop.run_in_executor(
                None, lambda: self.prompt_session.prompt("neura> ")
            )
            return user_input

        except KeyboardInterrupt:
            raise
        except EOFError:
            raise
        except Exception as e:
            logger.error(f"Input error: {e}")
            return ""

    async def _save_session(self) -> None:
        """
        Save conversation session to memory.

        Stores important conversations for future recall.
        """
        try:
            # Only save if there were meaningful interactions
            if self.session.commands_executed < 3:
                return

            # Build session summary
            summary_lines = [
                f"Flow Session {self.session.session_id[:8]}",
                f"Duration: {self.session.started_at.isoformat()}",
                f"Commands executed: {self.session.commands_executed}",
                "",
                "Conversation:",
            ]

            # Add conversation history
            for msg in self.session.conversation_history[-10:]:
                summary_lines.append(f"{msg.role}: {msg.content[:100]}")

            summary = "\n".join(summary_lines)

            # Store in memory (via API)
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(f"{self.api_base}/api/memory/store", json={"content": summary})

            logger.info(f"Session saved: {self.session.session_id}")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def start_voice_mode(self) -> None:
        """
        Start voice interaction mode (Jarvis mode).

        Continuous voice loop:
        1. Listen for speech (VAD detection)
        2. Transcribe with STT
        3. Process command/question
        4. Generate response with Cortex
        5. Speak response with TTS
        6. Loop back to step 1

        Press Ctrl+C to exit.
        """
        try:
            import os
            import tempfile

            from neura.voice.commands import VoiceCommandParser
            from neura.voice.recorder import AudioRecorder
            from neura.voice.stt import WhisperSTT
            from neura.voice.tts import SystemTTS
            from neura.voice.vad import SimpleVAD
        except ImportError as e:
            self.ui.print_error(
                f"Voice dependencies not available: {e}\n"
                "Install with: poetry add sounddevice scipy numpy",
                title="Import Error",
            )
            return

        # Initialize voice components
        recorder = AudioRecorder(sample_rate=16000)

        # Try Python API first (more reliable), fallback to CLI
        try:
            from neura.voice.stt_python import WhisperSTTPython

            stt = WhisperSTTPython(model="tiny")
            if not stt.is_available():
                from neura.voice.stt import WhisperSTT

                stt = WhisperSTT(model="tiny")
        except ImportError:
            from neura.voice.stt import WhisperSTT

            stt = WhisperSTT(model="tiny")

        tts = SystemTTS()
        vad = SimpleVAD(threshold=0.01)
        parser = VoiceCommandParser()

        # Check availability
        if not tts.is_available():
            self.ui.print_error("TTS not available on this system", title="Voice Error")
            return

        # Welcome message (bilingual)
        self.ui.console.print("\n[bold cyan]🎤 JARVIS MODE ACTIVATED / MODE JARVIS ACTIVÉ[/bold cyan]")
        self.ui.console.print("[dim]🇬🇧 English & 🇫🇷 Français supported[/dim]")
        self.ui.console.print("[dim]Say 'neura' or 'hey neura' to wake up[/dim]")
        self.ui.console.print("[dim]Dites 'neura' pour activer[/dim]")
        self.ui.console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        # Initialize context and proactive engines
        from neura.core.context import get_context_engine
        from neura.core.proactive import get_proactive_engine
        
        context_engine = get_context_engine()
        proactive_engine = get_proactive_engine()
        
        # Get initial context
        context = await context_engine.get_context()
        
        # Personalized welcome based on context
        time_greeting = ""
        if context.temporal.time_of_day.value == "morning":
            time_greeting = "Good morning! "
        elif context.temporal.time_of_day.value == "evening":
            time_greeting = "Good evening! "
        
        welcome_msg = f"{time_greeting}I'm Neura, your cognitive assistant. I'm ready to help."
        
        # Add battery warning if low
        if context.system.battery_level < 30:
            welcome_msg += f" By the way, your battery is at {context.system.battery_level}%."
        
        await tts.synthesize(welcome_msg)

        # Voice loop
        running = True
        loop_count = 0

        while running:
            try:
                # Check for proactive suggestions every 10 loops (~50 seconds)
                if loop_count % 10 == 0:
                    suggestions = await proactive_engine.get_suggestions()
                    for suggestion in suggestions:
                        if await proactive_engine.should_interrupt(suggestion):
                            formatted = proactive_engine.format_suggestion(suggestion)
                            self.ui.console.print(f"\n[yellow]{formatted}[/yellow]")
                            await tts.synthesize(suggestion.message)
                
                loop_count += 1
                
                # Record audio chunk
                self.ui.console.print("[dim]🎧 Listening...[/dim]", end="\r")

                audio_result = recorder.record(duration=5.0)

                if audio_result.is_failure():
                    logger.error(f"Recording failed: {audio_result.error}")
                    await asyncio.sleep(1)
                    continue

                audio = audio_result.data

                # Check if speech detected
                if not vad.is_speech(audio):
                    # Silence - continue listening
                    continue

                self.ui.console.print("[cyan]🎤 Speech detected...[/cyan]")

                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    save_result = recorder.save_wav(audio, tmp.name)

                    if save_result.is_failure():
                        logger.error(f"Save failed: {save_result.error}")
                        continue

                    tmp_path = tmp.name

                # Transcribe (auto-detect language: French or English)
                if stt.is_available():
                    self.ui.console.print("[dim]📝 Transcribing...[/dim]")
                    trans_result = await stt.transcribe(tmp_path, language=None)  # Auto-detect

                    # Cleanup temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass

                    if trans_result.is_failure():
                        logger.error(f"Transcription failed: {trans_result.error}")
                        await tts.synthesize("Sorry, I didn't catch that.")
                        continue

                    text = trans_result.data.text.strip()
                    detected_lang = trans_result.data.language or "en"

                    if not text:
                        continue

                    # Show detected language
                    lang_flag = "🇫🇷" if detected_lang == "fr" else "🇬🇧"
                    self.ui.console.print(f"[green]You {lang_flag}:[/green] {text}")

                    # Parse voice command
                    command = parser.parse(text)

                    # Check for exit
                    if command.name == "exit":
                        goodbye_msg = "Au revoir !" if detected_lang == "fr" else "Goodbye!"
                        await tts.synthesize(goodbye_msg)
                        running = False
                        break

                    # Execute command
                    response = await self.registry.execute(command, self.session)

                    if response.content and response.content != "__EXIT__":
                        self.ui.console.print(f"[blue]Neura:[/blue] {response.content[:200]}")

                        # Auto-store important interactions
                        from neura.memory.auto_store import get_auto_store
                        auto_store = get_auto_store()
                        await auto_store.process_interaction(
                            user_input=text,
                            assistant_response=response.content,
                            command_type=command.name
                        )

                        # Speak response with personality
                        from neura.core.personality import get_personality
                        personality = get_personality()
                        
                        # Add personality prefix for success
                        if response.success:
                            prefix = personality.get_response("success")
                            speak_text = f"{prefix}. {response.content[:500]}"
                        else:
                            speak_text = response.content[:500]
                        
                        await tts.synthesize(speak_text)

                else:
                    # STT not available
                    self.ui.console.print("[yellow]⚠ Whisper not installed[/yellow]")
                    self.ui.console.print("[dim]Install with: pip install openai-whisper[/dim]")
                    await tts.synthesize(
                        "Speech recognition not available. Please install Whisper."
                    )
                    running = False

            except KeyboardInterrupt:
                self.ui.console.print("\n[cyan]🎤 Jarvis mode stopped[/cyan]")
                await tts.synthesize("Jarvis mode stopped.")
                running = False
                break

            except Exception as e:
                logger.error(f"Voice mode error: {e}", exc_info=True)
                self.ui.console.print(f"[red]Error: {e}[/red]")
                await tts.synthesize("An error occurred.")
                await asyncio.sleep(1)


async def start_repl(
    save_history: bool = True,
    context_size: int = 2048,
    api_base: str = "http://localhost:8000",
    voice_mode: bool = False,
) -> None:
    """
    Start Flow REPL with given configuration.

    Args:
        save_history: Whether to save command history
        context_size: Context window size
        api_base: Neura API base URL
        voice_mode: Enable voice interaction mode (Jarvis)
    """
    config = FlowConfig(save_history=save_history, context_window=context_size)

    repl = FlowREPL(config=config, api_base=api_base)

    if voice_mode:
        await repl.start_voice_mode()
    else:
        await repl.start()
