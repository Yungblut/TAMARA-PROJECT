"""
TAMARA Tool Registry
Central registry for available tools.
"""

from typing import Dict, List, Any, Optional
from .base import BaseTool, ToolDefinition
from ..config import get_config


class ToolRegistry:
    """
    Central registry of all TAMARA tools.
    
    Manages registration, lookup and execution of tools
    for Ollama's Function Calling system.
    
    Example:
        registry = ToolRegistry()
        registry.register(MyTool())
        
        # Get tools for Ollama
        tools = registry.get_ollama_tools()
        
        # Execute a tool
        result = await registry.execute_tool("my_tool", {"arg": "value"})
    """
    
    def __init__(self):
        """Initialize registry with default tools."""
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Initialize registry with enabled tools.
        
        Reads configuration to know which tools are enabled
        and registers them automatically.
        """
        if self._initialized:
            return
        
        config = get_config()
        
        # Check if tools are enabled
        if not config.tools.enabled:
            print("[Tools] Tools system disabled")
            return
        
        # Check if database is enabled
        if config.database.enabled:
            self._register_database_tools()
        
        self._initialized = True
        print(f"[Tools] Registered {len(self._tools)} tools")
    
    def _register_database_tools(self) -> None:
        """Register database tools."""
        from .database.tools import (
            ListTablesTool,
            DescribeTableTool,
            QueryDatabaseTool,
            GetTableCountTool,
        )
        
        self.register(ListTablesTool())
        self.register(DescribeTableTool())
        self.register(QueryDatabaseTool())
        self.register(GetTableCountTool())
        
        print("[Tools] Database tools registered")
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a new tool.
        
        Args:
            tool: BaseTool instance to register.
        """
        self._tools[tool.definition.name] = tool
        print(f"[Tools] Registered: {tool.definition.name}")
    
    def unregister(self, name: str) -> bool:
        """
        Remove a tool from the registry.
        
        Args:
            name: Tool name.
            
        Returns:
            True if removed, False if not found.
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name.
            
        Returns:
            Tool instance or None.
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Return all registered tools.
        
        Returns:
            List of BaseTool instances.
        """
        return list(self._tools.values())
    
    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions in Ollama format.
        
        This format is expected by Ollama's API
        for the `tools` parameter in chat().
        
        Returns:
            List of dictionaries with Ollama structure.
        """
        return [
            tool.definition.to_ollama_format()
            for tool in self._tools.values()
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name.
            arguments: Dictionary with arguments.
            
        Returns:
            Execution result as string.
        """
        tool = self._tools.get(name)
        
        if not tool:
            available = ", ".join(self._tools.keys())
            return f"Tool '{name}' not found. Available: {available}"
        
        try:
            result = await tool.execute(**arguments)
            print(f"[Tools] Executed: {name} -> {len(result)} chars")
            return result
            
        except Exception as e:
            error_msg = f"Error executing {name}: {str(e)}"
            print(f"[Tools] {error_msg}")
            return error_msg
    
    @property
    def count(self) -> int:
        """Number of registered tools."""
        return len(self._tools)
    
    @property
    def tool_names(self) -> List[str]:
        """List of registered tool names."""
        return list(self._tools.keys())


# =============================================================================
# Singleton Instance
# =============================================================================

_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get ToolRegistry singleton instance.
    
    Returns:
        ToolRegistry instance.
    """
    global _tool_registry
    
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    
    return _tool_registry


def init_tool_registry() -> ToolRegistry:
    """
    Initialize ToolRegistry singleton.
    
    Calls initialize() to register enabled tools.
    
    Returns:
        Initialized ToolRegistry instance.
    """
    registry = get_tool_registry()
    registry.initialize()
    return registry
