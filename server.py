"""
TAMARA WebSocket Server
Main application entry point.
Version 3.0 - Modernized with structlog, lifespan, and Pydantic Settings.
"""

import threading
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import get_settings
from src.llm_engine import get_llm_engine
from src.logging import setup_logging
from src.tts_engine import get_tts_engine
from src.websocket_handler import get_ws_handler

log = structlog.get_logger("tamara.server")

# Configuration
config = get_settings()


# ============================================
# Startup / Shutdown
# ============================================


def init_database() -> bool:
    """Initialize MariaDB connection if enabled."""
    if not config.database.enabled:
        log.info("Database disabled in config")
        return False

    try:
        from src.tools.database.client import init_db_client

        client = init_db_client(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password.get_secret_value(),
            database=config.database.database,
            allow_write=config.database.allow_write,
        )

        if client.connect():
            log.info(
                "Database connected",
                database=config.database.database,
                host=config.database.host,
            )
            return True
        else:
            log.error("Failed to connect to database")
            return False

    except ImportError:
        log.error("mariadb package not installed", hint="Run: uv add mariadb")
        return False
    except Exception as e:
        log.error("Database initialization failed", error=str(e))
        return False


def init_tools() -> None:
    """Initialize the tools system."""
    if not config.tools.enabled:
        log.info("Tools system disabled in config")
        return

    try:
        from src.tools.registry import init_tool_registry

        registry = init_tool_registry()

        llm = get_llm_engine()
        llm.set_tool_registry(registry)

        log.info("Tools system initialized", count=registry.count)

    except Exception as e:
        log.error("Tools initialization failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Setup logging
    setup_logging(log_level=config.server.log_level.upper())

    log.info(
        "TAMARA Server v3.0 starting",
        port=config.server.port,
        model=config.llm.model,
        voice=config.tts.voice,
    )

    # Initialize TTS in background thread
    def init_tts():
        tts = get_tts_engine()
        tts.initialize()

    threading.Thread(target=init_tts, daemon=True).start()

    # Initialize database (if enabled)
    db_ok = init_database()

    # Initialize tools system (if enabled)
    if db_ok or not config.database.enabled:
        init_tools()

    log.info(
        "Server ready",
        tools=config.tools.enabled,
        database=config.database.enabled,
        url=f"http://localhost:{config.server.port}",
    )

    yield

    # Shutdown
    log.info("Server shutting down")


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="TAMARA Server",
    description="Intelligent Assistant with TTS, LLM and Tool Calling",
    version="3.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================
# HTTP Routes
# ============================================


@app.get("/")
async def serve_index():
    """Serve the main HTML interface."""
    return FileResponse("templates/index.html")


@app.get("/api/status")
async def get_status():
    """Return system status."""
    tts = get_tts_engine()
    llm = get_llm_engine()

    return JSONResponse(
        {
            "status": "online",
            "tts_ready": tts.is_ready,
            "model": config.llm.model,
            "voice": config.tts.voice,
            "history_length": llm.history_length,
            "tools_enabled": llm.tools_enabled,
            "database_enabled": config.database.enabled,
        }
    )


@app.post("/api/reset")
async def reset_history():
    """Reset conversation history."""
    llm = get_llm_engine()
    llm.reset()

    return JSONResponse({"status": "reset", "message": "History reset"})


# ============================================
# WebSocket
# ============================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for bidirectional communication."""
    handler = get_ws_handler()
    await handler.handle_connection(websocket)


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    setup_logging(log_level=config.server.log_level.upper())
    uvicorn.run(
        "server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.server.log_level,
    )
