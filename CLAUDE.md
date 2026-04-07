# TAMARA - Project Guide

## What is this project?

TAMARA (Totally Awesome Modular AI Responsive Assistant) is a 100% local voice assistant running on an RTX 3090 (24GB VRAM). It combines LLM inference, text-to-speech, speech-to-text, and tool calling into a single application with a web interface.

**Primary language**: Spanish (configurable)
**Privacy**: Everything runs locally -- no data sent to external services.

## Architecture

Separated frontend/backend:

- **Backend** (port 8000): Python FastAPI server handling WebSocket, AI inference, TTS, STT
- **Frontend** (port 3000): React + Next.js 16 with shadcn/ui and assistant-ui
- **LLM**: Qwen2.5-32B Q4_K_M via Ollama (local)
- **TTS**: Kokoro-82M ONNX (<1GB VRAM, #1 TTS Arena)
- **STT**: faster-whisper Large V3 Turbo int8 (~2GB VRAM, lazy loaded)
- **Database**: MariaDB (async via asyncmy, optional)
- **Tools**: MCP (Model Context Protocol) -- Database, Filesystem, DuckDuckGo

### VRAM Management

The RTX 3090 has 24GB. The LLM uses ~18.5GB permanently. Kokoro TTS uses <1GB (always loaded). STT is **lazy loaded**:
- STT loads when mic activates, unloads after 30s silence
- Peak: LLM (~18.5GB) + Kokoro (<1GB) + STT (~2GB) + overhead (~1.5GB) = ~23GB

## Tech Stack

| Layer | Technology |
|-------|-----------|
| TTS | Kokoro-82M ONNX + Misaki G2P |
| STT | faster-whisper Large V3 Turbo (int8, lazy loaded) |
| AI Framework | PydanticAI with OllamaModel |
| Web Framework | FastAPI (async, DI with Depends) |
| Frontend | Next.js 16 + React + TypeScript |
| UI Components | shadcn/ui + assistant-ui |
| Styling | Tailwind CSS v4 (glassmorphism dark theme) |
| State | Zustand |
| Config | Pydantic Settings (auto env loading + YAML) |
| Database | asyncmy (async MariaDB) |
| Logging | structlog (structured JSON) |
| Package Manager | UV |
| Linter/Formatter | Ruff |
| Tests | pytest + pytest-asyncio (backend), Vitest (frontend) |

## Project Structure

```
server.py                    # FastAPI entry point (lifespan, DI)
src/
    config.py                # Pydantic Settings
    logging.py               # structlog setup
    dependencies.py          # FastAPI Depends providers
    agent.py                 # PydanticAI agent (LLM + tools)
    tts_engine.py            # Kokoro-82M ONNX + Misaki
    tts_service.py           # TTS async queue
    stt_service.py           # faster-whisper
    vram_manager.py          # GPU memory coordinator
    websocket_handler.py     # WebSocket handler
    database/client.py       # Async MariaDB
    mcp/server.py            # FastMCP (expose tools)
    mcp/client.py            # MCP client (consume external tools)
frontend/                    # Next.js 16 project
    app/                     # App Router pages
    components/              # React components
    lib/                     # Utilities (websocket client)
    stores/                  # Zustand stores
tests/                       # pytest test suite
```

## Development

### Prerequisites

- Python 3.11+ (currently using 3.14)
- Node.js 20+ (currently using 24)
- UV (Python package manager)
- Ollama running locally with `qwen2.5:32b` pulled
- MariaDB (optional, for database tools)
- eSpeak-NG (for TTS phonemization)

### Setup

```bash
# Backend
uv sync
cp .env.example .env  # Edit with your credentials

# Frontend
cd frontend && npm install

# Models
ollama pull qwen2.5:32b
```

### Running

```bash
# Backend (terminal 1)
uv run python server.py

# Frontend (terminal 2)
cd frontend && npm run dev
```

### Testing

```bash
# Backend
uv run pytest

# Frontend
cd frontend && npm test
```

### Linting

```bash
uv run ruff check --fix .
uv run ruff format .
```

## Conventions

- **Language**: Python code and comments in English. UI text in Spanish.
- **Async**: All I/O operations must be async. Never block the event loop.
- **DI**: Use FastAPI `Depends` for all service injection. No global singletons.
- **Config**: All settings via Pydantic Settings. Secrets use `SecretStr`.
- **Logging**: Use `structlog.get_logger()`. Never `print()`.
- **Types**: Type hints required on all function signatures.
- **Tests**: New features need tests. Use PydanticAI's `TestModel` for agent tests.
- **Frontend**: TypeScript strict mode. Components in `components/` with shadcn/ui patterns.

## Key Design Decisions

1. **PydanticAI over raw Ollama**: Type-safe agents, built-in tool calling, async streaming, testable with TestModel
2. **Kokoro-82M TTS**: #1 TTS Arena, <1GB VRAM, RTF 0.03, Apache 2.0. Fish Speech S2 Pro was considered but requires 12-24GB VRAM (incompatible with 32B LLM)
3. **MCP over custom tools**: Standard protocol, 10K+ servers, Linux Foundation governed, interoperable
4. **Separated frontend/backend**: Clear responsibility split, independent deployment, proper React tooling
5. **Lazy VRAM loading**: Enables running LLM + TTS + STT on 24GB by time-sharing GPU memory
