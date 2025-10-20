# 🏗️ NEURA Architecture

System design and principles of NEURA Cognitive OS.

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [System Architecture](#system-architecture)
4. [Core Modules](#core-modules)
5. [Data Flow](#data-flow)
6. [Security Model](#security-model)
7. [Scalability](#scalability)

---

## Overview

NEURA is a **local-first cognitive operating system** that augments human intelligence through ethical AI. The architecture is designed around three core principles:

1. **Privacy by Design**: All data stays local
2. **Transparency**: Every decision is auditable
3. **Sovereignty**: User has complete control

---

## Design Principles

### 1. Local-First Architecture

```
┌─────────────────────────────────────┐
│         User's Machine              │
│  ┌─────────────────────────────┐   │
│  │         NEURA Core          │   │
│  │  ┌──────────────────────┐   │   │
│  │  │   Local LLM (Ollama) │   │   │
│  │  └──────────────────────┘   │   │
│  │  ┌──────────────────────┐   │   │
│  │  │  Local Vector DB     │   │   │
│  │  └──────────────────────┘   │   │
│  │  ┌──────────────────────┐   │   │
│  │  │  Encrypted Storage   │   │   │
│  │  └──────────────────────┘   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
        ↓ (Optional)
┌─────────────────────────────────────┐
│    External Services (Optional)     │
│  - Web Search                       │
│  - Calendar Sync                    │
│  - Email (IMAP)                     │
└─────────────────────────────────────┘
```

**No cloud dependencies for core functionality.**

### 2. Modular Design

Each module is:
- **Independent**: Can function standalone
- **Composable**: Works with other modules
- **Replaceable**: Can be swapped with alternatives
- **Testable**: Isolated unit tests

### 3. Event-Driven

```python
# All modules communicate via events
event_bus.emit("memory.stored", {
    "id": "mem_123",
    "content": "...",
    "tags": [...]
})

# Other modules can subscribe
@event_bus.on("memory.stored")
def on_memory_stored(event):
    # Update context, trigger actions, etc.
    pass
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │   Voice  │  │   API    │  │   GUI    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
┌───────┴─────────────┴─────────────┴─────────────┴──────────┐
│                      Core Layer                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Event Bus (PubSub)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Cortex  │  │  Memory  │  │   Vault  │  │  Policy  │   │
│  │  (LLM)   │  │  (Store) │  │  (Crypt) │  │  (OPA)   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
┌───────┴─────────────┴─────────────┴─────────────┴──────────┐
│                   Integration Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Motor   │  │   Flow   │  │  Voice   │  │   WHY    │   │
│  │ (Actions)│  │  (UI)    │  │ (STT/TTS)│  │ (Audit)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
┌───────┴─────────────┴─────────────┴─────────────┴──────────┐
│                     System Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              macOS System APIs                       │  │
│  │  (AppleScript, Finder, Calendar, Mail, etc.)        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
User Request
     ↓
┌────────────┐
│    Flow    │ ← User interface (CLI/Voice/API)
└─────┬──────┘
      ↓
┌────────────┐
│   Cortex   │ ← LLM reasoning
└─────┬──────┘
      ↓
┌────────────┐
│   Memory   │ ← Context retrieval
└─────┬──────┘
      ↓
┌────────────┐
│   Policy   │ ← Safety check
└─────┬──────┘
      ↓
┌────────────┐
│   Motor    │ ← Action execution
└─────┬──────┘
      ↓
┌────────────┐
│    WHY     │ ← Audit logging
└────────────┘
```

---

## Core Modules

### 1. Core (`neura/core/`)

**Purpose**: Foundation layer with shared utilities.

**Components**:
- `api.py`: FastAPI application
- `config.py`: Configuration management
- `events.py`: Event bus implementation
- `types.py`: Shared type definitions
- `exceptions.py`: Custom exceptions
- `context.py`: Request context management

**Key Features**:
- Centralized configuration
- Event-driven communication
- Type safety with Pydantic
- Structured error handling

### 2. Cortex (`neura/cortex/`)

**Purpose**: LLM reasoning engine.

**Architecture**:
```python
class CortexEngine:
    def __init__(self):
        self.llm = OllamaClient()
        self.context_manager = ContextManager()
        self.prompt_builder = PromptBuilder()
    
    async def ask(self, query: str) -> Response:
        # 1. Build context from memory
        context = await self.context_manager.get_context(query)
        
        # 2. Build prompt
        prompt = self.prompt_builder.build(query, context)
        
        # 3. Query LLM
        response = await self.llm.generate(prompt)
        
        # 4. Post-process
        return self.post_process(response)
```

**Features**:
- Streaming responses
- Context-aware prompting
- Token management
- Model switching

### 3. Memory (`neura/memory/`)

**Purpose**: Hybrid memory system.

**Architecture**:
```
┌─────────────────────────────────────┐
│         Memory System               │
│  ┌─────────────────────────────┐   │
│  │   SQLite FTS5 (Full-Text)   │   │
│  │   - Fast keyword search     │   │
│  │   - Structured queries      │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │   Qdrant (Vector Search)    │   │
│  │   - Semantic similarity     │   │
│  │   - Embeddings              │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │   Graph (Relationships)     │   │
│  │   - Entity connections      │   │
│  │   - Knowledge graph         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Storage Strategy**:
1. **Hot**: Recent memories (in-memory cache)
2. **Warm**: Frequently accessed (SQLite)
3. **Cold**: Archived (compressed)

### 4. Vault (`neura/vault/`)

**Purpose**: Encrypted secret storage.

**Security Layers**:
```
User Password
     ↓
Argon2 KDF (memory-hard)
     ↓
Master Key (256-bit)
     ↓
AES-256-GCM Encryption
     ↓
SQLCipher Database
```

**Features**:
- Per-secret encryption
- Key rotation
- Secure deletion
- Audit trail

### 5. Policy (`neura/policy/`)

**Purpose**: Governance and safety.

**OPA Integration**:
```rego
# Example policy rule
package neura.motor

# Allow safe read operations
allow {
    input.action in ["read_file", "list_files"]
}

# Require confirmation for writes
require_confirmation {
    input.action in ["create_file", "delete_file"]
    input.path != "/tmp/*"
}

# Deny dangerous operations
deny {
    input.action == "delete_file"
    startswith(input.path, "/System")
}
```

**Policy Evaluation**:
1. Check if action is allowed
2. Check if confirmation needed
3. Check risk level
4. Log decision

### 6. Motor (`neura/motor/`)

**Purpose**: System automation.

**Action Pipeline**:
```
Action Request
     ↓
Policy Check
     ↓
User Confirmation (if needed)
     ↓
Executor Selection
     ↓
AppleScript/Shell/API
     ↓
Result Validation
     ↓
WHY Journal
```

**Executors**:
- **AppleScript**: macOS app control
- **Shell**: System commands
- **API**: Web services
- **Python**: Native operations

### 7. Flow (`neura/flow/`)

**Purpose**: User interface layer.

**Components**:
- **REPL**: Interactive shell
- **Rich Formatter**: Beautiful output
- **Completer**: Auto-completion
- **Confirmations**: User prompts

### 8. Voice (`neura/voice/`)

**Purpose**: Speech interface.

**Pipeline**:
```
Microphone
     ↓
VAD (Voice Activity Detection)
     ↓
Whisper (STT)
     ↓
NLP Processing
     ↓
Cortex
     ↓
TTS (pyttsx3)
     ↓
Speakers
```

### 9. WHY Journal (`neura/core/why_journal.py`)

**Purpose**: Audit trail.

**Entry Format**:
```json
{
  "id": "why_abc123",
  "timestamp": "2025-01-20T10:30:00Z",
  "action": "open_application",
  "reason": "User requested via voice command",
  "context": {
    "application": "Safari",
    "user": "default"
  },
  "outcome": "success",
  "policy_decision": {
    "allowed": true,
    "risk_level": "low"
  }
}
```

---

## Data Flow

### Example: "Open Safari"

```
1. User: "Open Safari"
        ↓
2. Voice: Transcribe → "Open Safari"
        ↓
3. Flow: Parse command
        ↓
4. Cortex: Understand intent
        ↓
5. Memory: Check context (no relevant memories)
        ↓
6. Policy: Check if allowed
        ↓
7. Motor: Execute AppleScript
        ↓
8. WHY: Log action
        ↓
9. Flow: Confirm to user
```

### Example: "Remember my birthday is March 15"

```
1. User: "Remember my birthday is March 15"
        ↓
2. Cortex: Extract information
        ↓
3. Memory: Store with tags ["personal", "dates"]
        ↓
4. Memory: Generate embedding
        ↓
5. Memory: Store in Qdrant
        ↓
6. WHY: Log storage
        ↓
7. Flow: Confirm stored
```

---

## Security Model

### Threat Model

**Protected Against**:
- ✅ Unauthorized data access
- ✅ Data exfiltration
- ✅ Malicious commands
- ✅ Memory tampering
- ✅ Credential theft

**Not Protected Against**:
- ❌ Physical access to unlocked machine
- ❌ Keyloggers (OS-level)
- ❌ Root/admin malware

### Defense in Depth

```
Layer 1: User Authentication
         (Master password)
         ↓
Layer 2: Encryption at Rest
         (SQLCipher, AES-256)
         ↓
Layer 3: Policy Engine
         (OPA rules)
         ↓
Layer 4: Audit Trail
         (WHY Journal)
         ↓
Layer 5: Secure Deletion
         (Overwrite + sync)
```

### Privacy Guarantees

1. **No telemetry**: Zero data sent to external servers
2. **Local processing**: All LLM inference local
3. **Encrypted storage**: All sensitive data encrypted
4. **Audit trail**: Complete action history
5. **User control**: Delete/export anytime

---

## Scalability

### Current Limits

- **Memory**: ~1M entries (SQLite + Qdrant)
- **Vault**: ~10K secrets
- **WHY Journal**: ~100K entries
- **Concurrent requests**: ~100/sec

### Future Scaling

**Phase 1** (v0.2):
- Distributed memory (multi-node Qdrant)
- Sharded vault
- Compressed journal

**Phase 2** (v0.3):
- Multi-user support
- Remote API
- Cloud sync (optional)

**Phase 3** (v1.0):
- Enterprise deployment
- High availability
- Load balancing

---

## Technology Stack

### Core
- **Python 3.12+**: Modern async/await
- **FastAPI**: High-performance API
- **Pydantic**: Type safety
- **Poetry**: Dependency management

### LLM
- **Ollama**: Local LLM server
- **llama.cpp**: Efficient inference

### Storage
- **SQLite**: Structured data
- **SQLCipher**: Encrypted SQLite
- **Qdrant**: Vector database

### Security
- **Argon2**: Password hashing
- **Cryptography**: AES encryption
- **OPA**: Policy engine

### Voice
- **Whisper**: Speech-to-text
- **pyttsx3**: Text-to-speech
- **PyAudio**: Audio I/O

### UI
- **Rich**: Terminal formatting
- **Prompt Toolkit**: Interactive CLI

---

## Design Patterns

### 1. Repository Pattern

```python
class MemoryRepository:
    async def store(self, memory: Memory) -> str:
        pass
    
    async def retrieve(self, id: str) -> Memory:
        pass
    
    async def search(self, query: str) -> List[Memory]:
        pass
```

### 2. Strategy Pattern

```python
class Executor(ABC):
    @abstractmethod
    async def execute(self, action: Action) -> Result:
        pass

class AppleScriptExecutor(Executor):
    async def execute(self, action: Action) -> Result:
        # AppleScript-specific logic
        pass
```

### 3. Observer Pattern

```python
class EventBus:
    def emit(self, event: str, data: dict):
        for handler in self.handlers[event]:
            handler(data)
    
    def on(self, event: str, handler: Callable):
        self.handlers[event].append(handler)
```

---

## Testing Strategy

### Unit Tests
- Each module tested in isolation
- Mocked dependencies
- Fast execution (<1s)

### Integration Tests
- Cross-module interactions
- Real dependencies
- Moderate speed (~10s)

### End-to-End Tests
- Full user workflows
- Real LLM + DB
- Slow (~1min)

**Coverage Target**: >80%

---

## Future Architecture

### v0.2: Multi-Agent

```
┌─────────────────────────────────────┐
│         Agent Orchestrator          │
│  ┌──────────┐  ┌──────────┐        │
│  │ Planner  │  │ Executor │        │
│  │  Agent   │→ │  Agent   │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │ Research │  │ Critic   │        │
│  │  Agent   │  │  Agent   │        │
│  └──────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

### v0.3: Distributed

```
┌─────────────────────────────────────┐
│         Load Balancer               │
└────────┬────────────────────────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│ Node1 │ │ Node2│ │ Node3│ │ NodeN│
└───┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
    │        │        │        │
    └────────┴────────┴────────┘
              │
    ┌─────────▼──────────┐
    │  Distributed Store │
    └────────────────────┘
```

---

**Questions?** See [Contributing Guide](../CONTRIBUTING.md) or open an issue!
