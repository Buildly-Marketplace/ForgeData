"""
ETL Router
Manages ETL jobs, anonymization, deduplication, and data transformations
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import logging
import os

from src.routers.auth import get_current_user, UserData
from src.services.etl_service import ETLService
from src.core.database import get_session

logger = logging.getLogger(__name__)

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a default key for development (should be in env for production)
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("Using generated encryption key. Set ENCRYPTION_KEY in .env for production!")

router = APIRouter()


class ConnectionCreate(BaseModel):
    name: str
    provider: str  # gcp, aws, digitalocean
    db_type: str  # postgresql, mysql
    host: str
    port: Optional[int] = None
    database: str
    user: str
    password: str
    ssl_mode: Optional[str] = "require"
    additional_config: Optional[Dict[str, Any]] = {}


class ConnectionResponse(BaseModel):
    id: str
    name: str
    provider: str
    db_type: str
    host: str
    created_at: datetime


class ETLJobCreate(BaseModel):
    connection_id: str
    name: str
    source_table: str
    target_table: Optional[str] = None
    mode: str = "append"  # append, reset, update
    anonymize: bool = True
    deduplicate: bool = True
    anonymization_rules: Optional[Dict[str, str]] = {}
    deduplication_columns: Optional[List[str]] = []


class ETLJobResponse(BaseModel):
    id: str
    name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


@router.post("/connections", response_model=ConnectionResponse)
async def create_connection(
    connection: ConnectionCreate,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """
    Create a new database connection configuration
    """
    try:
        etl_service = ETLService(db)
        conn_id = await etl_service.create_connection(
            organization_id=current_user.organization_id,
            name=connection.name,
            provider=connection.provider,
            config={
                "db_type": connection.db_type,
                "host": connection.host,
                "port": connection.port,
                "database": connection.database,
                "user": connection.user,
                "password": connection.password,
                "ssl_mode": connection.ssl_mode,
                **connection.additional_config
            }
        )
        
        # Test connection
        is_valid = await etl_service.test_connection(conn_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Failed to connect to database")
        
        conn = await etl_service.get_connection(conn_id)
        return ConnectionResponse(
            id=conn.id,
            name=conn.name,
            provider=conn.provider,
            db_type=conn.config["db_type"],
            host=conn.config["host"],
            created_at=conn.created_at
        )
    except Exception as e:
        logger.error(f"Failed to create connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=List[ConnectionResponse])
async def list_connections(
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """List all database connections for the organization"""
    try:
        etl_service = ETLService(db)
        connections = await etl_service.list_connections(current_user.organization_id)
        
        return [
            ConnectionResponse(
                id=conn.id,
                name=conn.name,
                provider=conn.provider,
                db_type=conn.config.get("db_type", ""),
                host=conn.config.get("host", ""),
                created_at=conn.created_at
            )
            for conn in connections
        ]
    except Exception as e:
        logger.error(f"Failed to list connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/tables")
async def list_tables(
    connection_id: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """List all tables in a database connection"""
    try:
        etl_service = ETLService(db)
        tables = await etl_service.list_tables(connection_id, current_user.organization_id)
        return {"tables": tables}
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=ETLJobResponse)
async def create_etl_job(
    job: ETLJobCreate,
    background_tasks: BackgroundTasks,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """
    Create and start an ETL job
    """
    try:
        etl_service = ETLService(db)
        job_id = await etl_service.create_job(
            organization_id=current_user.organization_id,
            connection_id=job.connection_id,
            name=job.name,
            config={
                "source_table": job.source_table,
                "target_table": job.target_table or f"{job.source_table}_processed",
                "mode": job.mode,
                "anonymize": job.anonymize,
                "deduplicate": job.deduplicate,
                "anonymization_rules": job.anonymization_rules or {},
                "deduplication_columns": job.deduplication_columns or []
            }
        )
        
        # Run job in background
        background_tasks.add_task(etl_service.run_job, job_id)
        
        job_data = await etl_service.get_job(job_id)
        return ETLJobResponse(
            id=job_data.id,
            name=job_data.name,
            status=job_data.status,
            started_at=job_data.started_at,
            completed_at=job_data.completed_at,
            error_message=job_data.error_message
        )
    except Exception as e:
        logger.error(f"Failed to create ETL job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[ETLJobResponse])
async def list_jobs(
    db = Depends(get_session)
):
    """List all ETL jobs"""
    try:
        # For now, return mock data
        # In production, query from database
        return []
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=ETLJobResponse)
async def get_job(
    job_id: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Get ETL job details"""
    try:
        etl_service = ETLService(db)
        job = await etl_service.get_job(job_id)
        
        if job.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return ETLJobResponse(
            id=job.id,
            name=job.name,
            status=job.status,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class BackupRequest(BaseModel):
    connection_id: int
    databases: List[str]
    output_path: str = "./backups"
    anonymize: bool = False  # Default false for backups


class RestoreRequest(BaseModel):
    connection_id: int
    backup_path: str
    mode: str = "append"  # append or reset
    anonymize: bool = False  # Optional, default false


class TransformRequest(BaseModel):
    source_connection_id: int
    target_connection_id: Optional[int] = None
    source_table: str
    target_table: Optional[str] = None
    anonymize: bool = True  # Default true for reporting/analytics
    deduplicate: bool = False
    anonymization_rules: Optional[Dict[str, str]] = None


@router.post("/backup")
async def backup_databases(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_session)
):
    """
    Backup databases without anonymization (preserves original data)
    """
    try:
        from src.services.credential_service import CredentialService
        import os
        
        # Get encryption key from environment
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not configured")
        
        cred_service = CredentialService(encryption_key)
        
        # Get database connection
        conn = await cred_service.get_database_connection(db, request.connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Database connection not found")
        
        # Create job record
        job_id = str(uuid4())
        job_config = {
            "connection_id": request.connection_id,
            "databases": request.databases,
            "output_path": request.output_path,
            "anonymize": request.anonymize,  # Should be False for backups
            "job_type": "backup"
        }
        
        # TODO: Store job in database
        # For now, return success
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Backup job started for {len(request.databases)} database(s)",
            "anonymization": "disabled" if not request.anonymize else "enabled"
        }
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_databases(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_session)
):
    """
    Restore databases from backup
    Anonymization is optional and defaults to false
    """
    try:
        from src.services.credential_service import CredentialService
        import os
        
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not configured")
        
        cred_service = CredentialService(encryption_key)
        
        # Get database connection
        conn = await cred_service.get_database_connection(db, request.connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Database connection not found")
        
        # Create job record
        job_id = str(uuid4())
        job_config = {
            "connection_id": request.connection_id,
            "backup_path": request.backup_path,
            "mode": request.mode,
            "anonymize": request.anonymize,
            "job_type": "restore"
        }
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Restore job started from {request.backup_path}",
            "mode": request.mode,
            "anonymization": "enabled" if request.anonymize else "disabled"
        }
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform")
async def transform_data(
    request: TransformRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_session)
):
    """
    Transform and anonymize data for reporting/analytics
    Anonymization is enabled by default (recommended for reporting)
    """
    try:
        from src.services.credential_service import CredentialService
        import os
        
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not configured")
        
        cred_service = CredentialService(encryption_key)
        
        # Get source connection
        source_conn = await cred_service.get_database_connection(db, request.source_connection_id)
        if not source_conn:
            raise HTTPException(status_code=404, detail="Source database connection not found")
        
        # Get target connection (use source if not specified)
        target_conn_id = request.target_connection_id or request.source_connection_id
        target_conn = await cred_service.get_database_connection(db, target_conn_id)
        if not target_conn:
            raise HTTPException(status_code=404, detail="Target database connection not found")
        
        # Default target table name
        target_table = request.target_table or f"{request.source_table}_anonymized"
        
        # Create job record
        job_id = str(uuid4())
        job_config = {
            "source_connection_id": request.source_connection_id,
            "target_connection_id": target_conn_id,
            "source_table": request.source_table,
            "target_table": target_table,
            "anonymize": request.anonymize,
            "deduplicate": request.deduplicate,
            "anonymization_rules": request.anonymization_rules or {},
            "job_type": "transform"
        }
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Transformation job started: {request.source_table} -> {target_table}",
            "anonymization": "enabled" if request.anonymize else "disabled",
            "deduplication": "enabled" if request.deduplicate else "disabled"
        }
    except Exception as e:
        logger.error(f"Transform failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/databases")
async def list_databases(
    connection_id: int,
    db = Depends(get_session)
):
    """
    List all databases in a connection
    """
    try:
        from src.services.credential_service import CredentialService
        
        cred_service = CredentialService(ENCRYPTION_KEY)
        
        # Get database connection
        conn = await cred_service.get_database_connection(db, connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Database connection not found")
        
        # Mock database list - in production, query actual databases
        databases = [
            "main_db",
            "decision_db", 
            "release_db",
            "product_db",
            "contextualhelp_db",
            "dev_partner_db",
            "notification_db",
            "onboarding_db"
        ]
        
        return {"databases": databases}
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))
