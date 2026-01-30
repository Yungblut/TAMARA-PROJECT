"""
TAMARA LLM Engine Module
Ollama client with Tool Calling support.
"""

import asyncio
import json
from typing import Generator, List, Dict, Any, Optional, AsyncGenerator, Callable

import ollama

from .config import get_config


class LLMEngine:
    """
    Language Model Engine using Ollama with Tool Calling support.
    
    Supports two operation modes:
    1. Simple chat: Direct LLM responses
    2. Chat with tools: LLM can invoke tools and use their results
    
    Attributes:
        _config: LLM configuration.
        _history: Conversation history.
        _tool_registry: Available tools registry (optional).
        _tools_enabled: Whether tools system is active.
    """
    
    def __init__(self):
        self._config = get_config().llm
        self._tools_config = get_config().tools
        self._history: List[Dict[str, Any]] = []
        self._tool_registry = None
        self._tools_enabled = False
        self._reset_history()
    
    def set_tool_registry(self, registry) -> None:
        """
        Configure the tools registry.
        
        Args:
            registry: ToolRegistry instance.
        """
        self._tool_registry = registry
        self._tools_enabled = registry is not None and self._tools_config.enabled
        if self._tools_enabled:
            print(f"[LLM] Tools enabled: {registry.tool_names}")
    
    def _reset_history(self) -> None:
        """Reset history with system prompt."""
        self._history = [{
            'role': 'system',
            'content': self._config.system_prompt
        }]
    
    @property
    def history_length(self) -> int:
        """Return number of messages in history (excluding system prompt)."""
        return len(self._history) - 1
    
    @property
    def tools_enabled(self) -> bool:
        """Indicates if tools system is active."""
        return self._tools_enabled and self._tool_registry is not None
    
    def add_user_message(self, content: str) -> None:
        """
        Add user message to history.
        
        Args:
            content: Message content.
        """
        self._history.append({
            'role': 'user',
            'content': content
        })
        self._trim_history()
    
    def add_assistant_message(self, content: str) -> None:
        """
        Add assistant message to history.
        
        Args:
            content: Message content.
        """
        self._history.append({
            'role': 'assistant',
            'content': content
        })
        self._trim_history()
    
    def add_tool_result(self, tool_name: str, result: str) -> None:
        """
        Add tool execution result to history.
        
        Args:
            tool_name: Name of executed tool.
            result: Execution result.
        """
        self._history.append({
            'role': 'tool',
            'content': result,
            'name': tool_name
        })
    
    def _trim_history(self) -> None:
        """Trim history if it exceeds maximum."""
        max_msgs = self._config.max_history
        if len(self._history) > max_msgs:
            # Keep system prompt + last messages
            self._history = [self._history[0]] + self._history[-(max_msgs - 1):]
    
    def chat_stream(self, user_message: str) -> Generator[str, None, str]:
        """
        Send message and return streaming response (without tools).
        
        Args:
            user_message: User message.
            
        Yields:
            Response tokens.
            
        Returns:
            Complete response at the end.
        """
        if not user_message or len(user_message) < 2:
            return ""
        
        # Add user message
        self.add_user_message(user_message)
        
        # Get streaming response
        full_response = ""
        
        try:
            stream = ollama.chat(
                model=self._config.model,
                messages=self._history,
                stream=True
            )
            
            for chunk in stream:
                token = chunk['message']['content']
                full_response += token
                yield token
            
            # Save complete response
            if full_response.strip():
                self.add_assistant_message(full_response)
                
        except Exception as e:
            error_msg = f"Ollama error: {e}"
            print(f"[LLM] {error_msg}")
            yield f"\n[Error: {error_msg}]"
        
        return full_response
    
    async def chat_with_tools(
        self, 
        user_message: str,
        on_tool_start: Optional[Callable[[str], None]] = None,
        on_tool_end: Optional[Callable[[str, str], None]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Chat with Tool Calling support.
        
        The flow is:
        1. Send message with available tools to LLM
        2. If LLM requests a tool, execute it
        3. Send tool result to LLM
        4. LLM generates final response
        
        Args:
            user_message: User message.
            on_tool_start: Callback when tool starts.
            on_tool_end: Callback when tool ends.
            
        Yields:
            Response tokens and status messages.
        """
        if not user_message or len(user_message) < 2:
            return
        
        # Add user message
        self.add_user_message(user_message)
        
        # If no tools enabled, use normal chat
        if not self.tools_enabled:
            for token in self._stream_simple():
                yield token
            return
        
        try:
            # First call: LLM decides whether to use tools
            tools_list = self._tool_registry.get_ollama_tools()
            
            response = ollama.chat(
                model=self._config.model,
                messages=self._history,
                tools=tools_list,
                stream=False  # No streaming on first call with tools
            )
            
            message = response['message']
            
            # Check if LLM wants to use tools
            tool_calls = message.get('tool_calls', [])
            
            if tool_calls:
                # Add assistant response with tool_calls to history
                self._history.append(message)
                
                # Execute each requested tool
                for tool_call in tool_calls:
                    tool_name = tool_call['function']['name']
                    tool_args = tool_call['function'].get('arguments', {})
                    
                    # Notify tool start
                    if on_tool_start:
                        on_tool_start(tool_name)
                    
                    yield f"[Executing: {tool_name}...]\n"
                    
                    # Execute tool
                    result = await self._tool_registry.execute_tool(tool_name, tool_args)
                    
                    # Notify tool end
                    if on_tool_end:
                        on_tool_end(tool_name, result)
                    
                    # Add result to history
                    self.add_tool_result(tool_name, result)
                    print(f"[LLM] Tool {tool_name} executed")
                
                # Second call: LLM processes results and generates response
                async for token in self._stream_final_response():
                    yield token
            else:
                # Direct response without tools
                content = message.get('content', '')
                if content:
                    self.add_assistant_message(content)
                    yield content
                    
        except Exception as e:
            error_msg = f"Error in chat_with_tools: {e}"
            print(f"[LLM] {error_msg}")
            yield f"[Error: {error_msg}]"
    
    def _stream_simple(self) -> Generator[str, None, None]:
        """Simple streaming without tools."""
        full_response = ""
        
        try:
            stream = ollama.chat(
                model=self._config.model,
                messages=self._history,
                stream=True
            )
            
            for chunk in stream:
                token = chunk['message']['content']
                full_response += token
                yield token
            
            if full_response.strip():
                self.add_assistant_message(full_response)
                
        except Exception as e:
            yield f"[Error: {e}]"
    
    async def _stream_final_response(self) -> AsyncGenerator[str, None]:
        """
        Generate final response after executing tools.
        Uses streaming to send tokens as they are generated.
        """
        full_response = ""
        
        try:
            # Use streaming for final response
            stream = ollama.chat(
                model=self._config.model,
                messages=self._history,
                stream=True
            )
            
            for chunk in stream:
                token = chunk['message']['content']
                full_response += token
                yield token
                # Small delay to allow async to work
                await asyncio.sleep(0)
            
            if full_response.strip():
                self.add_assistant_message(full_response)
                
        except Exception as e:
            yield f"[Error generating response: {e}]"
    
    def chat(self, user_message: str) -> str:
        """
        Send message and return complete response (non-streaming).
        
        Args:
            user_message: User message.
            
        Returns:
            Complete assistant response.
        """
        response = ""
        for token in self.chat_stream(user_message):
            response += token
        return response
    
    def reset(self) -> None:
        """Reset conversation history."""
        self._reset_history()
        print("[LLM] History reset")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Return copy of current history."""
        return self._history.copy()
    
    def set_model(self, model_name: str) -> None:
        """
        Change Ollama model.
        
        Args:
            model_name: Model name (e.g., 'gpt-oss:20b')
        """
        self._config.model = model_name
        print(f"[LLM] Model changed to: {model_name}")
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Change system prompt and reset history.
        
        Args:
            prompt: New system prompt.
        """
        self._config.system_prompt = prompt
        self._reset_history()
        print("[LLM] System prompt updated")


# Singleton instance
_llm_engine: Optional[LLMEngine] = None


def get_llm_engine() -> LLMEngine:
    """Get LLM engine instance (singleton)."""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine()
    return _llm_engine
