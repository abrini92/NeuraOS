# 🔌 NEURA API Reference

Complete API documentation for NEURA Cognitive OS.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, NEURA runs locally and doesn't require authentication. Future versions will support API keys for remote access.

---

## Table of Contents

1. [Core API](#core-api)
2. [Cortex (LLM)](#cortex-llm)
3. [Memory](#memory)
4. [Vault](#vault)
5. [Motor (Automation)](#motor-automation)
6. [Policy](#policy)
7. [Voice](#voice)
8. [WHY Journal](#why-journal)

---

## Core API

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600,
  "components": {
    "cortex": "ok",
    "memory": "ok",
    "vault": "ok"
  }
}
```

### System Info

```http
GET /system/info
```

**Response:**
```json
{
  "os": "macOS",
  "version": "14.0",
  "python": "3.12.0",
  "ollama": "0.1.0",
  "memory_usage": "45%",
  "disk_usage": "60%"
}
```

---

## Cortex (LLM)

### Ask Question

```http
POST /cortex/ask
```

**Request:**
```json
{
  "query": "What's the weather like?",
  "context": {
    "location": "San Francisco",
    "user_preferences": {}
  },
  "stream": false
}
```

**Response:**
```json
{
  "response": "I don't have real-time weather data...",
  "confidence": 0.85,
  "sources": ["memory", "reasoning"],
  "tokens_used": 150,
  "processing_time": 1.2
}
```

### Streaming Response

```http
POST /cortex/ask?stream=true
```

**Response:** Server-Sent Events (SSE)
```
data: {"chunk": "I", "done": false}
data: {"chunk": " don't", "done": false}
data: {"chunk": " have", "done": false}
...
data: {"done": true, "tokens": 150}
```

### Get Model Info

```http
GET /cortex/model
```

**Response:**
```json
{
  "name": "llama3.2",
  "size": "7B",
  "context_length": 4096,
  "loaded": true
}
```

---

## Memory

### Store Memory

```http
POST /memory/store
```

**Request:**
```json
{
  "content": "My favorite coffee is espresso",
  "tags": ["preferences", "food"],
  "importance": 0.8,
  "metadata": {
    "source": "conversation",
    "timestamp": "2025-01-20T10:30:00Z"
  }
}
```

**Response:**
```json
{
  "id": "mem_abc123",
  "stored": true,
  "embedding_generated": true
}
```

### Search Memories

```http
POST /memory/search
```

**Request:**
```json
{
  "query": "coffee preferences",
  "limit": 5,
  "min_score": 0.7,
  "filters": {
    "tags": ["preferences"]
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "mem_abc123",
      "content": "My favorite coffee is espresso",
      "score": 0.92,
      "tags": ["preferences", "food"],
      "created_at": "2025-01-20T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Get Memory by ID

```http
GET /memory/{memory_id}
```

**Response:**
```json
{
  "id": "mem_abc123",
  "content": "My favorite coffee is espresso",
  "tags": ["preferences", "food"],
  "importance": 0.8,
  "created_at": "2025-01-20T10:30:00Z",
  "accessed_count": 5,
  "last_accessed": "2025-01-21T08:15:00Z"
}
```

### Delete Memory

```http
DELETE /memory/{memory_id}
```

**Response:**
```json
{
  "deleted": true,
  "id": "mem_abc123"
}
```

### List Memories by Tags

```http
GET /memory/by-tags?tags=preferences,food&limit=10
```

**Response:**
```json
{
  "memories": [...],
  "total": 5,
  "page": 1
}
```

---

## Vault

### Store Secret

```http
POST /vault/store
```

**Request:**
```json
{
  "key": "github_token",
  "value": "ghp_abc123xyz",
  "tags": ["api", "github"],
  "master_password": "your_master_password"
}
```

**Response:**
```json
{
  "stored": true,
  "key": "github_token",
  "encrypted": true
}
```

### Retrieve Secret

```http
POST /vault/retrieve
```

**Request:**
```json
{
  "key": "github_token",
  "master_password": "your_master_password"
}
```

**Response:**
```json
{
  "key": "github_token",
  "value": "ghp_abc123xyz",
  "tags": ["api", "github"],
  "created_at": "2025-01-20T10:30:00Z"
}
```

### List Vault Keys

```http
GET /vault/keys
```

**Response:**
```json
{
  "keys": [
    {
      "key": "github_token",
      "tags": ["api", "github"],
      "created_at": "2025-01-20T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Delete Secret

```http
DELETE /vault/{key}
```

**Request:**
```json
{
  "master_password": "your_master_password"
}
```

**Response:**
```json
{
  "deleted": true,
  "key": "github_token"
}
```

---

## Motor (Automation)

### Execute Action

```http
POST /motor/execute
```

**Request:**
```json
{
  "action": "open_application",
  "parameters": {
    "application": "Safari"
  },
  "require_confirmation": false
}
```

**Response:**
```json
{
  "executed": true,
  "action": "open_application",
  "result": {
    "success": true,
    "message": "Safari opened successfully"
  },
  "policy_check": {
    "allowed": true,
    "reason": "Safe action"
  }
}
```

### List Available Actions

```http
GET /motor/actions
```

**Response:**
```json
{
  "actions": [
    {
      "name": "open_application",
      "description": "Open a macOS application",
      "parameters": ["application"],
      "safe": true
    },
    {
      "name": "create_file",
      "description": "Create a new file",
      "parameters": ["path", "content"],
      "safe": false,
      "requires_confirmation": true
    }
  ]
}
```

### AppleScript Execution

```http
POST /motor/applescript
```

**Request:**
```json
{
  "script": "tell application \"Safari\" to activate",
  "timeout": 5
}
```

**Response:**
```json
{
  "executed": true,
  "output": "",
  "error": null,
  "execution_time": 0.5
}
```

---

## Policy

### Check Action

```http
POST /policy/check
```

**Request:**
```json
{
  "action": "delete_file",
  "parameters": {
    "path": "/Users/user/important.txt"
  },
  "context": {
    "user": "default",
    "time": "2025-01-20T10:30:00Z"
  }
}
```

**Response:**
```json
{
  "allowed": false,
  "reason": "Destructive action requires explicit confirmation",
  "requires_confirmation": true,
  "risk_level": "high"
}
```

### Get Policy Rules

```http
GET /policy/rules
```

**Response:**
```json
{
  "rules": [
    {
      "name": "safe_read_actions",
      "description": "Allow read-only operations",
      "actions": ["read_file", "list_files", "search"]
    }
  ]
}
```

---

## Voice

### Start Recording

```http
POST /voice/record/start
```

**Response:**
```json
{
  "recording": true,
  "session_id": "rec_abc123"
}
```

### Stop Recording

```http
POST /voice/record/stop
```

**Request:**
```json
{
  "session_id": "rec_abc123"
}
```

**Response:**
```json
{
  "transcription": "What's the weather like today?",
  "confidence": 0.95,
  "duration": 2.5,
  "language": "en"
}
```

### Text to Speech

```http
POST /voice/speak
```

**Request:**
```json
{
  "text": "Hello, how can I help you?",
  "voice": "default",
  "rate": 150
}
```

**Response:**
```json
{
  "spoken": true,
  "duration": 1.8
}
```

---

## WHY Journal

### Get Recent Entries

```http
GET /why/recent?limit=10
```

**Response:**
```json
{
  "entries": [
    {
      "id": "why_abc123",
      "timestamp": "2025-01-20T10:30:00Z",
      "action": "open_application",
      "reason": "User requested",
      "outcome": "success",
      "context": {
        "application": "Safari"
      }
    }
  ],
  "total": 10
}
```

### Search Journal

```http
POST /why/search
```

**Request:**
```json
{
  "query": "file operations",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "actions": ["create_file", "delete_file"]
}
```

**Response:**
```json
{
  "entries": [...],
  "total": 5
}
```

### Export Journal

```http
GET /why/export?format=json&start_date=2025-01-01
```

**Response:** JSON file download

---

## Error Responses

All endpoints may return these error codes:

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "message": "Missing required parameter: query",
  "code": "INVALID_REQUEST"
}
```

### 403 Forbidden
```json
{
  "error": "Action not allowed",
  "message": "Policy violation: destructive action",
  "code": "POLICY_VIOLATION"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal error",
  "message": "LLM service unavailable",
  "code": "SERVICE_ERROR"
}
```

---

## Rate Limits

Local API has no rate limits. Future cloud versions will implement:

- **Free tier**: 100 requests/hour
- **Pro tier**: 1000 requests/hour
- **Enterprise**: Unlimited

---

## Webhooks

Coming in v0.2.0:

```http
POST /webhooks/register
```

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["memory.stored", "action.executed"],
  "secret": "webhook_secret"
}
```

---

## SDK Examples

### Python

```python
from neura_sdk import NeuraClient

client = NeuraClient("http://localhost:8000")

# Ask a question
response = client.cortex.ask("What's on my calendar?")
print(response.text)

# Store a memory
client.memory.store(
    content="Meeting at 2pm",
    tags=["calendar", "work"]
)

# Execute action
client.motor.execute(
    action="open_application",
    parameters={"application": "Safari"}
)
```

### JavaScript

```javascript
import { NeuraClient } from 'neura-sdk';

const client = new NeuraClient('http://localhost:8000');

// Ask a question
const response = await client.cortex.ask('What\'s on my calendar?');
console.log(response.text);

// Store a memory
await client.memory.store({
  content: 'Meeting at 2pm',
  tags: ['calendar', 'work']
});
```

---

## OpenAPI Specification

Full OpenAPI 3.0 spec available at:

```
http://localhost:8000/openapi.json
```

Interactive docs:

```
http://localhost:8000/docs
```

---

**Questions?** Open an issue on [GitHub](https://github.com/abrini92/NeuraOS/issues)
