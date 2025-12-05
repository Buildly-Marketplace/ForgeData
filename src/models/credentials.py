"""Database models for cloud credentials and connections."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from src.core.database import Base


class CloudProvider(str, enum.Enum):
    """Supported cloud providers."""
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"
    AWS = "aws"
    AZURE = "azure"


class DatabaseType(str, enum.Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class CloudCredential(Base):
    """Store encrypted cloud provider credentials."""
    
    __tablename__ = "cloud_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(Enum(CloudProvider), nullable=False)
    
    # Encrypted fields (encrypted with app secret key)
    credentials_encrypted = Column(Text, nullable=False)  # JSON encrypted credentials
    
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # One primary per provider
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata
    description = Column(String(255), nullable=True)
    created_by = Column(String(100), nullable=True)


class DatabaseConnection(Base):
    """Store database connection strings."""
    
    __tablename__ = "database_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(Enum(CloudProvider), nullable=False)
    db_type = Column(Enum(DatabaseType), nullable=False)
    
    # Connection details (encrypted)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username_encrypted = Column(Text, nullable=False)
    password_encrypted = Column(Text, nullable=False)
    database = Column(String(100), nullable=False)
    
    # SSL settings
    ssl_enabled = Column(Boolean, default=True)
    ssl_ca_cert = Column(Text, nullable=True)  # CA certificate content
    
    # Additional connection params (JSON encrypted)
    extra_params_encrypted = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata
    description = Column(String(255), nullable=True)
    created_by = Column(String(100), nullable=True)


class OnboardingStatus(Base):
    """Track onboarding completion status."""
    
    __tablename__ = "onboarding_status"
    
    id = Column(Integer, primary_key=True)
    step = Column(String(50), unique=True, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    data = Column(Text, nullable=True)  # JSON data for the step
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
