"""
Databricks SQL API Client Wrapper
"""
import logging
from typing import Optional, List, Dict, Any
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from databricks.sql import connect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type hint only - Connection is not directly importable
    from databricks.sql import Connection
import time

logger = logging.getLogger(__name__)


class DatabricksClient:
    """Wrapper for Databricks SQL API operations"""
    
    def __init__(
        self,
        workspace_url: Optional[str] = None,
        token: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        workspace_client: Optional[WorkspaceClient] = None
    ):
        """
        Initialize Databricks client
        
        Args:
            workspace_url: Databricks workspace URL (optional if using workspace_client)
            token: Databricks personal access token (optional if using workspace_client or SP)
            warehouse_id: SQL Warehouse ID (required for SQL queries)
            workspace_client: Optional pre-configured WorkspaceClient (uses SP if None and in Databricks Apps)
        """
        if workspace_client:
            # Use provided WorkspaceClient (may be SP, PAT, or OAuth-based)
            self.w = workspace_client
            self.workspace_url = self.w.config.host
            # Get token if available (may be None for SP auth)
            # Try multiple ways to get the token from WorkspaceClient config
            self.token = (
                getattr(self.w.config, 'token', None) or 
                getattr(self.w.config, '_token', None) or
                getattr(self.w.config, 'access_token', None) or
                (hasattr(self.w.config, '__dict__') and self.w.config.__dict__.get('token')) or
                None
            )
            # Log token status for debugging
            import logging
            logger = logging.getLogger(__name__)
            if self.token:
                logger.info(f"✅ Token extracted from WorkspaceClient (length: {len(self.token)})")
            else:
                logger.warning("⚠️  No token found in WorkspaceClient - will use SP auth")
        elif workspace_url and token:
            # Use explicit workspace URL and token
            self.workspace_url = workspace_url
            self.token = token
            self.w = WorkspaceClient(host=workspace_url, token=token)
        else:
            # Default: Use app's Service Principal (WorkspaceClient() uses platform-provided SP creds)
            # This works in Databricks Apps where DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET, DATABRICKS_HOST are provided
            self.w = WorkspaceClient()
            self.workspace_url = self.w.config.host
            self.token = None  # SP auth doesn't use token
        
        self.warehouse_id = warehouse_id
        self._connection = None  # Connection object from databricks.sql.connect()
    
    def get_connection(self):
        """Get or create SQL connection"""
        if self._connection is None or self._connection.is_closed:
            if not self.warehouse_id:
                raise ValueError("warehouse_id is required for SQL connections")
            
            # For SP auth, we need to use SDK's statement execution API instead
            # databricks.sql.connect() requires a token, but SP uses client_id/secret
            if not self.token:
                raise ValueError("SQL connection requires token. Use execute_query_sdk() for SP authentication.")
            
            self._connection = connect(
                server_hostname=self.workspace_url.replace("https://", ""),
                http_path=f"/sql/1.0/warehouses/{self.warehouse_id}",
                token=self.token
            )
        
        return self._connection
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            parameters: Optional query parameters
            timeout: Query timeout in seconds
            
        Returns:
            List of dictionaries representing query results
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Replace parameters in query if provided
            if parameters:
                for key, value in parameters.items():
                    # Simple parameter replacement (for :param_name format)
                    query = query.replace(f":{key}", str(value))
            
            logger.debug(f"Executing query: {query[:200]}...")
            cursor.execute(query)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]
            
            cursor.close()
            
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def execute_query_sdk(
        self,
        query: str,
        warehouse_id: Optional[str] = None,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Execute query using Databricks SDK (alternative method)
        
        Args:
            query: SQL query string
            warehouse_id: SQL Warehouse ID (uses instance default if not provided)
            timeout: Query timeout in seconds (must be between 5-50, default: 30)
            
        Returns:
            List of dictionaries representing query results
        """
        warehouse_id = warehouse_id or self.warehouse_id
        if not warehouse_id:
            raise ValueError("warehouse_id is required")
        
        # Databricks SQL Execution API requires wait_timeout between 5-50 seconds
        # Clamp timeout to valid range
        if timeout < 5:
            timeout = 5
        elif timeout > 50:
            timeout = 50
        
        try:
            # Use SQL Execution API
            # Note: wait_timeout must be between 5-50 seconds
            execution = self.w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=query,
                wait_timeout=f"{timeout}s"
            )

            # Check execution state
            # Note: State might be PENDING if query takes longer than wait_timeout
            # In that case, we'll get the final state from get_statement() below
            state = execution.status.state
            if state != StatementState.SUCCEEDED and state != StatementState.PENDING:
                error_message = f"Query failed with state: {state}"
                
                # Try to get detailed error message from various sources
                error_details = []
                
                # Check execution.status for error details
                if hasattr(execution, 'status'):
                    status = execution.status
                    # Check all possible error fields
                    for attr in ['status_message', 'message', 'error', 'error_message', 'error_code', 'error_description']:
                        if hasattr(status, attr):
                            value = getattr(status, attr, None)
                            if value:
                                error_details.append(f"{attr}: {value}")
                
                # Check execution.result for error details
                if hasattr(execution, 'result') and execution.result:
                    result = execution.result
                    for attr in ['error', 'error_message', 'error_code', 'error_description']:
                        if hasattr(result, attr):
                            value = getattr(result, attr, None)
                            if value:
                                error_details.append(f"result.{attr}: {value}")
                    
                    # Check manifest for errors
                    if hasattr(result, 'manifest') and result.manifest:
                        manifest = result.manifest
                        for attr in ['error', 'error_message', 'error_code']:
                            if hasattr(manifest, attr):
                                value = getattr(manifest, attr, None)
                                if value:
                                    error_details.append(f"manifest.{attr}: {value}")
                
                # If we still don't have details, try to get the full execution object as string
                if not error_details:
                    try:
                        import json
                        exec_dict = execution.__dict__ if hasattr(execution, '__dict__') else {}
                        error_details.append(f"Full execution: {json.dumps(str(exec_dict), indent=2)[:500]}")
                    except:
                        pass
                
                if error_details:
                    error_message += f" - {' | '.join(error_details)}"
                else:
                    error_message += " - No detailed error message available"
                
                # Log the query for debugging (first 500 chars)
                logger.error(f"Query execution failed: {error_message}")
                logger.error(f"Failed query (first 500 chars): {query[:500]}")
                
                # Also try to get statement details if available
                if hasattr(execution, 'statement_id'):
                    try:
                        statement_details = self.w.statement_execution.get_statement(execution.statement_id)
                        logger.error(f"Statement details: {statement_details}")
                    except Exception as e:
                        logger.debug(f"Could not get statement details: {e}")
                
                raise Exception(error_message)
            
            # Extract results
            results = []
            # Always use get_statement() to get the full result with schema
            try:
                statement_details = self.w.statement_execution.get_statement(execution.statement_id)
                
                # Check if we have result data
                if statement_details.result and hasattr(statement_details.result, 'data_array'):
                    data_array = statement_details.result.data_array
                    
                    if data_array:
                        # Get column names from manifest schema
                        column_names = []
                        if (hasattr(statement_details.result, 'manifest') and 
                            statement_details.result.manifest and
                            hasattr(statement_details.result.manifest, 'schema') and
                            statement_details.result.manifest.schema and
                            hasattr(statement_details.result.manifest.schema, 'columns')):
                            columns = statement_details.result.manifest.schema.columns
                            column_names = [col.name for col in columns]
                        else:
                            # Fallback: infer column names from first row
                            if len(data_array) > 0:
                                first_row = data_array[0]
                                if isinstance(first_row, (list, tuple)):
                                    column_names = [f"column_{i}" for i in range(len(first_row))]
                                elif isinstance(first_row, dict):
                                    column_names = list(first_row.keys())
                        
                        # Convert rows to dictionaries
                        if column_names:
                            for row in data_array:
                                if isinstance(row, (list, tuple)):
                                    results.append(dict(zip(column_names, row)))
                                elif isinstance(row, dict):
                                    results.append(row)
                                else:
                                    results.append({column_names[0]: row})
                        else:
                            # No column names, return as-is
                            results = list(data_array) if isinstance(data_array, list) else [data_array]
                            
            except Exception as e:
                logger.error(f"Error extracting results from statement: {e}")
                # Last resort: try execution.result directly (may not have schema)
                if execution.result and hasattr(execution.result, 'data_array'):
                    logger.warning("Using execution.result directly (no schema available)")
                    if execution.result.data_array:
                        # Infer column names from first row
                        first_row = execution.result.data_array[0]
                        if isinstance(first_row, (list, tuple)):
                            column_names = [f"col_{i}" for i in range(len(first_row))]
                            for row in execution.result.data_array:
                                results.append(dict(zip(column_names, row)))
                        else:
                            results = list(execution.result.data_array)
                else:
                    raise Exception(f"Could not extract results: {e}")
            
            logger.info(f"Query executed successfully via SDK, returned {len(results)} rows")
            return results
            
        except ValueError as e:
            # Re-raise ValueError (e.g., missing warehouse_id) as-is
            logger.error(f"Configuration error: {str(e)}")
            raise
        except Exception as e:
            # Provide more detailed error information
            error_msg = str(e)
            logger.error(f"Error executing query via SDK: {error_msg}")
            
            # Check for common error patterns and provide helpful messages
            if "warehouse" in error_msg.lower() or "warehouse_id" in error_msg.lower():
                raise ValueError(f"Warehouse configuration error: {error_msg}. Ensure DATABRICKS_WAREHOUSE_ID is set and the warehouse is accessible.")
            elif "permission" in error_msg.lower() or "unauthorized" in error_msg.lower():
                raise PermissionError(f"Permission denied: {error_msg}. Ensure the Service Principal has access to the SQL warehouse and system tables.")
            elif "timeout" in error_msg.lower():
                raise TimeoutError(f"Query timeout: {error_msg}. The query took longer than {timeout} seconds.")
            else:
                raise Exception(f"Query execution failed: {error_msg}")
    
    def close(self):
        """Close SQL connection"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
