#!/usr/bin/env python3
"""
Pre-download Whisper model for faster first-time use.
"""

import subprocess
import tempfile
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def setup_whisper():
    """Download Whisper tiny model."""
    console.print("\n[bold cyan]🎤 Setting up Whisper for Jarvis Mode[/bold cyan]\n")
    
    console.print("[dim]Creating test audio file...[/dim]")
    
    # Create a tiny test audio file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_file = f.name
    
    # Create silent 1-second WAV file
    import wave
    import struct
    
    with wave.open(test_file, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(16000)  # 16kHz
        
        # 1 second of silence
        for _ in range(16000):
            wav.writeframes(struct.pack('<h', 0))
    
    console.print("[cyan]📥 Downloading Whisper 'tiny' model...[/cyan]")
    console.print("[dim]This will take 1-2 minutes the first time[/dim]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Downloading...", total=None)
            
            # Run whisper on test file to trigger model download
            result = subprocess.run(
                ['whisper', test_file, '--model', 'tiny', '--output_format', 'txt'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            progress.update(task, completed=True)
        
        if result.returncode == 0:
            console.print("\n[green]✅ Whisper model downloaded successfully![/green]")
            console.print("\n[bold]Ready for Jarvis mode![/bold] 🎤")
            console.print("\nRun: [cyan]poetry run neura jarvis[/cyan]\n")
        else:
            console.print(f"\n[red]❌ Error:[/red] {result.stderr}")
    
    except subprocess.TimeoutExpired:
        console.print("\n[red]❌ Download timed out. Please check your internet connection.[/red]")
    
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
    
    finally:
        # Clean up
        try:
            Path(test_file).unlink()
            Path(test_file).with_suffix('.txt').unlink(missing_ok=True)
        except:
            pass

if __name__ == "__main__":
    setup_whisper()
