"""
Reporting Service
Handles report creation, execution, and star schema queries
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

from src.core.database import Report, ConnectionConfig, DatabaseConnectionFactory

logger = logging.getLogger(__name__)


class ReportingService:
    """Service for reporting operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_report(
        self,
        organization_id: str,
        name: str,
        description: str,
        query_config: Dict[str, Any],
        visualization_config: Dict[str, Any]
    ) -> str:
        """Create a new report"""
        report_id = str(uuid4())
        report = Report(
            id=report_id,
            organization_id=organization_id,
            name=name,
            description=description,
            query_config=query_config,
            visualization_config=visualization_config
        )
        
        self.db.add(report)
        await self.db.commit()
        return report_id
    
    async def get_report(self, report_id: str) -> Report:
        """Get report by ID"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise ValueError("Report not found")
        return report
    
    async def list_reports(self, organization_id: str) -> List[Report]:
        """List all reports for an organization"""
        result = await self.db.execute(
            select(Report).where(Report.organization_id == organization_id)
        )
        return result.scalars().all()
    
    async def execute_report(
        self,
        report_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Execute a report and return results"""
        report = await self.get_report(report_id)
        query_config = report.query_config
        
        # Get connection
        connection_id = query_config.get("connection_id")
        if not connection_id:
            raise ValueError("Report missing connection_id")
        
        result = await self.db.execute(
            select(ConnectionConfig).where(ConnectionConfig.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise ValueError("Connection not found")
        
        # Build and execute query
        query = self._build_query(query_config, filters, limit)
        results = await self._execute_query(connection, query)
        
        return results
    
    def _build_query(
        self,
        query_config: Dict[str, Any],
        filters: Optional[Dict[str, Any]],
        limit: int
    ) -> str:
        """Build SQL query from configuration"""
        # Extract query components
        table = query_config.get("table")
        columns = query_config.get("columns", ["*"])
        where_clause = query_config.get("where")
        group_by = query_config.get("group_by")
        order_by = query_config.get("order_by")
        
        # Build SELECT clause
        if isinstance(columns, list):
            select_clause = ", ".join(columns)
        else:
            select_clause = columns
        
        query = f"SELECT {select_clause} FROM {table}"
        
        # Add WHERE clause
        where_conditions = []
        if where_clause:
            where_conditions.append(where_clause)
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    where_conditions.append(f"{key} = '{value}'")
                else:
                    where_conditions.append(f"{key} = {value}")
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add GROUP BY
        if group_by:
            query += f" GROUP BY {group_by}"
        
        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT
        query += f" LIMIT {limit}"
        
        return query
    
    async def _execute_query(
        self,
        connection: ConnectionConfig,
        query: str
    ) -> Dict[str, Any]:
        """Execute query and return results"""
        from sqlalchemy import create_engine
        
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        engine = create_engine(connection_string)
        
        try:
            df = pd.read_sql(query, engine)
            
            return {
                "data": df.to_dict(orient="records"),
                "columns": list(df.columns),
                "row_count": len(df)
            }
        finally:
            engine.dispose()
    
    async def delete_report(self, report_id: str):
        """Delete a report"""
        report = await self.get_report(report_id)
        await self.db.delete(report)
        await self.db.commit()
