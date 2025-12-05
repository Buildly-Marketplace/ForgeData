"""
ETL Service
Handles ETL operations, anonymization, and deduplication
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any, Optional
import pandas as pd
import logging
import asyncio

from src.core.database import (
    ConnectionConfig,
    ETLJob,
    DatabaseConnectionFactory
)

logger = logging.getLogger(__name__)


class ETLService:
    """Service for ETL operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_connection(
        self,
        organization_id: str,
        name: str,
        provider: str,
        config: Dict[str, Any]
    ) -> str:
        """Create a new database connection configuration"""
        conn_id = str(uuid4())
        connection = ConnectionConfig(
            id=conn_id,
            organization_id=organization_id,
            name=name,
            provider=provider,
            connection_type=config.get("db_type", "postgresql"),
            config=config
        )
        
        self.db.add(connection)
        await self.db.commit()
        return conn_id
    
    async def get_connection(self, connection_id: str) -> ConnectionConfig:
        """Get connection by ID"""
        result = await self.db.execute(
            select(ConnectionConfig).where(ConnectionConfig.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise ValueError("Connection not found")
        return connection
    
    async def list_connections(self, organization_id: str) -> List[ConnectionConfig]:
        """List all connections for an organization"""
        result = await self.db.execute(
            select(ConnectionConfig).where(
                ConnectionConfig.organization_id == organization_id
            )
        )
        return result.scalars().all()
    
    async def test_connection(self, connection_id: str) -> bool:
        """Test database connection"""
        try:
            connection = await self.get_connection(connection_id)
            connection_string = DatabaseConnectionFactory.create_connection_string(
                connection.provider,
                connection.config
            )
            
            # Create a temporary sync engine for testing
            from sqlalchemy import create_engine
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def list_tables(self, connection_id: str, organization_id: str) -> List[str]:
        """List all tables in a database"""
        connection = await self.get_connection(connection_id)
        if connection.organization_id != organization_id:
            raise ValueError("Unauthorized access to connection")
        
        connection_string = DatabaseConnectionFactory.create_connection_string(
            connection.provider,
            connection.config
        )
        
        from sqlalchemy import create_engine, inspect
        engine = create_engine(connection_string)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()
        
        return tables
    
    async def create_job(
        self,
        organization_id: str,
        connection_id: str,
        name: str,
        config: Dict[str, Any]
    ) -> str:
        """Create a new ETL job"""
        job_id = str(uuid4())
        job = ETLJob(
            id=job_id,
            organization_id=organization_id,
            connection_id=connection_id,
            name=name,
            status="pending",
            config=config
        )
        
        self.db.add(job)
        await self.db.commit()
        return job_id
    
    async def get_job(self, job_id: str) -> ETLJob:
        """Get job by ID"""
        result = await self.db.execute(
            select(ETLJob).where(ETLJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError("Job not found")
        return job
    
    async def list_jobs(self, organization_id: str) -> List[ETLJob]:
        """List all jobs for an organization"""
        result = await self.db.execute(
            select(ETLJob).where(ETLJob.organization_id == organization_id)
        )
        return result.scalars().all()
    
    async def run_job(self, job_id: str):
        """Execute an ETL job"""
        job = await self.get_job(job_id)
        
        try:
            # Update job status
            job.status = "running"
            job.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Get connection
            connection = await self.get_connection(job.connection_id)
            connection_string = DatabaseConnectionFactory.create_connection_string(
                connection.provider,
                connection.config
            )
            
            # Execute ETL process
            await self._execute_etl(connection_string, job)
            
            # Mark as completed
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"ETL job {job_id} failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await self.db.commit()
    
    async def _execute_etl(self, connection_string: str, job: ETLJob):
        """Execute the ETL process"""
        from sqlalchemy import create_engine
        import pandas as pd
        
        engine = create_engine(connection_string)
        
        try:
            # Read source data
            source_table = job.config["source_table"]
            logger.info(f"Reading data from {source_table}")
            df = pd.read_sql_table(source_table, engine)
            
            # Apply anonymization if enabled
            if job.config.get("anonymize", False):
                df = self._anonymize_data(df, job.config.get("anonymization_rules", {}))
            
            # Apply deduplication if enabled
            if job.config.get("deduplicate", False):
                dedup_columns = job.config.get("deduplication_columns", [])
                if dedup_columns:
                    df = df.drop_duplicates(subset=dedup_columns, keep="first")
                else:
                    df = df.drop_duplicates()
            
            # Write to target table
            target_table = job.config["target_table"]
            mode = job.config.get("mode", "append")
            
            if mode == "reset":
                df.to_sql(target_table, engine, if_exists="replace", index=False)
            elif mode == "append":
                df.to_sql(target_table, engine, if_exists="append", index=False)
            else:
                raise ValueError(f"Unsupported mode: {mode}")
            
            logger.info(f"ETL completed: {len(df)} rows processed")
            
        finally:
            engine.dispose()
    
    def _anonymize_data(self, df: pd.DataFrame, rules: Dict[str, str]) -> pd.DataFrame:
        """
        Anonymize sensitive data in DataFrame
        Rules format: {column_name: method}
        Methods: hash, mask, redact, substitute, generalize
        """
        import hashlib
        import random
        import string
        
        df = df.copy()
        
        for column, method in rules.items():
            if column not in df.columns:
                continue
            
            if method == "hash":
                # Hash the value
                df[column] = df[column].apply(
                    lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:16] if pd.notna(x) else x
                )
            
            elif method == "mask":
                # Mask with asterisks (keep first and last char)
                df[column] = df[column].apply(
                    lambda x: x[0] + '*' * (len(str(x)) - 2) + x[-1] 
                    if pd.notna(x) and len(str(x)) > 2 else '***'
                )
            
            elif method == "redact":
                # Remove completely
                df[column] = "[REDACTED]"
            
            elif method == "substitute":
                # Replace with random similar value
                if df[column].dtype == 'object':
                    df[column] = df[column].apply(
                        lambda x: ''.join(random.choices(string.ascii_letters, k=len(str(x)))) 
                        if pd.notna(x) else x
                    )
                else:
                    df[column] = df[column].apply(
                        lambda x: random.randint(1, 100000) if pd.notna(x) else x
                    )
            
            elif method == "generalize":
                # Generalize to category/range
                if pd.api.types.is_numeric_dtype(df[column]):
                    # Round to nearest 10
                    df[column] = (df[column] // 10) * 10
                else:
                    df[column] = "GENERALIZED"
        
        return df
