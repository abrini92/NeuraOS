# 📖 NEURA User Guide

## Getting Started with NEURA

Welcome to NEURA, your local-first cognitive operating system. This guide will help you get up and running.

## Table of Contents

1. [Installation](#installation)
2. [First Launch](#first-launch)
3. [Basic Usage](#basic-usage)
4. [Voice Commands](#voice-commands)
5. [Memory System](#memory-system)
6. [Automation](#automation)
7. [Security & Privacy](#security--privacy)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

**macOS Requirements:**
- macOS 12.0 (Monterey) or later
- Python 3.12+
- Ollama (for local LLM)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

### Step 1: Install Dependencies

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install ollama python@3.12 portaudio poetry

# Start Ollama service
brew services start ollama

# Pull a language model
ollama pull llama3.2
```

### Step 2: Install NEURA

```bash
# Clone the repository
git clone https://github.com/abrini92/NeuraOS.git
cd NeuraOS/neura

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

### Step 3: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Key Configuration Options:**

```env
# LLM Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# Memory Configuration
MEMORY_DB_PATH=./data/memory.db
QDRANT_PATH=./data/qdrant

# Vault Configuration
VAULT_DB_PATH=./data/vault.db

# Voice Configuration
VOICE_ENABLED=true
STT_ENGINE=whisper
TTS_ENGINE=pyttsx3
```

---

## First Launch

### Starting the API Server

```bash
# Start NEURA API
poetry run uvicorn neura.core.api:app --reload --port 8000

# Or use the startup script
./neura/setup.sh
```

The API will be available at: `http://localhost:8000`

### Using the CLI

```bash
# Interactive CLI
poetry run neura

# Simple CLI
poetry run python -m neura.cli_simple

# With voice enabled
poetry run neura --voice
```

### Initial Setup Wizard

On first launch, NEURA will guide you through:

1. **Master Password**: Set up vault encryption
2. **Personality**: Choose NEURA's interaction style
3. **Permissions**: Configure system access
4. **Voice Setup**: Test microphone and speakers

---

## Basic Usage

### Text Interface

```bash
# Start interactive session
poetry run neura

# Example commands
> What's the weather like?
> Remind me to call John at 3pm
> Search my notes for "project ideas"
> Create a new file called todo.txt
```

### Voice Interface

```bash
# Enable voice mode
poetry run neura --voice

# Wake word: "Hey NEURA"
# Then speak your command

# Example voice commands:
"Hey NEURA, what time is it?"
"Hey NEURA, open Safari"
"Hey NEURA, find my last email from Sarah"
```

### API Usage

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/cortex/ask",
    json={"query": "What's on my calendar today?"}
)
print(response.json())

# Store a memory
response = requests.post(
    "http://localhost:8000/memory/store",
    json={
        "content": "Meeting with team at 2pm",
        "tags": ["calendar", "work"]
    }
)
```

---

## Voice Commands

### System Commands

- **"Open [application]"** - Launch applications
- **"Close [application]"** - Quit applications
- **"What time is it?"** - Get current time
- **"Set volume to [level]"** - Adjust system volume

### File Management

- **"Create file [name]"** - Create new file
- **"Find files containing [text]"** - Search files
- **"Open [filename]"** - Open specific file
- **"Show recent files"** - List recent files

### Calendar & Reminders

- **"What's on my calendar?"** - Show today's events
- **"Add event [details]"** - Create calendar event
- **"Remind me to [task]"** - Set reminder
- **"Show my reminders"** - List active reminders

### Email & Communication

- **"Check my email"** - Get unread count
- **"Read latest email"** - Read most recent
- **"Send email to [contact]"** - Compose email
- **"Search emails for [query]"** - Search inbox

### Memory & Notes

- **"Remember that [fact]"** - Store information
- **"What do you know about [topic]?"** - Recall info
- **"Search my notes for [query]"** - Find notes
- **"Create note [content]"** - New note

---

## Memory System

### How Memory Works

NEURA uses a hybrid memory system:

1. **Short-term**: Recent conversation context
2. **Working**: Active session information
3. **Long-term**: Persistent knowledge base

### Storing Memories

```python
# Via API
POST /memory/store
{
    "content": "My favorite coffee shop is Blue Bottle",
    "tags": ["preferences", "food"],
    "importance": 0.8
}

# Via CLI
> remember that I prefer dark mode
> store this: my birthday is March 15th
```

### Searching Memories

```python
# Semantic search
POST /memory/search
{
    "query": "coffee preferences",
    "limit": 5
}

# Tag-based search
GET /memory/by-tags?tags=preferences,food
```

### Memory Privacy

- All memories are encrypted at rest
- Semantic embeddings are local (no cloud)
- You can delete memories anytime
- Export your data in JSON format

---

## Automation

### Safe Actions

NEURA can safely perform these actions:

✅ **Always Allowed:**
- Read system information
- Search files (read-only)
- Get calendar events
- Check email (read-only)
- Web searches

⚠️ **Requires Confirmation:**
- Create/modify files
- Send emails
- Create calendar events
- Open applications
- System commands

🚫 **Never Allowed:**
- Delete system files
- Modify system settings
- Access passwords
- Network configuration

### Policy Configuration

Edit `neura/policy/rules/motor_safe_actions.rego`:

```rego
# Allow specific applications
allow {
    input.action == "open_application"
    input.application in ["Safari", "Notes", "Calendar"]
}

# Require confirmation for file operations
require_confirmation {
    input.action in ["create_file", "modify_file"]
}
```

### Creating Automations

```python
# Example: Morning routine
POST /motor/execute
{
    "action": "routine",
    "steps": [
        {"action": "open_application", "app": "Calendar"},
        {"action": "get_weather"},
        {"action": "check_email"}
    ]
}
```

---

## Security & Privacy

### Encryption

- **Vault**: AES-256 encryption with Argon2 key derivation
- **Memory**: SQLite with SQLCipher
- **Transport**: TLS for API communication

### Master Password

Your master password:
- Never stored in plain text
- Required for vault access
- Can be changed anytime
- Use a strong, unique password

### Data Location

All data is stored locally:
```
~/.neura/
├── data/
│   ├── memory.db      # Encrypted memories
│   ├── vault.db       # Encrypted vault
│   └── qdrant/        # Vector embeddings
├── logs/
│   └── why.jsonl      # Audit trail
└── config/
    └── settings.json  # User preferences
```

### Audit Trail

Every action is logged in the WHY Journal:

```bash
# View audit log
poetry run python -c "from neura.core.why_journal import WHYJournal; \
    journal = WHYJournal(); \
    for entry in journal.get_recent(10): print(entry)"
```

### Privacy Best Practices

1. **Use a strong master password**
2. **Enable disk encryption** (FileVault on macOS)
3. **Regular backups** of `~/.neura/data/`
4. **Review audit logs** periodically
5. **Keep NEURA updated**

---

## Troubleshooting

### Common Issues

#### NEURA won't start

```bash
# Check Ollama is running
ollama list

# Restart Ollama
brew services restart ollama

# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
poetry install --sync
```

#### Voice not working

```bash
# Test microphone
poetry run python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_default_input_device_info())"

# Test speakers
poetry run python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('test'); engine.runAndWait()"

# Check permissions
# System Settings > Privacy & Security > Microphone
```

#### Memory search not working

```bash
# Rebuild embeddings
poetry run python -c "from neura.memory.embeddings import rebuild_embeddings; rebuild_embeddings()"

# Check Qdrant
curl http://localhost:6333/collections
```

#### API errors

```bash
# Check logs
tail -f ~/.neura/logs/api.log

# Restart API
pkill -f "uvicorn neura.core.api"
poetry run uvicorn neura.core.api:app --reload
```

### Getting Help

- **GitHub Issues**: https://github.com/abrini92/NeuraOS/issues
- **Discussions**: https://github.com/abrini92/NeuraOS/discussions
- **Documentation**: https://github.com/abrini92/NeuraOS/tree/main/docs

### Debug Mode

```bash
# Enable verbose logging
export NEURA_LOG_LEVEL=DEBUG
poetry run neura

# Check system info
poetry run python -c "from neura.core.config import get_system_info; print(get_system_info())"
```

---

## Next Steps

- 📚 Read the [API Reference](api-reference.md)
- 🏗️ Understand the [Architecture](architecture.md)
- 🔒 Review [Security Best Practices](security.md)
- 🤝 Learn how to [Contribute](../CONTRIBUTING.md)

---

**Need more help?** Join our community discussions or open an issue on GitHub!
