# 🧠 NEURA - Cognitive Operating System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**NEURA** is a local-first, privacy-focused cognitive operating system that augments human intelligence through ethical AI. Built on principles of sovereignty, transparency, and user control.

## 🌟 Philosophy

- **🔒 Local-First**: All data and processing stay on your machine
- **🛡️ Privacy by Design**: Zero telemetry, zero cloud dependencies
- **⚖️ Ethical AI**: Transparent decision-making with audit trails
- **🎯 Sovereign**: You own your data, you control your AI

## ✨ Features

### Core Capabilities

- **🧠 Cortex**: Local LLM engine powered by Ollama
- **💾 Memory**: Hybrid storage (SQLite FTS5 + Qdrant embeddings)
- **🔐 Vault**: Military-grade encryption (SQLCipher + Argon2)
- **⚖️ Policy**: OPA-based governance engine
- **🤖 Motor**: Safe system automation with AppleScript
- **💬 Flow**: Conversational CLI/TUI interface
- **🎤 Voice**: Local STT/TTS (Whisper + pyttsx3)
- **📝 WHY Journal**: Complete audit trail of all decisions

### Advanced Features

- **Context-Aware**: Understands your workflow and environment
- **Proactive Assistance**: Anticipates needs without being intrusive
- **Multi-Modal**: Text, voice, and system integration
- **Extensible**: Plugin architecture for custom capabilities

## 🚀 Quick Start

### Prerequisites

```bash
# macOS (required)
brew install ollama python@3.12 portaudio

# Start Ollama
ollama serve

# Pull a model (e.g., llama3.2)
ollama pull llama3.2
```

### Installation

```bash
# Clone the repository
git clone https://github.com/abrini92/NeuraOS.git
cd NeuraOS/neura

# Install dependencies
poetry install

# Or with pip
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### Launch

```bash
# Start the API server
poetry run uvicorn neura.core.api:app --reload

# Or use the CLI
poetry run neura

# Or use the simple CLI
poetry run python -m neura.cli_simple
```

## 📚 Architecture

```
neura/
├── core/          # Core system (API, events, config)
├── cortex/        # LLM reasoning engine
├── memory/        # Hybrid memory system
├── vault/         # Encrypted storage
├── policy/        # Governance & safety
├── motor/         # System automation
├── flow/          # User interface
├── voice/         # Speech I/O
└── daemon/        # Background services
```

## 🔧 Development

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=neura --cov-report=html

# Specific module
poetry run pytest tests/unit/test_cortex.py
```

### Code Quality

```bash
# Format code
poetry run black neura/

# Type checking
poetry run mypy neura/

# Linting
poetry run ruff check neura/
```

## 🛣️ Roadmap

### Phase Alpha (Current)
- [x] Core architecture
- [x] Local LLM integration
- [x] Memory system
- [x] Vault encryption
- [x] Policy engine
- [x] Motor automation
- [x] Voice interface
- [x] WHY Journal

### Phase Beta (Q1 2025)
- [ ] Advanced context awareness
- [ ] Multi-agent collaboration
- [ ] Enhanced proactive features
- [ ] Mobile companion app
- [ ] Plugin marketplace

### Phase 1.0 (Q2 2025)
- [ ] Production-ready stability
- [ ] Comprehensive documentation
- [ ] Community ecosystem
- [ ] Enterprise features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/NeuraOS.git

# Create a branch
git checkout -b feature/amazing-feature

# Make changes and test
poetry run pytest

# Commit and push
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

## 📖 Documentation

- **[User Guide](docs/user-guide.md)**: Getting started with NEURA
- **[API Reference](docs/api-reference.md)**: Complete API documentation
- **[Architecture](docs/architecture.md)**: System design and principles
- **[Security](docs/security.md)**: Security model and best practices

## 🔒 Security

NEURA takes security seriously:

- **End-to-end encryption** for sensitive data
- **Zero-knowledge architecture** - we can't access your data
- **Audit trails** for all system actions
- **Policy-based access control**

Found a security issue? Please email: security@neura.dev

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** - Local LLM infrastructure
- **FastAPI** - Modern web framework
- **Qdrant** - Vector database
- **Open Policy Agent** - Policy engine
- **Whisper** - Speech recognition

## 💬 Community

- **GitHub Discussions**: [Join the conversation](https://github.com/abrini92/NeuraOS/discussions)
- **Discord**: Coming soon
- **Twitter**: [@NeuraOS](https://twitter.com/NeuraOS)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=abrini92/NeuraOS&type=Date)](https://star-history.com/#abrini92/NeuraOS&Date)

---

**Built with ❤️ for a more sovereign digital future**

*NEURA - Your mind, your data, your control*
