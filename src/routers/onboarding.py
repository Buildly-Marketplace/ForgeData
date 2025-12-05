"""Onboarding API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from pathlib import Path

from src.core.database import get_session
from src.services.credential_service import CredentialService
from src.models.credentials import CloudProvider, DatabaseType


router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a default key for development (should be in env for production)
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"WARNING: Using generated encryption key. Set ENCRYPTION_KEY in .env for production!")


async def get_db():
    """Dependency for database session."""
    async for session in get_session():
        yield session


def get_credential_service():
    """Dependency for credential service."""
    return CredentialService(ENCRYPTION_KEY)


# Pydantic models

class GCPCredentialsCreate(BaseModel):
    name: str = Field(..., description="Friendly name for this credential set")
    project_id: str
    service_account_json: Optional[str] = None  # Full JSON content
    use_gcloud_cli: bool = Field(default=True, description="Use gcloud CLI authentication")
    description: Optional[str] = None
    is_primary: bool = Field(default=False)


class DatabaseConnectionCreate(BaseModel):
    name: str = Field(..., description="Friendly name for this connection")
    provider: CloudProvider
    db_type: DatabaseType
    host: str
    port: int
    username: str
    password: str
    database: str
    ssl_enabled: bool = True
    ssl_ca_cert: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_primary: bool = Field(default=False)


class OnboardingStepUpdate(BaseModel):
    step: str
    completed: bool = True
    data: Optional[Dict[str, Any]] = None


# Endpoints

@router.get("/status")
async def get_onboarding_status(
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Get current onboarding status."""
    return await credential_service.get_onboarding_status(db)


@router.post("/credentials/gcp")
async def create_gcp_credentials(
    credentials: GCPCredentialsCreate,
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Create GCP credentials for the application."""
    
    cred_data = {
        "project_id": credentials.project_id,
        "use_gcloud_cli": credentials.use_gcloud_cli
    }
    
    if credentials.service_account_json:
        cred_data["service_account_json"] = credentials.service_account_json
    
    try:
        credential = await credential_service.create_cloud_credential(
            db=db,
            name=credentials.name,
            provider=CloudProvider.GCP,
            credentials=cred_data,
            description=credentials.description,
            is_primary=credentials.is_primary
        )
        
        # Update onboarding step
        await credential_service.update_onboarding_step(
            db=db,
            step="gcp_credentials",
            completed=True,
            data={"credential_id": credential.id}
        )
        
        return {
            "id": credential.id,
            "name": credential.name,
            "provider": credential.provider.value,
            "is_primary": credential.is_primary,
            "message": "GCP credentials stored successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create GCP credentials: {str(e)}"
        )


@router.post("/connections/database")
async def create_database_connection(
    connection: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Create a database connection."""
    
    try:
        db_connection = await credential_service.create_database_connection(
            db=db,
            name=connection.name,
            provider=connection.provider,
            db_type=connection.db_type,
            host=connection.host,
            port=connection.port,
            username=connection.username,
            password=connection.password,
            database=connection.database,
            ssl_enabled=connection.ssl_enabled,
            ssl_ca_cert=connection.ssl_ca_cert,
            extra_params=connection.extra_params,
            description=connection.description,
            is_primary=connection.is_primary
        )
        
        # Update onboarding step based on provider
        step_name = f"{connection.provider.value}_database"
        await credential_service.update_onboarding_step(
            db=db,
            step=step_name,
            completed=True,
            data={"connection_id": db_connection.id}
        )
        
        return {
            "id": db_connection.id,
            "name": db_connection.name,
            "provider": db_connection.provider.value,
            "db_type": db_connection.db_type.value,
            "is_primary": db_connection.is_primary,
            "message": "Database connection stored successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create database connection: {str(e)}"
        )


@router.post("/quick-setup")
async def quick_setup(
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Quick setup using existing GCP and Digital Ocean credentials."""
    
    from cryptography.fernet import Fernet
    import sqlite3
    from datetime import datetime
    
    # Use sync SQLite for simplicity
    db_path = "./forgedata.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Example GCP credentials
        gcp_cred_data = {
            "project_id": "example-project",
            "use_gcloud_cli": True
        }
        
        cursor.execute("""
            INSERT INTO cloud_credentials 
            (name, provider, credentials_encrypted, is_active, is_primary, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Example GCP Project",
            "gcp",
            credential_service._encrypt_json(gcp_cred_data),
            1,
            1,
            "Primary GCP project using gcloud CLI authentication",
            datetime.now().isoformat()
        ))
        gcp_cred_id = cursor.lastrowid
        
        # Example GCP database connection
        cursor.execute("""
            INSERT INTO database_connections
            (name, provider, db_type, host, port, username_encrypted, password_encrypted, 
             database, ssl_enabled, is_active, is_primary, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Example GCP Database",
            "gcp",
            "postgresql",
            "example-instance.example.com",
            5432,
            credential_service._encrypt("example_user"),
            credential_service._encrypt("REPLACE_WITH_YOUR_PASSWORD"),
            "exampledb",
            0,
            1,
            1,
            "GCP Cloud SQL via Cloud SQL Proxy",
            datetime.now().isoformat()
        ))
        gcp_db_id = cursor.lastrowid
        
        # Example Digital Ocean database connection
        cursor.execute("""
            INSERT INTO database_connections
            (name, provider, db_type, host, port, username_encrypted, password_encrypted, 
             database, ssl_enabled, ssl_ca_cert, is_active, is_primary, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Example Digital Ocean Database",
            "digitalocean",
            "postgresql",
            "example-db.ondigitalocean.com",
            25060,
            credential_service._encrypt("example_admin"),
            credential_service._encrypt("REPLACE_WITH_YOUR_PASSWORD"),
            "defaultdb",
            1,
            None,
            1,
            1,
            "Digital Ocean Managed PostgreSQL - Example",
            datetime.now().isoformat()
        ))
        do_db_id = cursor.lastrowid
        
        # Onboarding status
        for step, step_id in [
            ("gcp_credentials", gcp_cred_id),
            ("gcp_database", gcp_db_id),
            ("digitalocean_database", do_db_id),
            ("onboarding_complete", 1)
        ]:
            cursor.execute("""
                INSERT OR REPLACE INTO onboarding_status
                (step, completed, completed_at, created_at)
                VALUES (?, ?, ?, ?)
            """, (step, 1, datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        
        return {
            "message": "Quick setup completed successfully",
            "gcp_credential_id": gcp_cred_id,
            "gcp_database_id": gcp_db_id,
            "digitalocean_database_id": do_db_id,
            "onboarding_complete": True
        }
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Setup failed: {str(e)}"
        )
    finally:
        conn.close()


@router.get("/credentials")
async def list_all_credentials(
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """List all stored credentials (cloud and database)."""
    
    cloud_creds = await credential_service.list_cloud_credentials(db)
    db_connections = await credential_service.list_database_connections(db)
    
    return {
        "cloud_credentials": cloud_creds,
        "database_connections": db_connections
    }


@router.get("/connections/database/{connection_id}")
async def get_database_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Get a specific database connection (with credentials masked in response)."""
    
    connection = await credential_service.get_database_connection(db, connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found"
        )
    
    # Mask password in response
    connection["password"] = "********"
    return connection


@router.get("/connections/database/{connection_id}/connection-string")
async def get_connection_string(
    connection_id: int,
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Get full connection string for a database connection."""
    
    conn_string = await credential_service.get_connection_string(db, connection_id)
    if not conn_string:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found"
        )
    
    return {"connection_string": conn_string}


@router.post("/steps/{step}/complete")
async def complete_onboarding_step(
    step: str,
    update: OnboardingStepUpdate,
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """Mark an onboarding step as complete."""
    
    status = await credential_service.update_onboarding_step(
        db=db,
        step=step,
        completed=update.completed,
        data=update.data
    )
    
    return {
        "step": status.step,
        "completed": status.completed,
        "completed_at": status.completed_at
    }


# Additional endpoints for UI
@router.get("/cloud-credentials")
async def list_cloud_credentials(
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """List all cloud credentials."""
    credentials = await credential_service.list_cloud_credentials(db)
    return credentials


@router.get("/database-connections")
async def list_database_connections(
    db: Session = Depends(get_db),
    credential_service: CredentialService = Depends(get_credential_service)
):
    """List all database connections."""
    connections = await credential_service.list_database_connections(db)
    return connections
