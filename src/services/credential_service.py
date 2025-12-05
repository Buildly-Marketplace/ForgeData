"""Service for managing cloud credentials and database connections."""

import json
from typing import Optional, List, Dict, Any
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.credentials import (
    CloudCredential, 
    DatabaseConnection, 
    OnboardingStatus,
    CloudProvider,
    DatabaseType
)


class CredentialService:
    """Handles encryption/decryption and CRUD for credentials."""
    
    def __init__(self, encryption_key: str):
        """Initialize with encryption key."""
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def _encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def _encrypt_json(self, data: dict) -> str:
        """Encrypt JSON data."""
        return self._encrypt(json.dumps(data))
    
    def _decrypt_json(self, encrypted_data: str) -> dict:
        """Decrypt JSON data."""
        return json.loads(self._decrypt(encrypted_data))
    
    # Cloud Credentials
    
    async def create_cloud_credential(
        self,
        db: Session,
        name: str,
        provider: CloudProvider,
        credentials: dict,
        description: str = None,
        created_by: str = None,
        is_primary: bool = False
    ) -> CloudCredential:
        """Create new cloud credential."""
        
        # If setting as primary, unset other primary credentials for this provider
        if is_primary:
            stmt = select(CloudCredential).where(
                CloudCredential.provider == provider,
                CloudCredential.is_primary == True
            )
            result = await db.execute(stmt)
            existing_primary = result.scalars().all()
            for cred in existing_primary:
                cred.is_primary = False
        
        credential = CloudCredential(
            name=name,
            provider=provider,
            credentials_encrypted=self._encrypt_json(credentials),
            description=description,
            created_by=created_by,
            is_primary=is_primary
        )
        
        db.add(credential)
        db.commit()
        db.refresh(credential)
        return credential
    
    async def get_cloud_credential(self, db: AsyncSession, credential_id: int) -> Optional[Dict[str, Any]]:
        """Get cloud credential by ID with decrypted data."""
        stmt = select(CloudCredential).where(CloudCredential.id == credential_id)
        result = await db.execute(stmt)
        credential = result.scalar_one_or_none()
        
        if not credential:
            return None
        
        return {
            "id": credential.id,
            "name": credential.name,
            "provider": credential.provider.value,
            "credentials": self._decrypt_json(credential.credentials_encrypted),
            "is_active": credential.is_active,
            "is_primary": credential.is_primary,
            "description": credential.description,
            "created_at": credential.created_at,
            "updated_at": credential.updated_at
        }
    
    async def get_primary_cloud_credential(self, db: AsyncSession, provider: CloudProvider) -> Optional[Dict[str, Any]]:
        """Get primary cloud credential for a provider."""
        stmt = select(CloudCredential).where(
            CloudCredential.provider == provider,
            CloudCredential.is_primary == True,
            CloudCredential.is_active == True
        )
        result = await db.execute(stmt)
        credential = result.scalar_one_or_none()
        
        if not credential:
            return None
        
        return {
            "id": credential.id,
            "name": credential.name,
            "provider": credential.provider.value,
            "credentials": self._decrypt_json(credential.credentials_encrypted),
            "is_active": credential.is_active,
            "is_primary": credential.is_primary,
            "description": credential.description
        }
    
    async def list_cloud_credentials(self, db: AsyncSession, provider: Optional[CloudProvider] = None) -> List[Dict[str, Any]]:
        """List all cloud credentials (without decrypted data)."""
        stmt = select(CloudCredential)
        if provider:
            stmt = stmt.where(CloudCredential.provider == provider)
        
        result = await db.execute(stmt)
        credentials = result.scalars().all()
        
        return [
            {
                "id": cred.id,
                "name": cred.name,
                "provider": cred.provider.value,
                "is_active": cred.is_active,
                "is_primary": cred.is_primary,
                "description": cred.description,
                "created_at": cred.created_at
            }
            for cred in credentials
        ]
    
    # Database Connections
    
    async def create_database_connection(
        self,
        db: Session,
        name: str,
        provider: CloudProvider,
        db_type: DatabaseType,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        ssl_enabled: bool = True,
        ssl_ca_cert: str = None,
        extra_params: dict = None,
        description: str = None,
        created_by: str = None,
        is_primary: bool = False
    ) -> DatabaseConnection:
        """Create new database connection."""
        
        # If setting as primary, unset other primary connections for this provider
        if is_primary:
            stmt = select(DatabaseConnection).where(
                DatabaseConnection.provider == provider,
                DatabaseConnection.is_primary == True
            )
            result = await db.execute(stmt)
            existing_primary = result.scalars().all()
            for conn in existing_primary:
                conn.is_primary = False
        
        connection = DatabaseConnection(
            name=name,
            provider=provider,
            db_type=db_type,
            host=host,
            port=port,
            username_encrypted=self._encrypt(username),
            password_encrypted=self._encrypt(password),
            database=database,
            ssl_enabled=ssl_enabled,
            ssl_ca_cert=ssl_ca_cert,
            extra_params_encrypted=self._encrypt_json(extra_params) if extra_params else None,
            description=description,
            created_by=created_by,
            is_primary=is_primary
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection
    
    async def get_database_connection(self, db: AsyncSession, connection_id: int) -> Optional[Dict[str, Any]]:
        """Get database connection by ID with decrypted credentials."""
        stmt = select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
        result = await db.execute(stmt)
        connection = result.scalar_one_or_none()
        
        if not connection:
            return None
        
        return {
            "id": connection.id,
            "name": connection.name,
            "provider": connection.provider.value,
            "db_type": connection.db_type.value,
            "host": connection.host,
            "port": connection.port,
            "username": self._decrypt(connection.username_encrypted),
            "password": self._decrypt(connection.password_encrypted),
            "database": connection.database,
            "ssl_enabled": connection.ssl_enabled,
            "ssl_ca_cert": connection.ssl_ca_cert,
            "extra_params": self._decrypt_json(connection.extra_params_encrypted) if connection.extra_params_encrypted else {},
            "is_active": connection.is_active,
            "is_primary": connection.is_primary,
            "description": connection.description,
            "created_at": connection.created_at,
            "updated_at": connection.updated_at
        }
    
    async def get_connection_string(self, db: AsyncSession, connection_id: int) -> Optional[str]:
        """Get full connection string for a database connection."""
        conn_data = await self.get_database_connection(db, connection_id)
        if not conn_data:
            return None
        
        ssl_param = "?sslmode=require" if conn_data["ssl_enabled"] else ""
        
        return (
            f"{conn_data['db_type']}://{conn_data['username']}:{conn_data['password']}"
            f"@{conn_data['host']}:{conn_data['port']}/{conn_data['database']}{ssl_param}"
        )
    
    async def get_primary_database_connection(self, db: AsyncSession, provider: CloudProvider) -> Optional[Dict[str, Any]]:
        """Get primary database connection for a provider."""
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.provider == provider,
            DatabaseConnection.is_primary == True,
            DatabaseConnection.is_active == True
        )
        result = await db.execute(stmt)
        connection = result.scalar_one_or_none()
        
        if not connection:
            return None
        
        return await self.get_database_connection(db, connection.id)
    
    async def list_database_connections(
        self, 
        db: Session, 
        provider: Optional[CloudProvider] = None,
        db_type: Optional[DatabaseType] = None
    ) -> List[Dict[str, Any]]:
        """List all database connections (without decrypted passwords)."""
        stmt = select(DatabaseConnection)
        if provider:
            stmt = stmt.where(DatabaseConnection.provider == provider)
        if db_type:
            stmt = stmt.where(DatabaseConnection.db_type == db_type)
        
        result = await db.execute(stmt)
        connections = result.scalars().all()
        
        return [
            {
                "id": conn.id,
                "name": conn.name,
                "provider": conn.provider.value,
                "db_type": conn.db_type.value,
                "host": conn.host,
                "port": conn.port,
                "database": conn.database,
                "ssl_enabled": conn.ssl_enabled,
                "is_active": conn.is_active,
                "is_primary": conn.is_primary,
                "description": conn.description,
                "created_at": conn.created_at
            }
            for conn in connections
        ]
    
    # Onboarding Status
    
    async def update_onboarding_step(
        self, 
        db: Session, 
        step: str, 
        completed: bool = True, 
        data: dict = None
    ) -> OnboardingStatus:
        """Update onboarding step status."""
        stmt = select(OnboardingStatus).where(OnboardingStatus.step == step)
        result = await db.execute(stmt)
        status = result.scalar_one_or_none()
        
        if not status:
            status = OnboardingStatus(step=step)
            db.add(status)
        
        status.completed = completed
        if completed:
            from datetime import datetime
            status.completed_at = datetime.now()
        if data:
            status.data = json.dumps(data)
        
        db.commit()
        db.refresh(status)
        return status
    
    async def get_onboarding_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get overall onboarding status."""
        stmt = select(OnboardingStatus)
        result = await db.execute(stmt)
        steps = result.scalars().all()
        
        return {
            "steps": {
                step.step: {
                    "completed": step.completed,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "data": json.loads(step.data) if step.data else None
                }
                for step in steps
            },
            "is_complete": all(step.completed for step in steps) if steps else False
        }
