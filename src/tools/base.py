"""
TAMARA Tools - Base Classes
Base classes for tool definition.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolDefinition:
    """
    Tool definition for Ollama Function Calling.
    
    This class represents the metadata of a tool that will be
    sent to the LLM so it can decide when to use it.
    
    Attributes:
        name: Unique tool name.
        description: Clear description of what the tool does.
        parameters: JSON schema of accepted parameters.
    """
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=lambda: {
        "type": "object",
        "properties": {},
        "required": []
    })
    
    def to_ollama_format(self) -> Dict[str, Any]:
        """
        Convert definition to Ollama expected format.
        
        Returns:
            Dictionary with tool structure for Ollama API.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class BaseTool(ABC):
    """
    Abstract base class for all TAMARA tools.
    
    To create a new tool:
    1. Inherit from BaseTool
    2. Implement the `definition` property
    3. Implement the `execute` method
    
    Example:
        class MyTool(BaseTool):
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="my_tool",
                    description="Does something useful",
                    parameters={...}
                )
            
            async def execute(self, **kwargs) -> str:
                return "Result"
    """
    
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """
        Return the tool definition.
        
        This property is used by the ToolRegistry to
        register the tool and send it to the LLM.
        
        Returns:
            ToolDefinition with name, description and parameters.
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Parameters defined in the definition.
            
        Returns:
            Execution result as string.
            This result will be sent back to the LLM.
        """
        pass
    
    @property
    def name(self) -> str:
        """Shortcut to get tool name."""
        return self.definition.name
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
