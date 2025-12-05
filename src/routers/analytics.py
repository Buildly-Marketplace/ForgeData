"""
Analytics router for database-native visualization (star schema approach)
Similar to Superset - direct database querying with dimensional modeling support
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import json

from src.services.credential_service import CredentialService
from src.models.credentials import CloudProvider
from src.routers.onboarding import get_credential_service
from src.core.database import get_session


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


class StarSchemaQuery(BaseModel):
    """Star schema query model for dimensional analysis"""
    fact_table: str = Field(..., description="The fact table name")
    dimensions: List[str] = Field(default=[], description="Dimension tables to join")
    metrics: List[str] = Field(..., description="Metrics to aggregate (e.g., 'SUM(amount)', 'COUNT(*)')")
    group_by: List[str] = Field(default=[], description="Dimensions to group by")
    filters: Dict[str, Any] = Field(default={}, description="WHERE clause filters")
    order_by: Optional[str] = Field(None, description="ORDER BY clause")
    limit: Optional[int] = Field(100, description="Result limit")


class DatabaseQuery(BaseModel):
    """Direct SQL query model"""
    connection_id: int = Field(..., description="Database connection ID")
    query: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(1000, description="Maximum rows to return")


class DataExplorerQuery(BaseModel):
    """Interactive data explorer query"""
    connection_id: int
    table: str
    columns: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    aggregations: Optional[Dict[str, str]] = None  # {"column": "function"}
    group_by: Optional[List[str]] = None
    order_by: Optional[str] = None
    limit: int = 100


def get_db_engine(connection_string: str):
    """Create database engine from connection string"""
    return create_engine(connection_string)


@router.post("/query/sql")
async def execute_sql_query(
    query: DatabaseQuery,
    credential_service: CredentialService = Depends(get_credential_service)
):
    """
    Execute raw SQL query against a database connection.
    Supports complex analytics queries, joins, and aggregations.
    """
    # Get connection details
    import sqlite3
    conn = sqlite3.connect("./forgedata.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT host, port, username_encrypted, password_encrypted, database, ssl_enabled, db_type FROM database_connections WHERE id = ?",
        (query.connection_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found"
        )
    
    host, port, user_enc, pass_enc, database, ssl_enabled, db_type = result
    
    # Decrypt credentials
    username = credential_service._decrypt(user_enc)
    password = credential_service._decrypt(pass_enc)
    
    # Build connection string
    ssl_param = "?sslmode=require" if ssl_enabled else ""
    connection_string = f"{db_type}://{username}:{password}@{host}:{port}/{database}{ssl_param}"
    
    try:
        engine = get_db_engine(connection_string)
        
        # Execute query with pandas for easy JSON conversion
        df = pd.read_sql_query(text(query.query), engine, params={})
        
        # Apply limit
        if query.limit:
            df = df.head(query.limit)
        
        # Convert to JSON-serializable format
        result_data = df.to_dict(orient='records')
        
        return {
            "status": "success",
            "rows": len(result_data),
            "columns": list(df.columns),
            "data": result_data,
            "query": query.query
        }
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query execution failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/schema/{connection_id}")
async def get_database_schema(
    connection_id: int,
    credential_service: CredentialService = Depends(get_credential_service)
):
    """
    Get complete database schema including tables, columns, types, and relationships.
    Useful for building star schema queries and data exploration.
    """
    import sqlite3
    conn = sqlite3.connect("./forgedata.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT host, port, username_encrypted, password_encrypted, database, ssl_enabled, db_type FROM database_connections WHERE id = ?",
        (connection_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found"
        )
    
    host, port, user_enc, pass_enc, database, ssl_enabled, db_type = result
    
    # Decrypt credentials
    username = credential_service._decrypt(user_enc)
    password = credential_service._decrypt(pass_enc)
    
    # Build connection string
    ssl_param = "?sslmode=require" if ssl_enabled else ""
    connection_string = f"{db_type}://{username}:{password}@{host}:{port}/{database}{ssl_param}"
    
    try:
        engine = get_db_engine(connection_string)
        inspector = inspect(engine)
        
        schema_info = {
            "database": database,
            "tables": []
        }
        
        for table_name in inspector.get_table_names():
            columns = []
            for col in inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": str(col.get("default")) if col.get("default") else None
                })
            
            # Get foreign keys for relationship mapping
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    "columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                })
            
            # Get primary keys
            pk = inspector.get_pk_constraint(table_name)
            primary_keys = pk.get("constrained_columns", []) if pk else []
            
            # Get indexes
            indexes = []
            for idx in inspector.get_indexes(table_name):
                indexes.append({
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx.get("unique", False)
                })
            
            schema_info["tables"].append({
                "name": table_name,
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "row_count": None  # Can be expensive, make optional
            })
        
        return schema_info
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema introspection failed: {str(e)}"
        )


@router.post("/explore")
async def explore_data(
    query: DataExplorerQuery,
    credential_service: CredentialService = Depends(get_credential_service)
):
    """
    Interactive data exploration with filters, aggregations, and grouping.
    Builds SQL queries dynamically based on user selections.
    """
    import sqlite3
    conn = sqlite3.connect("./forgedata.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT host, port, username_encrypted, password_encrypted, database, ssl_enabled, db_type FROM database_connections WHERE id = ?",
        (query.connection_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found"
        )
    
    host, port, user_enc, pass_enc, database, ssl_enabled, db_type = result
    
    username = credential_service._decrypt(user_enc)
    password = credential_service._decrypt(pass_enc)
    
    ssl_param = "?sslmode=require" if ssl_enabled else ""
    connection_string = f"{db_type}://{username}:{password}@{host}:{port}/{database}{ssl_param}"
    
    # Build dynamic SQL query
    select_parts = []
    
    if query.aggregations:
        # Aggregation mode
        for col, func in query.aggregations.items():
            select_parts.append(f"{func}({col}) as {col}_{func.lower()}")
        if query.group_by:
            select_parts.extend(query.group_by)
    else:
        # Regular select
        if query.columns:
            select_parts = query.columns
        else:
            select_parts = ["*"]
    
    sql = f"SELECT {', '.join(select_parts)} FROM {query.table}"
    
    # Add filters
    if query.filters:
        where_clauses = []
        for col, value in query.filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{col} = '{value}'")
            elif isinstance(value, (int, float)):
                where_clauses.append(f"{col} = {value}")
            elif isinstance(value, dict):
                # Support operators like {"op": ">=", "value": 100}
                op = value.get("op", "=")
                val = value.get("value")
                if isinstance(val, str):
                    where_clauses.append(f"{col} {op} '{val}'")
                else:
                    where_clauses.append(f"{col} {op} {val}")
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
    
    # Add GROUP BY
    if query.group_by:
        sql += f" GROUP BY {', '.join(query.group_by)}"
    
    # Add ORDER BY
    if query.order_by:
        sql += f" ORDER BY {query.order_by}"
    
    # Add LIMIT
    sql += f" LIMIT {query.limit}"
    
    try:
        engine = get_db_engine(connection_string)
        df = pd.read_sql_query(text(sql), engine)
        
        return {
            "status": "success",
            "table": query.table,
            "rows": len(df),
            "columns": list(df.columns),
            "data": df.to_dict(orient='records'),
            "query_executed": sql,
            "aggregations": query.aggregations is not None
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query execution failed: {str(e)}"
        )


@router.get("/star-schema/suggestions/{connection_id}")
async def suggest_star_schema(
    connection_id: int,
    credential_service: CredentialService = Depends(get_credential_service)
):
    """
    Analyze database schema and suggest potential fact and dimension tables
    for star schema modeling based on relationships and naming conventions.
    """
    # Get schema first
    schema = await get_database_schema(connection_id, credential_service)
    
    fact_candidates = []
    dimension_candidates = []
    
    for table in schema["tables"]:
        table_name = table["name"]
        
        # Heuristics for identifying fact vs dimension tables
        has_many_fks = len(table["foreign_keys"]) >= 2
        has_metrics = any(
            col["type"].lower() in ["integer", "numeric", "decimal", "float", "double"]
            for col in table["columns"]
            if col["name"].lower() in ["amount", "quantity", "total", "count", "sum"]
        )
        has_dates = any(
            col["type"].lower() in ["date", "timestamp", "datetime"]
            for col in table["columns"]
        )
        
        # Fact table indicators
        if has_many_fks and (has_metrics or has_dates):
            fact_candidates.append({
                "table": table_name,
                "reason": "Multiple foreign keys with numeric metrics",
                "foreign_keys": len(table["foreign_keys"]),
                "metric_columns": [
                    col["name"] for col in table["columns"]
                    if col["type"].lower() in ["integer", "numeric", "decimal", "float"]
                ]
            })
        
        # Dimension table indicators
        elif len(table["foreign_keys"]) <= 1:
            dimension_candidates.append({
                "table": table_name,
                "reason": "Few foreign keys, likely descriptive data",
                "columns": len(table["columns"]),
                "has_pk": len(table["primary_keys"]) > 0
            })
    
    return {
        "fact_tables": fact_candidates,
        "dimension_tables": dimension_candidates,
        "star_schema_ready": len(fact_candidates) > 0 and len(dimension_candidates) >= 2
    }


@router.post("/pivot")
async def create_pivot_table(
    connection_id: int,
    table: str,
    rows: List[str],
    columns: List[str],
    values: str,
    aggregation: str = "SUM",
    credential_service: CredentialService = Depends(get_credential_service)
):
    """
    Create a pivot table from database data.
    Similar to Excel pivot tables or Superset's pivot functionality.
    """
    import sqlite3
    conn = sqlite3.connect("./forgedata.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT host, port, username_encrypted, password_encrypted, database, ssl_enabled, db_type FROM database_connections WHERE id = ?",
        (connection_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    host, port, user_enc, pass_enc, database, ssl_enabled, db_type = result
    username = credential_service._decrypt(user_enc)
    password = credential_service._decrypt(pass_enc)
    
    ssl_param = "?sslmode=require" if ssl_enabled else ""
    connection_string = f"{db_type}://{username}:{password}@{host}:{port}/{database}{ssl_param}"
    
    try:
        engine = get_db_engine(connection_string)
        
        # Load data
        df = pd.read_sql_query(text(f"SELECT * FROM {table}"), engine)
        
        # Create pivot table
        pivot = pd.pivot_table(
            df,
            values=values,
            index=rows,
            columns=columns,
            aggfunc=aggregation.lower(),
            fill_value=0
        )
        
        # Convert to records format
        pivot_reset = pivot.reset_index()
        
        return {
            "status": "success",
            "pivot_data": pivot_reset.to_dict(orient='records'),
            "rows": rows,
            "columns": columns,
            "values": values,
            "aggregation": aggregation
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Pivot creation failed: {str(e)}"
        )


@router.get("/dashboards")
async def list_dashboards():
    """List available pre-built dashboards"""
    return {
        "dashboards": [
            {
                "id": "overview_dashboard",
                "name": "System Overview",
                "description": "Key metrics from all databases",
                "charts": ["user_growth", "decision_stats", "product_overview"]
            },
            {
                "id": "migration_status",
                "name": "Migration Status",
                "description": "GCP to Digital Ocean migration analytics",
                "charts": ["database_sizes", "table_counts", "row_counts"]
            }
        ]
    }
