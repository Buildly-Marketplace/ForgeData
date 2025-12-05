"""
Explorer Service
Provides database browsing and ad-hoc query capabilities
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, inspect
from typing import List, Dict, Any
import pandas as pd
import logging

from src.core.database import ConnectionConfig, DatabaseConnectionFactory

logger = logging.getLogger(__name__)


class ExplorerService:
    """Service for data exploration"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_schema(
        self,
        connection_id: str,
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """Get complete database schema"""
        connection = await self._get_connection(connection_id, organization_id)
        
        from sqlalchemy import create_engine
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        engine = create_engine(connection_string)
        inspector = inspect(engine)
        
        try:
            schema = []
            for table_name in inspector.get_table_names():
                columns = []
                for column in inspector.get_columns(table_name):
                    columns.append({
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column.get("nullable", True),
                        "default": str(column.get("default")) if column.get("default") else None
                    })
                
                schema.append({
                    "table_name": table_name,
                    "columns": columns
                })
            
            return schema
        finally:
            engine.dispose()
    
    async def get_table_data(
        self,
        connection_id: str,
        organization_id: str,
        table_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get data from a specific table"""
        connection = await self._get_connection(connection_id, organization_id)
        
        from sqlalchemy import create_engine
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        engine = create_engine(connection_string)
        
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
            df = pd.read_sql(query, engine)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            count_df = pd.read_sql(count_query, engine)
            total_count = int(count_df.iloc[0]["total"])
            
            return {
                "data": df.to_dict(orient="records"),
                "columns": list(df.columns),
                "row_count": len(df),
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        finally:
            engine.dispose()
    
    async def get_table_schema(
        self,
        connection_id: str,
        organization_id: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Get schema for a specific table"""
        connection = await self._get_connection(connection_id, organization_id)
        
        from sqlalchemy import create_engine
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        engine = create_engine(connection_string)
        inspector = inspect(engine)
        
        try:
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True),
                    "default": str(column.get("default")) if column.get("default") else None,
                    "primary_key": column.get("primary_key", False)
                })
            
            # Get row count
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            count_df = pd.read_sql(count_query, engine)
            row_count = int(count_df.iloc[0]["total"])
            
            return {
                "columns": columns,
                "row_count": row_count
            }
        finally:
            engine.dispose()
    
    async def execute_query(
        self,
        connection_id: str,
        organization_id: str,
        query: str,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Execute a custom SQL query"""
        connection = await self._get_connection(connection_id, organization_id)
        
        # Validate query (basic security check)
        query_upper = query.upper().strip()
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        from sqlalchemy import create_engine
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        engine = create_engine(connection_string)
        
        try:
            # Add LIMIT if not present
            if "LIMIT" not in query_upper:
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            df = pd.read_sql(query, engine)
            
            return {
                "data": df.to_dict(orient="records"),
                "columns": list(df.columns),
                "row_count": len(df),
                "query": query
            }
        finally:
            engine.dispose()
    
    async def get_database_stats(
        self,
        connection_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get database statistics"""
        connection = await self._get_connection(connection_id, organization_id)
        
        from sqlalchemy import create_engine
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        engine = create_engine(connection_string)
        inspector = inspect(engine)
        
        try:
            tables = inspector.get_table_names()
            
            table_stats = []
            total_rows = 0
            
            for table_name in tables:
                try:
                    count_query = f"SELECT COUNT(*) as total FROM {table_name}"
                    count_df = pd.read_sql(count_query, engine)
                    row_count = int(count_df.iloc[0]["total"])
                    total_rows += row_count
                    
                    columns = inspector.get_columns(table_name)
                    
                    table_stats.append({
                        "table_name": table_name,
                        "row_count": row_count,
                        "column_count": len(columns)
                    })
                except Exception as e:
                    logger.warning(f"Failed to get stats for table {table_name}: {e}")
            
            return {
                "total_tables": len(tables),
                "total_rows": total_rows,
                "tables": table_stats
            }
        finally:
            engine.dispose()
    
    async def _get_connection(
        self,
        connection_id: str,
        organization_id: str
    ) -> ConnectionConfig:
        """Get and validate connection"""
        result = await self.db.execute(
            select(ConnectionConfig).where(ConnectionConfig.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise ValueError("Connection not found")
        
        if connection.organization_id != organization_id:
            raise ValueError("Unauthorized access to connection")
        
        return connection
