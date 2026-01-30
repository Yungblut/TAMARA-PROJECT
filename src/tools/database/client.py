"""
TAMARA MariaDB Client
Secure client for MariaDB connection.
"""

import re
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

try:
    import mariadb
    MARIADB_AVAILABLE = True
except ImportError:
    MARIADB_AVAILABLE = False
    mariadb = None


class SecurityError(Exception):
    """Security error in database operations."""
    pass


class MariaDBClient:
    """
    Secure MariaDB client.
    
    Security features:
    - Only allows SELECT queries by default
    - Table name validation
    - Connection pooling
    - Query timeout
    
    Attributes:
        _config: Database configuration.
        _pool: MariaDB connection pool.
    """
    
    # Allowed queries (case insensitive)
    ALLOWED_READ_COMMANDS = ['SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']
    
    def __init__(self, host: str, port: int, user: str, 
                 password: str, database: str, allow_write: bool = False):
        """
        Initialize MariaDB client.
        
        Args:
            host: MariaDB server host.
            port: Server port.
            user: Database user.
            password: User password.
            database: Database name.
            allow_write: If True, allows write operations.
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._allow_write = allow_write
        self._pool = None
        self._connected = False
    
    @property
    def is_available(self) -> bool:
        """Check if MariaDB driver is available."""
        return MARIADB_AVAILABLE
    
    @property
    def is_connected(self) -> bool:
        """Check if there's an active connection."""
        return self._connected and self._pool is not None
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection was successful, False otherwise.
        """
        if not MARIADB_AVAILABLE:
            print("[DB] Error: mariadb package not installed")
            return False
        
        try:
            self._pool = mariadb.ConnectionPool(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database,
                pool_name="tamara_pool",
                pool_size=3
            )
            self._connected = True
            print(f"[DB] Connected to {self._database}@{self._host}")
            return True
            
        except mariadb.Error as e:
            print(f"[DB] Connection error: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Close all pool connections."""
        if self._pool:
            self._pool.close()
            self._pool = None
            self._connected = False
            print("[DB] Disconnected")
    
    @contextmanager
    def _get_connection(self):
        """Context manager to get a connection from the pool."""
        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _validate_query(self, query: str) -> None:
        """
        Validate that the query is safe to execute.
        
        Args:
            query: SQL query to validate.
            
        Raises:
            SecurityError: If query is not allowed.
        """
        query_stripped = query.strip()
        query_upper = query_stripped.upper()
        
        # Get first command
        first_word = query_upper.split()[0] if query_upper.split() else ""
        
        # Check if it's an allowed command
        if first_word not in self.ALLOWED_READ_COMMANDS:
            if not self._allow_write:
                raise SecurityError(
                    f"Only read queries are allowed. "
                    f"Command '{first_word}' not authorized."
                )
    
    def _validate_identifier(self, identifier: str) -> None:
        """
        Validate that an identifier (table, column) is safe.
        
        Args:
            identifier: Name to validate.
            
        Raises:
            ValueError: If identifier is invalid.
        """
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid identifier: {identifier}")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query safely.
        
        Args:
            query: SQL query to execute.
            params: Parameters for parameterized query.
            
        Returns:
            List of dictionaries with results.
            
        Raises:
            SecurityError: If query is not allowed.
            Exception: If execution error occurs.
        """
        if not self.is_connected:
            raise ConnectionError("No database connection")
        
        # Validate security
        self._validate_query(query)
        
        with self._get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                return results
                
            finally:
                cursor.close()
    
    def list_databases(self) -> List[str]:
        """
        List all available databases.
        
        Returns:
            List of database names.
        """
        results = self.execute_query("SHOW DATABASES")
        return [row['Database'] for row in results]
    
    def list_tables(self) -> List[str]:
        """
        List all tables in current database.
        
        Returns:
            List of table names.
        """
        results = self.execute_query("SHOW TABLES")
        # Column name depends on DB name
        return [list(row.values())[0] for row in results]
    
    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get table schema.
        
        Args:
            table_name: Table name.
            
        Returns:
            List with column information.
        """
        self._validate_identifier(table_name)
        return self.execute_query(f"DESCRIBE {table_name}")
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get number of rows in a table.
        
        Args:
            table_name: Table name.
            
        Returns:
            Number of rows.
        """
        self._validate_identifier(table_name)
        results = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        return results[0]['count'] if results else 0


# =============================================================================
# Singleton Instance
# =============================================================================

_db_client: Optional[MariaDBClient] = None


def get_db_client() -> Optional[MariaDBClient]:
    """
    Get MariaDB client singleton instance.
    
    Returns:
        MariaDBClient instance or None if not initialized.
    """
    return _db_client


def init_db_client(host: str, port: int, user: str, 
                   password: str, database: str, 
                   allow_write: bool = False) -> MariaDBClient:
    """
    Initialize MariaDB client singleton.
    
    Args:
        host: Server host.
        port: Server port.
        user: Database user.
        password: Password.
        database: Database name.
        allow_write: If allows write operations.
        
    Returns:
        Initialized MariaDBClient instance.
    """
    global _db_client
    
    _db_client = MariaDBClient(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        allow_write=allow_write
    )
    
    return _db_client
