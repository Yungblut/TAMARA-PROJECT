"""
TAMARA WebSocket Handler Module
Handles WebSocket connections and message processing.
Includes Tool Calling support and tool notifications.
"""

from typing import Set, Optional
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect

from .tts_engine import get_tts_engine
from .llm_engine import get_llm_engine


@dataclass
class ConnectionManager:
    """Manages active WebSocket connections."""
    
    active_connections: Set[WebSocket] = field(default_factory=set)
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[WS] Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection."""
        self.active_connections.discard(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict) -> None:
        """Send message to all active connections."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up dead connections
        self.active_connections -= disconnected


class WebSocketHandler:
    """
    Handles WebSocket message logic.
    
    Integrates LLM (with Tool Calling) and TTS to process messages
    and generate responses with agentic capabilities.
    
    Supported message types:
    - message: User chat message
    - ping: Keepalive
    - reset: Reset history
    
    Response types:
    - thinking: LLM is processing
    - token: A response token
    - tool_executing: A tool is being executed
    - tool_result: Tool execution result
    - audio: TTS audio chunk
    - done: Response completed
    - error: Processing error
    """
    
    def __init__(self):
        self.manager = ConnectionManager()
        self._tts = get_tts_engine()
        self._llm = get_llm_engine()
    
    async def handle_connection(self, websocket: WebSocket) -> None:
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: Client WebSocket connection.
        """
        await self.manager.connect(websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
                await self._process_message(websocket, data)
                
        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
        except Exception as e:
            print(f"[WS] Error: {e}")
            self.manager.disconnect(websocket)
    
    async def _process_message(self, websocket: WebSocket, data: dict) -> None:
        """
        Process a received message.
        
        Args:
            websocket: Client connection.
            data: Message data.
        """
        msg_type = data.get("type", "")
        
        if msg_type == "message":
            await self._handle_chat_message(websocket, data.get("content", ""))
        
        elif msg_type == "ping":
            await websocket.send_json({"type": "pong"})
        
        elif msg_type == "reset":
            self._llm.reset()
            await websocket.send_json({
                "type": "system",
                "content": "History reset"
            })
    
    async def _handle_chat_message(self, websocket: WebSocket, content: str) -> None:
        """
        Process a user chat message.
        
        If tools are enabled, uses chat_with_tools.
        Otherwise, uses simple chat_stream.
        
        Args:
            websocket: Client connection.
            content: Message content.
        """
        if not content or len(content) < 2:
            return
        
        # Notify that we're processing
        await websocket.send_json({"type": "thinking"})
        
        try:
            # Decide which method to use based on tools availability
            if self._llm.tools_enabled:
                await self._handle_chat_with_tools(websocket, content)
            else:
                await self._handle_simple_chat(websocket, content)
            
            # Notify response complete
            await websocket.send_json({"type": "done"})
            
        except Exception as e:
            print(f"[WS] Chat error: {e}")
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
    
    async def _handle_simple_chat(self, websocket: WebSocket, content: str) -> None:
        """
        Handle simple chat without tools.
        
        Args:
            websocket: Client connection.
            content: User message.
        """
        buffer = ""
        
        # Stream tokens from LLM
        for token in self._llm.chat_stream(content):
            # Send token to client
            await websocket.send_json({
                "type": "token",
                "content": token
            })
            
            buffer += token
            
            # When a sentence ends, generate audio
            if token in ['.', '!', '?', '\n', ':'] and buffer.strip():
                await self._send_audio(websocket, buffer)
                buffer = ""
        
        # Send audio for remaining buffer
        if buffer.strip():
            await self._send_audio(websocket, buffer)
    
    async def _handle_chat_with_tools(self, websocket: WebSocket, content: str) -> None:
        """
        Handle chat with tool support.
        
        Args:
            websocket: Client connection.
            content: User message.
        """
        buffer = ""
        
        # Callbacks to notify client about tools
        async def on_tool_start(tool_name: str):
            await websocket.send_json({
                "type": "tool_executing",
                "tool": tool_name
            })
        
        async def on_tool_end(tool_name: str, result: str):
            await websocket.send_json({
                "type": "tool_result",
                "tool": tool_name,
                "result": result[:200]  # Limit result size
            })
        
        # Use async generator with tools
        async for token in self._llm.chat_with_tools(
            content,
            on_tool_start=lambda t: websocket.send_json({"type": "tool_executing", "tool": t}),
            on_tool_end=lambda t, r: None  # Internal logging only
        ):
            # Detect tool status messages
            if token.startswith("[Executing:"):
                await websocket.send_json({
                    "type": "tool_executing",
                    "tool": token.replace("[Executing:", "").replace("...]", "").strip()
                })
                continue
            
            # Send token to client
            await websocket.send_json({
                "type": "token",
                "content": token
            })
            
            buffer += token
            
            # When a sentence ends, generate audio
            if token in ['.', '!', '?', '\n', ':'] and buffer.strip():
                # Don't generate audio for tool messages
                if not buffer.startswith("["):
                    await self._send_audio(websocket, buffer)
                buffer = ""
        
        # Send audio for remaining buffer
        if buffer.strip() and not buffer.startswith("["):
            await self._send_audio(websocket, buffer)
    
    async def _send_audio(self, websocket: WebSocket, text: str) -> None:
        """
        Generate and send TTS audio.
        
        Args:
            websocket: Client connection.
            text: Text to convert to audio.
        """
        # Clean text of special characters
        clean_text = text.replace("[", "").replace("]", "").strip()
        
        if not clean_text:
            return
        
        audio_b64 = self._tts.generate_audio(clean_text)
        if audio_b64:
            await websocket.send_json({
                "type": "audio",
                "content": audio_b64
            })


# Singleton instance
_ws_handler: Optional[WebSocketHandler] = None


def get_ws_handler() -> WebSocketHandler:
    """Get WebSocket handler instance (singleton)."""
    global _ws_handler
    if _ws_handler is None:
        _ws_handler = WebSocketHandler()
    return _ws_handler
