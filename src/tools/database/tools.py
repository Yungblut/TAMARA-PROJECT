"""
TAMARA Database Tools
MariaDB tools for Ollama Function Calling.
"""

from typing import Any, Dict, List
from ..base import BaseTool, ToolDefinition
from .client import get_db_client


class ListTablesTool(BaseTool):
    """
    Tool to list database tables.
    
    Allows the LLM to know which tables are available
    before making queries.
    """
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_database_tables",
            description=(
                "List all available tables in the MariaDB database. "
                "Use this tool to know which tables exist before making queries."
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    
    async def execute(self, **kwargs) -> str:
        """List available tables."""
        client = get_db_client()
        
        if not client or not client.is_connected:
            return "Error: No database connection."
        
        try:
            tables = client.list_tables()
            
            if not tables:
                return "The database has no tables."
            
            return f"Available tables ({len(tables)}): {', '.join(tables)}"
            
        except Exception as e:
            return f"Error listing tables: {str(e)}"


class DescribeTableTool(BaseTool):
    """
    Tool to get a table's schema.
    
    Allows the LLM to understand the table structure
    before building queries.
    """
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="describe_table",
            description=(
                "Get the structure (columns, data types) of a specific table. "
                "Use this to understand what columns a table has before making queries. "
                "You need to provide the exact table name."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe (e.g., 'users', 'products')"
                    }
                },
                "required": ["table_name"]
            }
        )
    
    async def execute(self, table_name: str = "", **kwargs) -> str:
        """Describe a table's structure."""
        if not table_name:
            return "Error: You must provide the table name."
        
        client = get_db_client()
        
        if not client or not client.is_connected:
            return "Error: No database connection."
        
        try:
            schema = client.describe_table(table_name)
            
            if not schema:
                return f"Table '{table_name}' does not exist or is empty."
            
            # Format schema in readable way
            lines = [f"Structure of table '{table_name}':"]
            for col in schema:
                null_str = "NULL" if col.get('Null') == 'YES' else "NOT NULL"
                key_str = f" ({col.get('Key')})" if col.get('Key') else ""
                lines.append(f"  - {col['Field']}: {col['Type']} {null_str}{key_str}")
            
            return "\n".join(lines)
            
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error describing table: {str(e)}"


class QueryDatabaseTool(BaseTool):
    """
    Tool to execute SELECT queries on the database.
    
    This is the main tool that allows the LLM
    to query data from MariaDB using SQL.
    """
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="query_database",
            description=(
                "Execute a SQL SELECT query on the MariaDB database. "
                "Use this tool when the user asks for specific data. "
                "IMPORTANT: Only read queries (SELECT) are allowed. "
                "First use 'list_database_tables' to see available tables "
                "and 'describe_table' to know the structure before making complex queries."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The SQL SELECT query to execute. "
                            "Example: 'SELECT * FROM users LIMIT 10'"
                        )
                    }
                },
                "required": ["query"]
            }
        )
    
    async def execute(self, query: str = "", **kwargs) -> str:
        """Execute a SELECT query and return results."""
        if not query:
            return "Error: You must provide a SQL query."
        
        client = get_db_client()
        
        if not client or not client.is_connected:
            return "Error: No database connection."
        
        try:
            results = client.execute_query(query)
            
            if not results:
                return "The query returned no results."
            
            return self._format_results(results)
            
        except Exception as e:
            error_msg = str(e)
            # Clean sensitive error messages
            if "SecurityError" in error_msg or "not authorized" in error_msg.lower():
                return f"Security error: {error_msg}"
            return f"Error executing query: {error_msg}"
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format query results for the LLM.
        
        Args:
            results: List of dictionaries with results.
            
        Returns:
            Formatted string with results.
        """
        count = len(results)
        
        # For single result, show directly
        if count == 1:
            row = results[0]
            if len(row) == 1:
                # Query like COUNT(*) or similar
                return str(list(row.values())[0])
            return str(row)
        
        # For multiple results
        output_lines = [f"Found {count} results:"]
        
        # Limit to 15 results to not overload the LLM
        max_show = 15
        for i, row in enumerate(results[:max_show]):
            output_lines.append(f"  {i+1}. {row}")
        
        if count > max_show:
            output_lines.append(f"  ... and {count - max_show} more results.")
        
        return "\n".join(output_lines)


class GetTableCountTool(BaseTool):
    """
    Tool to get row count of a table.
    
    Useful shortcut for questions like "How many users are there?"
    """
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_table_count",
            description=(
                "Get the total number of records (rows) in a table. "
                "Use this tool when the user asks 'how many?' "
                "about a specific entity."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to count (e.g., 'users', 'orders')"
                    }
                },
                "required": ["table_name"]
            }
        )
    
    async def execute(self, table_name: str = "", **kwargs) -> str:
        """Get row count of a table."""
        if not table_name:
            return "Error: You must provide the table name."
        
        client = get_db_client()
        
        if not client or not client.is_connected:
            return "Error: No database connection."
        
        try:
            count = client.get_table_count(table_name)
            return f"Table '{table_name}' has {count} records."
            
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error counting records: {str(e)}"
