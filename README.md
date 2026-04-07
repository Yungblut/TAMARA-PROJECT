# TAMARA - Totally Awesome Modular AI Responsive Assistant

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/license-AGPL--3.0-red)
![GPU](https://img.shields.io/badge/GPU-RTX%203090-76B900)

**100% local voice assistant with Tool Calling, streaming responses, and neural TTS**

*Privacy-first AI assistant running entirely on your hardware. No data leaves your machine.*

[Features](#features) | [Quick Start](#quick-start) | [Architecture](#architecture) | [Database Setup](#database-setup) | [Configuration](#configuration) | [Contributing](#contributing)

</div>

---

## Features

- **Local LLM Inference** -- Qwen2.5-32B via Ollama, running on your GPU
- **Neural Text-to-Speech** -- Kokoro-82M ONNX with Misaki G2P for natural Spanish voice
- **Server-side STT** -- faster-whisper Large V3 Turbo for local speech recognition
- **Tool Calling / Function Calling** -- LLM autonomously queries MariaDB databases
- **Web Search** -- DuckDuckGo integration via MCP (no API key required)
- **Filesystem Access** -- Read and manage local files via MCP tools
- **Real-time Streaming** -- Token-by-token responses via WebSocket
- **MCP Integration** -- Model Context Protocol for extensible tool ecosystem (10K+ servers available)
- **Modern Web Interface** -- React + Next.js with glassmorphism dark theme (planned)
- **100% Private** -- Everything runs locally on your RTX 3090, zero cloud dependencies

### What Can TAMARA Do?

Ask TAMARA anything in natural language -- she decides which tools to use:

| Question | What TAMARA does |
|----------|-----------------|
| *"What tables are in the database?"* | Lists all tables via `list_database_tables` tool |
| *"How many users are there?"* | Executes `get_table_count` on the users table |
| *"What products cost more than $100?"* | Builds and runs a SELECT query with WHERE filter |
| *"Search for the latest news about AI"* | Queries DuckDuckGo via MCP web search |
| *"What files are in my Documents folder?"* | Lists files via Filesystem MCP |
| *"Read the contents of config.yaml"* | Reads local files via Filesystem MCP |

### MCP Tools (Model Context Protocol)

TAMARA uses MCP for a standardized, extensible tool ecosystem:

| MCP Server | Capability | Status |
|------------|-----------|--------|
| **Database** | Query MariaDB with natural language (SELECT only by default) | Available |
| **DuckDuckGo** | Web search without API keys -- fully local and private | Planned (Phase 3) |
| **Filesystem** | Read, write, and manage local files securely | Planned (Phase 3) |

MCP is governed by the Linux Foundation with 10,000+ public servers available. Adding new capabilities is as simple as connecting a new MCP server.

---

## Technology Stack

### Backend (Python)

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async web framework with WebSocket support |
| **Ollama** | Local LLM inference (Qwen2.5-32B Q4_K_M) |
| **PydanticAI** | Type-safe AI agent framework (planned Phase 1) |
| **Kokoro-82M ONNX** | Neural TTS -- #1 on TTS Arena, <1GB VRAM |
| **Misaki** | Spanish grapheme-to-phoneme for TTS |
| **faster-whisper** | Local STT -- Large V3 Turbo, int8 (planned Phase 1) |
| **MariaDB** | Relational database for Tool Calling |
| **Pydantic Settings** | Type-safe configuration with auto env loading |
| **structlog** | Structured JSON logging |
| **UV** | Fast Python package manager (10-100x faster than pip) |
| **Ruff** | Linter + formatter (replaces flake8, black, isort) |

### Frontend (Current: Vanilla JS | Planned: React + Next.js)

| Technology | Purpose |
|------------|---------|
| **HTML5 + CSS3 + JS** | Current interface with Iron Man theme |
| **Web Speech API** | Browser-native speech recognition (fallback) |
| **WebSocket** | Real-time bidirectional communication |

### Planned Frontend (Phase 2)

| Technology | Purpose |
|------------|---------|
| **Next.js 16** | React framework with Turbopack |
| **shadcn/ui** | Component library |
| **assistant-ui** | Specialized chat UI components |
| **Tailwind CSS v4** | Utility-first CSS with glassmorphism theme |
| **Zustand** | Lightweight state management |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **[UV](https://docs.astral.sh/uv/)** -- Python package manager
- **[Ollama](https://ollama.ai/)** -- Local LLM runtime
- **[eSpeak-NG](https://github.com/espeak-ng/espeak-ng)** -- Required for TTS phonemization
- **MariaDB** (optional) -- For database tool calling
- **NVIDIA GPU** -- RTX 3090 recommended (24GB VRAM)

### Installation

```bash
# Clone the repository
git clone https://github.com/Yungblut/TAMARA-PROJECT.git
cd TAMARA-PROJECT

# Install dependencies with UV
uv sync
uv sync --extra dev  # For development tools (ruff, pytest, mypy)

# Pull the LLM model
ollama pull qwen2.5:32b

# Download TTS models (place in kokoro-models/)
# - kokoro-v1.0.onnx
# - voices-v1.0.bin

# Configure environment
cp .env.example .env
# Edit .env with your database credentials (if using MariaDB)
```

### Running

```bash
uv run python server.py
```

Open **http://localhost:8000** in your browser.

### Development

```bash
# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Run tests (coming in Phase 3)
uv run pytest
```

---

## Architecture

```
                            USER
                     (Voice / Keyboard)
                            |
                            v
+-----------------------------------------------------------+
|                    WEB INTERFACE                           |
|            (HTML + CSS + JavaScript)                       |
|  +----------------+ +-------------+ +------------------+  |
|  | Web Speech API | | WebSocket   | | Audio Player     |  |
|  | (Browser STT)  | | Client      | | (Base64 WAV)     |  |
|  +----------------+ +-------------+ +------------------+  |
+-----------------------------------------------------------+
                            |
                   WebSocket (ws://localhost:8000/ws)
                            |
                            v
+-----------------------------------------------------------+
|                    PYTHON SERVER                           |
|                     (FastAPI)                              |
|                                                           |
|  +---------------+ +---------------+ +-----------------+  |
|  | WebSocket     | | LLM Engine    | | TTS Engine      |  |
|  | Handler       |<| (Ollama)      | | (Kokoro+Misaki) |  |
|  +-------+-------+ +-------+-------+ +-----------------+  |
|          |                  |                              |
|          |          +-------v--------+                     |
|          |          | MCP Tools      |                     |
|          |          | +------------+ |                     |
|          |          | | Database   | |                     |
|          |          | | DuckDuckGo | |                     |
|          |          | | Filesystem | |                     |
|          |          | +------------+ |                     |
|          |          +-------+--------+                     |
+-----------------------------------------------------------+
                              |
               +--------------+--------------+
               |              |              |
               v              v              v
        +----------+   +-----------+   +-----------+
        | MariaDB  |   | DuckDuck  |   | Local     |
        | Database |   | Go Search |   | Files     |
        +----------+   +-----------+   +-----------+
```

---

## VRAM Budget (RTX 3090 -- 24GB)

| Component | VRAM | Strategy |
|-----------|------|----------|
| Qwen2.5-32B Q4_K_M | ~18,500 MB | Always loaded via Ollama |
| Kokoro-82M TTS | ~500 MB | Always loaded |
| faster-whisper int8 | ~2,000 MB | Lazy loaded on mic activation |
| CUDA overhead | ~1,500 MB | Runtime |
| **Total peak** | **~22,500 MB** | ~1.5GB headroom |

---

## Database Setup

### 1. Configure Credentials

```bash
cp .env.example .env
```

Edit `.env`:
```env
TAMARA_DB_HOST=localhost
TAMARA_DB_PORT=3306
TAMARA_DB_USER=tamara_user
TAMARA_DB_PASSWORD=your_secure_password
TAMARA_DB_NAME=tamara_db
```

### 2. Create Database (Optional)

```bash
mysql -u root -p < setup_database.sql
```

Creates sample tables (`usuarios`, `productos`, `pedidos`) with demo data.

### 3. Enable in Configuration

```yaml
# config.yaml
database:
  enabled: true
```

---

## Configuration

### config.yaml

```yaml
llm:
  model: "qwen2.5:32b"       # Ollama model name
  max_history: 500            # Conversation history limit

tts:
  voice: "ef_dora"            # TTS voice style
  speed: 1.1                  # Speech speed (0.5-2.0)
  language: "es"              # Target language

server:
  host: "0.0.0.0"
  port: 8000

database:
  enabled: false              # Enable MariaDB integration

tools:
  enabled: true               # Enable Tool Calling
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TAMARA_DB_HOST` | MariaDB host | localhost |
| `TAMARA_DB_PORT` | MariaDB port | 3306 |
| `TAMARA_DB_USER` | Database user | root |
| `TAMARA_DB_PASSWORD` | User password | -- |
| `TAMARA_DB_NAME` | Database name | -- |
| `TAMARA_DB_ALLOW_WRITE` | Allow INSERT/UPDATE | false |
| `TAMARA_LLM_MODEL` | Override LLM model | qwen2.5:32b |

---

## Project Structure

```
TAMARA-PROJECT/
    server.py                  # FastAPI entry point (lifespan, structlog)
    config.yaml                # Application configuration
    pyproject.toml             # Dependencies + tooling (UV, Ruff, pytest)
    .env.example               # Environment template
    setup_database.sql         # MariaDB sample data

    src/
        __init__.py
        config.py              # Pydantic Settings (type-safe config)
        logging.py             # structlog configuration
        llm_engine.py          # Ollama LLM with Tool Calling
        tts_engine.py          # Kokoro TTS + Misaki G2P
        websocket_handler.py   # WebSocket message handling

        tools/                 # Tool Calling system
            base.py            # Abstract base tool class
            registry.py        # Central tool registry
            database/
                client.py      # Secure MariaDB client
                tools.py       # Database tool implementations

    static/                    # Frontend assets
        css/styles.css         # Iron Man theme
        js/app.js              # WebSocket client

    templates/
        index.html             # Main web interface

    kokoro-models/             # TTS models (not in git)
        kokoro-v1.0.onnx
        voices-v1.0.bin
```

---

## Security

- **Read-only by default** -- Database tools only allow SELECT queries
- **SQL injection prevention** -- Identifier validation + parameterized queries
- **SecretStr** -- Database passwords never logged accidentally
- **Connection pooling** -- Secure connection lifecycle management
- **Environment variables** -- Sensitive data stays outside code

---

## Refactoring Roadmap

TAMARA is undergoing a professional-grade modernization:

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 0** | Done | UV, pyproject.toml, Pydantic Settings, Ruff, structlog, FastAPI lifespan |
| **Phase 1** | Planned | PydanticAI agent, async DB, faster-whisper STT, dependency injection |
| **Phase 2** | Planned | React + Next.js frontend, shadcn/ui, Tailwind CSS v4, glassmorphism |
| **Phase 3** | Planned | MCP (DuckDuckGo + Filesystem), comprehensive tests, Docker, GitHub Actions CI |

---

## API Reference

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/status` | GET | System status (TTS, LLM, tools, DB) |
| `/api/reset` | POST | Reset conversation history |

### WebSocket Protocol

**Client -> Server:**
```json
{"type": "message", "content": "user message"}
{"type": "ping"}
{"type": "reset"}
```

**Server -> Client:**
```json
{"type": "thinking"}
{"type": "token", "content": "response token"}
{"type": "tool_executing", "tool": "tool_name"}
{"type": "audio", "content": "base64_wav_audio"}
{"type": "done"}
{"type": "error", "content": "error message"}
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

Please run `uv run ruff check --fix . && uv run ruff format .` before committing.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** -- see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with Ollama, Kokoro TTS, FastAPI, and PydanticAI**

*100% local. 100% private. Your AI, your hardware.*

</div>
