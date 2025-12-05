"""
Data Explorer Router
Browse and query databases, tables, and data in real-time
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from src.routers.auth import get_current_user, UserData
from src.services.explorer_service import ExplorerService
from src.core.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


class TableSchema(BaseModel):
    table_name: str
    columns: List[Dict[str, str]]
    row_count: Optional[int]


class QueryRequest(BaseModel):
    connection_id: str
    query: str
    limit: Optional[int] = 1000


@router.get("/connections/{connection_id}/schema")
async def get_database_schema(
    connection_id: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Get complete database schema"""
    try:
        explorer_service = ExplorerService(db)
        schema = await explorer_service.get_schema(connection_id, current_user.organization_id)
        return {"schema": schema}
    except Exception as e:
        logger.error(f"Failed to get schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/tables/{table_name}")
async def get_table_data(
    connection_id: str,
    table_name: str,
    limit: int = Query(100, le=10000),
    offset: int = Query(0, ge=0),
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Get data from a specific table"""
    try:
        explorer_service = ExplorerService(db)
        data = await explorer_service.get_table_data(
            connection_id,
            current_user.organization_id,
            table_name,
            limit=limit,
            offset=offset
        )
        return data
    except Exception as e:
        logger.error(f"Failed to get table data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/tables/{table_name}/schema")
async def get_table_schema(
    connection_id: str,
    table_name: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Get schema for a specific table"""
    try:
        explorer_service = ExplorerService(db)
        schema = await explorer_service.get_table_schema(
            connection_id,
            current_user.organization_id,
            table_name
        )
        return TableSchema(
            table_name=table_name,
            columns=schema["columns"],
            row_count=schema.get("row_count")
        )
    except Exception as e:
        logger.error(f"Failed to get table schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def execute_query(
    query_request: QueryRequest,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Execute a custom SQL query"""
    try:
        explorer_service = ExplorerService(db)
        results = await explorer_service.execute_query(
            query_request.connection_id,
            current_user.organization_id,
            query_request.query,
            limit=query_request.limit
        )
        return results
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/stats")
async def get_database_stats(
    connection_id: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Get database statistics"""
    try:
        explorer_service = ExplorerService(db)
        stats = await explorer_service.get_database_stats(
            connection_id,
            current_user.organization_id
        )
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
