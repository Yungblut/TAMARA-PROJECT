"""
TAMARA WebSocket Server
Main application entry point.
Version 2.1 - With Tool Calling and MariaDB support.
"""

import threading

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from src.config import get_config
from src.tts_engine import get_tts_engine
from src.llm_engine import get_llm_engine
from src.websocket_handler import get_ws_handler


# Configuration
config = get_config()

# Create FastAPI application
app = FastAPI(
    title="TAMARA Server",
    description="Intelligent Assistant with TTS, LLM and Tool Calling",
    version="2.1.0"
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
    
    return JSONResponse({
        "status": "online",
        "tts_ready": tts.is_ready,
        "model": config.llm.model,
        "voice": config.tts.voice,
        "history_length": llm.history_length,
        "tools_enabled": llm.tools_enabled,
        "database_enabled": config.database.enabled
    })


@app.post("/api/reset")
async def reset_history():
    """Reset conversation history."""
    llm = get_llm_engine()
    llm.reset()
    
    return JSONResponse({
        "status": "reset",
        "message": "History reset"
    })


# ============================================
# WebSocket
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for bidirectional communication."""
    handler = get_ws_handler()
    await handler.handle_connection(websocket)


# ============================================
# Startup
# ============================================

def init_database():
    """Initialize MariaDB connection if enabled."""
    if not config.database.enabled:
        print("[DB] Database disabled in config")
        return False
    
    try:
        from src.tools.database.client import init_db_client
        
        client = init_db_client(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database,
            allow_write=config.database.allow_write
        )
        
        if client.connect():
            print(f"[DB] Connected to {config.database.database}@{config.database.host}")
            return True
        else:
            print("[DB] Failed to connect to database")
            return False
            
    except ImportError:
        print("[DB] Error: mariadb package not installed. Run: pip install mariadb")
        return False
    except Exception as e:
        print(f"[DB] Error initializing database: {e}")
        return False


def init_tools():
    """Initialize the tools system."""
    if not config.tools.enabled:
        print("[Tools] Tools system disabled in config")
        return
    
    try:
        from src.tools.registry import init_tool_registry, get_tool_registry
        
        # Initialize tool registry
        registry = init_tool_registry()
        
        # Connect registry to LLM Engine
        llm = get_llm_engine()
        llm.set_tool_registry(registry)
        
        print(f"[Tools] Tools system initialized ({registry.count} tools)")
        
    except Exception as e:
        print(f"[Tools] Error initializing tools: {e}")


@app.on_event("startup")
async def startup_event():
    """Server startup initialization."""
    print("\n" + "=" * 50)
    print("       TAMARA Server v2.1 - Starting...")
    print("       With Tool Calling support")
    print("=" * 50 + "\n")
    
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
    
    # Show status
    print(f"\n[Server] Port: {config.server.port}")
    print(f"[Server] LLM Model: {config.llm.model}")
    print(f"[Server] TTS Voice: {config.tts.voice}")
    print(f"[Server] Tools: {'Enabled' if config.tools.enabled else 'Disabled'}")
    print(f"[Server] Database: {'Enabled' if config.database.enabled else 'Disabled'}")
    print(f"\n[Server] Interface: http://localhost:{config.server.port}")
    print(f"[Server] WebSocket: ws://localhost:{config.server.port}/ws")
    print()


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.server.log_level
    )
